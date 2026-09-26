# KAKTUS – Schülerzeitung

Paket 7 ergänzt [Dockerfile](Dockerfile), [produktives Compose](compose.production.yaml),
eine Proxyvorlage sowie [Betriebs-/Backup-/Restore-Anleitung](docs/BETRIEB.md) und
die kurze [Bedienungsanleitung für die Lehrkraft](docs/LEHRKRAFT.md).
Containerbuild und lokale Prüfungen ersetzen keine öffentliche Startfreigabe:
PostgreSQL-Gesamtabnahme, isolierter Restore und Schul-/Domainfreigaben bleiben offen.
Compose immer mit `--env-file deploy/compose.env` aufrufen, damit die Entwicklungs-`.env`
nicht als Compose-Interpolation eingelesen wird. Produktive Geheimnisse liegen separat
in der ignorierten `deploy/production.env`; das Image enthält keine `.env`.

Django 5.2 LTS, Python 3.12+, PostgreSQL auf dem vorhandenen Server. Paket 6 ergänzt abgesicherte Einreichungen, Herzen und einen Löschbefehl. Paket 5 liefert das öffentliche Frontend nach dem freigegebenen Design A: Startseite, Artikel, Rubriken, Suche und Autorenseiten. Die Redaktion verwendet lokal gebündeltes Tiptap, Bildprüfung, Einsendungsübernahme und eine geschützte Vorschau mit derselben Artikelvorlage. Es gibt keine Registrierung und keine fachliche REST-API. Die PostgreSQL-Verbindung ist vorhanden; die Integrationstests bleiben bis zur ausdrücklichen Bestätigung der entbehrlichen Testdatenbank gesperrt.

## Umgebung einrichten (PowerShell)

Die ursprüngliche `.venv` ist defekt und bleibt unverändert. Die neue, geprüfte Umgebung heißt `.venv-backend`.

```powershell
$env:UV_PROJECT_ENVIRONMENT='.venv-backend'
$env:UV_CACHE_DIR='.uv-cache'
uv sync --locked --python 'C:\Users\Timon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Copy-Item .env.example .env
```

Auf anderen Rechnern beim Sync den Pfad einer funktionierenden Python-Installation einsetzen. `.env` lokal ausfüllen; echte Geheimnisse niemals einchecken oder in den Chat schreiben. Alternativ direkt Umgebungsvariablen setzen, diese haben Vorrang. `DJANGO_SECRET_KEY` muss ein eigener zufälliger Schlüssel sein.

`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` und `PGSSLMODE` zeigen ausdrücklich auf die freigegebene Entwicklungsdatenbank des bestehenden PostgreSQL-Dienstes. Es werden keine Serverdatenbanken oder Benutzer automatisch angelegt und keine Datenbankcontainer verwendet. Eine neue leere Entwicklungsdatenbank mit begrenztem Benutzer muss vom Betreiber bereitgestellt werden. `PGDATABASE` für Demos muss auf `_dev` enden. Keine Produktionsverbindung verwenden.

```powershell
& '.\.venv-backend\Scripts\python.exe' manage.py check
& '.\.venv-backend\Scripts\python.exe' manage.py migrate
& '.\.venv-backend\Scripts\python.exe' manage.py createsuperuser
& '.\.venv-backend\Scripts\python.exe' manage.py load_demo
& '.\.venv-backend\Scripts\python.exe' manage.py runserver
```

`http://127.0.0.1:8000/` öffnet die Zeitung, `/admin/` die Redaktion: Artikel, Bilder, Autorendarstellungen und Einsendungen. Superuser verwalten zusätzlich Konten, Rubriken und Zeitungseinstellungen. Für lokale CSS-/JS-/Fontauslieferung beim Entwicklungsserver `DJANGO_DEBUG=true` setzen. `load_demo` ist wiederholbar und erzeugt ausdrücklich fiktive Beiträge, private Einsendungen und generierte Farbflächen, keine Konten. Es überschreibt keine bestehenden Artikel. Beim ersten `migrate` entstehen die eigene User-Tabelle und die Gruppen **Redaktion** und **Veröffentlichung**. Veröffentlichung enthält auch die Redaktionsrechte. Für Adminzugang ist zusätzlich `is_staff` notwendig. Nur vertrauenswürdige Superuser verwalten Konten und Gruppen.

