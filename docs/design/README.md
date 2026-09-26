# KAKTUS — drei Designrichtungen

Status: Nutzer hat Option A gewählt („Option A gefällt uns am besten“). Die [acht Detailansichten](option-a/README.md) sind fertig; sie wurden mit „Ja das sieht gut aus.“ freigegeben. Verbindlicher Designvertrag: [DESIGN.md](../../DESIGN.md). Die ursprünglichen Vergleichstafeln zeigen Desktop und Mobil; PNG, 1536 × 1024 Pixel, erzeugt mit image_gen, nicht als laufende Webseite.

| Richtung | Bild | Charakter | Abwägung |
|---|---|---|---|
| A — Klassische Zeitung | [PNG öffnen](a-klassische-zeitung.png) | Serifentitel, feine Linien, klassischer Aufmacher mit Seitenspalte | Sehr ruhig und glaubwürdig; wirkt erwachsener |
| B — Editorial + School Pop | [PNG öffnen](b-editorial-school-pop.png) | Orange-roter Titel, klare Sans-Serif, sparsame Markerakzente | Beste Verbindung zur gewünschten Schülerzeitungsidentität; Dekoration sparsam halten |
| C — Jugendliches Kulturmagazin | [PNG öffnen](c-jugendliches-kulturmagazin.png) | Stark verdichtete Schrift, große Größenkontraste, asymmetrische Fotos | Eigenständig und dynamisch; Textseiten müssen deutlich ruhiger werden |

Verbindliche Auswahl: A — Klassische Zeitung. Die frühere Empfehlung B ist damit überholt.

## Bildprüfung und Grenzen

- Alle drei Tafeln visuell angesehen: jeweils Desktop und mobile Spalte vorhanden, drei Hauptartikel erkennbar, kleines Schullogo ergänzend, deutliche gestalterische Unterschiede.
- Hauptüberschriften lesbar; Reihenfolge aus Aufmacher, Nebenartikeln, aktuellen Beiträgen und untergeordneter Pausenecke erkennbar. Mobile Ansichten zeigen den oberen Seitenabschnitt, keine vollständige lange Startseite.
- Bilder enthalten fiktive Inhalte und generierte Fotos, keine realen redaktionellen Nachrichten. Die vollständigen Prompts stehen in [GENERIERUNGSPROMPTS.md](GENERIERUNGSPROMPTS.md).
- Generierte Nebentexte, Slogans, zusätzliche Artikeltitel und dekorative Bildbeschriftungen sind keine bestätigten Schulangaben. Sie werden nicht ungeprüft in die Umsetzung übernommen. Die Bildtafel A zeigt illustrative Rankingzahlen nicht streng sortiert; im Produkt gilt die dokumentierte serverseitige Rangfolge.
- Diese Phase prüft die Designrichtung. Browserfunktion, tatsächliche Schriftverfügbarkeit, Kontrastmessungen, Touch-Zielgrößen und responsives Verhalten werden erst am ausgearbeiteten Design beziehungsweise der Implementierung geprüft.

## Nächster Schritt nach Auswahl

Gewählte Richtung in acht Detailansichten ausarbeiten: Startseite, Artikel und Einreichungsformular jeweils Desktop/Mobil; Adminübersicht und Artikelbearbeitung jeweils Desktop. Danach Freigabe einholen und erst dann verbindliches DESIGN.md mit Farben, Schriftwahl, Komponenten und responsiven Regeln schreiben. Noch kein Frontend-Code.
