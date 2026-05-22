CREATE TABLE IF NOT EXISTS form_step_audit (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uuid CHAR(36) NOT NULL UNIQUE,
  session_uuid CHAR(36) NOT NULL,
  source VARCHAR(120) NOT NULL DEFAULT '',
  event_name VARCHAR(80) NOT NULL DEFAULT '',
  step_number TINYINT UNSIGNED NULL,
  step_label VARCHAR(160) NULL,
  payload_json JSON NULL,
  client_ip_hash CHAR(64) NULL,
  user_agent TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_step_session_created (session_uuid, created_at),
  INDEX idx_step_source_created (source, created_at),
  INDEX idx_step_event_created (event_name, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