## Redaktion bedienen

1. Unter **Bilder** JPEG, PNG oder WebP hochladen und einen Alternativtext sowie bei Bedarf eine Bildunterschrift erfassen. Grenzen: 10 MB und 25 Megapixel, keine Animationen. Dateien werden dekodiert, aus frischen Pixeln als WebP gespeichert und von Metadaten befreit.
2. Unter **Artikel** Titel, Artikeladresse, Teaser, Rubrik und eine bewusst gewählte Autorendarstellung erfassen. Redaktionell hochgeladene Bilder bilden eine gemeinsame Bildbibliothek. Anhänge privater Einsendungen sind dort nicht auswählbar; erst die Übernahme gibt sie für den verknüpften Artikel frei.
3. Gewünschte **Textbilder** auswählen und über **Bild einfügen** im Editor platzieren. Der Editor unterstützt Absätze, Zwischenüberschriften, Fett, Kursiv, Listen und sichere Links. Die HTML-Positivliste und interne Bildzuordnung werden zusätzlich serverseitig erzwungen.
4. **Entwurf speichern** oder **Ungespeicherte Vorschau öffnen**. Die Vorschau öffnet per CSRF-geschütztem POST einen neuen Tab und speichert nichts. Sie verwendet dieselbe Artikelvorlage wie die öffentliche Ansicht, mit privater Bildroute, Vorschauhinweis und Indexierungssperre.
5. In der Artikelliste die Aktionen **Veröffentlichen**, **Zurückziehen (als Entwurf)** oder **Als Aufmacher setzen** verwenden. Diese benötigen das Freigaberecht. Redaktion allein darf Entwürfe bearbeiten; veröffentlichte Artikel sowie deren gemeinsam verwendete Bilder/Autorendarstellungen sind für sie schreibgeschützt. Statusfelder lassen sich auch durch direkte Formular-POSTs nicht ändern.
6. Einsendungen in Prüfung nehmen, ablehnen oder **Als Entwurf übernehmen**. Wiederholte Übernahme liefert denselben verknüpften Entwurf. Name und Klasse bleiben intern; es wird keine Autorendarstellung automatisch erzeugt.

## Editor bauen

Die fertigen statischen Dateien samt Drittlizenzen liegen unter `news/static/news/`; der Betrieb benötigt weder Node noch einen Frontend-Server. Zum Ändern des Editors:

```powershell
npm ci
npm run build
```

