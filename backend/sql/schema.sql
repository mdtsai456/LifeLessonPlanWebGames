-- LifeLessonPlan_test.Game definition

CREATE TABLE `Game` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `game_code` varchar(50) NOT NULL,
  `game_name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_game_code` (`game_code`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameMaterial definition

CREATE TABLE `GameMaterial` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `material_code` varchar(100) NOT NULL,
  `material_name` varchar(150) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_game_material_code` (`material_code`)
) ENGINE=InnoDB AUTO_INCREMENT=197 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameWorkflowDefault definition

CREATE TABLE `GameWorkflowDefault` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `json_path` varchar(500) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.Tag definition

CREATE TABLE `Tag` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `tag_code` varchar(100) NOT NULL,
  `tag_name` varchar(150) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tag_code` (`tag_code`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.Teacher definition

CREATE TABLE `Teacher` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_teacher_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameMaterialDefault definition

CREATE TABLE `GameMaterialDefault` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `game_id` bigint(20) unsigned NOT NULL,
  `json_path` varchar(500) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_game_material_default_game_id` (`game_id`),
  CONSTRAINT `fk_game_material_default_game` FOREIGN KEY (`game_id`) REFERENCES `Game` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameMaterialTag definition

CREATE TABLE `GameMaterialTag` (
  `game_material_id` bigint(20) unsigned NOT NULL,
  `tag_id` bigint(20) unsigned NOT NULL,
  PRIMARY KEY (`game_material_id`,`tag_id`),
  KEY `idx_game_material_tag_tag_id` (`tag_id`),
  CONSTRAINT `fk_game_material_tag_material` FOREIGN KEY (`game_material_id`) REFERENCES `GameMaterial` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_material_tag_tag` FOREIGN KEY (`tag_id`) REFERENCES `Tag` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameTag definition

CREATE TABLE `GameTag` (
  `game_id` bigint(20) unsigned NOT NULL,
  `tag_id` bigint(20) unsigned NOT NULL,
  PRIMARY KEY (`game_id`,`tag_id`),
  KEY `idx_game_tag_tag_id` (`tag_id`),
  CONSTRAINT `fk_game_tag_game` FOREIGN KEY (`game_id`) REFERENCES `Game` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_game_tag_tag` FOREIGN KEY (`tag_id`) REFERENCES `Tag` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.Student definition

CREATE TABLE `Student` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `teacher_id` bigint(20) unsigned NOT NULL,
  `username` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_student_username` (`username`),
  UNIQUE KEY `uk_student_id_teacher_id` (`id`,`teacher_id`),
  KEY `fk_student_teacher` (`teacher_id`),
  CONSTRAINT `fk_student_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `Teacher` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=87 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameMaterialCustomization definition

CREATE TABLE `GameMaterialCustomization` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `teacher_id` bigint(20) unsigned NOT NULL,
  `student_id` bigint(20) unsigned NOT NULL,
  `game_id` bigint(20) unsigned NOT NULL,
  `json_path` varchar(500) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_material_customization_game_id` (`game_id`),
  KEY `fk_material_customization_student_teacher` (`student_id`,`teacher_id`),
  KEY `fk_material_customization_teacher` (`teacher_id`),
  CONSTRAINT `fk_material_customization_game` FOREIGN KEY (`game_id`) REFERENCES `Game` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_material_customization_student_teacher` FOREIGN KEY (`student_id`, `teacher_id`) REFERENCES `Student` (`id`, `teacher_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_material_customization_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `Teacher` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- LifeLessonPlan_test.GameWorkflowCustomization definition

CREATE TABLE `GameWorkflowCustomization` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `teacher_id` bigint(20) unsigned NOT NULL,
  `student_id` bigint(20) unsigned NOT NULL,
  `json_path` varchar(500) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workflow_teacher_student` (`teacher_id`,`student_id`),
  KEY `fk_workflow_student_teacher` (`student_id`,`teacher_id`),
  CONSTRAINT `fk_workflow_student_teacher` FOREIGN KEY (`student_id`, `teacher_id`) REFERENCES `Student` (`id`, `teacher_id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_workflow_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `Teacher` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=128 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;