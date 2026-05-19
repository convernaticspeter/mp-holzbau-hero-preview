<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';
require __DIR__ . '/leadtable-client.php';

try {
    $config = app_config();
    $pdo = db();
    $payload = require_post_json();

    validate_honeypot($payload);
    validate_required_fields($payload);
    enforce_rate_limit($pdo, $config);

    $uuid = insert_lead($pdo, $payload);

    // Fire a best-effort immediate delivery attempt. The browser receives OK
    // as long as the lead was saved locally, even if LeadTable is down.
    $result = forward_to_leadtable($payload, $config);
    if ($result['ok'] ?? false) {
        update_delivery_success($pdo, $uuid, (string)($result['response'] ?? ''));
    } else {
        update_delivery_failure($pdo, $uuid, (string)($result['error'] ?? 'unknown_error'));
    }

    json_response(200, ['ok' => true, 'queued' => true, 'id' => $uuid]);
} catch (Throwable $e) {
    error_log('lead-submit error: ' . $e->getMessage());
    json_response(500, ['ok' => false, 'error' => 'server_error']);
}
