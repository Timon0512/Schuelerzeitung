# SEO und Google-Indexierung

Öffentliche Zieladresse laut Projektkonfiguration:
`https://sz-aggertal-gymnasium.timon-franz.de/`.
Der Zeitungsname kommt weiterhin aus den Zeitungseinstellungen im Admin.

## Subdomain und Hauptdomain

Die Schülerzeitung kann auf der Subdomain eine eigene inhaltliche Identität haben.
Ein anderer Themenschwerpunkt als auf `timon-franz.de` ist für sich genommen kein
Indexierungshindernis. Google unterstützt ausdrücklich eigene Websitenamen auf
Subdomains. Das `WebSite`-Markup auf der Startseite nennt deshalb den Zeitungsnamen
und die Startseite der Schülerzeitung. Es beschreibt die Hauptdomain nicht als
Zeitung oder als identischen Inhalt.

Canonical-Tags und Sitemap-URLs müssen auf die Schülerzeitung zeigen. Keine
Canonicals auf die Hauptdomain setzen, um die Subdomain dort „anzumelden“.
Eine Weiterleitung gehört nur auf zusätzliche Adressen derselben Zeitung,
beispielsweise `schuelerzeitung.timon-franz.de`, nicht auf die eigenständige
Hauptwebsite. Die Weiterleitung muss Pfad und Querystring erhalten.

## Vor der Anmeldung

1. Änderungen auf dem Webserver veröffentlichen. Es sind keine neuen Migrationen
   oder zusätzlichen Pakete erforderlich.
2. Für die Zielsubdomain einen passenden DNS-Eintrag und gültiges HTTPS einrichten.
   Die Startseite und ein veröffentlichter Artikel müssen ohne Anmeldung mit HTTP
   200 erreichbar sein. HTTP dauerhaft auf die HTTPS-Zieladresse weiterleiten.
3. `DJANGO_ALLOWED_HOSTS` und die HTTPS-CSRF-Origin auf die richtige Subdomain
   einstellen. Hinter dem isolierten Proxy muss dieser `Host` und
   `X-Forwarded-Proto` korrekt setzen; dafür `DJANGO_TRUST_PROXY_PROTO=true`
   verwenden, wie in der Proxyvorlage beschrieben.
4. Direkt prüfen:
   - `/robots.txt`: HTTP 200, Textdatei mit Sitemap-Verweis auf diese Subdomain.
   - `/sitemap.xml`: HTTP 200, XML mit erreichbaren Teilsitemaps.
   - `/sitemap-articles.xml`: nur aktuell öffentliche Artikel auf der HTTPS-Zieladresse.
   - Quelltext der Startseite: passender Titel, Canonical auf diese Startseite,
     `WebSite`-JSON-LD mit dem Zeitungsnamen, kein `noindex`.
   - Quelltext eines öffentlichen Artikels: Canonical auf den Artikel,
     `NewsArticle`-JSON-LD, kein `noindex`.
5. Falls Hosting oder Proxy zusätzlich ein `X-Robots-Tag: noindex` setzen,
   diese Sperre für öffentliche Inhalte entfernen. Die Anwendung hält Suche,
   Einreichung, Vorschau und Rechtstextseiten weiterhin gezielt auf `noindex`.

`robots.txt` gilt jeweils für ihren eigenen Host. Eine Datei auf `timon-franz.de`
ersetzt die Datei auf der Subdomain nicht. Die Datei blockiert das Crawling von
Admin und Redaktionsrouten. Öffentlich erreichbare `noindex`-Seiten bleiben
crawlbar, damit Suchmaschinen das Meta-Tag lesen können. Private Inhalte bleiben
durch Anmeldung und Berechtigungsprüfungen geschützt.

## In Google Search Console anmelden

