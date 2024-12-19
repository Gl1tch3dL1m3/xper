-- --------------------------------------------------------
-- Hostiteľ:                     129.80.149.56
-- Verze serveru:                8.0.40-0ubuntu0.20.04.1 - (Ubuntu)
-- OS serveru:                   Linux
-- HeidiSQL Verzia:              12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Exportování struktury databáze pro
CREATE DATABASE IF NOT EXISTS `s150071_main` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `s150071_main`;

-- Exportování struktury pro tabulka s150071_main.blacklist
CREATE TABLE IF NOT EXISTS `blacklist` (
  `server_id` bigint DEFAULT NULL,
  `item` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Export dat nebyl vybrán.

-- Exportování struktury pro tabulka s150071_main.boosters
CREATE TABLE IF NOT EXISTS `boosters` (
  `server_id` bigint DEFAULT NULL,
  `item` bigint DEFAULT NULL,
  `rate` tinyint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Export dat nebyl vybrán.

-- Exportování struktury pro tabulka s150071_main.rewards
CREATE TABLE IF NOT EXISTS `rewards` (
  `server_id` bigint DEFAULT NULL,
  `item` bigint DEFAULT NULL,
  `req_level` smallint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Export dat nebyl vybrán.

-- Exportování struktury pro tabulka s150071_main.servers
CREATE TABLE IF NOT EXISTS `servers` (
  `server_id` bigint DEFAULT NULL,
  `is_enabled` tinyint DEFAULT NULL,
  `level_up_channel` bigint DEFAULT NULL,
  `level_up_message` tinytext,
  `antispam` tinyint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Export dat nebyl vybrán.

-- Exportování struktury pro tabulka s150071_main.users
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` bigint DEFAULT NULL,
  `server_id` bigint DEFAULT NULL,
  `xp` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Export dat nebyl vybrán.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
