<?php
declare(strict_types=1);

function ensure_google_ads_conversion_table(PDO $pdo): void
{
    static $ensured = false;
    if ($ensured) {
        return;
    }

    $pdo->exec("CREATE TABLE IF NOT EXISTS google_ads_conversion_uploads (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");

    $ensured = true;
}

function google_ads_conversion_config(array $config): array
{
    $ads = $config['google_ads'] ?? [];
    $customerId = preg_replace('/\D+/', '', (string)($ads['customer_id'] ?? ''));
    $conversionActionId = preg_replace('/\D+/', '', (string)($ads['conversion_action_id'] ?? ''));
    $resource = (string)($ads['conversion_action_resource'] ?? '');
    if ($resource === '' && $customerId !== '' && $conversionActionId !== '') {
        $resource = 'customers/' . $customerId . '/conversionActions/' . $conversionActionId;
    }
    $serviceAccountEmail = (string)($ads['data_manager_service_account_email'] ?? '');
    $privateKey = (string)($ads['data_manager_private_key'] ?? '');
    $serviceAccountJson = trim((string)($ads['data_manager_service_account_json_base64'] ?? ''));
    if ($serviceAccountJson !== '') {
        $decodedJson = base64_decode($serviceAccountJson, true);
        $jsonText = is_string($decodedJson) ? $decodedJson : $serviceAccountJson;
        $serviceAccount = json_decode($jsonText, true);
        if (is_array($serviceAccount)) {
            $serviceAccountEmail = $serviceAccountEmail ?: (string)($serviceAccount['client_email'] ?? '');
            $privateKey = $privateKey ?: (string)($serviceAccount['private_key'] ?? '');
        }
    }

    return [
        'enabled' => filter_var((string)($ads['enabled'] ?? 'false'), FILTER_VALIDATE_BOOLEAN),
        'api_version' => (string)($ads['api_version'] ?? 'v23'),
        'customer_id' => $customerId,
        'login_customer_id' => preg_replace('/\D+/', '', (string)($ads['login_customer_id'] ?? '')),
        'conversion_action_resource' => $resource,
        'conversion_action_id' => $conversionActionId,
        'developer_token' => (string)($ads['developer_token'] ?? ''),
        'client_id' => (string)($ads['client_id'] ?? ''),
        'client_secret' => (string)($ads['client_secret'] ?? ''),
        'refresh_token' => (string)($ads['refresh_token'] ?? ''),
        'conversion_value' => (float)($ads['conversion_value'] ?? 400.0),
        'currency_code' => strtoupper((string)($ads['currency_code'] ?? 'EUR')),
        'max_attempts' => max(1, (int)($ads['max_attempts'] ?? 20)),
        'batch_size' => max(1, min(50, (int)($ads['batch_size'] ?? 10))),
        'timeout_seconds' => max(3, (int)($ads['timeout_seconds'] ?? 20)),
        'upload_mode' => strtolower((string)($ads['upload_mode'] ?? 'google_ads')),
        'data_manager_enabled' => filter_var((string)($ads['data_manager_enabled'] ?? 'false'), FILTER_VALIDATE_BOOLEAN),
        'data_manager_validate_only' => filter_var((string)($ads['data_manager_validate_only'] ?? 'false'), FILTER_VALIDATE_BOOLEAN),
        'data_manager_service_account_email' => $serviceAccountEmail,
        'data_manager_private_key' => $privateKey,
        'data_manager_destination_reference' => (string)($ads['data_manager_destination_reference'] ?? 'mp_lead'),
    ];
}

function google_ads_uses_data_manager(array $gads): bool
{
    return ($gads['upload_mode'] ?? '') === 'datamanager' || ($gads['data_manager_enabled'] ?? false);
}

