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
        'google_ads' => [
            'enabled' => env_value('GOOGLE_ADS_CONVERSIONS_ENABLED', 'false'),
            'api_version' => env_value('GOOGLE_ADS_API_VERSION', 'v23'),
            'customer_id' => env_value('GOOGLE_ADS_CUSTOMER_ID', '4921325707'),
            'login_customer_id' => env_value('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
            'conversion_action_id' => env_value('GOOGLE_ADS_CONVERSION_ACTION_ID', '7568021279'),
            'conversion_action_resource' => env_value('GOOGLE_ADS_CONVERSION_ACTION_RESOURCE'),
            'developer_token' => env_value('GOOGLE_ADS_DEVELOPER_TOKEN'),
            'client_id' => env_value('GOOGLE_ADS_CLIENT_ID'),
            'client_secret' => env_value('GOOGLE_ADS_CLIENT_SECRET'),
            'refresh_token' => env_value('GOOGLE_ADS_REFRESH_TOKEN'),
            'conversion_value' => (float)env_value('GOOGLE_ADS_CONVERSION_VALUE', '400'),
            'currency_code' => env_value('GOOGLE_ADS_CONVERSION_CURRENCY', 'EUR'),
            'max_attempts' => (int)env_value('GOOGLE_ADS_CONVERSION_MAX_ATTEMPTS', '20'),
            'batch_size' => (int)env_value('GOOGLE_ADS_CONVERSION_BATCH_SIZE', '10'),
            'timeout_seconds' => (int)env_value('GOOGLE_ADS_TIMEOUT_SECONDS', '20'),
            'upload_mode' => env_value('GOOGLE_ADS_CONVERSION_UPLOAD_MODE', 'google_ads'),
            'data_manager_enabled' => env_value('GOOGLE_DATAMANAGER_ENABLED', 'false'),
            'data_manager_validate_only' => env_value('GOOGLE_DATAMANAGER_VALIDATE_ONLY', 'false'),
            'data_manager_service_account_json_base64' => env_value('GOOGLE_DATAMANAGER_SERVICE_ACCOUNT_JSON_BASE64'),
            'data_manager_service_account_email' => env_value('GOOGLE_DATAMANAGER_SERVICE_ACCOUNT_EMAIL'),
            'data_manager_private_key' => env_value('GOOGLE_DATAMANAGER_PRIVATE_KEY'),
            'data_manager_destination_reference' => env_value('GOOGLE_DATAMANAGER_DESTINATION_REFERENCE', 'mp_lead'),
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
