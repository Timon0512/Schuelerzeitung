# Übergabe — 26.09.2026

## Paket 7 – Betrieb implementiert, Gesamtabnahme mit externen Blockern

README.md, diese Übergabe (gemeint mit UBERGABE.md), Paketprompt 07, PRODUCT.md und
beide Konzepte gelesen. Vorhandene uncommittete Paket-6-Änderungen erhalten.
Keine Serveränderung, Datenbankmigration, öffentliche Inbetriebnahme oder Commit.
Testdatenbank-Bestätigung erneut angefragt; bis Abschluss nicht eingegangen.

### Ergebnis

- `Dockerfile`, `.dockerignore`, `compose.production.yaml`: Python 3.12.14 und uv
  0.12.13 mit Registry-Digests, gelockte Installation einschließlich Gunicorn 23,
  collectstatic beim Build, UID/GID 10001, schreibgeschütztes Root-Dateisystem,
  temporärer Speicher, persistenter privater Bind-Mount, ausschließlich lokaler Port.
  Kein DB-Container, keine DB-Portfreigabe, keine Geheimnisse im Buildkontext.
- `deploy/gunicorn.conf.py`, `production.env.example`, `compose.env`,
  `nginx.conf.example`: konfigurierbarer Host-PostgreSQL-Zugang, HTTPS-Proxyvorlage
  mit Body-/Loginlimit, getrennte statische Auslieferung und gesperrte Dateipfade.
  Öffentliche und private Uploads bleiben ausschließlich über Django-Rechteprüfungen
  erreichbar. Kein automatischer Proxy- oder Migrationsstart.
- `config/settings.py`: Medien-/Static-Pfade konfigurierbar, explizites Proxy-Proto-
  Vertrauen, HSTS-Alter, Produktionssperren gegen Debug, schwachen Schlüssel,
  Wildcard-Hosts und unsichere CSRF-Origins. `tests/test_deployment_unit.py` prüft
  diese Grenzen ohne DB. `tests/container_smoke.py` prüft das tatsächlich gebaute Image.
- `docs/BETRIEB.md`: Start/Updates, DB-Rechte, namentliche Konten, Proxyvertrauen,
  Schreibstopp als Konsistenzstrategie, gemeinsames Sicherungsverzeichnis mit Kennung,
  Prüfsummen und COMPLETE-Markierung, pg_dump/pg_restore und Medienarchiv,
  isolierter Restore-Ablauf sowie Startblocker. Keine Sicherung echter Daten erstellt.
- `docs/LEHRKRAFT.md`: kurze deutsche Anleitung von Einsendungsprüfung über Entwurf,
  Bilder und Vorschau bis Veröffentlichung/Rücknahme. README und Paketstatus ergänzt.

