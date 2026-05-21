<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';
require __DIR__ . '/leadtable-client.php';

$auditId = null;
$pdo = null;

try {
    $config = app_config();
    $pdo = db();
    $submission = read_json_submission();

    if (!($submission['ok'] ?? false)) {
        $rawBody = (string)($submission['raw_body'] ?? '');
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $auditId = insert_submission_audit($pdo, $config, null, $rawBody, 'rejected', (string)(($submission['body']['error'] ?? 'invalid_submission')));
        }
        json_response((int)$submission['status'], (array)$submission['body']);
    }

    $payload = $submission['payload'];
    $rawBody = (string)$submission['raw_body'];
    $auditId = insert_submission_audit($pdo, $config, $payload, $rawBody, 'received');

    validate_honeypot($payload);
    validate_required_fields($payload);
    enforce_rate_limit($pdo, $config);

    $uuid = insert_lead($pdo, $payload);
    update_submission_audit($pdo, $auditId, 'queued', null, $uuid);

    // Fire a best-effort immediate delivery attempt. The browser receives OK
    // as long as the lead was saved locally, even if LeadTable is down.
    $result = forward_to_leadtable($payload, $config);
    if ($result['ok'] ?? false) {
        update_delivery_success($pdo, $uuid, (string)($result['response'] ?? ''));
        update_submission_audit($pdo, $auditId, 'delivered', null, $uuid);
    } else {
        $error = (string)($result['error'] ?? 'unknown_error');
        update_delivery_failure($pdo, $uuid, $error);
        update_submission_audit($pdo, $auditId, 'failed', $error, $uuid);
    }

    json_response(200, ['ok' => true, 'queued' => true, 'id' => $uuid]);
} catch (LeadHttpException $e) {
    if ($pdo instanceof PDO && $auditId !== null) {
        $errorCode = (string)($e->body['error'] ?? $e->body['reason'] ?? 'rejected');
        $status = (($e->body['reason'] ?? '') === 'honeypot') ? 'honeypot' : 'rejected';
        update_submission_audit($pdo, $auditId, $status, $errorCode);
    }
    json_response($e->status, $e->body);
} catch (Throwable $e) {
    error_log('lead-submit error: ' . $e->getMessage());
    if ($pdo instanceof PDO && $auditId !== null) {
        update_submission_audit($pdo, $auditId, 'failed', 'server_error');
    }
    json_response(500, ['ok' => false, 'error' => 'server_error']);
}
