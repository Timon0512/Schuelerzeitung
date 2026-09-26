# Designvertrag — Option A, Detailfreigabe ausstehend

Historischer Entwurf: Die Detailansichten sind inzwischen freigegeben. Verbindlich ist jetzt [DESIGN.md](../../../DESIGN.md); diesen Entwurf nicht als konkurrierende Quelle weiterpflegen.

## Visuelle Leitidee

Klassische Zeitung für die Schulgemeinschaft: typografische Hierarchie, starke Bilder, große ruhige Flächen und feine Linien. Keine dekorativen Schatten oder abgerundeten Kartencontainer. Orange/Rot akzentuiert Rubriken, Links und primäre Aktionen. KAKTUS bleibt austauschbarer typografischer Titel; Schullogo klein und unverzerrt.

## Vorgesehene Tokens

| Token | Wert | Anwendung |
|---|---|---|
| paper | #FAF8F4 | Öffentliche Grundfläche |
| surface | #FFFFFF | Formulare, Editor |
| ink | #242321 | Primärtext |
| muted | #5E5953 | Metadaten, Hilfetext |
| line | #D7D1C9 | Zurückhaltende Trennlinien |
| rule | #393631 | Redaktionelle Haupttrennlinien |
| accent | #B84318 | Links, aktive Zustände, Primärbutton |
| accent-hover | #91320F | Hover, gedrückte Aktion |
| pause | #FBE7DA | Pausenecke |
| focus | #174C82 | Sichtbare Fokusmarkierung |
| error | #A12622 | Feldfehler mit Fehlermeldung |
| success | #24613B | Bestätigung mit Text |

Die Werte sind beabsichtigte CSS-Tokens, keine Behauptung über exakt aus dem Raster ausgelesene Farben. Kontraste am Code prüfen. Weißer Text auf accent, ink auf paper/surface; keine kleine orange Schrift in hellerem Dekorationsorange.

## Typografie

- Geplante lokal auszuliefernde Schriftfamilien: Source Serif 4 für Wortmarke, Headlines und Lesetext; Source Sans 3 für Navigation, Metadaten, Formulare und Admin. Lizenzdateien beim Einbinden mitführen. Tatsächliche Schriftdateien werden erst im Frontend-Paket eingebunden.
- Desktop-Wortmarke 80–96 px; mobil 40–48 px. H1 Desktop 44–56 px, mobil 32–36 px; Zeilenhöhe 1.08–1.15. Keine festen Umbrüche, die auf schmalen Geräten überlaufen.
- Artikeltext 20 px Desktop, 18 px mobil, Zeilenhöhe 1.65, Lesespalte maximal 68ch. UI-Text 16 px; wesentliche Hinweise nicht kleiner als 14 px.
- Admin-Feldbeschriftungen und Daten in Sans-Serif. Der Zeitungstitel kann Serif bleiben; Branding darf die Bedienfläche nicht dominieren.

## Raster und Abstände

- Maximalbreite öffentlicher Inhalt 1280 px, mittig. Außenabstand 16 px bis 479 px, 24 px bis 1023 px, 40 px darüber.
- Skala 4, 8, 12, 16, 24, 32, 48, 64 px; zusammengehörige Elemente eng, Abschnitte deutlich getrennt.
- Ab 1024 px Startseite Aufmacher/Nebenartikel ungefähr 2:1. Unter 768 px durchgehend eine Spalte. Dazwischen Aufmacher volle Breite, Nebenartikel in zwei Spalten, wenn ausreichend Platz.
- Artikel-Lesesäule maximal 760 px; große Titelbilder dürfen bis 960 px reichen. Textbilder mobil als eigener Block; keine schmale Resttextspalte.
- Unter 1024 px Hauptnavigation hinter Menübutton, Suche separat erreichbar. Geöffnetes Menü mit Fokusführung, Escape und klarer Schließen-Aktion.
- Formular Desktop Hauptspalte plus schmale Erklärungsspalte; unter 768 px Felder einzeln, Erklärung nach Absenden-Button.
- Admin Desktop Seitenleiste 200–220 px, Editor mit rechter Aktionsspalte; bei Platzmangel Aktionen in den normalen Fluss verschieben. Tabellen müssen ohne Verlust der Aktionen auf schmalen Displays bedienbar bleiben.

## Komponenten und Zustände

- Bilder mit festem Seitenverhältnis und object-fit; kein zwingendes Titelbild. Fehlendes Foto führt zu bewusstem Textlayout, nicht kaputtem Platzhalter.
- Feine Regeln 1 px; Formulare 4 px Radius, Fotos gerade Kanten. Keine Schatten nötig.
- Buttons mindestens 44 px hoch; sichtbarer Hover und 3 px Fokusrahmen mit Abstand. Nicht ausschließlich Farbe als Zustandsanzeige.
- Suche: Suchbegriff erhalten, Anzahl/Trefferliste, Nulltreffer mit Vorschlag, Pagination.
- Einreichung: Feldfehler direkt am Feld, Fehlerübersicht, Eingaben erhalten, Sendezustand und eindeutige Empfangsbestätigung; kein automatischer Veröffentlichungsstatus.
- Herz: nicht gesetzt, gesetzt, läuft, Fehler. Veränderung erst bei bestätigtem Serverergebnis oder mit Rücknahme bei Fehler; zugänglicher Name und Zustand.
- Admin: Entwurf/Veröffentlicht/Archiviert und Einsendungsstatus in Klartext. Veröffentlichung nur für berechtigte Konten. Ungespeicherte Vorschau bleibt privat.
- Überflüssige Bewegung vermeiden; reduced-motion berücksichtigen. Keine animierten Artikel-Einblendungen, die das Lesen verzögern.

## Inhaltsregeln

Mockup-Slogans, Nachrichten und Fotos sind Beispiele. Keine als Tatsache erscheinenden Behauptungen automatisch übernehmen. Keine erfundenen offiziellen Schultexte. Herzrangliste ausdrücklich auf die letzten sieben Tage beziehen; Gesamtherzen am Artikel separat. Klassenangaben ausschließlich intern. Nicht freigegebene Schultexte bleiben Startblocker.