`frontend/editor.js` verwendet Tiptap 3 (aktuell im Lockfile 3.31.3) mit StarterKit und einer eingeschränkten internen Image-Erweiterung. Der Build erzeugt auch `THIRD-PARTY-LICENSES.txt`. Keine CDN- oder Cloudaufrufe. Grundlage: [offizielle Tiptap-Dokumentation](https://tiptap.dev/docs/editor/getting-started/install/vanilla-javascript).

## PostgreSQL-Tests

`PGTESTDATABASE` muss eine separate, entbehrliche Datenbank mit Suffix `_test` bezeichnen und sich von `PGDATABASE` unterscheiden. Mit `KAKTUS_TEST_DATABASE_CONFIRMED=true` bestätigt der Betreiber ausdrücklich, dass diese Testdatenbank keine zu erhaltenden Daten enthält. Tests sind nur bei `DJANGO_ENV=development` möglich. Es gibt keinen SQLite-Fallback.

Django erstellt normalerweise die Testdatenbank und entfernt sie anschließend. Das benötigt passende Rechte des dedizierten Testbenutzers. Falls der Betreiber die leere Testdatenbank vorab bereitstellt, `--keepdb` verwenden; Django migriert sie und leert ihre Testtabellen. Niemals eine bestehende fremde oder produktive Datenbank als Testziel angeben. Der Namensschutz ersetzt keine getrennten Datenbankzugriffsrechte.

```powershell
& '.\.venv-backend\Scripts\python.exe' manage.py test news --noinput
# Bei ausdrücklich bereitgestellter leerer Testdatenbank:
& '.\.venv-backend\Scripts\python.exe' manage.py test news --keepdb --noinput
# Ergänzende Prüfungen ohne Datenbankzugriff:
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration tests.test_editorial_unit -v
& '.\.venv-backend\Scripts\python.exe' manage.py makemigrations --check --dry-run
```

Die 31 PostgreSQL-Tests prüfen außerdem direkte Admin-Schreibwege, idempotente Übernahme, Bildreferenzen, geschützte Vorschau, öffentliche Sichtbarkeit, Slugweiterleitungen, Suche/Pagination, Wochenrangliste und Logoauslieferung. Erst ein erfolgreicher Testlauf gegen eine leere PostgreSQL-Testdatenbank weist diese Regeln nach. 25 datenbankfreie Tests prüfen Konfiguration, HTML-Bereinigung, Uploadverarbeitung, Vorlagen und Interaktionsschutz. Die neuen PostgreSQL-Tests ergänzen den vollständigen Einreichungs-/Redaktionsablauf, CSRF, Rate-Limits, parallele Herzen und Aufbewahrung. Ein isolierter Editor-Browsertest liegt unter `tests/browser_editor.cjs`; er benötigt Playwright mit installiertem Chromium. Bei extern bereitgestelltem Playwright dessen Modulpfad über `PLAYWRIGHT_MODULE` setzen, dann `node tests/browser_editor.cjs` ausführen. Er ersetzt keinen angemeldeten Admin-Test gegen PostgreSQL.

## Öffentliches Frontend prüfen

```powershell
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_configuration tests.test_editorial_unit tests.test_frontend_unit tests.test_interactions_unit -v
& '.\.venv-backend\Scripts\python.exe' -m tests.frontend_fixtures
# Playwright mit Chromium bereitstellen; bei externer Installation PLAYWRIGHT_MODULE setzen:
node tests/browser_frontend.cjs
```

Die Browserprüfung lädt echte Django-Vorlagen mit ausdrücklich fiktiven Daten, ganz ohne Datenbank. Sie prüft 24 Seiten/Zustände bei 360, 768 und 1440 Pixeln, lokale Schriften, Bildladung, Überläufe, Menüfokus/Escape, Navigation ohne JavaScript und Formulareingaben. Screenshots liegen unter `.qa/frontend/`. Diese Fixtures werden nicht als öffentliche Routen ausgeliefert und ersetzen keine PostgreSQL-Integrationstests.

Öffentliche Routen: `/`, `/artikel`, `/rubrik/<slug>`, `/artikel/<slug>`, `/autoren`, `/autor/<slug>`, `/suche?q=…`, `/mitmachen`, `/ueber-uns`, `/artikel-einreichen`, `/impressum`, `/datenschutz` und `/sitemap.xml`. Alle Artikellisten, verwandte Beiträge und Sitemap verwenden die zentrale öffentliche Auswahl. Die Suche berücksichtigt nur freigegebene Autorennamen. Die Pausenecke wird über die aktive Rubrik mit Slug `pausenecke` eingebunden. Die Wochenrangliste zählt nur bestehende Herzen der letzten sieben Tage, maximal fünf Artikel, ohne Nullwerte.

Einreichung und Herzen sind an echte POST-Schreibwege angeschlossen und funktionieren ohne JavaScript. Vor dem Start müssen die neuen Migrationen `news.0003` und `reactions.0003` auf der freigegebenen Entwicklungsdatenbank angewendet werden; in dieser Aufgabe wurden keine Migrationen auf eine bestehende Datenbank angewendet. `GET /artikel-einreichen` zeigt das Formular; ein erfolgreicher POST speichert privat und leitet auf eine einmalige, sitzungsgebundene Empfangsbestätigung um. Ungültige Eingaben bleiben erhalten; eine Datei muss bei erneutem Absenden erneut ausgewählt werden. Das versteckte Feld `website` muss leer bleiben. Name, Klasse, Titel und Klartext sind standardmäßig auf 120/40/200/50.000 Zeichen begrenzt. Ein optionales Bild wird tatsächlich dekodiert und frisch als WebP ohne Metadaten gespeichert.

Artikelansichten setzen ein zufälliges Browser-Cookie `kaktus_visitor` für standardmäßig ein Jahr (`HttpOnly`, `SameSite=Lax`, in Produktion `Secure`). `POST /artikel/<slug>/herz` benötigt dieses zurückgesendete Cookie und CSRF; ein Klick setzt, ein weiterer entfernt das Herz. Die Datenbank speichert ausschließlich dessen SHA-256-Hash. Ein Artikellock serialisiert parallele Klicks, zusätzlich bleibt der Unique-Constraint aktiv. Zwei parallele Klicks desselben Browsers ergeben deshalb wieder den Ausgangszustand. Ohne gültiges Cookie wird kein Herz geschrieben. Das ist keine personenbezogene Abstimmung über mehrere Browser hinweg.

`config/settings.py` und `.env.example` enthalten alle Feld-, Bild-, Request-, Zeitfenster- und Aufbewahrungsgrenzen. Feld-/Bildgrenzen können unterhalb der festen Modellobergrenzen reduziert werden. Standardmäßig sind fünf Einreichungsversuche je Stunde/IP und 60 Herz-POSTs je Minute/IP erlaubt; auch ungültige und CSRF-abgewiesene Versuche zählen. PostgreSQL-Upserts zählen atomar, ohne Redis. IPs werden nur als mit dem Zeitfenster wechselnde HMAC-Schlüssel gespeichert; abgelaufene Einträge werden beim nächsten Interaktions-POST entfernt. Feste Zeitfenster sind keine gleitenden Zeitfenster: an einer Fenstergrenze sind zwei Kontingente kurz nacheinander möglich. `X-Forwarded-For` wird ausschließlich hinter `TRUSTED_PROXY_NETWORKS` von rechts bis zum ersten untrusted Hop ausgewertet. Der Proxy muss die Weiterleitungskette korrekt überschreiben/ergänzen. Ohne Konfiguration gilt nur `REMOTE_ADDR`.

Request-Bodies sind vor Multipart-/CSRF-Verarbeitung auf 11 MB für Einsendungen bzw. 4 KB für Herzen begrenzt; zusätzlich gelten höchstens 20 Felder/eine Datei. Zu große Requests liefern 413, überschrittene Rate-Limits 429 mit `Retry-After`. Der Reverse-Proxy muss im Betrieb ebenfalls eine Body-Grenze setzen, da Webserver/ASGI Eingaben vor Django puffern können. Die Anwendung protokolliert keine Einsendungsinhalte; POST-Daten sind für Django-Fehlerberichte markiert. Im öffentlichen Betrieb muss `DEBUG=false` gelten.

## Aufbewahrung und Löschvorschau

`SUBMISSION_RETENTION_DAYS` und `REACTION_RETENTION_DAYS` stehen standardmäßig auf `0` (jeweilige Löschung deaktiviert). Die Schule muss positive Fristen bestätigen; erst dann `RETENTION_CONFIRMED=true` setzen. Das Alter zählt ab Einreichung bzw. Herzvergabe, für Einsendungen unabhängig vom Prüfstatus. Es wird kein automatischer Zeitplan eingerichtet.

```powershell
# Nur Anzahl der betroffenen Datensätze/Bilder, keine Namen oder Texte:
& '.\.venv-backend\Scripts\python.exe' manage.py purge_interactions
# Erst nach bestätigten Fristen tatsächlich ausführen:
& '.\.venv-backend\Scripts\python.exe' manage.py purge_interactions --execute
```

Der Befehl entfernt alte Einsendungen/Herzen und abgelaufene Limits. Bilder werden nur entfernt, wenn weder ein Artikel (auch ein Entwurf), eine andere Einsendung noch das Branding sie referenziert; Dateien erst nach erfolgreichem Datenbank-Commit. Übernommene Artikel bleiben erhalten. `Media.submission_origin` bewahrt die Herkunft auch nach dem Löschen der Einsendung und verhindert eine spätere unbeabsichtigte Freigabe in allgemeiner Bildbibliothek oder Logoauswahl. Bestehende Einsendungsbilder werden durch eine Datenmigration markiert. Der Befehl löscht keine Backups; deren Fristen gehören zur Betriebsplanung.

Schriften Source Serif 4 und Source Sans 3 liegen einschließlich OFL-Lizenzen unter `news/static/news/fonts/`. Das bestehende Schullogo wird klein eingebunden; ein in den Zeitungseinstellungen gewähltes Logo ersetzt es. `/zeitungslogo` liefert nur dieses explizit ausgewählte Bild aus und schließt Einsendungsbilder aus. Impressum und Datenschutz sind deutlich als ausstehende Schultexte markiert; sie sind nicht zur Indexierung freigegeben.

## Schnittstellen für Folgepakete

- `Article.objects.public()` ist die zentrale öffentliche Auswahl (`published` und Datum erreicht). `lead()` bevorzugt den gewählten sichtbaren Aufmacher, sonst den neuesten öffentlichen Artikel. `Author.objects.public()`, `Media.objects.public()` und `news/selectors.py` wenden diese Regel ebenfalls an.
- `news/services.py` kapselt Veröffentlichen, Zurückziehen und Aufmacherwahl mit Berechtigungsprüfung. Ein PostgreSQL Advisory Lock serialisiert Aufmacherwechsel auch bei leerer Tabelle; ein partieller Unique-Constraint verhindert mehrere gesetzte Aufmacher unabhängig vom Schreibweg.
- `Article.save()` setzt das erste Veröffentlichungsdatum, erhält es beim erneuten Veröffentlichen, bereinigt HTML und pflegt historische Slugs. Öffentliches Auflösen erfolgt mit `resolve_article`, sodass Rücknahmen auch Weiterleitungen sperren. QuerySet-Updates/Bulk-Operationen umgehen Modellhooks und sind für Inhaltsänderungen verboten; alle redaktionellen Schreibwege müssen in Paket 4 die Services bzw. geprüfte Modellschreibwege nutzen. Die ORM ist kein Berechtigungssystem für beliebigen internen Python-Code.
- `ArticleMedia` hält Zuordnung, Reihenfolge und Bildunterschrift von Textbildern bereit. `save_editorial` validiert die erlaubte Bildbibliothek und synchronisiert Zuordnungen. `clean_body` entfernt fremde Bildreferenzen und erzeugt Bild-URLs/Alt-Texte aus serverseitig zugelassenen Medien. Die finale Artikelvorlage sollte die aktuellen Bildmetadaten beim Rendern berücksichtigen; für private Vorschau liefert `clean_body(..., private=True)` geschützte Bild-URLs und Bildunterschriften.
- Alle Uploads liegen unter `media/private`. Öffentlich verfügbar sind ausschließlich Medien mit einer aktuellen Zuordnung zu einem öffentlichen Artikel, durch `GET /medien/<UUID>`, sowie das explizit ausgewählte Zeitungslogo über `/zeitungslogo`. Rücknahmen greifen beim nächsten Request, sofern kein anderer öffentlicher Artikel dasselbe Bild verwendet. Antworten tragen `no-store`; bereits heruntergeladene Dateien lassen sich nicht zurückrufen. Niemals `MEDIA_ROOT` direkt durch Django `static()` oder einen Proxy freigeben. `GET /redaktion/medien/<UUID>` prüft Staff-Anmeldung und Medienleserecht; für Einsendungsbilder zusätzlich Einsendungsleserecht.
- `convert_submission` serialisiert Übernahmen und erstellt genau einen Entwurf; `Submission.article` ist zusätzlich eindeutig. Private Namen/Klassen werden nicht in Autorendaten kopiert. Das öffentliche Einsendungsformular verwendet denselben Decoder `decode_image`.
- `POST /redaktion/vorschau` nutzt `ArticleForm`, validiert auch ungespeicherte Daten und liefert `no-store` sowie `noindex`. Beide Artikelansichten verwenden `templates/news/article.html` und `news.public.article_context`; aktuelle Alt-Texte und Zuordnungsbildunterschriften werden beim Rendern eingesetzt.

Der bestätigte Designvertrag bleibt [DESIGN.md](DESIGN.md). Prüfstand und externe Blocker stehen in der [Übergabe](docs/arbeitspakete/UEBERGABE.md).
