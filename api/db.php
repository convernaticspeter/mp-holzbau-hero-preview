<?php
declare(strict_types=1);

function env_value(string $key, string $default = ''): string
{
    static $loaded = false;

    if (!$loaded) {
        $envPath = __DIR__ . '/.env';
        if (is_file($envPath)) {
            foreach (file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
                $line = trim($line);
                if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) {
                    continue;
                }
                list($envKey, $envVal) = explode('=', $line, 2);
                $envKey = trim($envKey);
                $envVal = trim($envVal, " \t\n\r\0\x0B\"'");
                if ($envKey !== '' && getenv($envKey) === false) {
                    putenv($envKey . '=' . $envVal);
                }
            }
        }
        $loaded = true;
    }

    $value = getenv($key);
    return $value === false ? $default : $value;
}

function app_config(): array
{
    return [
        'db' => [
            'host' => env_value('DB_HOST', 'localhost'),
            'name' => env_value('DB_NAME'),
            'user' => env_value('DB_USER'),
            'pass' => env_value('DB_PASS'),
            'charset' => env_value('DB_CHARSET', 'utf8mb4'),
        ],
        'leadtable_webhook_url' => env_value('LEADTABLE_WEBHOOK_URL'),
        'rate_limit_salt' => env_value('RATE_LIMIT_SALT'),
        'rate_limit' => [
            'window_seconds' => (int)env_value('RATE_LIMIT_WINDOW_SECONDS', '3600'),
            'max_requests' => (int)env_value('RATE_LIMIT_MAX_REQUESTS', '10'),
        ],
        'retry' => [
            'max_attempts' => (int)env_value('RETRY_MAX_ATTEMPTS', '30'),
            'batch_size' => (int)env_value('RETRY_BATCH_SIZE', '20'),
        ],
        'cron_token' => env_value('CRON_TOKEN'),
    ];
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $cfg = app_config()['db'];
    foreach (['name', 'user', 'pass'] as $requiredKey) {
        if (($cfg[$requiredKey] ?? '') === '') {
            throw new RuntimeException('Missing DB_' . strtoupper($requiredKey) . ' in api/.env');
        }
    }

    $charset = $cfg['charset'] ?: 'utf8mb4';
    $dsn = sprintf('mysql:host=%s;dbname=%s;charset=%s', $cfg['host'], $cfg['name'], $charset);

    $pdo = new PDO($dsn, $cfg['user'], $cfg['pass'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);

    return $pdo;
}
