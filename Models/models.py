#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : models.py
# @Time      : 2025/9/16 13:35
# @IDE       : PyCharm
# @Function  :
# 假设你的 Base 和 User 模型定义如下：
import random
import uuid

from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy import Index

from sqlalchemy.orm import sessionmaker

# 这里的 Base 和 User 模型与你提供的相同
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    # id = Column(Integer, autoincrement=True,primary_key=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, comment="用户名")
    email = Column(String(100), unique=True, index=True, comment="邮箱")
    hashed_password = Column(String(255), comment="哈希密码")
    is_active = Column(TINYINT, default=1, comment="1:激活, 0:禁用")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                        comment="更新时间")

    # 创建一个名为 'idx_username_email' 的组合索引，包含 username 和 email
    __table_args__ = (
        Index('idx_username_email', "username", "email"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# 定义数据库连接字符串
# 请根据你的实际情况修改用户名、密码、主机、端口和数据库名
DATABASE_URL = "mysql+pymysql://root:He800407@localhost:3306/test"
# DATABASE_URL = "mysql+aiomysql://root:He800407@localhost:3306/test"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables_if_not_exist():
    """
    检查数据库中 'users' 表是否存在。
    如果不存在，则创建它。
    """
    # 检查表是否存在
    if not engine.dialect.has_table(connection=engine.connect(), table_name="users"):
        print("表 'users' 不存在，开始创建...")
        # 调用 Base.metadata.create_all() 来创建所有由 Base 声明的表
        Base.metadata.create_all(bind=engine)
        print("表 'users' 创建成功！")
    else:
        print("表 'users' 已存在。")


def bulk_create_test_users(count=100):
    db = SessionLocal()
    try:
        # 生成用户列表
        users_to_add = []
        for i in range(count):
            username = uuid.uuid4().hex

            users_to_add.append(
                User(
                    username=username,  # 生成一个随机用户名
                    email=f"{username}@example.com",
                    hashed_password=f"hashed_password_{username}",
                    is_active=random.choice([0, 1])
                )
            )

        # 批量添加并提交
        db.bulk_save_objects(users_to_add)
        db.commit()
        print(f"成功创建了 {count} 个测试用户。")

    except Exception as e:
        db.rollback()
        print(f"批量创建用户失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print(uuid.uuid4().hex[:10])
    create_tables_if_not_exist()
    bulk_create_test_users()