function google_ads_is_configured(array $gads): bool
{
    if (!($gads['enabled'] ?? false) || ($gads['customer_id'] ?? '') === '') {
        return false;
    }

    if (google_ads_uses_data_manager($gads)) {
        return ($gads['conversion_action_resource'] ?? '') !== ''
            && ($gads['data_manager_service_account_email'] ?? '') !== ''
            && ($gads['data_manager_private_key'] ?? '') !== '';
    }

    return ($gads['conversion_action_resource'] ?? '') !== ''
        && ($gads['developer_token'] ?? '') !== ''
        && ($gads['client_id'] ?? '') !== ''
        && ($gads['client_secret'] ?? '') !== ''
        && ($gads['refresh_token'] ?? '') !== '';
}

function google_ads_pick_click_id(array $payload): ?array
{
    $fields = is_array($payload['fields'] ?? null) ? $payload['fields'] : [];
    foreach (['gclid', 'gbraid', 'wbraid'] as $key) {
        $value = trim((string)($fields[$key] ?? ''));
        if ($value !== '') {
            return ['type' => $key, 'value' => $value];
        }
    }
    return null;
}

function google_ads_consent_for_payload(array $payload): string
{
    $fields = is_array($payload['fields'] ?? null) ? $payload['fields'] : [];
    return trim((string)($fields['consent_state'] ?? 'unset')) ?: 'unset';
}

function google_ads_source_for_payload(array $payload): string
{
    $fields = is_array($payload['fields'] ?? null) ? $payload['fields'] : [];
    return trim((string)($fields['source'] ?? ''));
}

