<?php
declare(strict_types=1);

require __DIR__ . '/db.php';
require __DIR__ . '/functions.php';
require __DIR__ . '/leadtable-client.php';

try {
    $config = app_config();

    if (PHP_SAPI !== 'cli') {
        $token = (string)($_GET['token'] ?? $_POST['token'] ?? '');
        if ($token === '' || !hash_equals((string)($config['cron_token'] ?? ''), $token)) {
            json_response(403, ['ok' => false, 'error' => 'forbidden']);
        }
    }

    $pdo = db();
    $maxAttempts = (int)($config['retry']['max_attempts'] ?? 30);
    $batchSize = (int)($config['retry']['batch_size'] ?? 20);

    $stmt = $pdo->prepare("SELECT uuid, payload_json, attempts FROM lead_queue WHERE status = 'pending' AND attempts < ? ORDER BY created_at ASC LIMIT " . max(1, min(100, $batchSize)));
    $stmt->execute([$maxAttempts]);
    $rows = $stmt->fetchAll();

    $delivered = 0;
    $failed = 0;

    foreach ($rows as $row) {
        $payload = json_decode((string)$row['payload_json'], true);
        if (!is_array($payload)) {
            update_delivery_failure($pdo, $row['uuid'], 'invalid_payload_json');
            $failed++;
            continue;
        }

        $result = forward_to_leadtable($payload, $config);
        if ($result['ok'] ?? false) {
            update_delivery_success($pdo, $row['uuid'], (string)($result['response'] ?? ''));
            $delivered++;
        } else {
            update_delivery_failure($pdo, $row['uuid'], (string)($result['error'] ?? 'unknown_error'));
            $failed++;
        }
    }

    $markFailed = $pdo->prepare("UPDATE lead_queue SET status = 'failed' WHERE status = 'pending' AND attempts >= ?");
    $markFailed->execute([$maxAttempts]);

    $body = [
        'ok' => true,
        'checked' => count($rows),
        'delivered' => $delivered,
        'failed_attempts' => $failed,
        'marked_failed' => $markFailed->rowCount(),
    ];

    if (PHP_SAPI === 'cli') {
        echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . PHP_EOL;
        exit;
    }

    json_response(200, $body);
} catch (Throwable $e) {
    error_log('retry-leads error: ' . $e->getMessage());
    if (PHP_SAPI === 'cli') {
        fwrite(STDERR, "retry-leads error\n");
        exit(1);
    }
    json_response(500, ['ok' => false, 'error' => 'server_error']);
}
