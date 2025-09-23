/* 创建数据库 fastapi */
CREATE DATABASE IF NOT EXISTS `fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

/* 打开数据库 fastapi */
USE `fastapi`;

/* 创建telegram管理用户表 */
DROP TABLE IF EXISTS `telegram_users`;
CREATE TABLE IF NOT EXISTS `telegram_users` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `is_admin` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '管理员标识：0-普通用户, 1-管理员',
    `status` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '状态：0-失效, 1-正常',
    `chat_id` BIGINT NOT NULL COMMENT 'Telegram聊天ID',
    UNIQUE KEY `uniq_username` (`username`),
    UNIQUE KEY `uniq_chat_id` (`chat_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'telegram管理用户表' ROW_FORMAT = DYNAMIC;

/* 插入初始数据 */
/* 管理员用户 */
INSERT INTO `telegram_users` (`username`, `is_admin`, `status`, `chat_id`) VALUES ('admin', 1, 1, 5312177749);

/* 测试用户 */
INSERT INTO `telegram_users` (`username`, `is_admin`, `status`, `chat_id`) VALUES ('测试', 0, 1, -4944286056);