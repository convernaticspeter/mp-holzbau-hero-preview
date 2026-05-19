# M&P Holzbau Lead Queue

PHP + MariaDB queue for landingpage leads before forwarding to LeadTable.

## Deploy steps

1. Create MariaDB tables:

```sql
SOURCE api/schema.sql;
```

2. Copy env file:

```bash
cp api/.env.example api/.env
```

3. Fill in `api/.env`:
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`
- `LEADTABLE_WEBHOOK_URL`
- random `RATE_LIMIT_SALT`
- random `CRON_TOKEN` if URL cron is used

Generate secrets:

```bash
php -r "echo bin2hex(random_bytes(32)), PHP_EOL;" # RATE_LIMIT_SALT
php -r "echo bin2hex(random_bytes(24)), PHP_EOL;" # CRON_TOKEN
```

No `config.php` is needed. The PHP entrypoints read `api/.env` directly without Composer/phpdotenv.
Keep the real `api/.env` out of git.

4. Cron every 5 minutes, preferably CLI:

```cron
*/5 * * * * /usr/bin/php /absolute/path/to/api/retry-leads.php >/dev/null 2>&1
```

If only URL cron is available:

```text
https://meistercarports.at/api/retry-leads.php?token=YOUR_CRON_TOKEN
```

## Endpoints

- `POST /api/lead-submit.php` — public landingpage endpoint
- `GET /api/retry-leads.php?token=...` — optional URL cron; CLI does not need token
- `GET /api/health.php` — returns queue counts; can be removed if not wanted

## Behavior

- Honeypot field `website` filled → silent OK, not queued
- All required fields missing → HTTP 422
- Per-IP rate limit → HTTP 429
- Lead is stored in MariaDB first
- Immediate LeadTable delivery is best-effort
- Browser receives OK if the lead was queued, even when LeadTable is down
