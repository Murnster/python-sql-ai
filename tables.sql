-- games
CREATE TABLE `games` (
  `game_id` int NOT NULL AUTO_INCREMENT,
  `status` varchar(50) DEFAULT NULL,
  `season` int DEFAULT NULL,
  `week` int DEFAULT NULL,
  `week_day` varchar(10) DEFAULT NULL,
  `event_date` date DEFAULT NULL,
  `team_identifier_winner` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `team_city_name_winner` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `nfl_team_name_winner` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `team_identifier_loser` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `team_city_name_loser` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `nfl_team_name_loser` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `location_winner` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `location_loser` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `score_winner` int DEFAULT NULL,
  `score_loser` int DEFAULT NULL,
  `boxscore_stats_link` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  PRIMARY KEY (`game_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6733 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

-- game_stats
CREATE TABLE `game_stats` (
	`stat_id` int NOT NULL AUTO_INCREMENT,
	`game_id` int NOT NULL,
	`season` int DEFAULT NULL,
	`event_date` date DEFAULT NULL,
	`team_identifier` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
	`team_city_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
	`nfl_team_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
	`rushing_attempts` bigint DEFAULT NULL,
	`rushing_yards` bigint DEFAULT NULL,
	`rushing_touchdowns` bigint DEFAULT NULL,
	`passing_completions` bigint DEFAULT NULL,
	`passing_attempts` bigint DEFAULT NULL,
	`passing_completion_percentage` double DEFAULT NULL,
	`passing_yards` bigint DEFAULT NULL,
	`passing_touchdowns` bigint DEFAULT NULL,
	`passing_interceptions` bigint DEFAULT NULL,
	`passer_rating` double DEFAULT NULL,
	`net_passing_yards` bigint DEFAULT NULL,
	`total_yards` bigint DEFAULT NULL,
	`times_sacked` bigint DEFAULT NULL,
	`yards_sacked_for` bigint DEFAULT NULL,
	`fumbles` bigint DEFAULT NULL,
	`fumbles_lost` bigint DEFAULT NULL,
	`turnovers` bigint DEFAULT NULL,
	`penalties` bigint DEFAULT NULL,
	`penalty_yards` bigint DEFAULT NULL,
	`first_downs` bigint DEFAULT NULL,
	`third_down_conversions` bigint DEFAULT NULL,
	`third_down_attempts` bigint DEFAULT NULL,
	`third_down_conversion_percentage` double DEFAULT NULL,
	`fourth_down_conversions` bigint DEFAULT NULL,
	`fourth_down_attempts` bigint DEFAULT NULL,
	`fourth_down_conversion_percentage` double DEFAULT NULL,
	`time_of_possession` bigint DEFAULT NULL,
	`boxscore_stats_link` text,
	PRIMARY KEY (`stat_id`),
	KEY `fk_game_stats_game` (`game_id`),
	CONSTRAINT `fk_game_stats_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13461 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci