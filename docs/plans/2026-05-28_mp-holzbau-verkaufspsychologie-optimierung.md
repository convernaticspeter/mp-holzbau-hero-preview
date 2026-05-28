# M&P Holzbau Landingpage — Verkaufspsychologische Optimierung Implementation Plan

> **Für ausführenden Agent:** Diese Datei ist die verbindliche Schritt-für-Schritt-Anleitung. Nicht neu entscheiden, nicht umformulieren, nicht erweitern. Exakt diese Änderungen umsetzen, danach lokal und live verifizieren.

**Quelle / geprüfte Variante:** `https://mp-holzbau-hero.preview.convernatics.eu/?v=a9a3b40`  
**Repo:** `/Users/theo/OneDrive/_REPOS/mp-holzbau-hero-preview`  
**Primäre Datei:** `index.html`  
**Ziel:** Die Landingpage soll den ersten Klick psychologisch stärker entlasten, die frühe Überforderung reduzieren und das Modal menschlicher/beratender statt prüfend wirken lassen.

---

## 0. Strategische Entscheidungen — bereits getroffen

Diese Entscheidungen sind fix. Nicht diskutieren, nicht neu abwägen.

1. **Primäres Conversion-Ziel:** Formular-/Quiz-Start erhöhen, ohne Billig-Leads maximal aufzublasen.
2. **Hero-CTA bleibt sichtbar und dominant.** Sekundärer Referenz-Link wird visuell schwächer, nicht entfernt.
3. **Haupt-CTA-Text wird geändert zu:** `Projekt von Peter einschätzen lassen`
4. **CTA-Microcopy wird direkt unter dem Hero-Button ergänzt:**
   - `60 Sekunden · kostenlos · unverbindlich · kein Konfigurator`
   - `Peter Preissinger schaut persönlich drauf.`
5. **Hero-H1 bekommt Komma:** `Carports, die so lange halten wie Ihr Haus.`
6. **Obere Referenzstrecke wird auf 3 Karten reduziert:**
   - Referenz 01: Fassadenintegration / Architektenvilla
   - Referenz 03: Satteldach / Klassisches Wohnhaus
   - Referenz 06: Nähe zum Eingang / Alltag
7. **Die anderen 7 Referenzen werden nicht gelöscht**, sondern in eine spätere Galerie-Sektion verschoben.
8. **Modal wird auf 4 echte Entscheidungsfragen reduziert:**
   - Frage 1: `Worum geht es bei Ihrem Carport?`
   - Frage 2: `Was ist Ihnen besonders wichtig?`
   - Frage 3: `Wo ungefähr soll M&P einschätzen?`
   - Frage 4: `Wie darf Peter Sie erreichen?`
9. **Der bisherige Bremsen-Step wird entfernt:** `Was bremst Sie gerade noch?`
10. **PLZ-Tonalität wird weich gemacht:** keine Sprache wie `Standortprüfung`, `Liefergebiet wird abgeglichen`, `ob M&P in Ihrer Region tätig ist` im sichtbaren Modal.
11. **PLZ bleibt Pflicht**, aber nur als PLZ. Keine Straße einführen.
12. **Keine neuen Bilder generieren.** Nur vorhandene Bilder umsortieren.
13. **Keine neuen Tracking-Endpunkte bauen.** Bestehendes Step-Logging nur an die geänderten Steps anpassen.
14. **Keine Design-Revolution.** Nur Conversion-/Friction-/Text-/Flow-Änderungen.

---

## 1. Vorbereitungscheck

### 1.1 Arbeitsstand prüfen

Im Repo ausführen:

```bash
cd "/Users/theo/OneDrive/_REPOS/mp-holzbau-hero-preview"
git status -sb
```

**Erwartung:** Es können bereits untracked Assets/Drafts vorhanden sein. Diese nicht anfassen. Nur `index.html` und diese Plan-Datei sind relevant.

### 1.2 Sicherstellen, dass die Zielversion in `index.html` vorhanden ist

Suchen:

```bash
python3 - <<'PY'
from pathlib import Path
p=Path('index.html')
t=p.read_text()
checks=[
  'Carports die <span class="hl">so lange halten</span> wie Ihr Haus.',
  'Mein Carport-Projekt starten',
  'Was soll unter Dach?',
  'Was bremst Sie gerade noch?',
  'Standortprüfung',
  'Liefergebiet wird abgeglichen.',
]
for c in checks:
    print(('OK   ' if c in t else 'MISS ')+c)
PY
```

**Erwartung:** Alle sechs Zeilen zeigen `OK`.

Wenn nicht: abbrechen und Peter/Maya melden, weil die Datei nicht der geprüften Variante entspricht.

---

## 2. Hero psychologisch entlasten

### Objective
Der Hero soll nicht nur hochwertig wirken, sondern den Klick auf den Projekt-Check sofort risikoarm machen.

### File
- Modify: `index.html`, Hero-Bereich um Zeilen ca. `1827–1832`

### 2.1 Nav-CTA und Hero-CTA Text ändern

Ersetze alle sichtbaren CTA-Texte:

```html
Mein Carport-Projekt starten
```

mit:

```html
Projekt von Peter einschätzen lassen
```

**Achtung:** Nicht blind in Tracking- oder Kommentartexten ersetzen, nur sichtbare Buttontexte.

Mindestens diese Stellen ändern:

- Navigation Button in Zeile ca. `1827`
- Hero Button in Zeile ca. `1830`
- Quiz-Zone Button in Zeile ca. `2140`

Sticky Button unten kann kürzer bleiben, aber ebenfalls klarer werden:

```html
Projekt starten
```

ersetzen durch:

```html
Einschätzung starten
```

### 2.2 Hero-H1 korrigieren

Ersetze:

```html
<h1>Carports die <span class="hl">so lange halten</span> wie Ihr Haus.</h1>
```

mit:

```html
<h1>Carports, die <span class="hl">so lange halten</span> wie Ihr Haus.</h1>
```

### 2.3 Hero-Microcopy direkt unter Button ergänzen

Aktueller Hero-Ausschnitt:

```html
<div class="actions"><button class="btn btn-primary" type="button" onclick="openQuiz()"><span>Mein Carport-Projekt starten</span></button></div><a class="hero-link" href="#wunsch">Referenzen ansehen</a>
```

Ersetzen durch:

```html
<div class="actions"><button class="btn btn-primary" type="button" onclick="openQuiz()"><span>Projekt von Peter einschätzen lassen</span></button></div>
<p class="cta-reassurance">60 Sekunden · kostenlos · unverbindlich · kein Konfigurator<br><strong>Peter Preissinger schaut persönlich drauf.</strong></p>
<a class="hero-link" href="#wunsch">Referenzen ansehen</a>
```

### 2.4 CSS für `.cta-reassurance` ergänzen

Im `<style>`-Block bei den finalen Hero-/Typography-Regeln ergänzen, möglichst nahe bei `.micro` / `.hero .micro`:

```css
.cta-reassurance{
  margin:12px 0 0;
  max-width:560px;
  color:rgba(255,247,232,.86);
  font-size:14px;
  line-height:1.45;
  font-weight:750;
  text-shadow:0 2px 18px rgba(0,0,0,.72);
}
.cta-reassurance strong{
  color:#fff7e8;
  font-weight:950;
}
@media(max-width:640px){
  .cta-reassurance{
    max-width:32ch;
    text-align:center;
    font-size:13px;
    margin-top:12px;
  }
}
```

### 2.5 Sekundärlink schwächer machen

Falls `.hero-link` aktuell optisch wie ein zweiter CTA wirkt, CSS ergänzen/überschreiben:

```css
.hero-link{
  display:inline-block;
  margin-top:12px;
  color:rgba(255,247,232,.72);
  font-size:14px;
  font-weight:850;
  text-decoration:underline;
  text-decoration-thickness:1px;
  text-underline-offset:4px;
}
.hero-link:hover{color:#fff7e8}
```

**Ziel:** Der Blick soll zuerst auf den goldenen CTA gehen, nicht auf `Referenzen ansehen`.

---

## 3. Obere Wunschbild-/Referenzstrecke kürzen

### Objective
Die Seite soll nach dem Hero schneller Richtung Vertrauen und Anfrage führen. Der frühe Referenzblock darf inspirieren, aber nicht 10 Karten lang bremsen.

### File
- Modify: `index.html`, `#wunsch` ab Zeile ca. `1837–1985`

### 3.1 Nur 3 Referenzen im oberen Stack behalten

Im Bereich `<div class="card-stack" ...>` bleiben oben exakt diese drei `article.stack-card` sichtbar:

1. Original `data-idx="0"` — Architektenvilla / Fassadenintegration
2. Original `data-idx="2"` — Klassisches Wohnhaus / Satteldach
3. Original `data-idx="5"` — Hauseingang / Nah am Eingang

Alle anderen sieben Karten werden nicht gelöscht, sondern in Schritt 3.4 in eine spätere Galerie verschoben.

### 3.2 Stack-Indizes und Zählung anpassen

Nach dem Kürzen müssen die drei oberen Karten so aussehen:

- Karte 1: `data-idx="0"`, `Referenz · 01`, `01/03`
- Karte 2: `data-idx="1"`, `Referenz · 02`, `02/03`
- Karte 3: `data-idx="2"`, `Referenz · 03`, `03/03`

Die Inhalte bleiben inhaltlich gleich, nur Nummerierung/Zählung wird angepasst.

### 3.3 Progress-Dots auf 3 reduzieren

Aktuell gibt es 10 Buttons im `#stackDots`. Ersetze sie durch exakt:

```html
<button type="button" class="sp-dot" data-go="0" data-active="true" aria-label="Bild 01"></button><button type="button" class="sp-dot" data-go="1" aria-label="Bild 02"></button><button type="button" class="sp-dot" data-go="2" aria-label="Bild 03"></button>
```

### 3.4 Neue spätere Galerie-Sektion für die restlichen 7 Referenzen einfügen

Direkt nach dem `</section>` von `#wunsch` und vor `<section class="section trust-section" id="peter">` eine neue Sektion einfügen.

**Neue Sektion:**

```html
<section class="section reference-more" id="referenzen-mehr">
  <div class="wrap section-head">
    <div>
      <p class="eyebrow">Weitere Beispiele</p>
      <h2>Mehr Situationen, die M&P passend gelöst hat.</h2>
    </div>
    <p class="lead">Nicht jedes Haus braucht dieselbe Lösung. Diese Beispiele zeigen, wie M&P auf Einfahrt, Stauraum, Wetterseite und Wirkung am Haus reagiert.</p>
  </div>
  <div class="wide reference-grid">
    <!-- hier die 7 verschobenen Referenzkarten als kompakte Figuren einfügen -->
  </div>
</section>
```

Die 7 verschobenen Referenzen nicht als sticky `stack-card` verwenden, sondern als einfache `figure.reference-tile`.

Für jede verschobene Karte dieses Muster nutzen:

```html
<figure class="reference-tile">
  <img src="BILD_SRC" alt="ALT_TEXT" loading="lazy">
  <figcaption><strong>TITEL</strong><span>KURZER_NUTZEN</span></figcaption>
</figure>
```

**Die 7 Tiles:**

1. Bild `02_achtziger_haus_aufwertung.webp`  
   Titel: `Haus sichtbar aufgewertet`  
   Nutzen: `Warmes Holz macht die Einfahrt ruhiger und wertiger.`

2. Bild `04_landhaus_satteldach_honig.webp`  
   Titel: `Landhaus ruhig ergänzt`  
   Nutzen: `Holzton, Dachkante und Eingang wirken zusammen.`

3. Bild `05_lfoermiger_eck_carport.webp`  
   Titel: `Einfahrt um die Ecke gelöst`  
   Nutzen: `Die Form folgt dem Grundstück, nicht dem Standardmaß.`

4. Bild `07_geraeteraum_holzlager_stauraum.webp`  
   Titel: `Stauraum gleich mitgedacht`  
   Nutzen: `Auto, Werkzeug und Alltag in einer Lösung.`

5. Bild `08_lamellenwand_wetterseite-clean-kie.webp`  
   Titel: `Wetterseite geschützt`  
   Nutzen: `Lamellen halten Schlagregen zurück und bleiben optisch ruhig.`

6. Bild `ref-01-car-double-clearance.webp`  
   Titel: `Doppelcarport ohne Wucht`  
   Nutzen: `Zwei Stellplätze, aber eine ruhige Linie am Haus.`

7. Bild `10_designer_dunkel_fassadenwand_lichtband.webp`  
   Titel: `Dunkel, präzise, hochwertig`  
   Nutzen: `Wenn der Carport eine klare Aussage des Hauses sein soll.`

### 3.5 CSS für neue Galerie ergänzen

Im `<style>`-Block ergänzen:

```css
.reference-more{background:#fff7e8;color:#121610}
.reference-more h2{color:#121610}
.reference-more .lead{color:#51483b}
.reference-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:clamp(14px,1.6vw,22px);
}
.reference-tile{
  margin:0;
  background:#172419;
  overflow:hidden;
  border:1px solid rgba(9,13,9,.14);
  box-shadow:0 28px 90px -70px rgba(0,0,0,.78);
}
.reference-tile img{
  width:100%;
  height:clamp(230px,22vw,320px);
  object-fit:cover;
}
.reference-tile figcaption{
  background:#fff7e8;
  color:#211912;
  border-left:5px solid var(--gold);
  padding:16px 18px;
}
.reference-tile figcaption strong{
  display:block;
  font-family:Space,Inter,sans-serif;
  font-size:clamp(20px,1.8vw,28px);
  line-height:1.02;
  letter-spacing:-.035em;
  color:#121610;
}
.reference-tile figcaption span{
  display:block;
  margin-top:8px;
  color:#51483b;
  font-weight:750;
  line-height:1.45;
}
@media(max-width:980px){.reference-grid{grid-template-columns:1fr 1fr}}
@media(max-width:640px){.reference-grid{grid-template-columns:1fr}.reference-tile img{height:300px}}
```

### 3.6 Wunschbild-Scroll-Spacing prüfen

Weil der Stack nur noch 3 Karten hat, die große Scroll-Strecke reduzieren.

In CSS bei ca. Zeilen `1809–1814`:

Aktuell:

```css
#wunsch .stack-card{
  top:clamp(250px,30vh,315px);
  height:clamp(380px,52vh,600px);
  margin-bottom:clamp(52vh,68vh,86vh);
}
#wunsch .stack-card:last-child{margin-bottom:clamp(22px,3vw,46px)}
```

Ersetzen durch:

```css
#wunsch .stack-card{
  top:clamp(250px,30vh,315px);
  height:clamp(380px,52vh,600px);
  margin-bottom:clamp(30vh,44vh,58vh);
}
#wunsch .stack-card:last-child{margin-bottom:clamp(22px,3vw,46px)}
```

**Ziel:** Der Bereich soll wirken wie ein starker Auftakt, nicht wie ein Scroll-Tunnel. Sauber, nicht zäh.

