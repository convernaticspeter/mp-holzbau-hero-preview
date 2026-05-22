<?php
declare(strict_types=1);

class LeadHttpException extends RuntimeException
{
    public int $status;
    public array $body;

    public function __construct(int $status, array $body)
    {
        parent::__construct((string)($body['error'] ?? 'lead_http_error'));
        $this->status = $status;
        $this->body = $body;
    }
}

function lead_abort(int $status, array $body): void
{
    throw new LeadHttpException($status, $body);
}

function json_response(int $status, array $body): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function uuid_v4(): string
{
    $data = random_bytes(16);
    $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
    $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);
    return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
}

function get_client_ip(): string
{
    // Prefer REMOTE_ADDR. Don't trust X-Forwarded-For unless explicitly configured at server level.
    return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

function read_json_submission(): array
{
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        return ['ok' => false, 'status' => 204, 'body' => [], 'raw_body' => '', 'payload' => null];
    }
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        return ['ok' => false, 'status' => 405, 'body' => ['ok' => false, 'error' => 'method_not_allowed'], 'raw_body' => '', 'payload' => null];
    }

    $contentLength = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
    if ($contentLength > 51200) {
        $raw = file_get_contents('php://input') ?: '';
        return ['ok' => false, 'status' => 413, 'body' => ['ok' => false, 'error' => 'payload_too_large'], 'raw_body' => $raw, 'payload' => null];
    }

    $raw = file_get_contents('php://input') ?: '';
    $payload = json_decode($raw, true);
    if (!is_array($payload)) {
        return ['ok' => false, 'status' => 400, 'body' => ['ok' => false, 'error' => 'invalid_json'], 'raw_body' => $raw, 'payload' => null];
    }

    return ['ok' => true, 'status' => 200, 'body' => [], 'raw_body' => $raw, 'payload' => $payload];
}

function require_post_json(): array
{
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        json_response(204, []);
    }
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        json_response(405, ['ok' => false, 'error' => 'method_not_allowed']);
    }

    $contentLength = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
    if ($contentLength > 51200) {
        json_response(413, ['ok' => false, 'error' => 'payload_too_large']);
    }

    $raw = file_get_contents('php://input') ?: '';
    $payload = json_decode($raw, true);
    if (!is_array($payload)) {
        json_response(400, ['ok' => false, 'error' => 'invalid_json']);
    }

    return $payload;
}

function field_value(array $payload, string $key): string
{
    $fields = $payload['fields'] ?? [];
    $value = is_array($fields) ? ($fields[$key] ?? '') : '';
    if (is_array($value)) {
        return trim(implode(', ', $value));
    }
    return trim((string)$value);
}

function validate_honeypot(array $payload): void
{
    $hp = field_value($payload, 'website');
    if ($hp !== '') {
        // Pretend success so simple bots don't learn anything.
        lead_abort(200, ['ok' => true, 'queued' => false, 'reason' => 'honeypot']);
    }
}

function validate_required_fields(array $payload): void
{
    $source = field_value($payload, 'source');

    if ($source === 'landingpage.carports-zimmermeister') {
        $required = [
            'name', 'phone', 'plz', 'carport_typ', 'carport_position',
            'prioritaeten', 'zeitrahmen'
        ];
    } elseif ($source === 'landingpage.carports-kontaktformular') {
        $required = ['name', 'email', 'phone', 'ort', 'interesse', 'nachricht'];
    } else {
        lead_abort(400, ['ok' => false, 'error' => 'invalid_source']);
    }

    $missing = [];
    foreach ($required as $key) {
        if (field_value($payload, $key) === '' || field_value($payload, $key) === 'keine Angabe') {
            $missing[] = $key;
        }
    }

    if ($missing) {
        lead_abort(422, ['ok' => false, 'error' => 'missing_required_fields', 'fields' => $missing]);
    }
}

function enforce_rate_limit(PDO $pdo, array $config): void
{
    $limit = $config['rate_limit'] ?? [];
    $windowSeconds = (int)($limit['window_seconds'] ?? 3600);
    $maxRequests = (int)($limit['max_requests'] ?? 10);
    $salt = (string)($config['rate_limit_salt'] ?? '');

    if ($salt === '' || strpos($salt, 'CHANGE_ME') === 0) {
        // Fail closed-ish: still allow submissions if config not finalized, but don't crash lead intake.
        return;
    }

    $ipHash = hash('sha256', $salt . '|' . get_client_ip());
    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare('SELECT ip_hash, window_start, request_count FROM lead_rate_limits WHERE ip_hash = ? FOR UPDATE');
        $stmt->execute([$ipHash]);
        $row = $stmt->fetch();

        $now = new DateTimeImmutable('now');
        if (!$row) {
            $insert = $pdo->prepare('INSERT INTO lead_rate_limits (ip_hash, window_start, request_count) VALUES (?, NOW(), 1)');
            $insert->execute([$ipHash]);
            $pdo->commit();
            return;
        }

        $windowStart = new DateTimeImmutable($row['window_start']);
        $age = $now->getTimestamp() - $windowStart->getTimestamp();

        if ($age >= $windowSeconds) {
            $update = $pdo->prepare('UPDATE lead_rate_limits SET window_start = NOW(), request_count = 1 WHERE ip_hash = ?');
            $update->execute([$ipHash]);
            $pdo->commit();
            return;
        }

        if ((int)$row['request_count'] >= $maxRequests) {
            $pdo->commit();
            lead_abort(429, ['ok' => false, 'error' => 'rate_limited']);
        }

        $update = $pdo->prepare('UPDATE lead_rate_limits SET request_count = request_count + 1 WHERE ip_hash = ?');
        $update->execute([$ipHash]);
        $pdo->commit();
    } catch (Throwable $e) {
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }
        throw $e;
    }
}

