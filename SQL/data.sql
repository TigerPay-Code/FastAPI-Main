/* 创建数据库 fastapi */
CREATE DATABASE IF NOT EXISTS `fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/* 打开数据库 fastapi */
USE `fastapi`;

/* 创建telegram管理用户表 */
DROP TABLE IF EXISTS `telegram_users`;
CREATE TABLE IF NOT EXISTS `telegram_users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键ID',
    `username` VARCHAR(50) NOT NULL COMMENT 'Telegram用户名（唯一）',
    `is_admin` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '管理员身份：0-普通用户, 1-管理员',
    `user_type` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '用户类型：1-普通用户, 2-机器人, 3-群组',
    `user_role` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '用户角色：1-上游, 2-下游, 3-官方账号',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '状态：0-禁用, 1-启用',
    `chat_id` BIGINT NOT NULL COMMENT 'Telegram聊天ID（唯一）',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    UNIQUE KEY `uniq_username` (`username`),
    UNIQUE KEY `uniq_chat_id` (`chat_id`),
    KEY `idx_user_role` (`user_role`) COMMENT '加速角色查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='Telegram用户管理表（存储用户/机器人/群组信息）';

/* 插入初始数据 */
/* 管理员用户 */
INSERT INTO `telegram_users` (`username`, `is_admin`, `nature`, `attribute`, `status`, `chat_id`) VALUES ('modaohuohuo', 1, 1, 3, 1, 5312177749);

/* 测试群组 */
INSERT INTO `telegram_users` (`username`, `is_admin`, `nature`, `attribute`, `status`, `chat_id`) VALUES ('FastAPI服务', 0, 3, 3, 1, -4944286056);