---

## 4. Formular-/Modal-Flow umbauen

### Objective
Das Modal soll einfacher, wärmer und weniger prüfend wirken. Menschen sollen zuerst objektive Projektart und Wunsch beantworten, dann PLZ, dann Kontakt.

### File
- Modify: `index.html`, Modal ab Zeile ca. `2152–2164`
- Modify: `index.html`, JS ab Zeile ca. `2283–2316`

---

### 4.1 Sichtbare Modal-Steps ersetzen

Aktuelle Steps 1, 2, 3, 6, 7, 10, 11 bleiben strukturell erhalten, aber Text/Flow wird angepasst. Step 3 wird als sichtbare Frage entfernt.

#### Step 1 ersetzen

Aktuell:

```html
<div class="quiz-step active" data-step="1"><h3>Was soll unter Dach?</h3><p class="quiz-sub">Frage 1 von 3</p>...
```

Neu:

```html
<div class="quiz-step active" data-step="1"><h3>Worum geht es bei Ihrem Carport?</h3><p class="quiz-sub">Frage 1 von 4</p><div class="quiz-options"><div class="quiz-option" onclick="selectOption(this,'carportType','einzelcarport')"><span class="quiz-option-radio"></span>Carport für 1 Auto</div><div class="quiz-option" onclick="selectOption(this,'carportType','doppelcarport')"><span class="quiz-option-radio"></span>Doppelcarport</div><div class="quiz-option" onclick="selectOption(this,'carportType','gross-carport')"><span class="quiz-option-radio"></span>Carport mit Stauraum</div><div class="quiz-option" onclick="selectOption(this,'carportType','weiss-ich-noch-nicht')"><span class="quiz-option-radio"></span>Noch unsicher</div></div></div>
```

#### Step 2 ersetzen

Aktuell:

```html
<div class="quiz-step" data-step="2"><h3>Was soll sich mit dem Carport verändern?</h3>...
```

Neu:

```html
<div class="quiz-step" data-step="2"><h3>Was ist Ihnen besonders wichtig?</h3><p class="quiz-sub">Frage 2 von 4</p><div class="quiz-options"><div class="quiz-option" onclick="selectOption(this,'wish','passt-zum-haus')"><span class="quiz-option-radio"></span>Er soll gut zum Haus passen</div><div class="quiz-option" onclick="selectOption(this,'wish','auto-geschuetzt')"><span class="quiz-option-radio"></span>Trocken und bequem aussteigen</div><div class="quiz-option" onclick="selectOption(this,'wish','ordentlich-geplant-gebaut')"><span class="quiz-option-radio"></span>Langlebig und solide gebaut</div><div class="quiz-option" onclick="selectOption(this,'wish','ehrliche-erste-einschaetzung')"><span class="quiz-option-radio"></span>Ich will erst wissen, was möglich ist</div></div></div>
```

#### Step 3 entfernen

Aktuellen kompletten Step löschen:

```html
<div class="quiz-step" data-step="3"><h3>Was bremst Sie gerade noch?</h3>...</div>
```

#### Step 6 ersetzen

Aktuell:

```html
<div class="quiz-step" data-step="6"><h3>Wo soll der Carport entstehen?</h3><p class="quiz-sub">Standortprüfung</p><p class="quiz-hint">Bitte nur Ihre Postleitzahl eingeben. So sehen wir sofort, ob M&P in Ihrer Region tätig ist.</p>...
```

Neu:

```html
<div class="quiz-step" data-step="6"><h3>Wo ungefähr soll M&P einschätzen?</h3><p class="quiz-sub">Frage 3 von 4</p><p class="quiz-hint">PLZ reicht erstmal. Damit Peter Montagegebiet und erste Machbarkeit besser einordnen kann.</p><input type="text" class="quiz-input" placeholder="Postleitzahl (PLZ) *" id="zip" required inputmode="numeric" autocomplete="postal-code"><p class="quiz-hint error" id="zipHint" style="display:none;font-weight:850;margin-top:8px;">Bitte geben Sie eine 4-stellige PLZ ein.</p><div class="quiz-nav"><button class="btn btn-outline" type="button" onclick="prevStep()">Zurück</button><button class="btn" type="button" onclick="nextStep()" id="btnLocation">Weiter</button></div></div>
```

#### Step 7 ersetzen

Aktuell spricht Step 7 von `Ihre PLZ wird geprüft`, `Standortprüfung`, `Liefergebiet wird abgeglichen`.

Neu:

```html
<div class="quiz-step quiz-loading zip-check-step" data-step="7"><h3>Peter ordnet den Standort kurz ein …</h3><p class="quiz-sub">Erste Einschätzung</p><div class="answer-summary" id="mirrorLocation"></div><div class="zip-check-card"><div class="zip-loader" aria-hidden="true"><span></span><span></span><span></span></div><strong>Montagegebiet und Machbarkeit werden eingeordnet.</strong><p>Das dauert nur einen Moment. Danach können Sie Ihre Kontaktdaten hinterlassen.</p></div></div>
```