function enqueue_google_ads_conversion(PDO $pdo, string $leadQueueUuid, array $payload, array $config): ?int
{
    ensure_google_ads_conversion_table($pdo);
    $gads = google_ads_conversion_config($config);
    $click = google_ads_pick_click_id($payload);
    if ($click === null) {
        return null;
    }

    $uuid = uuid_v4();
    $source = google_ads_source_for_payload($payload);
    $consent = google_ads_consent_for_payload($payload);
    $request = google_ads_build_click_conversion_payload($gads, $click['type'], $click['value'], $leadQueueUuid, $consent);
    $stmt = $pdo->prepare("INSERT IGNORE INTO google_ads_conversion_uploads
        (uuid, lead_queue_uuid, source, click_id_type, click_id_value, conversion_action_resource, conversion_value, currency_code, order_id, consent_state, status, request_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)");
    $stmt->execute([
        $uuid,
        $leadQueueUuid,
        $source,
        $click['type'],
        $click['value'],
        (string)$gads['conversion_action_resource'],
        (float)$gads['conversion_value'],
        (string)$gads['currency_code'],
        $leadQueueUuid,
        $consent,
        json_encode($request, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
    ]);

    if ($stmt->rowCount() < 1) {
        $lookup = $pdo->prepare('SELECT id FROM google_ads_conversion_uploads WHERE lead_queue_uuid = ? LIMIT 1');
        $lookup->execute([$leadQueueUuid]);
        $existing = $lookup->fetch();
        return $existing ? (int)$existing['id'] : null;
    }
    return (int)$pdo->lastInsertId();
}

function google_ads_build_click_conversion_payload(array $gads, string $clickType, string $clickValue, string $orderId, string $consentState): array
{
    if (google_ads_uses_data_manager($gads)) {
        return data_manager_build_event_payload($gads, $clickType, $clickValue, $orderId, $consentState);
    }

    $conversion = [
        'conversionAction' => (string)$gads['conversion_action_resource'],
        'conversionDateTime' => google_ads_conversion_datetime(),
        'conversionValue' => (float)$gads['conversion_value'],
        'currencyCode' => (string)$gads['currency_code'],
        'orderId' => $orderId,
    ];
    $conversion[$clickType] = $clickValue;

    if ($consentState !== '') {
        $conversion['consent'] = [
            'adUserData' => $consentState === 'accepted' ? 'GRANTED' : 'DENIED',
        ];
    }

    return [
        'conversions' => [$conversion],
        'partialFailure' => true,
        'validateOnly' => false,
    ];
}

function data_manager_build_event_payload(array $gads, string $clickType, string $clickValue, string $orderId, string $consentState): array
{
    $reference = trim((string)($gads['data_manager_destination_reference'] ?? 'mp_lead')) ?: 'mp_lead';
    $destination = [
        'operatingAccount' => [
            'accountId' => (string)$gads['customer_id'],
            'accountType' => 'GOOGLE_ADS',
        ],
        'productDestinationId' => (string)$gads['conversion_action_id'],
        'reference' => $reference,
    ];

    if (($gads['login_customer_id'] ?? '') !== '') {
        $destination['loginAccount'] = [
            'accountId' => (string)$gads['login_customer_id'],
            'accountType' => 'GOOGLE_ADS',
        ];
    }

    $event = [
        'destinationReferences' => [$reference],
        'transactionId' => $orderId,
        'eventTimestamp' => data_manager_event_timestamp(),
        'adIdentifiers' => [$clickType => $clickValue],
        'currency' => (string)$gads['currency_code'],
        'conversionValue' => (float)$gads['conversion_value'],
    ];

    if ($consentState !== '') {
        $event['consent'] = [
            'adUserData' => $consentState === 'accepted' ? 'CONSENT_GRANTED' : 'CONSENT_DENIED',
        ];
    }

    return [
        'destinations' => [$destination],
        'events' => [$event],
        'validateOnly' => (bool)($gads['data_manager_validate_only'] ?? false),
    ];
}

function google_ads_conversion_datetime(): string
{
    $now = new DateTimeImmutable('now', new DateTimeZone('UTC'));
    return $now->format('Y-m-d H:i:sP');
}

function data_manager_event_timestamp(): string
{
    $now = new DateTimeImmutable('now', new DateTimeZone('UTC'));
    return $now->format('Y-m-d\TH:i:s\Z');
}

function base64url_encode(string $data): string
{
    return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}

function data_manager_private_key(array $gads): string
{
    $key = (string)($gads['data_manager_private_key'] ?? '');
    $decoded = base64_decode($key, true);
    if (is_string($decoded) && strpos($decoded, 'BEGIN PRIVATE KEY') !== false) {
        $key = $decoded;
    }
    $key = str_replace('\n', "\n", $key);
    if (strpos($key, 'BEGIN PRIVATE KEY') === false) {
        throw new RuntimeException('datamanager_missing_private_key');
    }
    return $key;
}

function data_manager_access_token(array $gads): string
{
    $email = (string)($gads['data_manager_service_account_email'] ?? '');
    if ($email === '') {
        throw new RuntimeException('datamanager_missing_service_account_email');
    }

    $now = time();
    $header = ['alg' => 'RS256', 'typ' => 'JWT'];
    $claims = [
        'iss' => $email,
        'scope' => 'https://www.googleapis.com/auth/datamanager',
        'aud' => 'https://oauth2.googleapis.com/token',
        'iat' => $now,
        'exp' => $now + 3600,
    ];

    $unsigned = base64url_encode(json_encode($header, JSON_UNESCAPED_SLASHES)) . '.' . base64url_encode(json_encode($claims, JSON_UNESCAPED_SLASHES));
    $signature = '';
    $ok = openssl_sign($unsigned, $signature, data_manager_private_key($gads), OPENSSL_ALGO_SHA256);
    if (!$ok) {
        throw new RuntimeException('datamanager_jwt_sign_failed');
    }

    $body = http_build_query([
        'grant_type' => 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion' => $unsigned . '.' . base64url_encode($signature),
    ]);

    $ch = curl_init('https://oauth2.googleapis.com/token');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $body,
        CURLOPT_HTTPHEADER => ['Content-Type: application/x-www-form-urlencoded'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => (int)$gads['timeout_seconds'],
    ]);
    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno !== 0) {
        throw new RuntimeException('datamanager_oauth_curl_' . $errno . ': ' . $error);
    }
    $data = json_decode(is_string($response) ? $response : '', true);
    if ($status < 200 || $status >= 300 || !is_array($data) || empty($data['access_token'])) {
        throw new RuntimeException('datamanager_oauth_http_' . $status . ': ' . substr((string)$response, 0, 500));
    }
    return (string)$data['access_token'];
}

