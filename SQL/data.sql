/* 创建数据库 fastapi */
CREATE DATABASE IF NOT EXISTS `fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/* 打开数据库 fastapi */
USE `fastapi`;

/* 创建telegram管理用户表 */
DROP TABLE IF EXISTS `telegram_users`;
CREATE TABLE IF NOT EXISTS `telegram_users` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `user_id` bigint(20) NOT NULL COMMENT '用户ID',
    `username` varchar(50) NOT NULL COMMENT '用户名',
    `chat_id` bigint(20) NOT NULL COMMENT '聊天ID'
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'telegram管理用户表' ROW_FORMAT = DYNAMIC;