#### Step 10 ersetzen

Aktuell:

```html
<h3>Ihre Angaben reichen jetzt schon für Peters erste Rückmeldung.</h3>
...
<strong>Die wichtigsten Eckdaten sind da.</strong>
<p>Mit Wunsch und Standort sieht M&P schon gut, was bei Ihrem Carport wichtig wird.</p>
```

Neu:

```html
<div class="quiz-step quiz-loading" data-step="10"><h3>Das reicht für eine erste Einschätzung.</h3><div class="answer-summary" id="mirrorFinal"></div><div class="quiz-loading-card"><div class="loading-check"><img src="assets/wired-flat-24-approved-checked-morph-check-appear.svg?v=b29916d" alt=""></div><strong>Projektart, Wunsch und PLZ sind da.</strong><p>Peter kann damit einschätzen, worauf er bei Ihrem Carport zuerst schauen muss.</p></div></div>
```

#### Step 11 ersetzen

Aktuell:

```html
<div class="quiz-step" data-step="11"><h3>Wie darf Peter Sie ansprechen?</h3><p class="quiz-sub">Kontakt · Ihre Telefonnummer nutzt M&P nur für Ihr Carport-Projekt.</p>...
```

Neu:

```html
<div class="quiz-step" data-step="11"><h3>Wie darf Peter Sie erreichen?</h3><p class="quiz-sub">Frage 4 von 4 · Ihre Telefonnummer nutzt M&P nur für Ihr Carport-Projekt.</p><input type="text" class="quiz-input" placeholder="Vor- und Nachname *" id="name" required><input type="tel" class="quiz-input" placeholder="Telefon *" id="phone" required><input type="text" id="quizWebsite" name="website" tabindex="-1" autocomplete="off" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;" aria-hidden="true"><div class="quiz-nav"><button class="btn btn-outline" type="button" onclick="prevStep()">Zurück</button><button class="btn" type="button" onclick="submitQuiz()" id="btnSubmit" disabled>Anfrage absenden</button></div><p style="font-size:12px;color:#5f5549;margin-top:16px;text-align:center;">Keine Verpflichtung. Peter meldet sich mit einer ehrlichen ersten Einschätzung. Ein Foto oder eine Skizze können Sie später optional mitschicken.</p></div>
```

#### Step 13 weicher formulieren

Aktuell:

```html
<h3>Leider außerhalb des aktuellen Liefergebiets.</h3>
<p>Danke für Ihre Anfrage.</p>
<p>Ihr Standort liegt aktuell außerhalb des Gebiets, in dem M&P regelmäßig tätig ist.</p>
<p>Sie können die PLZ ändern oder die Anfrage später noch einmal stellen, wenn sich Ihr Standort geändert hat.</p>
```

Neu:

```html
<h3>Diese PLZ liegt außerhalb des regulären Montagegebiets.</h3>
<p>Danke für Ihre Angaben.</p>
<p>M&P ist dort aktuell nicht regelmäßig unterwegs.</p>
<p>Sie können die PLZ ändern oder später erneut anfragen, falls es um einen anderen Standort geht.</p>
```

---

### 4.2 JS-Step-Flow anpassen

#### `getStepLabel` ersetzen

Aktuell:

```js
function getStepLabel(n){return ({1:'Carport-Art',2:'Wunsch',3:'Fokus',6:'PLZ',10:'Zusammenfassung',11:'Kontakt',12:'Übertragung',13:'Außerhalb Liefergebiet'})[n]||''}
```

Neu:

```js
function getStepLabel(n){return ({1:'Carport-Art',2:'Wichtigkeit',6:'PLZ',7:'Standort-Einordnung',10:'Zusammenfassung',11:'Kontakt',12:'Übertragung',13:'Außerhalb Montagegebiet'})[n]||''}
```

#### `labelFor` sichtbare Labels anpassen

In `labelFor(field,value)` diese Labels ersetzen:

```js
carportType:{'einzelcarport':'Carport für 1 Auto','doppelcarport':'Doppelcarport','gross-carport':'Carport mit Stauraum','weiss-ich-noch-nicht':'Noch unsicher'}
```

```js
wish:{'auto-geschuetzt':'trocken und bequem aussteigen','passt-zum-haus':'passt gut zum Haus','ordentlich-geplant-gebaut':'langlebig und solide gebaut','ehrliche-erste-einschaetzung':'erst wissen, was möglich ist'}
```

`firstFocus` kann im Objekt bleiben, wird aber im neuen Flow nicht mehr befüllt. Nicht löschen, damit alte Payload-Struktur nicht bricht.

#### `updateMirrors` anpassen

Aktuell enthält `mirrorFinal` auch `firstFocus`.

Ersetze die `mirrorFinal`-Zeile so, dass nur Art + Wunsch + PLZ gezeigt werden:

```js
const fin=document.getElementById('mirrorFinal');if(fin)fin.innerHTML=[quizData.carportType?chip('Art: '+labelFor('carportType',quizData.carportType)):'',quizData.wish?chip('Wichtig: '+labelFor('wish',quizData.wish)):'',quizData.zip?chip('PLZ: '+quizData.zip):''].join('')
```