function submission_ip_hash(array $config): string
{
    $salt = (string)($config['rate_limit_salt'] ?? '');
    if ($salt === '' || strpos($salt, 'CHANGE_ME') === 0) {
        return '';
    }
    return hash('sha256', $salt . '|' . get_client_ip());
}

function ensure_submission_audit_table(PDO $pdo): void
{
    static $ensured = false;
    if ($ensured) {
        return;
    }

    $pdo->exec("CREATE TABLE IF NOT EXISTS lead_submission_audit (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $ensured = true;
}

function insert_submission_audit(PDO $pdo, array $config, ?array $payload, string $rawBody, string $status = 'received', ?string $errorCode = null): int
{
    ensure_submission_audit_table($pdo);

    $source = is_array($payload) ? field_value($payload, 'source') : '';
    $payloadJson = is_array($payload) ? json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : null;
    $uuid = uuid_v4();
    $ipHash = submission_ip_hash($config);
    $userAgent = substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 1000);

    $stmt = $pdo->prepare('INSERT INTO lead_submission_audit (uuid, source, raw_body, payload_json, status, error_code, client_ip_hash, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
    $stmt->execute([$uuid, $source, $rawBody, $payloadJson, $status, $errorCode, $ipHash ?: null, $userAgent ?: null]);
    return (int)$pdo->lastInsertId();
}

function ensure_form_step_audit_table(PDO $pdo): void
{
    static $ensured = false;
    if ($ensured) {
        return;
    }

    $pdo->exec("CREATE TABLE IF NOT EXISTS form_step_audit (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $ensured = true;
}

function insert_form_step_audit(PDO $pdo, array $config, array $payload): string
{
    ensure_form_step_audit_table($pdo);

    $fields = $payload['fields'] ?? [];
    if (!is_array($fields)) {
        $fields = [];
    }

    $uuid = uuid_v4();
    $sessionUuid = trim((string)($payload['session_uuid'] ?? $fields['session_uuid'] ?? ''));
    $source = trim((string)($payload['source'] ?? $fields['source'] ?? ''));
    $eventName = trim((string)($payload['event_name'] ?? $fields['event_name'] ?? ''));
    $stepNumberRaw = $payload['step_number'] ?? $fields['step_number'] ?? null;
    $stepNumber = is_numeric($stepNumberRaw) ? max(0, min(255, (int)$stepNumberRaw)) : null;
    $stepLabel = substr(trim((string)($payload['step_label'] ?? $fields['step_label'] ?? '')), 0, 160);
    $payloadJson = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $ipHash = submission_ip_hash($config);
    $userAgent = substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 1000);

    $stmt = $pdo->prepare('INSERT INTO form_step_audit (uuid, session_uuid, source, event_name, step_number, step_label, payload_json, client_ip_hash, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
    $stmt->execute([$uuid, $sessionUuid, $source, $eventName, $stepNumber, $stepLabel ?: null, $payloadJson, $ipHash ?: null, $userAgent ?: null]);
    return $uuid;
}

function update_submission_audit(PDO $pdo, int $auditId, string $status, ?string $errorCode = null, ?string $leadQueueUuid = null): void
{
    $stmt = $pdo->prepare('UPDATE lead_submission_audit SET status = ?, error_code = ?, lead_queue_uuid = COALESCE(?, lead_queue_uuid) WHERE id = ?');
    $stmt->execute([$status, $errorCode, $leadQueueUuid, $auditId]);
}

function insert_lead(PDO $pdo, array $payload): string
{
    $uuid = uuid_v4();
    $source = field_value($payload, 'source');
    $json = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    $stmt = $pdo->prepare('INSERT INTO lead_queue (uuid, source, payload_json, status) VALUES (?, ?, ?, ?)');
    $stmt->execute([$uuid, $source, $json, 'pending']);
    return $uuid;
}

function update_delivery_success(PDO $pdo, string $uuid, string $response): void
{
    $stmt = $pdo->prepare("UPDATE lead_queue SET status = 'delivered', attempts = attempts + 1, leadtable_response = ?, last_error = NULL, delivered_at = NOW() WHERE uuid = ?");
    $stmt->execute([substr($response, 0, 5000), $uuid]);
}

function update_delivery_failure(PDO $pdo, string $uuid, string $error): void
{
    $stmt = $pdo->prepare("UPDATE lead_queue SET attempts = attempts + 1, last_error = ? WHERE uuid = ?");
    $stmt->execute([substr($error, 0, 5000), $uuid]);
}