function google_ads_access_token(array $gads): string
{
    $body = http_build_query([
        'client_id' => (string)$gads['client_id'],
        'client_secret' => (string)$gads['client_secret'],
        'refresh_token' => (string)$gads['refresh_token'],
        'grant_type' => 'refresh_token',
    ]);

    $ch = curl_init('https://oauth2.googleapis.com/token');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $body,
        CURLOPT_HTTPHEADER => ['Content-Type: application/x-www-form-urlencoded'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => (int)$gads['timeout_seconds'],
    ]);
    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno !== 0) {
        throw new RuntimeException('oauth_curl_' . $errno . ': ' . $error);
    }
    $data = json_decode(is_string($response) ? $response : '', true);
    if ($status < 200 || $status >= 300 || !is_array($data) || empty($data['access_token'])) {
        throw new RuntimeException('oauth_http_' . $status . ': ' . substr((string)$response, 0, 500));
    }
    return (string)$data['access_token'];
}

function google_ads_json_column(?string $value): ?string
{
    if ($value === null || $value === '') {
        return null;
    }
    json_decode($value, true);
    if (json_last_error() === JSON_ERROR_NONE) {
        return substr($value, 0, 5000);
    }
    return json_encode(['raw' => substr($value, 0, 4000)], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}

function upload_google_ads_conversion_row(PDO $pdo, array $row, array $config): bool
{
    $gads = google_ads_conversion_config($config);
    if (!google_ads_is_configured($gads)) {
        update_google_ads_conversion_failure($pdo, (int)$row['id'], 'google_ads_not_configured', false);
        return false;
    }

    $token = google_ads_uses_data_manager($gads) ? data_manager_access_token($gads) : google_ads_access_token($gads);
    $payload = (string)($row['request_json'] ?? '');
    if ($payload === '') {
        $payload = json_encode(google_ads_build_click_conversion_payload(
            $gads,
            (string)$row['click_id_type'],
            (string)$row['click_id_value'],
            (string)$row['order_id'],
            (string)$row['consent_state']
        ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }

    if (google_ads_uses_data_manager($gads)) {
        $url = 'https://datamanager.googleapis.com/v1/events:ingest';
        $headers = [
            'Authorization: Bearer ' . $token,
            'Content-Type: application/json',
            'Accept: application/json',
        ];
    } else {
        $url = sprintf('https://googleads.googleapis.com/%s/customers/%s:uploadClickConversions', rawurlencode((string)$gads['api_version']), rawurlencode((string)$gads['customer_id']));
        $headers = [
            'Authorization: Bearer ' . $token,
            'developer-token: ' . (string)$gads['developer_token'],
            'Content-Type: application/json',
            'Accept: application/json',
        ];
        if (($gads['login_customer_id'] ?? '') !== '') {
            $headers[] = 'login-customer-id: ' . (string)$gads['login_customer_id'];
        }
    }

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => (int)$gads['timeout_seconds'],
    ]);
    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno !== 0) {
        update_google_ads_conversion_failure($pdo, (int)$row['id'], 'google_ads_curl_' . $errno . ': ' . $error);
        return false;
    }

    $responseText = is_string($response) ? $response : '';
    $responseData = json_decode($responseText, true);
    if ($status < 200 || $status >= 300) {
        $prefix = google_ads_uses_data_manager($gads) ? 'datamanager_http_' : 'google_ads_http_';
        update_google_ads_conversion_failure($pdo, (int)$row['id'], $prefix . $status . ': ' . substr($responseText, 0, 1000), true, $responseText);
        return false;
    }

    if (!google_ads_uses_data_manager($gads) && is_array($responseData) && !empty($responseData['partialFailureError'])) {
        update_google_ads_conversion_failure($pdo, (int)$row['id'], 'google_ads_partial_failure: ' . substr(json_encode($responseData['partialFailureError'], JSON_UNESCAPED_SLASHES), 0, 1000), true, $responseText);
        return false;
    }

    $stmt = $pdo->prepare("UPDATE google_ads_conversion_uploads SET status = 'uploaded', attempts = attempts + 1, last_error = NULL, response_json = ?, uploaded_at = NOW() WHERE id = ?");
    $stmt->execute([google_ads_json_column($responseText), (int)$row['id']]);
    return true;
}

