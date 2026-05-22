<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';

function validate_step_audit_payload(array $payload): void
{
    $sessionUuid = trim((string)($payload['session_uuid'] ?? ''));
    $source = trim((string)($payload['source'] ?? ''));
    $eventName = trim((string)($payload['event_name'] ?? ''));
    $stepNumber = $payload['step_number'] ?? null;

    if (!preg_match('/^[a-f0-9-]{36}$/i', $sessionUuid)) {
        lead_abort(422, ['ok' => false, 'error' => 'invalid_session_uuid']);
    }
    if ($source !== 'landingpage.carports-zimmermeister') {
        lead_abort(400, ['ok' => false, 'error' => 'invalid_source']);
    }
    if ($eventName === '' || strlen($eventName) > 80) {
        lead_abort(422, ['ok' => false, 'error' => 'invalid_event_name']);
    }
    if ($stepNumber !== null && (!is_numeric($stepNumber) || (int)$stepNumber < 0 || (int)$stepNumber > 11)) {
        lead_abort(422, ['ok' => false, 'error' => 'invalid_step_number']);
    }
}

try {
    $config = app_config();
    $pdo = db();
    $submission = read_json_submission();

    if (!($submission['ok'] ?? false)) {
        json_response((int)$submission['status'], (array)$submission['body']);
    }

    $payload = $submission['payload'];
    validate_step_audit_payload($payload);
    $uuid = insert_form_step_audit($pdo, $config, $payload);

    json_response(200, ['ok' => true, 'id' => $uuid]);
} catch (LeadHttpException $e) {
    json_response($e->status, $e->body);
} catch (Throwable $e) {
    error_log('lead-step-log error: ' . $e->getMessage());
    json_response(500, ['ok' => false, 'error' => 'server_error']);
}
