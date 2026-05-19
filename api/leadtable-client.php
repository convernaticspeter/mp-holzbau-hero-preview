<?php
declare(strict_types=1);

function forward_to_leadtable(array $payload, array $config): array
{
    $url = (string)($config['leadtable_webhook_url'] ?? '');
    if ($url === '' || strpos($url, 'PASTE_FULL_TOKEN_HERE') !== false) {
        return ['ok' => false, 'error' => 'leadtable_webhook_not_configured'];
    }

    $body = json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $body,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json',
            'User-Agent: MP-Holzbau-LeadQueue/1.0',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 12,
    ]);

    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno !== 0) {
        return ['ok' => false, 'error' => 'curl_' . $errno . ': ' . $error];
    }

    $responseText = is_string($response) ? $response : '';
    if ($status < 200 || $status >= 300) {
        return ['ok' => false, 'error' => 'http_' . $status . ': ' . substr($responseText, 0, 1000)];
    }

    return ['ok' => true, 'response' => $responseText, 'status' => $status];
}
