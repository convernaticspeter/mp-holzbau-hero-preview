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