`mirrorLocation` soll nur PLZ anzeigen, nicht Straße:

```js
const loc=document.getElementById('mirrorLocation');if(loc)loc.innerHTML=chip('PLZ: '+quizData.zip);
```

#### `selectOption` beibehalten, aber `gross-carport` Extras korrigieren

Aktuell:

```js
if(field==='carportType'&&value==='gross-carport')quizData.extras=['zwei-fahrzeuge'];
```

Ersetzen durch:

```js
if(field==='carportType'&&value==='gross-carport')quizData.extras=['stauraum'];
```

#### `nextStep` ersetzen

Aktuell springt `currentStep===3` zu Step 6. Neuer Flow: Step 2 springt zu Step 6.

Ersetze die Funktion `nextStep()` vollständig durch:

```js
function nextStep(){
  if(currentStep===2){showStep(6);return}
  if(currentStep===6){
    quizData.street='';
    quizData.zip=cleanZip();
    const hint=document.getElementById('zipHint');
    if(quizData.zip.length<4){if(hint)hint.style.display='block';return}
    logQuizStep('step_completed',currentStep,true);
    showStep(7);
    setTimeout(()=>{
      if(!document.getElementById('quizOverlay')?.classList.contains('active')||currentStep!==7)return;
      if(!isAllowedZip(quizData.zip)){showStep(13);return}
      showStep(10)
    },1700);
    return
  }
  logQuizStep('step_completed',currentStep,true);
  showStep(currentStep+1)
}
```

#### `prevStep` ersetzen

Aktuell:

```js
function prevStep(){const back={6:3,10:6,11:6,13:6};showStep(back[currentStep]||Math.max(1,currentStep-1))}
```

Neu:

```js
function prevStep(){const back={6:2,10:6,11:6,13:6};showStep(back[currentStep]||Math.max(1,currentStep-1))}
```

#### `updateProgress` anpassen

Aktuell:

```js
const pct={1:10,2:34,3:58,6:72,7:78,10:86,11:94,12:100,13:72};
```

Neu:

```js
const pct={1:18,2:42,6:66,7:74,10:86,11:94,12:100,13:66};
```

#### Input Listener prüfen

Aktuell:

```js
['street','zip','name','phone'].forEach(...)
```

`street` existiert nicht sichtbar. Das ist okay, weil optional chaining verwendet wird. Trotzdem sauberer ersetzen durch:

```js
['zip','name','phone'].forEach(id=>document.getElementById(id)?.addEventListener('input',()=>{if(id==='zip')cleanZip(); if(id==='name'||id==='phone')checkContact();logInputDebounced()}));
```

---

## 5. Anfrage-Zone unten ebenfalls tonal korrigieren

### Objective
Die untere Projekt-Check-Zone darf nicht nach harter PLZ-Prüfung klingen.

### File
- Modify: `index.html`, Zeile ca. `2140`

Aktuell:

```html
<h2>Drei Fragen — dann meldet sich Peter Preissinger <span class="hl">persönlich</span>.</h2>
<p class="lead">Beschreiben Sie kurz, was Sie sich vorstellen. Die PLZ wird sofort geprüft — und Peter meldet sich mit einer ersten ehrlichen Rückmeldung.</p>
<div class="quiz-entry-points"><span>Wunsch</span><span>Standort</span><span>PLZ</span><span>Kontakt</span></div>
...
<h3>Starten Sie mit ein paar Angaben zur Situation. Die PLZ wird sofort geprüft. Alles Weitere klärt Peter persönlich.</h3>
<button ...><span>Mein Carport-Projekt starten</span><small>in 2 Min · persönlich · kostenlos</small></button>
```

Neu:

```html
<h2>Vier kurze Angaben — dann meldet sich Peter Preissinger <span class="hl">persönlich</span>.</h2>
<p class="lead">Sie geben Projektart, Wunsch, PLZ und Kontakt an. Peter schaut persönlich drauf und meldet sich mit einer ersten ehrlichen Einschätzung.</p>
<div class="quiz-entry-points"><span>Projektart</span><span>Wunsch</span><span>PLZ</span><span>Kontakt</span></div>
...
<h3>Starten Sie mit ein paar Angaben. Kein Konfigurator, kein Sofortpreis aus der Maschine — Peter schaut persönlich drauf.</h3>
<button ...><span>Projekt von Peter einschätzen lassen</span><small>60 Sekunden · kostenlos · unverbindlich</small></button>
```

---

## 6. Service-Area Copy minimal weicher machen

### Objective
Auch außerhalb des Modal soll Standort nicht nach Hürde klingen.

### File
- Modify: `index.html`, Zeilen ca. `2115–2137`

Aktuell:

```html
<p class="service-note">PLZ wird im Projekt-Check sofort geprüft. Passt der Standort, meldet sich Peter persönlich mit einer ersten Rückmeldung.</p>
```

Neu:

```html
<p class="service-note">Im Projekt-Check reicht zuerst die PLZ. So kann Peter Montagegebiet und erste Machbarkeit besser einordnen.</p>
```

