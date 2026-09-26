# Paket 6 — Einreichungen, Herzen und Rangliste

## Kopierbarer Prompt

Lies PRODUCT.md, Backend-Konzept und Übergabe. Implementiere die öffentlichen Interaktionen. Das Formular fragt Name, interne Klasse/Jahrgang, Titel, Rubrik, Klartext, Urheberschaftsbestätigung und optional ein Bild ab. JPEG/PNG/WebP bis 10 MB und 25 Megapixel nach tatsächlichem Dateityp prüfen, dekodieren und frisch speichern. CSRF, Honeypot, Request- und Feldgrenzen sowie datenbankgestützte Rate-Limits ohne Redis ergänzen. Ausgangswerte: Name 120, Klasse 40, Titel 200, Text 50.000 Zeichen; 5 Einreichungsversuche je Stunde und IP, 60 Herz-Requests je Minute und IP. Für Rate-Limits kurzlebige gehashte IP-Schlüssel mit ablaufenden Zeitfenstern verwenden; Proxy-Header nur von konfigurierten vertrauenswürdigen Proxys akzeptieren. Grenzen zentral konfigurierbar machen. Einsendungen und Bilder bleiben privat. Herzen funktionieren per POST mit zufälligem langlebigem SameSite-Cookie, gehashtem Token und Unique-Constraint; erneuter Klick entfernt das Herz. „Beliebt diese Woche“ zeigt bis zu fünf öffentliche Artikel nach bestehenden Herzen der letzten sieben Tage, bei Gleichstand neueste Veröffentlichung zuerst, keine Null-Herz-Einträge. Ergänze konfigurierbare Aufbewahrungsfristen und Löschbefehl mit Vorschau; ohne bestätigte Frist keine automatische Löschung. Löschen einer Einsendung darf übernommene Artikelbilder nicht zerstören.

## Abnahme

- Ende-zu-Ende: Einreichung, Prüfung, Entwurfsübernahme, Bearbeitung, Vorschau, Veröffentlichung, Zurückziehen.
- Ungültige Dateien, zu große Bilder, CSRF, Honeypot und Rate-Limit geprüft.
- Doppelte/parallele Herzen und sieben-Tage-Grenze getestet.
- Verständliche Feldfehler und Erfolgsbestätigung; sensible Inhalte nicht in Logs.