function update_google_ads_conversion_failure(PDO $pdo, int $id, string $error, bool $countAttempt = true, ?string $responseJson = null): void
{
    $sql = "UPDATE google_ads_conversion_uploads SET last_error = ?, response_json = COALESCE(?, response_json)";
    if ($countAttempt) {
        $sql .= ", attempts = attempts + 1";
    }
    $sql .= " WHERE id = ?";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([substr($error, 0, 5000), google_ads_json_column($responseJson), $id]);
}

function process_pending_google_ads_conversions(PDO $pdo, array $config, ?int $limit = null): array
{
    ensure_google_ads_conversion_table($pdo);
    $gads = google_ads_conversion_config($config);
    $batchSize = $limit ?? (int)$gads['batch_size'];
    $maxAttempts = (int)$gads['max_attempts'];

    if (!google_ads_is_configured($gads)) {
        return ['configured' => false, 'checked' => 0, 'uploaded' => 0, 'failed' => 0, 'marked_failed' => 0];
    }

    $stmt = $pdo->prepare("SELECT * FROM google_ads_conversion_uploads WHERE status = 'pending' AND attempts < ? ORDER BY created_at ASC LIMIT " . max(1, min(50, $batchSize)));
    $stmt->execute([$maxAttempts]);
    $rows = $stmt->fetchAll();

    $uploaded = 0;
    $failed = 0;
    foreach ($rows as $row) {
        try {
            if (upload_google_ads_conversion_row($pdo, $row, $config)) {
                $uploaded++;
            } else {
                $failed++;
            }
        } catch (Throwable $e) {
            update_google_ads_conversion_failure($pdo, (int)$row['id'], $e->getMessage());
            $failed++;
        }
    }

    $markFailed = $pdo->prepare("UPDATE google_ads_conversion_uploads SET status = 'failed' WHERE status = 'pending' AND attempts >= ?");
    $markFailed->execute([$maxAttempts]);

    return [
        'configured' => true,
        'checked' => count($rows),
        'uploaded' => $uploaded,
        'failed' => $failed,
        'marked_failed' => $markFailed->rowCount(),
    ];
}

function enqueue_and_try_google_ads_conversion(PDO $pdo, string $leadQueueUuid, array $payload, array $config): array
{
    $id = enqueue_google_ads_conversion($pdo, $leadQueueUuid, $payload, $config);
    if ($id === null) {
        return ['configured' => google_ads_is_configured(google_ads_conversion_config($config)), 'queued' => false, 'reason' => 'no_google_click_id'];
    }

    if (!google_ads_is_configured(google_ads_conversion_config($config))) {
        return ['configured' => false, 'queued' => false, 'pending' => true, 'reason' => 'google_ads_not_configured'];
    }

    $stmt = $pdo->prepare('SELECT * FROM google_ads_conversion_uploads WHERE id = ? LIMIT 1');
    $stmt->execute([$id]);
    $row = $stmt->fetch();
    if (!$row || ($row['status'] ?? '') !== 'pending') {
        return ['configured' => true, 'queued' => true, 'uploaded' => false, 'reason' => 'not_pending'];
    }

    try {
        $uploaded = upload_google_ads_conversion_row($pdo, $row, $config);
        return ['configured' => true, 'queued' => true, 'uploaded' => $uploaded];
    } catch (Throwable $e) {
        update_google_ads_conversion_failure($pdo, (int)$id, $e->getMessage());
        return ['configured' => true, 'queued' => true, 'uploaded' => false, 'error' => 'upload_failed'];
    }
}
