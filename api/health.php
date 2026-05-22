<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';
require __DIR__ . '/google-ads-conversions.php';

try {
    $pdo = db();
    $row = $pdo->query("SELECT
        SUM(status = 'pending') AS pending,
        SUM(status = 'delivered') AS delivered,
        SUM(status = 'failed') AS failed
        FROM lead_queue")->fetch();

    $conversionRow = ['pending' => 0, 'uploaded' => 0, 'failed' => 0, 'skipped' => 0];
    try {
        ensure_google_ads_conversion_table($pdo);
        $conversionRow = $pdo->query("SELECT
            SUM(status = 'pending') AS pending,
            SUM(status = 'uploaded') AS uploaded,
            SUM(status = 'failed') AS failed,
            SUM(status = 'skipped') AS skipped
            FROM google_ads_conversion_uploads")->fetch() ?: $conversionRow;
    } catch (Throwable $ignored) {}

    $stepRow = ['events_24h' => 0, 'sessions_24h' => 0];
    try {
        ensure_form_step_audit_table($pdo);
        $stepRow = $pdo->query("SELECT
            COUNT(*) AS events_24h,
            COUNT(DISTINCT session_uuid) AS sessions_24h
            FROM form_step_audit
            WHERE created_at >= (NOW() - INTERVAL 1 DAY)")->fetch() ?: $stepRow;
    } catch (Throwable $ignored) {}

    $conversionConfig = google_ads_conversion_config(app_config());

    json_response(200, [
        'ok' => true,
        'pending' => (int)($row['pending'] ?? 0),
        'delivered' => (int)($row['delivered'] ?? 0),
        'failed' => (int)($row['failed'] ?? 0),
        'google_ads_conversions' => [
            'enabled' => (bool)$conversionConfig['enabled'],
            'upload_mode' => $conversionConfig['upload_mode'],
            'configured' => google_ads_is_configured($conversionConfig),
            'data_manager_configured' => google_ads_is_configured(array_merge($conversionConfig, [
                'enabled' => true,
                'upload_mode' => 'datamanager',
                'data_manager_enabled' => true,
            ])),
            'pending' => (int)($conversionRow['pending'] ?? 0),
            'uploaded' => (int)($conversionRow['uploaded'] ?? 0),
            'failed' => (int)($conversionRow['failed'] ?? 0),
            'skipped' => (int)($conversionRow['skipped'] ?? 0),
        ],
        'form_step_audit' => [
            'events_24h' => (int)($stepRow['events_24h'] ?? 0),
            'sessions_24h' => (int)($stepRow['sessions_24h'] ?? 0),
        ],
    ]);
} catch (Throwable $e) {
    error_log('health error: ' . $e->getMessage());
    json_response(500, ['ok' => false, 'error' => 'server_error']);
}
