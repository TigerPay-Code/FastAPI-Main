# -*- coding: utf-8 -*-
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json
from Logger.logger_config import setup_logger


import os
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)


# 添加IP格式验证辅助函数
def is_valid_ip(ip):
    """验证IP地址格式是否有效"""
    try:
        # IPv4验证
        if '.' in ip:
            parts = list(map(int, ip.split('.')))
            return len(parts) == 4 and all(0 <= p <= 255 for p in parts)
        # IPv6验证（简化版）
        elif ':' in ip:
            parts = ip.split(':')
            return len(parts) <= 8 and all(0 <= int(part, 16) <= 65535 for part in parts if part)
        return False
    except (ValueError, TypeError):
        return False


def get_real_ip(request):
    try:
        # 优先从X-Forwarded-For获取（可能包含多个代理IP）
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for and isinstance(x_forwarded_for, str):
            # 取第一个有效IP（排除可能的空白字符）
            real_ip = x_forwarded_for.split(',')[0].strip()
            if real_ip and is_valid_ip(real_ip):
                return real_ip

        # 其次从X-Real-IP获取
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip and isinstance(x_real_ip, str):
            real_ip = x_real_ip.strip()
            if real_ip and is_valid_ip(real_ip):
                return real_ip

        # 最后从客户端连接信息获取
        if hasattr(request, 'client') and request.client:
            client_host = request.client.host
            if client_host and isinstance(client_host, str):
                real_ip = client_host.strip()
                if real_ip and is_valid_ip(real_ip):
                    return real_ip

        # 所有获取方式失败时返回默认值
        return "unknown"

    except Exception as e:
        # 记录异常但不中断程序
        logger.error(f"获取真实IP失败: {str(e)}")
        return "unknown"


class AccessMiddleware(BaseHTTPMiddleware):
    """
        支持 Redis 黑名单 + MySQL 封禁日志 + Telegram 告警 的安全中间件
        ---------------------------------------------------------------
        功能：
        1. 实时检测 IP 访问频率
        2. 达阈值自动封禁并记录日志
        3. Redis 黑名单自动过期解封
        4. Telegram 推送封禁告警
        5. MySQL 安全审计记录
    """
    def __init__(
        self,
        app: ASGIApp,
        db_pool: Pool,                # ✅ MySQL 异步连接池
        allow_origins=None,
        allow_credentials=True,
        allow_methods=None,
        allow_headers=None,
        blacklist_key="blacklist:ip",
        rate_key_prefix="reqcount:",
        threshold=100,      # 阈值：在 time_window 秒内允许的最大请求数
        time_window=60,     # 统计窗口时间
        ban_time=600,       # 封禁时长
        telegram_token=None,
        admin_chat_id=None,
        service_name="FastAPI Service",
    ):
        super().__init__(app)
        self.db_pool = db_pool
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]

        # Redis 键配置
        self.blacklist_key = blacklist_key
        self.rate_key_prefix = rate_key_prefix

        # 安全策略
        self.threshold = threshold
        self.time_window = time_window
        self.ban_time = ban_time

        # Telegram 告警
        self.telegram_token = telegram_token
        self.admin_chat_id = admin_chat_id
        self.service_name = service_name
        self.bot = Bot(token=self.telegram_token) if telegram_token and admin_chat_id else None
    async def load_blacklist(self):
        now = time.time()
        if now - self.last_refresh > self.refresh_interval:
            # 优先从 Redis 获取（如果存在）
            redis = ASYNC_DB.redis
            cache_key = "ip_blacklist:enabled"
            cached = await redis.get(cache_key)
            if cached:
                try:
                    self.blacklist = set(json.loads(cached))
                    self.last_refresh = now
                    return
                except Exception:
                    pass
            # 回退：从 MySQL 查询
            rows = await ASYNC_DB.mysql.fetchall("SELECT ip FROM ip_blacklist WHERE status=1")
            self.blacklist = {r["ip"] for r in rows}
            # 写入 Redis 缓存
            await redis.set(cache_key, list(self.blacklist), ex=60)
            self.last_refresh = now

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()  # 记录请求开始时间

        client_ip = get_real_ip(request)  # 获取访问者 IP
        if client_ip in self.blacklist_ip:
            print(f"⚠️ 拦截黑名单 IP：{client_ip}")
            return JSONResponse(status_code=403, content={
                "code": 403,
                "msg": f"你的 IP {client_ip} 已被禁止访问"
            })

        # ---------------- Token 验证 ----------------
        token = request.headers.get("X-API-Token")
        if not token or token != self.api_token:
            print(f"🚫 Token 无效：{token}")
            return JSONResponse(status_code=401, content={
                "code": 401,
                "msg": "无效的 API Token"
            })

        # ---------------- 请求处理 + 异常捕获 ----------------
        try:
            response = await call_next(request)  # 调用后续路由或中间件
        except Exception as e:
            # 记录异常并返回统一格式
            print(f"❌ 处理请求 {request.url.path} 出错：{e}")
            return JSONResponse(status_code=500, content={
                "code": 500,
                "msg": f"服务器内部错误: {str(e)}"
            })

        # ---------------- 后置逻辑：统计耗时 ----------------
        duration = round((time.time() - start_time) * 1000, 2)  # ms
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "ip": client_ip,
            "status": response.status_code,
            "duration_ms": duration,
        }
        print("📊 请求日志：", json.dumps(log_data, ensure_ascii=False))


        path = request.url.path
        method = request.method

        # ---------------- IP 黑名单拦截 ----------------
        if client_ip in BLACKLIST_IP:
            print(f"⚠️ 拦截黑名单 IP：{client_ip}")
            return JSONResponse(status_code=403, content={
                "code": 403,
                "msg": f"你的 IP {client_ip} 已被禁止访问"
            })

        # ---------------- Token 验证 ----------------
        token = request.headers.get("X-API-Token")
        if not token or token != API_TOKEN:
            print(f"🚫 Token 无效：{token}")
            return JSONResponse(status_code=401, content={
                "code": 401,
                "msg": "无效的 API Token"
            })

        # ---------------- 请求处理 + 异常捕获 ----------------
        try:
            response = await call_next(request)  # 调用后续路由或中间件
        except Exception as e:
            # 记录异常并返回统一格式
            print(f"❌ 处理请求 {path} 出错：{e}")
            return JSONResponse(status_code=500, content={
                "code": 500,
                "msg": f"服务器内部错误: {str(e)}"
            })

        # ---------------- 后置逻辑：统计耗时 ----------------
        duration = round((time.time() - start_time) * 1000, 2)  # ms
        log_data = {
            "method": method,
            "path": path,
            "ip": client_ip,
            "status": response.status_code,
            "duration_ms": duration,
        }
        print("📊 请求日志：", json.dumps(log_data, ensure_ascii=False))

        # 在响应头中加入耗时信息
        response.headers["X-Process-Time"] = str(duration) + "ms"
        return response
