# M&P Holzbau Landingpage — Deployment-Regelwerk

Dieses Projekt darf nie als „fertig/deployed“ gelten, nur weil Code geändert oder zu Git gepusht wurde. Fertig ist erst, wenn die öffentliche URL die erwartete Version ausliefert und die Lead-Strecke nachweislich speichert.

## 1. Grundregel: Kein Tracking ohne gespeicherten Lead

- Der Browser darf erst auf `danke.html` weiterleiten, nachdem `/api/lead-submit.php` mit HTTP `200` und `{"ok": true}` geantwortet hat.
- Die Google-Ads-Conversion darf erst nach erfolgreicher Serverantwort ausgelöst werden.
- Wenn die API nicht bestätigt, muss der Besucher auf der Seite bleiben und eine Fehlermeldung bekommen.
- Kein `fire-and-forget`, kein Redirect direkt nach `fetch()`, kein `gtag`-Callback als Ersatz für Lead-Speicherung.

## 2. Datenbank-Pflicht: alles zuerst lokal speichern

Jeder Formular-POST muss lokal in MariaDB landen, bevor externe Systeme beteiligt sind.

- `lead_submission_audit`: Roh-/Audit-Speicher für jeden eingehenden Formular-POST, auch wenn Validierung, Rate-Limit oder Weiterleitung später scheitern.
- `lead_queue`: verwertbare Leads, die an LeadTable ausgeliefert oder erneut versucht werden.
- LeadTable/Webhook ist nachgelagert und darf nie die einzige Speicherung sein.
- Der Browser bekommt Erfolg nur, wenn der POST mindestens lokal gespeichert wurde.

## 3. Deployment-Ablauf

1. **Vorher prüfen**
   - `git status --short` muss bewusst verstanden sein.
   - Repo, Branch, Preview-URL und ggf. Live-Ziel prüfen.
   - Bei API/Form-Änderungen: Frontend-Payload-Felder gegen PHP-Validierung abgleichen.

2. **Lokal testen**
   - PHP-Syntax: `find api -name '*.php' -print0 | xargs -0 -n1 php -l`
   - HTML/JS-Änderungen per Browser oder statischem Check prüfen.
   - Wenn Formular/API betroffen ist: Test-POST gegen Preview/Live nur mit klar erkennbarem Testlead.

3. **Commit & Push**
   - Kleine, nachvollziehbare Commits.
   - Keine Secrets in Git.

4. **Coolify explizit deployen**
   - Git-Push allein reicht nicht.
   - Richtige App anhand Repo + Domain prüfen.
   - Force-Deploy über Coolify API/UI auslösen.
   - Deployment-Status/Logs bis zum terminalen Erfolg prüfen.

5. **Öffentlich verifizieren**
   - Preview/Live mit Cache-Bust öffnen (`?v=<short-sha>`).
   - Served HTML enthält neue Marker/Strings und keine entfernten alten Strings.
   - Formular-Test: API antwortet `ok:true`, DB enthält `lead_submission_audit` + `lead_queue`, Danke-Seite/Conversion erst danach.

## 4. Live-Sync-Regel

Wenn Preview und Live getrennt sind, gilt Preview-Deploy nicht automatisch als Live-Deploy.

- Für `mp-holzbau-hero.preview.convernatics.eu`: Coolify-App deployen und prüfen.
- Für `m.meistercarports.at`: eigenen Live-Sync/Git-Pull/File-Upload nachziehen und danach live prüfen.
- Nie dem Kunden sagen „live“, wenn nur Preview aktualisiert wurde.

## 5. Pflicht-Checks nach Formular-Änderungen

- Browser-Konsole: keine JS-Errors beim Absenden.
- Network: `POST /api/lead-submit.php` wird nicht abgebrochen und antwortet `200`.
- Response: `ok:true`, `queued:true`, `id:<uuid>`.
- MariaDB: neuester Datensatz in `lead_submission_audit` und `lead_queue` vorhanden.
- LeadTable-Auslieferung: `status='delivered'` oder nachvollziehbarer Pending/Failure-Eintrag mit Retry.
- Google Conversion: nur nach erfolgreichem POST, nicht bei API-Fehlern.

## 6. Fehlerfall-Regel

Wenn ein Lead vermisst wird:

1. Zuerst DB prüfen: `lead_submission_audit`, dann `lead_queue`.
2. Dann Server-/PHP-Logs prüfen.
3. Dann Browser-/Clarity-Session prüfen.
4. Dann Google-Ads-Conversion prüfen.
5. Keine Lead-Rekonstruktion behaupten, wenn kein POST/Audit-Datensatz existiert.

## 7. Definition of Done

Eine Änderung ist erst erledigt, wenn alle zutreffenden Punkte stimmen:

- Code geändert.
- Syntax/Build geprüft.
- Commit gepusht.
- Coolify/Live-Deployment ausgelöst und erfolgreich abgeschlossen.
- Öffentliche URL zeigt die neue Version.
- Formularstrecke speichert lokal in DB.
- Externe Conversion/Weiterleitung passiert erst danach.