FAQ-Antwort bei `Wo ist M&P Holzbau tätig?` ändern.

Aktuell:

```html
M&P betreut Carport-Projekte in Wien, Niederösterreich, dem Burgenland und ausgewählten Randgebieten. Im Projekt-Check wird die PLZ direkt geprüft.
```

Neu:

```html
M&P betreut Carport-Projekte in Wien, Niederösterreich, dem Burgenland und ausgewählten Randgebieten. Im Projekt-Check reicht zuerst die PLZ, damit Peter den Standort grob einordnen kann.
```

---

## 7. Verbotene sichtbare Begriffe nach Umsetzung

Nach den Änderungen dürfen diese sichtbaren Begriffe nicht mehr im Modal/Formular-Kontext vorkommen:

- `Standortprüfung`
- `Liefergebiet wird abgeglichen`
- `ob M&P in Ihrer Region tätig ist`
- `Was bremst Sie gerade noch?`
- `Was soll unter Dach?`

Suchen:

```bash
python3 - <<'PY'
from pathlib import Path
text=Path('index.html').read_text()
for term in ['Standortprüfung','Liefergebiet wird abgeglichen','ob M&P in Ihrer Region tätig ist','Was bremst Sie gerade noch?','Was soll unter Dach?']:
    print(term, 'FOUND' if term in text else 'OK')
PY
```

**Erwartung:** Alle zeigen `OK`.

Hinweis: Wenn `Standortprüfung` nur in internen Kommentaren vorkommt, trotzdem entfernen. Keine unnötigen Altlasten.

---

## 8. Mechanische QA lokal

### 8.1 Syntax-/Strukturcheck

Ausführen:

```bash
cd "/Users/theo/OneDrive/_REPOS/mp-holzbau-hero-preview"
python3 - <<'PY'
from pathlib import Path
text=Path('index.html').read_text()
assert text.count('<div class="quiz-overlay" id="quizOverlay"')==1
assert 'Carports, die <span class="hl">so lange halten</span> wie Ihr Haus.' in text
assert 'Projekt von Peter einschätzen lassen' in text
assert 'Worum geht es bei Ihrem Carport?' in text
assert 'Was ist Ihnen besonders wichtig?' in text
assert 'Wo ungefähr soll M&P einschätzen?' in text
assert 'Wie darf Peter Sie erreichen?' in text
assert 'Was bremst Sie gerade noch?' not in text
assert 'Liefergebiet wird abgeglichen.' not in text
print('HTML text checks passed')
PY
```

### 8.2 Lokalen Server starten

Nicht Port 8765 verwenden, der war belegt. Verwende Port 8777:

```bash
cd "/Users/theo/OneDrive/_REPOS/mp-holzbau-hero-preview"
python3 -m http.server 8777
```

Wenn Port belegt ist:

```bash
lsof -i :8777
```

Dann anderen Port nehmen, z. B. `8788`.

### 8.3 Browser-QA Desktop

Öffnen:

```text
http://127.0.0.1:8777/index.html?v=local-psycho-qa
```

Prüfen:

- Hero-H1 zeigt Komma: `Carports, die ...`
- Hero-CTA lautet: `Projekt von Peter einschätzen lassen`
- Direkt darunter steht:
  - `60 Sekunden · kostenlos · unverbindlich · kein Konfigurator`
  - `Peter Preissinger schaut persönlich drauf.`
- `Referenzen ansehen` wirkt sekundär, nicht wie Hauptbutton.
- Im oberen Wunschbild-Block gibt es nur 3 Stack-Karten.
- Danach kommt eine `Weitere Beispiele`-Sektion mit 7 kompakten Referenz-Tiles.
- Es gibt keine großen Leerräume nach dem 3er-Stack.

### 8.4 Modal-QA

Klick auf Hero-CTA.

Flow muss exakt sein:

1. Step 1: `Worum geht es bei Ihrem Carport?`
   - `Carport für 1 Auto`
   - `Doppelcarport`
   - `Carport mit Stauraum`
   - `Noch unsicher`
2. Step 2: `Was ist Ihnen besonders wichtig?`
   - `Er soll gut zum Haus passen`
   - `Trocken und bequem aussteigen`
   - `Langlebig und solide gebaut`
   - `Ich will erst wissen, was möglich ist`
3. Step 3: `Wo ungefähr soll M&P einschätzen?`
   - Hinweis: `PLZ reicht erstmal. Damit Peter Montagegebiet und erste Machbarkeit besser einordnen kann.`
4. Nach PLZ: Loading Step mit:
   - `Peter ordnet den Standort kurz ein …`
   - `Montagegebiet und Machbarkeit werden eingeordnet.`
5. Contact Step:
   - `Wie darf Peter Sie erreichen?`
   - Hinweis mit `Frage 4 von 4`

### 8.5 PLZ-Flow testen

Test 1 — gültige PLZ:

- Step 1 beliebig wählen
- Step 2 beliebig wählen
- PLZ `1010` eingeben
- Weiter
- Erwartung: Loading → Zusammenfassung → Kontakt

