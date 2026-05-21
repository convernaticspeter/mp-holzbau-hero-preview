<?php
declare(strict_types=1);

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
        json_response(200, ['ok' => true, 'queued' => false]);
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
        json_response(400, ['ok' => false, 'error' => 'invalid_source']);
    }

    $missing = [];
    foreach ($required as $key) {
        if (field_value($payload, $key) === '' || field_value($payload, $key) === 'keine Angabe') {
            $missing[] = $key;
        }
    }

    if ($missing) {
        json_response(422, ['ok' => false, 'error' => 'missing_required_fields', 'fields' => $missing]);
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
            json_response(429, ['ok' => false, 'error' => 'rate_limited']);
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
