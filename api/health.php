<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';

try {
    $pdo = db();
    $row = $pdo->query("SELECT
        SUM(status = 'pending') AS pending,
        SUM(status = 'delivered') AS delivered,
        SUM(status = 'failed') AS failed
        FROM lead_queue")->fetch();

    json_response(200, [
        'ok' => true,
        'pending' => (int)($row['pending'] ?? 0),
        'delivered' => (int)($row['delivered'] ?? 0),
        'failed' => (int)($row['failed'] ?? 0),
    ]);
} catch (Throwable $e) {
    error_log('health error: ' . $e->getMessage());
    json_response(500, ['ok' => false, 'error' => 'server_error']);
}