1. [Google Search Console](https://search.google.com/search-console/) öffnen und
   **Property hinzufügen → URL-Präfix** wählen. Exakt
   `https://sz-aggertal-gymnasium.timon-franz.de/` eintragen. Damit lassen sich
   die Daten dieser Schülerzeitung separat auswerten.
2. Inhaberschaft bestätigen. Eine bereits per DNS bestätigte Domain-Property
   `timon-franz.de` deckt auch ihre Subdomains ab; mit demselben berechtigten
   Google-Konto kann die zusätzliche URL-Präfix-Property automatisch bestätigt
   werden. Alternativ eine Domain-Property für die Subdomain anlegen und den
   von Google vorgegebenen TXT-Eintrag beim DNS-Anbieter setzen.
3. Ohne DNS-Verifizierung ist bei der URL-Präfix-Property die Methode
   **HTML-Tag** möglich. Nur den `content`-Wert des von Google ausgegebenen Tags
   als `GOOGLE_SITE_VERIFICATION=...` in die tatsächlich verwendete
   Server-Umgebungsdatei übernehmen und den Webdienst neu erstellen/starten.
   Anschließend den Tag im Startseitenquelltext prüfen und in Search Console
   auf **Bestätigen** klicken. Die Konfiguration dauerhaft behalten.
4. Unter **Sitemaps** `sitemap.xml` einreichen. Der vollständige Pfad lautet
   `https://sz-aggertal-gymnasium.timon-franz.de/sitemap.xml`.
   Der Index enthält bereits die Teilsitemaps für Artikel, Seiten, Rubriken
   und öffentliche Autorendarstellungen.
5. Unter **URL-Prüfung** zunächst die Startseite und einen wichtigen öffentlichen
   Artikel eingeben, **Live-URL testen** und danach **Indexierung beantragen**.
   Weitere Artikel entdeckt Google über Sitemap und interne Links.
6. Im Bericht **Seitenindexierung** den Status und konkrete Ausschlussgründe
   beobachten. Beabsichtigtes `noindex` bei Suche oder Vorschau ist kein Fehler.
   Wiederholte Anträge für dieselbe URL beschleunigen die Verarbeitung nicht.

Eine Sitemap und ein Indexierungsantrag garantieren weder Aufnahme noch Ranking.
Google nennt für das Crawling Zeiträume von einigen Tagen bis zu mehreren Wochen.
Hilfreich sind aussagekräftige Artikelüberschriften, eigenständige Inhalte,
beschreibende Teaser und sinnvolle interne Links. Ein thematisch passender Link
von der Schulwebsite auf die Zeitung hilft beim Entdecken und bei der Zuordnung.

## Technischer Umfang

- Seitenspezifische Titel und normalisierte Beschreibungen; paginierte Listen
  nennen die Seitennummer und behalten ihre eigene Canonical-URL.
- Trackingparameter gehen nicht in die Canonicals ein.
- Strukturierte Daten: `WebSite` auf der Startseite und `NewsArticle` mit
  tatsächlichem Titel, Datum, Rubrik und vorhandenem Titelbild auf Artikeln.
  Autorendaten erscheinen nur bei öffentlich freigegebener Autorendarstellung.
  Keine strukturierten Daten oder Social-Metadaten auf `noindex`-Seiten.
- JSON-LD wird auch bei Anführungszeichen oder `</script>` im Inhalt sicher
  serialisiert. Open Graph und Twitter Cards verwenden dieselben Metadaten.
- `max-image-preview:large` erlaubt große Bildvorschauen öffentlicher Inhalte.
- Bestehende Sichtbarkeitsfilter, private Medien und sofortige Rücknahmen
  bleiben erhalten. Es wurde kein öffentliches Seiten-Caching eingeführt.

Prüfung ohne Datenbankzugriff:

```powershell
$env:DJANGO_ENV='development'
$env:DJANGO_DEBUG='true'
& '.\.venv-backend\Scripts\python.exe' -m unittest tests.test_seo_unit tests.test_frontend_unit tests.test_configuration tests.test_deployment_unit -q
```

Offizielle Grundlagen: [Search-Console-Properties](https://support.google.com/webmasters/answer/34592?hl=de),
[Bestätigung der Inhaberschaft](https://support.google.com/webmasters/answer/9008080?hl=de),
[Websitenamen auf Subdomains](https://developers.google.com/search/docs/appearance/site-names?hl=de),
[Artikel-Markup](https://developers.google.com/search/docs/appearance/structured-data/article?hl=de),
[Sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap?hl=de)
und [Crawling beantragen](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl?hl=de).
