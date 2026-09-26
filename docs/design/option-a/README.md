# Option A — ausgearbeitete Detailansichten

Die Richtung „Klassische Zeitung“ wurde durch „Option A gefällt uns am besten“ ausgewählt. Die acht Detailansichten wurden anschließend mit „Ja das sieht gut aus.“ freigegeben. Verbindlicher Designvertrag: [DESIGN.md](../../../DESIGN.md). Keine Frontend-Implementierung begonnen.

| Seite | Desktop | Mobil |
|---|---|---|
| Startseite | [Bild](01-startseite-desktop.png) | [Bild](02-startseite-mobil.png) |
| Artikel | [Bild](03-artikel-desktop.png) | [Bild](04-artikel-mobil.png) |
| Artikel einreichen | [Bild](05-einreichen-desktop.png) | [Bild](06-einreichen-mobil.png) |
| Redaktionsübersicht | [Bild](07-redaktion-desktop.png) | Nicht Bestandteil dieses Mockup-Pakets |
| Artikel bearbeiten | [Bild](08-artikelbearbeitung-desktop.png) | Nicht Bestandteil dieses Mockup-Pakets |

Die Bilder wurden mit dem eingebauten image_gen erstellt. Alle Nachrichten, Namen, Fotos und Zahlen sind fiktive Beispiele. Exakte Prompts: [Erstellung](GENERIERUNGSPROMPTS.md), [mobile Korrekturrunde](KORREKTURPROMPTS.md). Quelldateien und Zielpfade: [Manifest](manifest.json).

## Gestaltung

Große schwarze Serifenschrift als Zeitungstitel, warmer heller Hintergrund, feine Trennlinien, quadratische Bildkanten und sparsame orange-rote Akzente. Das vorhandene Schullogo bleibt ergänzend. Die Artikelansicht erhält eine ruhige Lesespalte; Formulare und Redaktion nutzen vertraute Bedienelemente. Die konkrete Übersetzung in Code steht im [Designvertrag als Entwurf](DESIGN-ENTWURF.md).

## Prüfung und verbindliche Umsetzungshinweise

Alle acht finalen Bilder wurden visuell betrachtet. Die erste mobile Ausgabe enthielt zu viel Desktopnavigation und zu kleine Schrift; die Korrekturrunde entfernte die Navigationszeile und verbesserte die Textgrößen. Es handelt sich um Rastermockups, nicht um getestete Browseransichten.

Die Bildgenerierung hat einzelne Details trotz Vorgaben nicht exakt umgesetzt. Für die Implementierung gelten deshalb diese Regeln ausdrücklich:

- Mobile Seitenränder 16–20 CSS-Pixel und Fließtext mindestens 18 CSS-Pixel; die breiteren Ränder einzelner Bilder sind nicht pixelgenau zu übernehmen.
- Bedienoberfläche einschließlich Formularbeschriftungen und Admin-Tabellen in Sans-Serif; Serifenschrift für Zeitungstitel, Artikelüberschriften und redaktionellen Lesetext. Die Bildausgaben zeigen teils mehr Serifenschrift.
- Keine Kontaktzusage im Einreichungsformular: „Wir lesen deinen Beitrag und prüfen ihn vor der Veröffentlichung.“ Der generierte mobile Nebentext „melden uns bei Bedarf“ ist ohne Kontaktfeld unzutreffend und wird ersetzt.
- „Mehr aus Schule“ enthält tatsächlich nur Artikel aus Schule. Im Desktop-Mockup sind zum Teil dieselben Illustrationsartikel wie auf der Startseite eingesetzt.
- Artikelherzen gesamt und Herzen der letzten sieben Tage sind unterschiedliche Werte. Die echte Rangliste erhält eindeutige Periodenbeschriftung und wird ausschließlich aus Daten berechnet.
- Auswahlanzeige und Statusfarben immer mit Text, Bedienziele mindestens 44 × 44 CSS-Pixel, Links und Fokus mit ausreichendem Kontrast. Der helle Illustrations-Akzent wird für kleine bedienbare Texte durch das dunklere Token ersetzt.
- Leichte Farbschattierungen in Rasterflächen sind keine Vorgabe für CSS-Verläufe. Primärbuttons werden einfarbig umgesetzt.

Keine funktionalen oder WCAG-Abnahmebehauptungen: Tastatur, echte Layoutgrenzen, Zustände und Screenreader werden am implementierten Frontend geprüft.

## Nächster Schritt

Paket 2 ist abgeschlossen. DESIGN.md und .impeccable/design.json sind vorhanden. Als Nächstes Paket 3 in einer separaten Aufgabe bearbeiten. Die Designfreigabe nicht erneut abfragen.