Test 2 — ungültige PLZ:

- Modal neu öffnen
- Step 1/2 beliebig
- PLZ `9999` eingeben
- Erwartung: Out-of-area Step mit neuem weichen Text:
  - `Diese PLZ liegt außerhalb des regulären Montagegebiets.`

Test 3 — ungültiges Format:

- PLZ `12` eingeben
- Weiter
- Erwartung: Hinweis `Bitte geben Sie eine 4-stellige PLZ ein.` bleibt sichtbar.

### 8.6 Console-QA

Im Browser DevTools prüfen:

- Keine JS-Fehler beim Öffnen des Modals.
- Keine JS-Fehler beim Durchklicken bis Kontakt.
- Keine JS-Fehler bei ungültiger PLZ.

Wenn Playwright/Browser-Tool verfügbar ist, zusätzlich per DOM prüfen:

```js
Array.from(document.querySelectorAll('h1,h2,h3,p,button,.quiz-option')).map(el=>el.innerText).filter(Boolean)
```

---

## 9. Git / Deployment-Regel

Peter will für LPs öffentliche Coolify-Previews, nicht localhost. Trotzdem: **erst lokal QA, dann commit/push/deploy.**

### 9.1 Commit

Nur relevante Dateien committen:

```bash
git add index.html docs/plans/2026-05-28_mp-holzbau-verkaufspsychologie-optimierung.md
git commit -m "feat: sharpen carport landing page conversion flow"
```

### 9.2 Push

```bash
git push origin main
```

### 9.3 Coolify Deploy

Nach Push prüfen, ob Coolify automatisch deployed. Wenn nicht, Force-Deploy für App:

- App/UUID laut Kontext: `y67wo5zm9h8dkdwintxov42x`
- Preview-Domain: `https://mp-holzbau-hero.preview.convernatics.eu/`

Nur vorhandenen Deploy-Workflow verwenden. Keine neue App anlegen.

### 9.4 Live-Verification

Nach Deployment öffnen:

```text
https://mp-holzbau-hero.preview.convernatics.eu/?v=<NEUER_COMMIT_SHA>
```

Prüfen:

- Hero-H1 korrigiert
- Hero-CTA + Microcopy sichtbar
- 3 Referenzen oben
- 7 Referenzen später
- Modal 4-Fragen-Flow funktioniert
- PLZ gültig/ungültig funktioniert
- Console ohne Fehler
- Mobile first screen nicht überladen

---

## 10. Abschlussmeldung an Peter

Kurz melden, keine Romane:

```text
Erledigt.

Geändert:
- Hero-CTA entlastet: 60 Sekunden · kostenlos · unverbindlich · kein Konfigurator
- CTA auf Peter-Persönlichkeit gedreht
- obere Referenzstrecke von 10 auf 3 gekürzt, Rest in spätere Galerie verschoben
- Modal auf 4 klare Fragen reduziert
- PLZ-Step weicher formuliert, nicht mehr als harte Standortprüfung
- H1-Komma korrigiert

Preview: https://mp-holzbau-hero.preview.convernatics.eu/?v=<commit>
```

---

## 11. Nicht machen

- Keine neue Bildgenerierung.
- Keine zusätzlichen Fragen ins Modal einbauen.
- Keine E-Mail-Pflicht ergänzen.
- Keine Adresse/Straße ergänzen.
- Keine neuen Sales-Sektionen hinzufügen.
- Keine Preis-Sektion neu bauen.
- Keine Dark-Pattern-Dringlichkeit einbauen.
- Keine großen Farb-/Designänderungen.
- Nicht Thomas-HTML übernehmen.
- Nicht mehr als `index.html` anfassen, außer diese Plan-Datei ist noch nicht committed.

---

## 12. Acceptance Criteria

Die Aufgabe ist erst fertig, wenn alle Punkte erfüllt sind:

- [ ] `index.html` enthält `Carports, die ...`
- [ ] Hero-CTA lautet `Projekt von Peter einschätzen lassen`
- [ ] Hero-Microcopy steht sichtbar unter dem CTA
- [ ] Oben im Wunschbild-Stack sind genau 3 Karten
- [ ] Spätere Galerie enthält genau 7 weitere Referenzen
- [ ] Modal Step 1 lautet `Worum geht es bei Ihrem Carport?`
- [ ] Modal Step 2 lautet `Was ist Ihnen besonders wichtig?`
- [ ] Modal Step 3 lautet `Wo ungefähr soll M&P einschätzen?`
- [ ] Modal Step 4 lautet `Wie darf Peter Sie erreichen?`
- [ ] Verbotene Begriffe sind nicht mehr enthalten
- [ ] Gültige PLZ führt zum Kontakt-Step
- [ ] Ungültige PLZ führt zum weichen Out-of-area-Step
- [ ] Browser Console ohne JS-Fehler
- [ ] Mobile Hero bleibt lesbar und CTA bleibt ohne langes Suchen erreichbar
- [ ] Public Coolify Preview mit neuem Commit-SHA geprüft
