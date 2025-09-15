import asyncio
import aioredis
import aiomysql


class AsyncDataHandler:
    """
    一个用于异步处理 Redis 和 MySQL 数据库操作的类。
    """

    def __init__(self, redis_config, mysql_config):
        self.redis_config = redis_config
        self.mysql_config = mysql_config
        self.redis_pool = None
        self.mysql_pool = None

    async def initialize(self):
        """
        异步初始化数据库连接池。
        """
        print("正在初始化 Redis 和 MySQL 连接池...")
        self.redis_pool = await aioredis.create_pool(
            (self.redis_config['host'], self.redis_config['port']),
            password=self.redis_config.get('password'),
            db=self.redis_config.get('db', 0)
        )

        self.mysql_pool = await aiomysql.create_pool(
            host=self.mysql_config['host'],
            port=self.mysql_config['port'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            db=self.mysql_config['db'],
            autocommit=True,  # 确保事务自动提交
            loop=asyncio.get_event_loop()
        )
        print("连接池初始化成功！")

    async def close(self):
        """
        异步关闭数据库连接池。
        """
        if self.redis_pool:
            self.redis_pool.close()
            await self.redis_pool.wait_closed()
            print("Redis 连接池已关闭。")

        if self.mysql_pool:
            self.mysql_pool.close()
            await self.mysql_pool.wait_closed()
            print("MySQL 连接池已关闭。")

    # --- Redis 操作 ---
    async def set_redis_value(self, key, value):
        """
        异步设置 Redis 键值对。
        """
        async with self.redis_pool.get() as conn:
            await conn.set(key, value)
            print(f"成功设置 Redis 键 '{key}'。")

    async def get_redis_value(self, key):
        """
        异步获取 Redis 键的值。
        """
        async with self.redis_pool.get() as conn:
            value = await conn.get(key, encoding='utf-8')
            print(f"成功获取 Redis 键 '{key}' 的值。")
            return value

    # --- MySQL 操作 ---
    async def insert_mysql_record(self, table, data):
        """
        异步向 MySQL 插入一条记录。
        """
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({values})"

        async with self.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(sql, list(data.values()))
                    print(f"成功向表 '{table}' 插入一条记录。")
                except Exception as e:
                    print(f"插入数据失败：{e}")

    async def fetch_mysql_record(self, table, conditions=None):
        """
        异步从 MySQL 查询记录。
        """
        sql = f"SELECT * FROM {table}"
        params = None
        if conditions:
            where_clauses = [f"{k} = %s" for k in conditions.keys()]
            sql += " WHERE " + " AND ".join(where_clauses)
            params = list(conditions.values())

        async with self.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:  # 使用 DictCursor 返回字典格式结果
                await cur.execute(sql, params)
                records = await cur.fetchall()
                print(f"成功从表 '{table}' 查询到 {len(records)} 条记录。")
                return records