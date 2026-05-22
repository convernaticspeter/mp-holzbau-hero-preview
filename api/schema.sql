CREATE TABLE IF NOT EXISTS lead_queue (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uuid CHAR(36) NOT NULL UNIQUE,
  source VARCHAR(120) NOT NULL,
  payload_json JSON NOT NULL,
  status ENUM('pending','delivered','failed') NOT NULL DEFAULT 'pending',
  attempts INT UNSIGNED NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  leadtable_response TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  delivered_at DATETIME NULL,
  INDEX idx_status_attempts_created (status, attempts, created_at),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lead_submission_audit (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uuid CHAR(36) NOT NULL UNIQUE,
  source VARCHAR(120) NOT NULL DEFAULT '',
  raw_body MEDIUMTEXT NOT NULL,
  payload_json JSON NULL,
  status ENUM('received','queued','delivered','failed','rejected','honeypot') NOT NULL DEFAULT 'received',
  error_code VARCHAR(160) NULL,
  lead_queue_uuid CHAR(36) NULL,
  client_ip_hash CHAR(64) NULL,
  user_agent TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_audit_status_created (status, created_at),
  INDEX idx_audit_lead_queue_uuid (lead_queue_uuid),
  INDEX idx_audit_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS lead_rate_limits (
  ip_hash CHAR(64) NOT NULL PRIMARY KEY,
  window_start DATETIME NOT NULL,
  request_count INT UNSIGNED NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_window_start (window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

CREATE TABLE IF NOT EXISTS google_ads_conversion_uploads (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uuid CHAR(36) NOT NULL UNIQUE,
  lead_queue_uuid CHAR(36) NOT NULL,
  source VARCHAR(120) NOT NULL DEFAULT '',
  click_id_type ENUM('gclid','gbraid','wbraid') NOT NULL,
  click_id_value VARCHAR(255) NOT NULL,
  conversion_action_resource VARCHAR(160) NOT NULL,
  conversion_value DECIMAL(10,2) NOT NULL DEFAULT 400.00,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',
  order_id VARCHAR(80) NOT NULL,
  consent_state VARCHAR(40) NOT NULL DEFAULT 'unset',
  status ENUM('pending','uploaded','failed','skipped') NOT NULL DEFAULT 'pending',
  attempts INT UNSIGNED NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  request_json JSON NULL,
  response_json JSON NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  uploaded_at DATETIME NULL,
  UNIQUE KEY uniq_lead_queue_uuid (lead_queue_uuid),
  INDEX idx_gads_status_attempts_created (status, attempts, created_at),
  INDEX idx_gads_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
