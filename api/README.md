# M&P Holzbau Lead Queue

PHP + MariaDB queue for landingpage leads before forwarding to LeadTable.

## Deploy steps

1. Create MariaDB tables:

```sql
SOURCE api/schema.sql;
```

For an existing installation, also run pending migrations, e.g.:

```sql
SOURCE api/migrations/2026-05-21-lead-submission-audit.sql;
SOURCE api/migrations/2026-05-22-lead-step-audit.sql;
```

This project intentionally stores every received form interaction before external delivery:
- `form_step_audit` = step-by-step quiz snapshots with the current entered data, so abandoned/incomplete multi-step forms are still recoverable.
- `lead_submission_audit` = raw/audit record for every final form POST, including rejected/honeypot/rate-limited submissions.
- `lead_queue` = valid lead queue for LeadTable delivery and retries.
- `google_ads_conversion_uploads` = server-side conversion uploads queued only after successful LeadTable delivery. Preferred upload path is Google Data Manager API via service account; legacy Google Ads API OAuth remains available as fallback.

The browser must only redirect to `danke.html` after `/api/lead-submit.php` returns HTTP 200 with `ok:true`. Google Ads conversion upload happens server-side after `lead_queue.status = delivered`, using the stored click ID (`gclid`, `gbraid`, or `wbraid`) and a stable `transactionId`/`orderId` equal to the local lead UUID. Data Manager API mode sends `events:ingest` with the Google Ads customer as `operatingAccount` and the conversion action ID as `productDestinationId`. While server-side upload config is missing or upload fails, the frontend keeps the old browser conversion as a temporary fallback; once the API response reports `uploaded:true`, no browser conversion is fired.

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
- Google conversion upload variables if server-side Ads feedback should be active:
  - `GOOGLE_ADS_CONVERSIONS_ENABLED=true`
  - `GOOGLE_ADS_CUSTOMER_ID=4921325707`
  - `GOOGLE_ADS_CONVERSION_ACTION_ID=7568021279`
  - `GOOGLE_ADS_CONVERSION_UPLOAD_MODE=datamanager`
  - `GOOGLE_DATAMANAGER_ENABLED=true`
  - `GOOGLE_DATAMANAGER_SERVICE_ACCOUNT_JSON_BASE64` — preferred: base64 of the full service-account JSON key file
  - alternatively `GOOGLE_DATAMANAGER_SERVICE_ACCOUNT_EMAIL` + `GOOGLE_DATAMANAGER_PRIVATE_KEY` manually
  - `GOOGLE_DATAMANAGER_VALIDATE_ONLY=true` for the first live credential test; switch to `false` after Google accepts the request
  - optional `GOOGLE_ADS_LOGIN_CUSTOMER_ID` when the service account is added to an MCC/manager rather than directly to the client account

Legacy Google Ads API OAuth mode remains supported by setting `GOOGLE_ADS_CONVERSION_UPLOAD_MODE=google_ads` and filling `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, and `GOOGLE_ADS_REFRESH_TOKEN`.

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

- `POST /api/lead-submit.php` — public landingpage endpoint for final lead submits
- `POST /api/lead-step-log.php` — public landingpage endpoint for best-effort quiz step snapshots
- `GET /api/retry-leads.php?token=...` — optional URL cron; CLI does not need token
- `GET /api/health.php` — returns queue counts; can be removed if not wanted

## Behavior

- Honeypot field `website` filled → silent OK, not queued
- Every quiz open/view/completed/closed event is stored best-effort in `form_step_audit` with the current entered data, independent of final submission.
- All required fields missing → HTTP 422
- Per-IP rate limit → HTTP 429
- Lead is stored in MariaDB first
- Immediate LeadTable delivery is best-effort
- Browser receives OK if the lead was queued, even when LeadTable is down
- Browser-side Google Ads conversion remains as fallback while server-side Data Manager/API config is unavailable
- Server-side Google Ads conversion is queued/uploaded only after successful LeadTable delivery
- `retry-leads.php` retries both LeadTable delivery and pending Google Ads conversion uploads
