<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';
require __DIR__ . '/leadtable-client.php';
require __DIR__ . '/google-ads-conversions.php';

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

    // Local persistence is the source of truth, but do not wait for cron for the
    // business handoff. Try the LeadTable/webhook delivery immediately once; if
    // the third-party endpoint is slow/down, the existing retry queue remains the
    // fallback instead of losing the lead.
    $deliveryStatus = 'queued_for_retry';
    $deliveryError = null;
    $googleAdsConversion = null;

    $delivery = forward_to_leadtable($payload, $config);
    if ($delivery['ok'] ?? false) {
        update_delivery_success($pdo, $uuid, (string)($delivery['response'] ?? ''));
        update_submission_audit($pdo, $auditId, 'delivered', null, $uuid);
        $deliveryStatus = 'delivered';

        try {
            $googleAdsConversion = enqueue_and_try_google_ads_conversion($pdo, $uuid, $payload, $config);
        } catch (Throwable $conversionError) {
            error_log('google ads conversion enqueue failed: ' . $conversionError->getMessage());
        }
    } else {
        $deliveryError = (string)($delivery['error'] ?? 'unknown_error');
        update_delivery_failure($pdo, $uuid, $deliveryError);
    }

    json_response(200, [
        'ok' => true,
        'queued' => $deliveryStatus !== 'delivered',
        'id' => $uuid,
        'delivery_status' => $deliveryStatus,
        'delivery_error' => $deliveryError,
        'google_ads_conversion' => $googleAdsConversion,
    ]);
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