### Tatsächlich ausgeführte Prüfungen

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv add 'gunicorn>=23,<24' --no-sync --python 'C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& '.\.venv-backend\Scripts\python.exe' manage.py check
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration tests.test_editorial_unit tests.test_frontend_unit tests.test_interactions_unit -q
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_deployment_unit -q
& '.\.venv-backend\Scripts\python.exe' -m tests.frontend_fixtures
$env:PLAYWRIGHT_MODULE='C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
& 'C:\Program Files\nodejs\node.exe' tests/browser_frontend.cjs
& 'C:\Program Files\nodejs\node.exe' tests/browser_editor.cjs
docker build -t kaktus:package7 .
docker compose --env-file deploy/compose.env -f compose.production.yaml config --no-env-resolution --quiet
docker run --rm --network none --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges -e DJANGO_ENV=production -e DJANGO_DEBUG=false -e DJANGO_SECRET_KEY=test-only-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ -e DJANGO_ALLOWED_HOSTS=zeitung.example.invalid -e DJANGO_CSRF_TRUSTED_ORIGINS=https://zeitung.example.invalid -e DJANGO_TRUST_PROXY_PROTO=true -e DJANGO_HSTS_SECONDS=31536000 kaktus:package7 python manage.py check --deploy --fail-level WARNING
docker run --rm --network none --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --mount "type=bind,source=$((Get-Location).Path)/tests/container_smoke.py,target=/tmp/container_smoke.py,readonly" -e DJANGO_ENV=production -e DJANGO_DEBUG=false -e DJANGO_SECRET_KEY=test-only-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ -e DJANGO_ALLOWED_HOSTS=zeitung.example.invalid -e DJANGO_CSRF_TRUSTED_ORIGINS=https://zeitung.example.invalid -e DJANGO_TRUST_PROXY_PROTO=true kaktus:package7 python /tmp/container_smoke.py
& '.\.venv-backend\Scripts\python.exe' manage.py test news --noinput
git diff --check
```

- Systemcheck ohne Probleme, **25 bestehende plus 3 neue datenbankfreie Tests bestanden**.
- **24 Seitenzustände bei 360/768/1440 px bestanden**, inklusive Navigation ohne JS,
  Fokus, Bildern/Schriften und Überläufen; keine JS-Fehler/externen Requests.
  **Editor bei 1280/390 px bestanden**. Chromium benötigte nach EPERM genehmigte
  Ausführung außerhalb der Sandbox; Screenshots in `.qa/`.
- **Containerbuild bestanden**, 139 statische Dateien gesammelt; zweiter Build mit
  fixierten Digests ebenfalls erfolgreich. Compose-Strukturprüfung bestanden ohne
  Auflösung der noch nicht angelegten Produktions-env-Datei. Beim ersten Compose-
  Aufruf wurde die Entwickler-.env automatisch interpoliert; Dokumentation verwendet
  deshalb jetzt ausdrücklich die leere `deploy/compose.env` und rohes Runtime-env_file.
- Produktionscheck meldet **genau W005/W021**, weil HSTS für Subdomains und Preload
  bewusst nicht ohne Domainfreigabe aktiviert wird. Daher erwarteter Exitcode 1 bei
  `--fail-level WARNING`; kein behaupteter warnungsfreier Deploymentcheck.
- **Gunicorn-Smoke bestanden**, ohne Netzwerk und DB: UID 10001, keine .env im Image,
  statische Assets vorhanden, Login mit Secure-CSRF-Cookie über vertrauenswürdigen
  HTTPS-Header, private Medien leiten anonyme Besucher zur Anmeldung. Erster Versuch
  hatte zu kurze Startwartezeit; nach Anpassung auf 10 Sekunden bestanden.
- **31 PostgreSQL-Tests gefunden, vor DB-Zugriff gesperrt**, da Freigabe fehlt.
  Rechte-/Medienregeln mit realen Datensätzen, Konkurrenztests und der gespeicherte
  vollständige Redaktionsablauf bleiben ungeprüft. Kein SQLite-Ersatz.
- `git diff --check` ohne Whitespacefehler. Kein Schema geändert.

### Offene Abnahme / nächster Einstieg

1. Entbehrliches PostgreSQL-Testziel ausdrücklich bestätigen und 31 Integrationstests
   ausführen; anschließend den echten Redaktionsablauf mit fiktiven Daten abnehmen.
2. Isoliertes Restore-Ziel bereitstellen und Backup/Restore mit gemeinsamem fiktivem
   Daten-/Medienbestand nach `docs/BETRIEB.md` wirklich durchführen. **Restore ungeprüft.**
3. Nginx-Vorlage auf dem Zielhost an Domain/Zertifikate anpassen, `nginx -t`, HTTPS,
   Headerüberschreibung, Loginlimit, Uploadgrenze, Medienrücknahme und DB-Firewall
   prüfen. Diese reale Proxy-/Serverprüfung wurde nicht durchgeführt.
4. Schultexte, Aufbewahrungsfristen, Namens-/Bildfreigaben und Lehrkraftabnahme offen.
   Paket 7 ist implementiert, aber die Gesamtanwendung noch nicht zum Start abgenommen.
   Kein weiteres Arbeitspaket automatisch begonnen.

---

## Paket 6 – Öffentliche Interaktionen implementiert, PostgreSQL-Abnahme offen

Gelesen: `README.md`, vorhandene `06-interaktionen.md`, diese Übergabe, `PRODUCT.md`, beide Konzepte und die betroffenen Backend-/Frontend-Dateien. Die gesuchte `UBERGABE.md` heißt `docs/arbeitspakete/UEBERGABE.md`. Der freigegebene Designvertrag wurde beibehalten. Anders als in der historischen Übergabe sind inzwischen `.env`, PostgreSQL-Verbindung und ein Git-Repository vorhanden. Geheimnisse wurden nicht ausgegeben oder verändert. `KAKTUS_TEST_DATABASE_CONFIRMED` ist weiterhin nicht `true`; die Bestätigung für die entbehrliche Testdatenbank wurde angefragt und liegt bislang nicht vor. Keine Datenbank angelegt, geleert oder migriert; kein SQLite-Ersatz und kein Datenbankcontainer.

### Ergebnis

- `submissions/views.py`, `services.py`, `news/submission_ui.py`: echte öffentliche GET/POST-Einreichung, ausschließlich aktive Rubriken, 120/40/200/50.000 Zeichen, erforderliche Urheberschaft, Honeypot, optional ein tatsächlich dekodiertes Bild. Neue WebP-Dateien ohne Metadaten bleiben privat. Fehler erhalten Texte und Auswahl; Dateien müssen erneut ausgewählt werden. Erfolgreiche Speicherung führt per Redirect zur einmaligen sitzungsgebundenen Empfangsbestätigung. Keine personenbezogenen Inhalte in eigenen Logs; POST-Daten und Speicherfunktion für Django-Fehlerberichte geschützt.
- `config/interaction_limits.py`, `reactions/limits.py`, `models.py`: Request-Grenzen vor Multipart-/CSRF-Verarbeitung (11 MB/4 KB), öffentliche Feld-/Dateianzahlgrenzen ohne Einschränkung der Adminformulare, Datenbank-Rate-Limits standardmäßig 5 Einreichungsversuche/Stunde und 60 Herz-POSTs/Minute. Auch fehlerhafte/CSRF-abgewiesene POSTs zählen. Atomare PostgreSQL-Upserts vermeiden Konkurrenzfehler auch beim Fensterwechsel. Fensterabhängige HMAC-IP-Schlüssel, keine Klartext-IP in der Tabelle, abgelaufene Fenster werden bei weiteren Interaktionen entfernt. Proxy-Ketten werden nur hinter explizit konfigurierten vertrauenswürdigen Netzen ausgewertet. 429 enthält `Retry-After`.
- `reactions/services.py`, `views.py`, `news/public.py`, `config/urls.py`: öffentlicher POST-Herzweg mit CSRF und zufälligem langlebigem HttpOnly-/SameSite-Cookie (Secure in Produktion). Gültiges zurückgesendetes Cookie ist Voraussetzung; nur SHA-256-Hash wird gespeichert. Ein Artikellock serialisiert Setzen/Entfernen und der Unique-Constraint bleibt aktiv. Zwei gleichzeitige Klicks ergeben wieder den Ausgangszustand. GET-Ansicht liest tatsächlichen Zustand und Zähler. Rangliste verwendet einen gemeinsamen Zeitstempel für das Sieben-Tage-Fenster, maximal fünf öffentliche Beiträge, ohne Nullwerte und mit stabiler Sortierung.
- `purge_interactions`: standardmäßig reine Vorschau mit Datensatz-/Bildanzahlen. `--execute` benötigt explizit bestätigte positive Fristen; Frist 0 deaktiviert die jeweilige Inhaltslöschung. Keine automatische Planung. Dateien werden erst nach Commit und nur ohne Artikel-/Einsendungs-/Brandingverweise entfernt. Übernommene Artikel und deren Bilder bleiben erhalten.
- `Media.submission_origin`, Medienauswahl und Logo-/Privatrouten: Herkunft bleibt nach Löschung einer Einsendung erhalten. Dadurch wird ein ehemaliges Einsendungsbild nicht automatisch allgemeines Redaktionsbild oder öffentliches Logo. Migration `news.0003_media_submission_origin` markiert auch bestehende Einsendungsbilder; `reactions.0003_ratelimitwindow` ergänzt Rate-Limit-Tabelle.
- `README.md`, `.env.example`, Paketübersicht aktualisiert. Alle Limits/Fristen dokumentiert. Bestehende Rechtstext-/Betriebsblocker bleiben offen. Paket 7 nicht begonnen.

### Tatsächlich ausgeführte Prüfungen

```powershell
& '.\.venv-backend\Scripts\python.exe' manage.py check
& '.\.venv-backend\Scripts\python.exe' manage.py makemigrations news reactions --noinput
& '.\.venv-backend\Scripts\python.exe' manage.py makemigrations --check --dry-run
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration tests.test_editorial_unit tests.test_frontend_unit tests.test_interactions_unit -q
& '.\.venv-backend\Scripts\python.exe' -m tests.frontend_fixtures
$env:PLAYWRIGHT_MODULE='C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
& 'C:\Program Files\nodejs\node.exe' tests/browser_frontend.cjs
& '.\.venv-backend\Scripts\python.exe' manage.py test news --noinput
git diff --check
```

- Django-Systemcheck: **0 Probleme**. Zwei Migrationen erzeugt; abschließend **No changes detected**. Die Migrationshistorienprüfung scheiterte zunächst an Namensauflösung in der Sandbox, funktionierte bei genehmigter rein lesender Wiederholung außerhalb der Sandbox. Keine Migration auf bestehende Datenbank angewendet.
- **25 datenbankfreie Tests bestanden**: die bisherigen 18 plus sieben neue Interaktionsprüfungen (IP-/Proxy-Vertrauensgrenze, rotierende Schlüssel, sichere Cookie-Eigenschaften, Body-/Feldgrenzen vor Weiterverarbeitung, Multipart-Wiederlesbarkeit, Honeypot/Feld-/Dateivalidierung, Löschsperre). Erwartete Warnungen betreffen ausschließlich das isolierte Überschreiben von Datenbankeinstellungen in Konfigurationstests.
- **24 echte Template-Fixtures bei 360, 768 und 1440 Pixeln bestanden**, einschließlich Formularzuständen, Schriften/Bildern, Überläufen, Fokus/Menü und Navigation ohne JavaScript. Keine JS-Fehler oder externen Requests. Chromium war zunächst durch `spawn EPERM` blockiert; genehmigte Wiederholung außerhalb der Sandbox bestanden. Diese Prüfung bestätigt Layout/Bedienung, keine gespeicherten Interaktionen.
- PostgreSQL: **31 Tests gefunden, vor Datenbankzugriff gesperrt**. Zehn neue Tests in `news/test_interactions.py` decken private Einreichung/Empfang, ungültige Angaben/Dateien, CSRF/Rate-Limits, Cookie/Toggle/Sichtbarkeit, Sieben-Tage-Grenze/Ties/Top-5, vollständigen redaktionellen Ablauf, Löschvorschau/Bilderhalt sowie parallele Klicks und Fensterwechsel ab. Diese Tests wurden mangels Bestätigung **nicht ausgeführt**; Konkurrenzverhalten und vollständige End-to-End-Abnahme werden nicht als nachgewiesen ausgegeben.
- `git diff --check`: keine Whitespace-Fehler; lediglich übliche Git-Hinweise zur LF/CRLF-Konvertierung. Keine fremden Änderungen überschrieben, kein Commit erstellt.

### Offene Abnahme / Weiterarbeit

1. Betreiber bestätigt, dass `PGTESTDATABASE` ausschließlich entbehrliche Testdaten enthält. Dann `KAKTUS_TEST_DATABASE_CONFIRMED=true` für den Testprozess setzen und alle 31 PostgreSQL-Tests ausführen. `--keepdb` nur bei ausdrücklich vorab bereitgestelltem leerem Testziel; niemals die Entwicklungs-/Produktivdatenbank als Testziel verwenden. Fehler vor Abnahme korrigieren.
2. Danach die zwei Migrationen auf der freigegebenen Entwicklungsdatenbank anwenden und den echten Formular-/Redaktionsablauf im Browser prüfen. Die Oberfläche ist im Code aktiviert und benötigt das neue Schema.
3. Fristen, Rechtstexte und reale Proxy-Konfiguration bleiben vor Inbetriebnahme zu bestätigen. Feste Rate-Fenster erlauben zwei Kontingente direkt an der Grenze; sie sind keine gleitenden Fenster. Eine Body-Grenze am Reverse-Proxy ist zusätzlich erforderlich, da Webserver/ASGI schon vor Django puffern können. Keine Behauptung eines produktionsfertigen Deployments.
4. Paket 7 kann anschließend Betrieb/Gesamtabnahme auf diesen Schreibwegen und `purge_interactions` aufbauen; kein automatischer Folgeauftrag.

---

## Paket 5 – Öffentliches Frontend implementiert, PostgreSQL-Abnahme offen

Vor Umsetzung gelesen: `README.md`, diese Übergabe, vorhandener Paketprompt `05-frontend.md`, `PRODUCT.md`, `DESIGN.md`, Konzepte und freigegebene Option-A-Mockups. Die gesuchte `UBERGABE.md` heißt im Projekt `docs/arbeitspakete/UEBERGABE.md`. Designfreigabe unverändert gültig; keine neue Auswahl nötig. Weiterhin keine `.env` oder bestätigte PostgreSQL-Entwicklungs-/Testverbindung vorgefunden. Keine Datenbank verändert, kein SQLite-Fallback, keine Datenbankcontainer. Paket 6 wurde nicht begonnen.

### Ergebnis und Dateien

- `news/public.py`, `config/urls.py`, `templates/news/`: Startseite mit Aufmacher, Nebenartikeln, aktuellen Beiträgen, Rubrikbereichen, Wochenrangliste und Pausenecke; Artikelübersicht, Rubrik-/Autorenlisten, Detailseiten, Suche samt Pagination, Mitmachen, Über uns sowie 404/500 und Leerzustände. Alle Artikelauswahlen laufen über `public()`; Suchabfragen begrenzen den Begriff auf 200 Zeichen und berücksichtigen nur freigegebene Autorennamen. Artikelweiterleitungen prüfen weiterhin die Sichtbarkeit und sind absichtlich nicht dauerhaft cachebar.
- `news/static/news/public.css`, `public.js`: Design-A-Farb-/Abstandswerte, 1280 px Inhaltsbreite, Serif-/Sans-Hierarchie, 2:1-Aufmacher, responsive Listen/Formulare, reservierte Bildflächen, Fokusrahmen. Mobile Navigation mit Fokusführung, Escape, Schließen und inaktivem Hintergrund; ohne JavaScript bleibt die Navigation sichtbar. Keine externen Browserdienste.
- `news/static/news/fonts/`: Source Serif 4 und Source Sans 3 lokal als variable TTF samt OFL-Lizenzen und Herkunft. `admin.css` nutzt nun ebenfalls die lokale UI-Schrift. `school-logo.jpg` ist eine unveränderte Kopie des vorhandenen kleinen Schullogos.
- `news/content.py`, `news/views.py`: öffentliche Artikel und private POST-Vorschau verwenden dieselbe `news/article.html` über `article_context`. Aktuelle Alt-Texte/Bildunterschriften werden neu gerendert; eine Zuordnungsbildunterschrift hat Vorrang vor der Medienbildunterschrift. Vorschau bleibt `no-store`/`noindex`, Bilder verwenden geschützte Routen. Inline-sichere Bildwrapper verhindern ungültige Figuren innerhalb von Editorabsätzen.
- `/zeitungslogo` liefert nur das explizit konfigurierte Logo aus, mit `no-store`/`nosniff`. Einsendungsbilder sind sowohl in der Adminauswahl als auch in der Route ausgeschlossen. Keine Freigabe von `MEDIA_ROOT`.
- `news/sitemaps.py`: Sitemapindex und paginierte Teilsitemaps für öffentliche Artikel, aktive Rubriken, freigegebene Autoren mit öffentlichen Artikeln und Informationsseiten. Canonical-/Open-Graph-Metadaten; Suche, Vorschau, unfertige Rechtstexte und Einreichung ohne Indexierung. Impressum und Datenschutz bleiben ausdrücklich ausstehende Schultexte.
- `news/submission_ui.py`, `templates/news/submission.html`, `heart.html`: Oberfläche mit Labels, Hilfen, Feldfehlern, Fehlerübersicht, erhaltenen Eingaben, Senden/Empfang sowie ungesetztem/gesetztem/laufendem/fehlgeschlagenem Herz. Öffentlich sind Einreichung und Herzen ausdrücklich deaktiviert; Einreichungs-POST wird mit 405 abgelehnt. Zustände nur in QA-Fixtures simuliert, keine Erfolgsrückmeldung ohne echte Verarbeitung.
- `news/test_public.py`, `tests/test_frontend_unit.py`, `tests/frontend_fixtures.py`, `tests/browser_frontend.cjs`: zusätzliche PostgreSQL-Integrationstests und datenbankfreie Vorlagen-/Browserprüfungen. Fixtures verwenden klar fiktive Texte und beschriftete Testflächen, keine angeblichen Nachrichten oder Schulfotos. Sie sind keine öffentlichen Routen.

### Ausgeführte Prüfungen

```powershell
$env:DJANGO_SECRET_KEY='local-check-only-not-for-serving'
& '.\.venv-backend\Scripts\python.exe' manage.py check
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration tests.test_editorial_unit tests.test_frontend_unit -q
& '.\.venv-backend\Scripts\python.exe' -m tests.frontend_fixtures
$env:PLAYWRIGHT_MODULE='C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
& 'C:\Program Files\nodejs\node.exe' tests/browser_frontend.cjs
& '.\.venv-backend\Scripts\python.exe' manage.py test news --noinput
```

- Systemcheck: **0 Probleme**. **18 datenbankfreie Tests bestanden** (5 Konfiguration, 8 Redaktion, 5 Frontend). Die Frontendtests verwenden `SimpleTestCase` und sperren unbeabsichtigte Datenbankabfragen.
- **24 echte Template-Fixtures bei 360, 768 und 1440 px bestanden**: keine horizontalen Überläufe, je eine H1, geladene lokale Schrift-/Bilddateien, Tastatur-Sprunglink und Fokusrahmen, mobiles Menü mit Fokusumlauf/Escape/Rückkehr, erhaltene Formulareingaben und deaktivierte Aktionen. Zusätzliche Navigation ohne JavaScript bestanden. Keine JavaScript-Ausnahmen, keine externen Browseranfragen. Screenshots unter `.qa/frontend/`.
- Der erste Browserlauf scheiterte an `spawn EPERM`; genehmigte Ausführung außerhalb der Sandbox funktionierte. Eine zunächst zu frühe Bildprüfung wurde korrigiert: Lazy-Images außerhalb des Viewports müssen vor Ganzseitenaufnahmen erst geladen/dekodiert werden. Kein Produktfehler. Die isolierten Artikel-Fixtures wurden auf tatsächlich gleiche Rubrik der verwandten Beiträge korrigiert; die produktive Auswahl war bereits gefiltert.
- Kontraste rechnerisch gegen die Designfarben geprüft: Haupttext/Papier **14,80:1**, Metadaten/Papier **6,53:1**, Akzent/Papier **5,14:1**, Weiß/Akzent **5,45:1**, Fehler/Papier **7,03:1**.
- Impeccable-Kontext und mechanischer Detektor einmal ausgeführt. Detektor kann Django-`static`-Tags nicht auflösen; seine Standard-Schwarz-Meldungen sind daher nicht aussagekräftig. Schriftgrößen-Advisories umfassen im schriftlichen Vertrag ausdrücklich erlaubte Größen. Unabhängige visuelle Abschlussprüfung: **ship im Umfang der Paket-5-Oberfläche**, keine notwendigen Korrekturen. Dokumentationsprüfung bestätigt vorhandene Designwerte; `DESIGN.md` und `.impeccable/design.json` bleiben unverändert. Desktop-Textbilder werden als gut lesbare Blöcke statt seitlicher Bildanordnung des Rastermockups dargestellt; schriftlicher Vertrag verlangt keinen Desktop-Float. Keine pixelgenaue Comp-Diff- oder vollständige WCAG-Abnahme behauptet.
- PostgreSQL: **21 Tests gefunden und vor Datenbankzugriff gesperrt**. Die sieben neuen Tests decken öffentliche Sichtbarkeit über Listen/Suche/Sitemap, private Autorennamen, Weiterleitungen/Rücknahmen, Pagination/verwandte Rubrik, Wochenherzen, Bildmetadaten/Logo und schreibgeschützte Einreichung ab. Diese Integration ist ohne bestätigte Testverbindung noch nicht nachgewiesen.
- Keine Modelländerung und keine neue Migration. Verzeichnis weiterhin kein Git-Repository; kein Commit erstellt.

### Offen und Einstieg für Paket 6

1. Bestätigte PostgreSQL-Entwicklungs-/Testverbindung bereitstellen und alle 21 Integrationstests ausführen. Danach tatsächliche Adminvorschau und öffentliche Seiten mit gespeicherten Medien gemeinsam prüfen. Die Fixture-Abnahme ersetzt das nicht.
2. Paket 6 bindet `SubmissionUIForm`/Zustandsvorlagen an den abgesicherten Einreichungsservice sowie echte Herz-Schreibwege an. Das UI-Formular allein validiert keine Bildinhalte: zwingend `decode_image`, Größenbegrenzung, CSRF, Rate-Limits und Honeypot ergänzen. Erst danach `submission_enabled`/`hearts_enabled` setzen und den Zustand aus bestätigten Serverdaten ableiten. Kein Herz-Identifikationscookie in Paket 5; das Formular verwendet bereits den normalen Django-CSRF-Token.
3. Übergebene UI-Kontextwerte: Einreichung `form`, `submission_enabled`, `submission_state='pending'`, `submission_received`; Herz `hearts_enabled`, `heart_action`, `heart_state`, `heart_selected`, `heart_count`. Das Herz-Fehlertemplate erwartet den unveränderten bisherigen Zähler/Zustand.
4. Vor öffentlicher Inbetriebnahme bleiben bestätigte Rechts-/Schultexte, echte Inhalte/Bildfreigaben und Betriebsabnahme erforderlich. Die bestehende PRODUCT.md-Schemawarnung betrifft ältere Skill-Metadaten; eine mögliche Aktualisierung über Impeccable `init` wurde nicht als Nebenarbeit ausgeführt.

---

## Paket 4 – Redaktion implementiert, PostgreSQL-Abnahme weiterhin offen

Vor Umsetzung gelesen: `README.md`, diese Übergabe, vorhandener Paketprompt `04-redaktion.md`, `PRODUCT.md`, `DESIGN.md` und beide Konzeptdateien. `UBERGABE.md` existiert nicht; die vorhandene Übergabedatei heißt `UEBERGABE.md`. Es gibt weiterhin keine `.env` und keine bereitgestellte PostgreSQL-Verbindung. Keine Datenbank wurde angelegt oder verändert; kein SQLite-Ersatz, keine Datenbankcontainer. Paket 5 wurde nicht begonnen.

### Ergebnis und Dateien

- `news/admin.py`, `news/forms.py`, `submissions/admin.py`: deutscher Admin für Artikel, Bilder, Autoren und Einsendungen; Listen, Filter, Suchfelder, Veröffentlichungs-/Rücknahme-/Aufmacheraktionen und bewusste Einsendungsübernahme. Rubriken und Branding bleiben den entsprechend berechtigten Administrationskonten vorbehalten.
- `news/services.py`: transaktionaler Redaktionsschreibweg mit erneuter Rechteprüfung, geschützten Statusfeldern und synchronisierten Bildzuordnungen. Veröffentlichte Artikel dürfen ohne Freigaberecht auch nicht indirekt über gemeinsame Medien oder Autoren verändert werden. Die bestehenden Advisory Locks serialisieren Inhaltsänderungen.
- `submissions/services.py`: idempotente, gesperrte Übernahme in einen verknüpften Entwurf. Klartext wird escaped, Name und Klasse nicht kopiert, Autor bleibt bewusst leer. Das Speichern einer internen Notiz überschreibt keine parallele Übernahme.
- `news/content.py`, `news/models.py`: zentrale HTML-Positivliste; Skripte, Events, Styles, Einbettungen und gefährliche Linkprotokolle entfernt. Bild-Tags benötigen `data-media-id` und eine explizite zugelassene Artikelzuordnung; URLs und Alternativtexte entstehen serverseitig. Redaktionelle Uploads sind eine gemeinsame Bildbibliothek, private Einsendungsanhänge erst nach Übernahme für den verknüpften Artikel auswählbar.
- `news/uploads.py`: maximal 10 MB/25 Megapixel; tatsächlicher JPEG-/PNG-/WebP-Typ, vollständige Dekodierung, keine Animationen, EXIF-Ausrichtung und neue WebP-Datei ohne Metadaten. Alt-Text im Uploadformular verpflichtend, Bildunterschrift optional.
- `frontend/`, `package.json`, `package-lock.json`, `news/static/news/`: Tiptap 3.31.3 lokal mit esbuild gebündelt, inklusive gesammelter Drittlizenzen. Keine Cloud, kein CDN, kein laufender Frontend-Server. Interne Bildauswahl, deutsche Werkzeugleiste, Tastaturfokus und mobile Umbrüche. Adminfarben folgen DESIGN.md; lokale Schriftdateien bleiben wie vorgesehen Paket 5, aktuell Arial/Georgia-Fallbacks.
- `news/views.py`, `config/urls.py`, `templates/`: private Medienroute mit Staff-/Leserechten; CSRF-geschützte POST-Vorschau ungespeicherter Daten, `no-store`, `noindex`. Die Vorschau ist eine vorbereitende Ansicht, noch nicht die finale öffentliche Artikelvorlage.
- `tests/test_editorial_unit.py`, `news/test_editorial.py`, `tests/browser_editor.cjs`: Offline-Sicherheitsprüfungen, PostgreSQL-Integrationstests und isolierte Browserprüfungen des tatsächlich ausgelieferten Editorbundles.

### Tatsächlich ausgeführte Prüfungen

PowerShell im Projektroot, ausschließlich temporärer Offline-Schlüssel:

```powershell
$env:DJANGO_SECRET_KEY='local-check-only-not-for-serving'
& '.\.venv-backend\Scripts\python.exe' manage.py check
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration tests.test_editorial_unit -v
& '.\.venv-backend\Scripts\python.exe' manage.py test news --noinput
$env:npm_config_cache=(Join-Path (Get-Location) '.npm-cache')
& 'C:\Program Files\nodejs\npm.cmd' install --no-audit --no-fund
& 'C:\Program Files\nodejs\npm.cmd' run build
& 'C:\Program Files\nodejs\node.exe' frontend/licenses.cjs
$env:PLAYWRIGHT_MODULE='C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
& 'C:\Program Files\nodejs\node.exe' tests/browser_editor.cjs
```

- Django-Systemcheck: **0 Probleme**. Konfigurationstests: **5 bestanden**. Redaktionstests ohne Datenbank: **8 bestanden**, einschließlich Templates, XSS/Protokollen, internen Bildreferenzen, Metadatenentfernung, Dateigrößen-/Pixelgrenzen, ungültigen Bildern und Animationen. Abschließender kombinierter Lauf mit `-m unittest tests.test_configuration tests.test_editorial_unit -q`: **13 Tests bestanden**.
- PostgreSQL: **14 Tests gefunden, vor Datenbankzugriff gesperrt**. Die fünf neuen Integrationstests decken Standardformular-/Aktionsrechte, gemeinsame Autorendaten, Übernahme, private Bilder und Vorschau samt CSRF ab. Rollen/Transaktionen/Admin-Requests sind damit noch nicht gegen PostgreSQL nachgewiesen.
- Abhängigkeiten installiert, Editor erfolgreich gebündelt (~385 KB), Drittlizenzen erzeugt. Esbuild scheiterte zunächst an der Sandbox-Verzeichnisauflösung; der genehmigte Build außerhalb der Sandbox bestand.
- Browser: **1280 und 390 Pixel bestanden**, Formatierung, interner Bildknoten, Tastaturfokus, Submit-Synchronisierung, kein horizontaler Überlauf und keine JavaScript-Ausnahmen. Screenshots unter `.qa/editor-1280.png` und `.qa/editor-390.png` angesehen. Dies war eine isolierte Editor-Fixture, keine angemeldete vollständige Admin-Sitzung. Testkorrekturen betrafen Fokusmodalität und getrennte Browserseiten, keine verdeckten Produktfehler. Chromium benötigte wegen `spawn EPERM` genehmigte Ausführung außerhalb der Sandbox.
- `makemigrations --check --dry-run`: **No changes detected**; temporär `PGHOST=127.0.0.1`, `PGPORT=1`, `PGDATABASE=kaktus_schema`. Erwartete Verbindungswarnung; keine Prüfung der Datenbankhistorie möglich. Keine neue Migration erforderlich.
- Impeccable-Kontext und mechanischer Detektor ausgeführt. Detektor konnte Django-Template-`static`-Tags nicht auflösen und meldete deshalb zwei advisory Standard-Schwarz-Farben; tatsächliche Editor-CSS und Browseransichten geprüft. Legacy-Metadaten in PRODUCT.md gemeldet, ohne den freigegebenen Produkt-/Designvertrag umzuschreiben.

### Noch offen und Einstieg für Paket 5

1. Betreiber stellt die ausdrücklich freigegebene Entwicklungsdatenbank und separate entbehrliche Testdatenbank lokal bereit; anschließend `manage.py test news --noinput` (oder `--keepdb` nur für entsprechend bereitgestelltes Testziel). Ohne das bleiben Paket 3/4 nicht vollständig abgenommen.
2. Nach Migration komplette Admin-Abläufe mit beiden Gruppen auf Desktop/Mobil prüfen: Upload, Entwurf, Vorschau, Übernahme, Veröffentlichen, Aufmacher, Zurückziehen und geteilte Medien. Der isolierte Browser-Test ersetzt dies nicht.
3. Paket 5 übernimmt die öffentliche Artikelvorlage und bindet die Vorschau an dieselbe Vorlage. Aktuelle Alt-Texte/Bildunterschriften beim Rendern aus Medien/Zuordnungen beziehen; `clean_body(..., private=True)` liefert bereits die private Vorschauvariante. Öffentliche Auswahlen weiterhin ausschließlich über `public()`.
4. Keine dauerhafte Dateisystem-URL für Medien freigeben. Logoauslieferung bleibt ein eigener, expliziter Fall in Paket 5. Das öffentliche Einreichungsformular in Paket 6 muss `decode_image` wiederverwenden.
5. Verzeichnis ist weiterhin kein Git-Repository; kein Commit erstellt.

---

## Paket 3 – Implementierung und offener Abnahmeblocker

Die Backend-Grundlage ist implementiert. **Paket 3 ist noch nicht vollständig abgenommen:** Es wurden weder lokale Datenbank-Umgebungsvariablen noch eine `.env` vorgefunden. Die angefragte separate Entwicklungs-/Testverbindung liegt noch nicht vor. Keine Serverdatenbank wurde angelegt oder verändert, keine Migration gegen eine echte Datenbank ausgeführt. Kein SQLite-Fallback, keine Datenbankcontainer. Paket 4 wurde nicht begonnen. Die Designfreigabe aus Paket 2 bleibt unverändert gültig.

### Neue bzw. geänderte Dateien

- `config/`, `manage.py`: Django-Einstellungen, ASGI/WSGI, deutscher Konten-Admin, PostgreSQL-Konfiguration, expliziter Schutz des Testziels und Konfigurationsprüfung vor Betriebs-/Änderungsbefehlen.
- `accounts/`: eigene AbstractUser-Klasse bereits in `0001_initial`; Gruppen Redaktion und Veröffentlichung werden nach Migrationen idempotent mit begrenzten Rechten eingerichtet.
- `news/`: Category, Author, Article, Media, ArticleMedia, SlugRedirect, SiteSetting; Migrationen; zentrale öffentliche QuerySets/Selektoren; berechtigungsgeprüfte Veröffentlichungs-/Aufmacherservices; geschützte Medienauslieferung; Demodatenbefehl und neun PostgreSQL-Tests.
- `submissions/`, `reactions/`: Einsendungs- und Herzmodelle, Migrationen und Datenbankconstraints.
- `tests/test_configuration.py`: fünf datenbankfreie Prüfungen der Schutzkonfiguration und des Migrationsgraphen.
- `pyproject.toml`, `uv.lock`: Django 5.2.17, psycopg 3.3.6, nh3 0.3.7, Pillow 12.3.0 und python-dotenv 1.2.3 samt transitiven Versionen gesperrt.
- `.env.example`, `.gitignore`, `README.md`: lokale Konfiguration und vollständige Start-/Testanleitung. Keine echten Zugangsdaten gespeichert.
- `.venv-backend/`: neue funktionsfähige Umgebung mit Python 3.12.14. Ursprüngliche defekte `.venv` unverändert.

### Tatsächlich ausgeführte Prüfungen

PowerShell, im Projektroot; für Offline-Prüfungen wurde nur pro Prozess `DJANGO_SECRET_KEY=local-check-only-not-for-serving` gesetzt, kein persistenter Betriebsschlüssel.

```powershell
$env:UV_PROJECT_ENVIRONMENT='.venv-backend'
$env:UV_CACHE_DIR='.uv-cache'
uv sync --python 'C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& '.\.venv-backend\Scripts\python.exe' manage.py check
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration -v
& '.\.venv-backend\Scripts\python.exe' manage.py test news --noinput
```

- Umgebung erfolgreich erstellt, zehn Pakete installiert; Django-Systemcheck: **0 Probleme**.
- Datenbankfreie Tests: **5 bestanden**. Django weist beim isolierten Überschreiben der Test-Konfiguration erwartungsgemäß auf `override_settings(DATABASES=...)` hin; diese Tests öffnen keine Verbindung.
- Datenbanktests: **9 gefunden, vor Datenbankzugriff ausdrücklich gesperrt**, weil die bestätigte separate PostgreSQL-Testverbindung fehlt. Rollen, konkurrierende Transaktionen, Constraints, Medienauslieferung und Demodaten sind somit vorbereitet, aber noch nicht gegen PostgreSQL nachgewiesen.
- `makemigrations accounts news submissions reactions` und anschließend `makemigrations news reactions` erzeugten die eingecheckbaren Migrationsdateien. Ohne Datenbanknamen brach der erste Erzeugungsversuch erwartungsgemäß ab. Zur rein lokalen Schemaerzeugung wurden danach pro Prozess `PGHOST=127.0.0.1`, `PGPORT=1`, `PGDATABASE=kaktus_schema` gesetzt. Django meldete die nicht erreichbare Verbindung als Warnung und erzeugte die Dateien; dies ist **kein erfolgreicher Migrationstest**.
- `makemigrations --check --dry-run`: keine Modelländerungen erkannt; Datenbank-Historienprüfung mangels Verbindung nicht möglich.
- `git status -sb`: Verzeichnis ist kein Git-Repository. Kein Commit erstellt.

### Nächster Schritt

Der Betreiber muss die freigegebene Entwicklungsverbindung und eine separate entbehrliche Testdatenbank lokal bereitstellen, siehe `README.md` und `.env.example`. Danach `manage.py test news --noinput` auf einer neu erstellten Testdatenbank ausführen, Fehler beheben und erst dann PostgreSQL-Abnahme bestätigen. Bei vorab bereitgestellter leerer Testdatenbank `--keepdb` verwenden. Anschließend Entwicklungsdatenbank migrieren und `load_demo` zweimal prüfen.

Paket 4 baut auf `news/services.py`, `news/selectors.py` und den Modellen auf: Artikeladmin samt Schutz aller direkten Schreibwege, Tiptap, sichere Bilddekodierung/Upload, private Admin-Medienroute, idempotente Einsendungsübernahme und Vorschau. Artikel sind bisher nicht im Admin registriert; ein unberechtigter Artikel-Schreibendpunkt wird deshalb nicht vorweg geöffnet. Nur der Kontenadmin ist vorhanden. Die aktuelle HTML-Positivliste enthält noch keine Bilder; sichere interne Editor-Bildreferenzen folgen in Paket 4. Alle Mediendateien bleiben in privater Ablage; öffentliche Zugänglichkeit wird bei jedem Request aus Artikelzuordnungen berechnet. SiteSetting-Logo hat noch keine gesonderte öffentliche Auslieferung.

---

## Historische Übergabe nach Paket 2

## Aktueller Stand

Paket 1 abgeschlossen. Nutzer hat Option A gewählt („Option A gefällt uns am besten“). Paket 2: acht Detailansichten unter docs/design/option-a/ fertig, einschließlich einer Korrekturrunde der drei Mobilansichten. Finale Detailfreigabe erteilt: „Ja das sieht gut aus.“ Paket 2 abgeschlossen. Pakete 3–7 nicht begonnen. Keine Anwendung implementiert, DESIGN.md und .impeccable/design.json als freigegebenen Designvertrag angelegt. Die beiden ursprünglichen Konzepte, logo.jpg, main.py und pyproject.toml wurden nicht verändert.

## Erstellte Dateien

- PRODUCT.md: bestätigte Produktanforderungen, technische Leitplanken, Datenschutz- und Betriebsblocker.
- docs/arbeitspakete/: sieben eigenständige Prompts, Voraussetzungen, Abnahmekriterien und Statusübersicht.
- docs/design/: drei PNGs, Einordnung und exakte Generierungsprompts.
- .impeccable/config.json: buildPath=comp, entsprechend der ausdrücklichen Vorgabe „Bilder vor Frontend“.
- docs/impeccable-installation.md: Quelle, Revision und Installationsnachweise.

## Prüfungen

- Skill-Installer meldete erfolgreiche Installation unter C:\Users\Timon\.codex\skills\impeccable.
- Engine-Probe erfolgreich: impeccable-engine 0.1.6.
- PNGs mit Pillow geöffnet und geprüft: alle 1536 × 1024, PNG, jeweils über 2 MB. Alle drei generierten Bilder visuell angesehen.
- Lokale Markdown-Links aufgelöst; abschließende Dateiprüfung siehe Abschlussbericht.
- Keine Anwendungstests, da noch keine Anwendung implementiert wurde.

## Besonderheiten

Die vorhandene .venv verweist auf eine nicht startbare Python-3.12-Installation. Für Skill-Installer und Bildmetadaten wurde die gebündelte Python-Laufzeit unter C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe genutzt. Paket 3 muss seine Entwicklungsumgebung explizit einrichten.

Der erste Impeccable-Kontextaufruf scheiterte am fehlenden Engine-Cache. Die Dateien wurden daraufhin direkt gelesen. Die Engine wurde anschließend erfolgreich installiert. Kein zweiter Kontextaufruf in derselben Sitzung. Für kommende Aufgaben ist der Launcher einsatzbereit; der Skill wird ab dem nächsten Gesprächsschritt automatisch angeboten.

## Weiterarbeit

1. A und alle acht Detailansichten sind freigegeben; keine weitere Auswahl oder Detailfreigabe abfragen.
2. DESIGN.md und .impeccable/design.json sind verbindlich; der frühere Entwurf bleibt nur als Historie. Bilder nicht erneut erzeugen, sofern keine Änderungen gewünscht sind.
3. Erst danach Paket 3 in einer separaten Aufgabe ausführen. Datenbankverbindung und getrennte Entwicklungs-/Testdatenbank sind dafür erforderlich; Passwörter nicht in Chat oder Repository schreiben.

Der Design-Auswahlpunkt ist erledigt. Die Weiterarbeit erfolgt gemäß Nutzerwunsch paketweise in separaten Aufgaben.

