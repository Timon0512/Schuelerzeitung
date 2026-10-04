---
name: Schulgeflüster — Klassische Zeitung
description: Freigegebene Option A für die Schülerzeitung des Aggertal-Gymnasiums
colors:
  paper: "#FAF8F4"
  surface: "#FFFFFF"
  ink: "#242321"
  muted: "#5E5953"
  line: "#D7D1C9"
  rule: "#393631"
  accent: "#B84318"
  accent-hover: "#91320F"
  pause: "#FBE7DA"
  focus: "#174C82"
  error: "#A12622"
  success: "#24613B"
typography:
  display:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(2.5rem, 6vw, 6rem)"
    fontWeight: 700
    lineHeight: 1.08
  headline:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(2rem, 4vw, 3.5rem)"
    fontWeight: 700
    lineHeight: 1.15
  body:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(1.125rem, 1.8vw, 1.25rem)"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Source Sans 3, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  image: "0px"
  control: "4px"
spacing:
  xs: "4px"
  sm: "8px"
  compact: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  section: "48px"
  major: "64px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.surface}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "12px 16px"
---

# Design System: Schulgeflüster

## Overview

**Creative North Star: „Klassische Zeitung für die Schulgemeinschaft“.**

Option A und die acht Detailansichten sind freigegeben. Belege: „Option A gefällt uns am besten“ und anschließend „Ja das sieht gut aus.“ auf die Frage zur Detailfreigabe. Grundlage sind [die acht PNG-Mockups](docs/design/option-a/README.md). Dieser Stand ist ein verbindlicher Designvertrag vor Implementierung, keine Behauptung über bereits vorhandenen oder getesteten Frontend-Code.

Große schwarze Serifenschrift, warme helle Flächen, feine Linien und sparsame orange-rote Akzente prägen die Zeitung. Journalistische Inhalte stehen vorne; die Pausenecke folgt weiter unten. Das vorhandene Schullogo bleibt ergänzend, der Zeitungstitel austauschbar.

## Colors

Die Tokens im Frontmatter sind die verbindliche Grundlage. paper und surface bilden helle Grundflächen, ink trägt den Lesetext, muted die Metadaten. accent kennzeichnet Links und primäre Aktionen. Kleine Texte verwenden das dunkle Akzenttoken, nicht das hellere Orange einzelner Rastermockups. pause hebt ausschließlich den lockeren Bereich hervor. Zustände benötigen zusätzlich eine Textbezeichnung.

## Typography

Source Serif 4 für Wortmarke, Artikelüberschriften und Lesetext; Source Sans 3 für Navigation, Metadaten, Formulare und Admin. Fonts im Frontend-Paket lokal einschließlich Lizenzdateien ausliefern. Kein externer Fontdienst.

Wortmarke Desktop 80–96 px, mobil 40–48 px; H1 Desktop 44–56 px, mobil 32–36 px. Artikeltext Desktop 20 px, mobil mindestens 18 px, Zeilenhöhe 1.65. UI 16 px, notwendige Hilfetexte mindestens 14 px. Keine erzwungenen Zeilenumbrüche, die Überläufe verursachen. Admin benutzt eine feste, zurückhaltende UI-Typoskala statt der großen Zeitungsskala.

## Layout

- Maximalbreite 1280 px, mittig. Außenabstand 16 px unter 480 px, 24 px bis 1023 px, darüber 40 px.
- Startseite ab 1024 px Aufmacher/Nebenartikel etwa 2:1; unter 768 px eine Spalte; dazwischen Aufmacher volle Breite, Nebenartikel bei Platz in zwei Spalten.
- Unter 1024 px Hauptnavigation über Menübutton; Suche separat erreichbar. Geöffnetes Menü mit Fokusführung, Escape und Schließen-Aktion.
- Artikelspalte maximal 760 px beziehungsweise 68ch; Titelbilder bis 960 px. Textbilder mobil als eigener Block, keine schmale Resttextspalte.
- Formular Desktop Haupt- und Erklärungsspalte, unter 768 px einspaltig. Erklärung nach dem Absenden-Button. Keine Kontaktfelder hinzufügen.
- Admin-Seitenleiste 200–220 px; Editor rechts mit Aktionsspalte. Bei Platzmangel Aktionen in den Seitenfluss übernehmen; Tabellenaktionen müssen erreichbar bleiben.

## Elevation & Depth

Flache Oberfläche ohne dekorative Schatten, Verläufe oder gestapelte Karten. Hierarchie durch Typografie, Abstände und 1-px-Trennlinien. Bewegung nur zur Zustandsrückmeldung; reduced-motion respektieren. Keine das Lesen verzögernden Einblendeanimationen.

## Shapes

Fotos mit geraden Kanten, Formulare mit 4 px Radius. Bildverhältnisse reservieren und object-fit verwenden. Fehlendes Titelbild ergibt bewusstes Textlayout statt kaputtem Platzhalter. Bedienziele mindestens 44 × 44 CSS-Pixel. Fokusrahmen 3 px in focus mit sichtbarem Abstand.

## Components

- Suche erhält Suchbegriff, Trefferzahl, Pagination und hilfreichen Nulltrefferzustand.
- Einreichung: permanente Labels, Fehlerübersicht und Feldfehler, Eingaben erhalten, Sendezustand und Empfangsbestätigung. Hinweis: „Wir lesen deinen Beitrag und prüfen ihn vor der Veröffentlichung.“ Keine Kontaktzusage ohne Kontaktfeld.
- Herz: ungesetzt, gesetzt, läuft und Fehler; serverbestätigte Änderung beziehungsweise Rücknahme bei Fehler. Zugänglicher Name und Zustand.
- Admin: Klartextstatus, Entwurf speichern, geschützte Vorschau und berechtigungsabhängige Veröffentlichung. Keine automatische Übernahme privater Autorendaten.
- Verwandte Artikel tatsächlich aus der angegebenen Rubrik. Rangliste nach Herzen der letzten sieben Tage; Periodenwert klar von Gesamtherzen am Artikel unterscheiden.

## Do's and Don'ts

- Die freigegebene Hierarchie und Identität auf weitere Seiten übertragen.
- Rasterabweichungen bei mobilen Rändern, Labels und Hellorange anhand dieses Vertrags korrigieren; keine unlesbare pixelgenaue Kopie erzeugen.
- Im Code Tastatur, Kontraste, Screenreader, Zustände und Layoutgrenzen prüfen; Mockups ersetzen diese Abnahme nicht.
- Keine fiktiven Nachrichten, institutionellen Slogans oder generierten Fotos als echte Schulangaben übernehmen.
- Keine Kommentare, Newsletter, sozialen Profile oder zusätzliche Zustimmungspflichten hinzufügen.
- Keine erneute Designauswahl oder Freigaberunde ohne wesentliche Änderungen beginnen.
