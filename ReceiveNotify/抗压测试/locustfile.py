import uuid

import requests
import threading
import time
import json
import random

# 要测试的 API 主机地址
API_HOST = "https://notify.king-sms.com"

# 要测试的所有路由列表
ROUTES = [
    "/global_pay_in_notify",
    "/global_pay_out_notify",
    "/global_refund_notify"
]

# 并发线程数
NUM_THREADS = 200

# 用于统计结果的全局变量，使用锁来确保线程安全
success_count = 0
failure_count = 0
lock = threading.Lock()


def send_request():
    """
    单个线程发送 POST 请求的函数
    """
    global success_count, failure_count

    # 随机选择一个路由
    route = random.choice(ROUTES)
    api_url = f"{API_HOST}{route}"

    # 准备一个随机的 JSON payload
    payload = {
        "state": 1,
        "sysOrderNo": 'sys-' + uuid.uuid4().hex,
        "mchOrderNo": 'mch-' + uuid.uuid4().hex,
        "amount": random.randint(100, 10000),
        "sign": uuid.uuid4().hex
    }

    # 定义请求头
    headers = {'Content-Type': 'application/json'}

    try:
        # 发送 POST 请求
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)

        # 检查响应状态码，200 表示成功
        if response.status_code == 200:
            with lock:
                success_count += 1
            print(f"请求 {route} 成功！状态码：{response.status_code}")
        else:
            with lock:
                failure_count += 1
            print(f"请求 {route} 失败！状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        with lock:
            failure_count += 1
        print(f"请求 {route} 时发生错误：{e}")


def run_stress_test():
    """
    主函数，创建并启动多线程
    """
    print(f"开始压力测试，将创建 {NUM_THREADS} 个线程...")
    threads = []
    start_time = time.time()

    # 创建线程
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=send_request)
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    end_time = time.time()
    total_time = end_time - start_time

    print("-" * 30)
    print("多路由压力测试完成！")
    print(f"总请求数：{NUM_THREADS}")
    print(f"成功请求：{success_count}")
    print(f"失败请求：{failure_count}")
    print(f"失败率：{((failure_count / NUM_THREADS) * 100):.2f}%")
    print(f"总耗时：{total_time:.2f} 秒")
    print(f"每秒请求数 (RPS)：{NUM_THREADS / total_time:.2f} 请求/秒")
    print("-" * 30)


if __name__ == "__main__":
    run_stress_test()
