# Technisches Konzept – Schülerzeitung des Aggertal-Gymnasiums

## 1. Projektziel

Geplant ist eine moderne, öffentlich erreichbare Webseite für die Schülerzeitung des **Aggertal-Gymnasiums**.

Der aktuelle Name der Schülerzeitung lautet **„Kaktus“**, kann sich aber später noch ändern. Das Frontend soll deshalb so aufgebaut werden, dass Name, Logo und Branding ohne strukturelle Änderungen ausgetauscht werden können.

Die Webseite soll den Charakter einer **klassischen Online-Zeitung** haben, aber trotzdem deutlich erkennen lassen, dass sie **von Schülerinnen und Schülern für Schülerinnen und Schüler** gemacht wird.

Die Zielgruppe umfasst Schülerinnen und Schüler ab **Klasse 5 bis zum Abitur**, außerdem Lehrkräfte, Eltern, ehemalige Schülerinnen und Schüler sowie andere interessierte Besucher.

Die Webseite soll öffentlich im Internet erreichbar sein.

---

# 2. Grundidee und Positionierung

Die Schülerzeitung soll nicht wie eine klassische Schulhomepage aussehen.

Stattdessen soll sie wie ein kleines digitales Magazin bzw. eine Online-Zeitung funktionieren:

- klare redaktionelle Hierarchie
- große Aufmacherartikel
- klassische Zeitungsrubriken
- moderne Artikelkarten
- gute Lesbarkeit
- mobile Optimierung
- jugendliche und lebendige Gestaltung
- einfache redaktionelle Pflege
- bewusst kein soziales Netzwerk

Die Seite darf farbig und verspielt sein, soll aber weiterhin professionell und übersichtlich wirken.

## Leitidee

> **Eine moderne Schülerzeitung mit klassischer Zeitungsstruktur und jugendlicher Identität.**

---

# 3. Gestaltungskonzept

## 3.1 Designrichtung

Empfohlene Designrichtung:

**Editorial + School Pop**

Die Basis ist ruhig und modern. Farbe, Illustrationen und kleine spielerische Elemente geben der Webseite den Schülerzeitungscharakter.

### Grundprinzip

- viel Weißraum
- klare Typografie
- große Bilder
- starke Überschriften
- farbige Akzente
- kleine handgezeichnete Elemente
- Sticker-, Marker- oder Kritzeloptik
- einzelne bewusst lockere Gestaltungselemente

Die Webseite soll nicht zu perfekt und steril aussehen.

Mögliche dekorative Elemente:

- handgezeichnete Pfeile
- Marker-Unterstreichungen
- Sterne
- kleine Kritzeleien
- Sticker
- leicht gedrehte Elemente
- Illustrationen von Schülerinnen und Schülern

Die eigentlichen Inhalte bleiben dabei klar strukturiert und gut lesbar.

---

# 4. Branding und Farben

Die Schulfarben des Aggertal-Gymnasiums sind vor allem:

- Orange
- Rot

Diese Farben bilden die Basis des Designs.

## Vorgeschlagene Farbstruktur

### Hauptfarben

- **Orange** – primäre Akzentfarbe
- **Rot** – sekundäre Akzentfarbe
- **Anthrazit** – Haupttext
- **Off-White / Creme** – Hintergrund

### Zusätzliche Rubrikenfarben

Die einzelnen Rubriken können eigene Farben erhalten.

Beispiel:

| Rubrik | Farbe |
|---|---|
| Schule | Orange |
| Meinung | Rot |
| Kultur | Violett |
| Sport | Grün |
| Wissen & Technik | Blau / Türkis |
| Kreativ | Gelb |
| Spaß & Unterhaltung | Pink |

Die Schulfarben bleiben das verbindende Element.

---

# 5. Name und Logo

Der aktuelle Name lautet:

**Kaktus**

Der Name kann sich später ändern.

Deshalb sollten folgende Elemente modular austauschbar sein:

- Name der Schülerzeitung
- Logo
- Untertitel
- primäre Illustration
- Branding-Grafiken

Aktuell könnte beispielsweise verwendet werden:

> **KAKTUS**  
> Die Schülerzeitung des Aggertal-Gymnasiums

Der Kaktus kann dezent als wiederkehrendes Gestaltungselement genutzt werden.

Beispiele:

- kleine Kaktus-Illustrationen
- Kaktus in der Pausenecke
- kleine Icons
- 404-Seite
- dekorative Elemente

Die grundlegende Website-Struktur darf jedoch nicht vom Namen „Kaktus“ abhängig sein.

---

# 6. Zielgruppen

Die Hauptzielgruppe sind Schülerinnen und Schüler des Aggertal-Gymnasiums.

Altersbereich ungefähr:

- Klasse 5
- Mittelstufe
- Oberstufe
- Abiturjahrgänge

Sekundäre Zielgruppen:

- Lehrkräfte
- Eltern
- ehemalige Schülerinnen und Schüler
- Interessierte aus der Region

Da die Altersspanne relativ groß ist, sollte die Seite gleichzeitig:

- leicht verständlich
- visuell interessant
- nicht kindlich
- nicht zu erwachsen
- mobil gut nutzbar

sein.

---

# 7. Frontend-Seitenstruktur

## Öffentliche Seiten

```text
/
Startseite

/artikel
Alle Artikel

/rubrik/schule
/rubrik/meinung
/rubrik/kultur
/rubrik/sport
/rubrik/wissen
/rubrik/kreativ
/rubrik/spass

/artikel/<slug>
Einzelner Artikel

/autoren
Redaktion / Autoren

/autor/<slug>
Optionale Autorenseite

/mitmachen
Informationen zur Mitarbeit

/artikel-einreichen
Artikel einreichen

/ueber-uns
Über die Schülerzeitung

/suche
Suche
```

Zusätzlich:

```text
/admin
```

für den späteren redaktionellen Bereich.

---

# 8. Navigation

Die Hauptnavigation soll bewusst nicht überladen werden.

Beispiel:

```text
Logo | Aktuell | Schule | Meinung | Kultur | Sport | Mehr | Suche
```

Unter „Mehr“ können weitere Bereiche liegen:

- Wissen & Technik
- Kreativ
- Spaß & Unterhaltung
- Redaktion
- Mitmachen
- Über uns

Auf Mobilgeräten wird die Navigation über ein Hamburger-Menü dargestellt.

---

# 9. Startseite

Die Startseite soll bewusst wie eine klassische Online-Zeitung aufgebaut sein.

Die wichtigste redaktionelle Entscheidung ist:

> **Option A – klassische Zeitung**

Das bedeutet:

- wichtige Artikel oben
- klare redaktionelle Gewichtung
- große Aufmacher
- Nachrichten und Reportagen zuerst
- lockere Inhalte weiter unten

---

# 10. Startseitenaufbau

## 10.1 Header

Beispiel:

```text
Aggertal-Gymnasium

KAKTUS
Die Schülerzeitung des Aggertal-Gymnasiums

Aktuell | Schule | Meinung | Kultur | Sport | Mehr
```

Zusätzlich:

- Suchfunktion
- eventuell Herz-Icon / beliebte Artikel
- mobile Navigation

---

# 11. Lead Story / Top Story

Ganz oben wird ein Hauptartikel besonders groß dargestellt.

Beispiel:

```text
┌─────────────────────────────────────┐
│                                     │
│          GROSSES TITELBILD          │
│                                     │
│ SCHULLEBEN                          │
│ Projektwoche 2026                   │
│ Was dieses Jahr anders wird         │
│                                     │
│ Von Hannah · 25. September          │
│                              ♥ 42   │
└─────────────────────────────────────┘
```

Daneben oder darunter:

- zwei kleinere Artikel
- aktuelle Meldungen
- wichtige Themen

---

# 12. Weitere Startseitenbereiche

Nach dem Hauptaufmacher folgen unterschiedliche Bereiche.

## Neueste Artikel

Klassisches Kartenraster.

## Aus dem Schulleben

Zum Beispiel:

- Reportagen
- Schulveranstaltungen
- AGs
- Projekte
- Klassenfahrten
- SV
- Schulaktionen

## Meinung

Kommentare und Meinungsbeiträge.

Dieser Bereich kann optisch etwas stärker hervorgehoben werden.

## Kultur & Medien

Zum Beispiel:

- Musik
- Filme
- Serien
- Bücher
- Games
- Veranstaltungen

## Sport

Zum Beispiel:

- Schulmannschaften
- Turniere
- allgemeine Sportthemen

## Wissen & Technik

Zum Beispiel:

- Wissenschaft
- Technik
- KI
- Digitalisierung
- interessante Wissensartikel

---

# 13. Spaßbereich / Pausenecke

Unterhalb der klassischen Zeitungsinhalte soll ein lockerer Bereich erscheinen.

Arbeitstitel:

> **Pausenecke**

oder aktuell:

> **Pausenecke 🌵**

Mögliche Inhalte:

- Spruch der Woche
- Umfragen
- Rätsel
- Quiz
- Comics
- Memes
- Foto der Woche
- unnützes Wissen
- Empfehlungen
- kleine Challenges
- humorvolle Schulbeobachtungen

Diese Inhalte sollen nicht den journalistischen Hauptbereich dominieren, aber der Webseite deutlich mehr Schülerzeitungscharakter geben.

---

# 14. Artikelkarten

Es sollen mehrere Kartentypen existieren.

## 14.1 Lead Story

Für besonders wichtige Artikel:

- großes Bild
- große Headline
- Kategorie
- Autor
- Datum
- Herz-Anzahl

## 14.2 Standardartikel

Beispiel:

```text
[ Foto ]

SCHULLEBEN

Die neue Schülervertretung
stellt sich vor

Von Sophie Müller
24. September · ♥ 16
```

## 14.3 Kompakte News

Für kurze Meldungen:

```text
SPORT

Basketballteam gewinnt
Kreismeisterschaft

25. September
```

Durch unterschiedliche Kartengrößen entsteht ein typisches Magazinlayout.

---

# 15. Artikelseite

Die Artikelseite soll deutlich ruhiger sein als die Startseite.

Ziel:

- hohe Lesbarkeit
- Fokus auf Text
- klare Hierarchie

Beispiel:

```text
SCHULLEBEN

Warum unsere Projektwoche
dieses Jahr anders wird

Dieses Jahr wartet auf die Schülerinnen
und Schüler ein neues Konzept.

Von Lara Müller
25. September 2026 · 5 Min. Lesezeit

[          TITELBILD          ]

--------------------------------

Artikeltext ...

Zwischenüberschrift

Artikeltext ...

♥ Mir gefällt der Artikel
37
```

Am Ende des Artikels:

> Mehr aus „Schulleben“

mit drei passenden Artikeln.

---

# 16. Artikeltypen

Langfristig können unterschiedliche Beitragstypen unterstützt werden.

Mögliche Typen:

- Nachricht
- Reportage
- Interview
- Kommentar / Meinung
- Rezension
- Umfrage
- Rätsel
- Quiz
- Comic

Für eine erste Version reicht technisch jedoch ein allgemeiner Artikeltyp.

---

# 17. Autoren

Autoren sollen sichtbar am Artikel angezeigt werden.

Beispiel:

> Von Marie Schmidt

oder alternativ:

> Von Marie S.

Da die Webseite öffentlich erreichbar ist und viele Autoren minderjährig sind, sollte die Schule festlegen können, wie Namen dargestellt werden.

Mögliche Optionen:

- Vorname + Nachname
- Vorname + erster Buchstabe des Nachnamens
- Redaktionsname / Pseudonym

Die Klassenstufe sollte auf der öffentlichen Seite standardmäßig **nicht** angezeigt werden.

Intern kann sie gespeichert werden.

---

# 18. Redaktion

Eine Seite „Redaktion“ soll die Menschen hinter der Schülerzeitung vorstellen.

Mögliche Darstellung:

```text
Lara

Redaktion Schülerzeitung

Schreibt über:
Schulalltag · Musik · Interviews
```

Optional:

- kleines Foto
- Illustration
- Avatar

Autorenfotos sollten nicht zwingend erforderlich sein.

---

# 19. Herz-Funktion

Artikel sollen eine einfache Herz-Funktion erhalten.

Beispiel:

```text
♡ Gefällt mir
27
```

Nach dem Klick:

```text
♥ Gefällt dir
28
```

Die Funktion soll bewusst kein soziales Netzwerk erzeugen.

Nicht vorgesehen:

- Follower
- öffentliche Nutzerprofile
- Like-Listen
- Kommentare
- Ranking einzelner Schülerinnen und Schüler

Die Herz-Funktion kann jedoch verwendet werden für:

- „Beliebt diese Woche“
- „Beliebteste Artikel“
- Monats-Highlights

---

# 20. Suche

Die Webseite sollte eine einfache Suche anbieten.

Durchsuchbar:

- Titel
- Teaser
- Artikeltext
- Autoren
- Rubriken

Die Suche sollte mobil leicht erreichbar sein.

---

# 21. Mobile First

Ein großer Teil der Nutzung wird voraussichtlich auf Smartphones stattfinden.

Deshalb sollte das Design Mobile First gedacht werden.

Beispiel:

```text
☰       KAKTUS        🔍

🔥 TOP STORY

[ großes Foto ]

Projektwoche 2026:
Das erwartet euch

von Jonas
♥ 52

----------------------

GERADE NEU

[Foto]
Abi-Motto steht fest
♥ 31

[Foto]
5 Fragen an Frau Weber
♥ 26
```

---

# 22. Artikel einreichen

Schülerinnen und Schüler sollen auch ohne Redaktionsmitgliedschaft Beiträge einreichen können.

Dafür gibt es eine öffentlich erreichbare Seite:

```text
/artikel-einreichen
```

Beispiel:

```text
DEIN ARTIKEL

Du möchtest etwas veröffentlichen?
Schick deinen Beitrag an die Redaktion.

Dein Name
[________________]

Klasse / Jahrgang
[________________]

Titel des Artikels
[________________]

Rubrik
[ Schule ▼ ]

Dein Artikel
[________________]

Bild oder Datei
[ Datei auswählen ]

☐ Ich habe den Text selbst geschrieben.

[ Artikel einreichen ]
```

Nach dem Absenden:

> Danke! Dein Artikel wurde an die Redaktion geschickt.  
> Er wird vor der Veröffentlichung geprüft.

Wichtig:

> Ein eingereichter Artikel wird niemals automatisch veröffentlicht.

---

# 23. Redaktionsworkflow

Für Version 1 ist ein sehr einfacher Workflow vorgesehen.

## Empfohlener MVP

Zunächst gibt es keine Schüleraccounts.

Nur die Lehrkraft oder wenige verantwortliche Personen haben Zugriff auf den Adminbereich.

Schüler reichen Beiträge über das öffentliche Formular ein.

Workflow:

```text
Schüler reicht Artikel ein
        ↓
Artikel landet im Adminbereich
        ↓
Lehrkraft prüft den Artikel
        ↓
Lehrkraft kann ihn bearbeiten
        ↓
Lehrkraft veröffentlicht den Artikel
```

---

# 24. Adminbereich – Anforderungen aus Frontend-Sicht

Der Adminbereich soll extrem einfach zu bedienen sein.

Zielgruppe:

> Personen ohne technische Kenntnisse.

Der Adminbereich sollte eher wie ein reduziertes CMS wirken und nicht wie eine technische Administrationsoberfläche.

Beispiel:

```text
Guten Morgen 👋

ARTIKEL

12 veröffentlicht
3 Entwürfe
2 neue Einreichungen

[ + Neuer Artikel ]

LETZTE ARTIKEL

Projektwoche 2026
Veröffentlicht
[ Bearbeiten ]

Interview mit Frau Müller
Entwurf
[ Weiterbearbeiten ]

NEUE EINREICHUNGEN

● 2 Artikel warten auf Prüfung
```

---

# 25. Neuen Artikel erstellen

Beispiel:

```text
Titel
[____________________________]

Kurzer Teaser
[____________________________]

Rubrik
[ Schulnews ▼ ]

Titelbild
[ Bild hochladen ]

Autor
[ Lara Schmidt ]

Artikel
┌──────────────────────────────┐
│ B  I  Überschrift  Link Bild │
│                              │
│ Hier einfach schreiben ...   │
│                              │
└──────────────────────────────┘

[ Vorschau ]

[ Als Entwurf speichern ]

[ Veröffentlichen ]
```

Es soll kein technisches Wissen notwendig sein.

Nicht erforderlich:

- HTML
- Markdown
- Dateipfade
- technische IDs
- Datenbankkenntnisse

---

# 26. Vorschaufunktion

Vor dem Veröffentlichen soll ein Artikel als echte Webseite angezeigt werden können.

Button:

> Vorschau

Damit kann die Lehrkraft prüfen:

- Überschrift
- Bilder
- Absätze
- Zwischenüberschriften
- Links
- mobile Darstellung
- allgemeines Layout

---

# 27. Eingereichte Artikel im Adminbereich

Beispiel:

```text
EINGEREICHTE ARTIKEL

● Warum wir mehr Fahrradständer brauchen
  von Marie · Klasse 8
  Eingereicht: 26.09.2026

  [ Ansehen ]
  [ Bearbeiten ]
  [ Ablehnen ]
```

Die Lehrkraft kann:

- Artikel lesen
- Text korrigieren
- Titel ändern
- Rubrik ändern
- Bilder ändern
- Autorendarstellung anpassen
- Beitrag ablehnen
- veröffentlichen

---

# 28. Spätere Schüleraccounts

Schüleraccounts sind für Version 1 nicht notwendig.

Die Architektur sollte jedoch so geplant werden, dass sie später ergänzt werden können.

Dann wäre folgender Workflow sinnvoll:

```text
ENTWURF
   ↓
EINGEREICHT
   ↓
IN PRÜFUNG
   ↓
FREIGEGEBEN
   ↓
VERÖFFENTLICHT
```

Ein Schüler darf:

- Artikel schreiben
- Artikel speichern
- Artikel zur Prüfung einreichen

Ein Schüler darf nicht:

- Artikel direkt veröffentlichen
- fremde Artikel bearbeiten
- Inhalte ohne Freigabe öffentlich stellen

Die Lehrkraft kann:

- eingereichte Artikel öffnen
- bearbeiten
- Änderungen anfordern
- freigeben
- veröffentlichen
- ablehnen

---

# 29. Mögliche spätere Rollen

Langfristig könnten verschiedene Rollen eingeführt werden.

## Schüler

- eigene Entwürfe
- eigene Artikel
- Artikel einreichen

## Redakteur

- Artikel prüfen
- Artikel bearbeiten

## Chefredaktion

- Artikel freigeben
- Startseite pflegen
- Top Story auswählen

## Administrator / Lehrkraft

- volle Rechte
- Benutzerverwaltung
- Rubrikenverwaltung
- Einstellungen

Für den MVP ist diese Rollenstruktur noch nicht notwendig.

---

# 30. Datenschutz und Minderjährige

Da die Webseite öffentlich erreichbar ist und Minderjährige Inhalte veröffentlichen, sollte Datenschutz von Anfang an berücksichtigt werden.

Wichtige Punkte:

- keine unnötige Veröffentlichung von Klassen
- konfigurierbare Darstellung von Autorennamen
- Autorenfotos nur optional
- keine öffentlichen Schülerprofile notwendig
- keine Kommentare zum Start
- keine persönlichen Kontaktdaten
- Einreichungen nicht automatisch veröffentlichen

Klassenangaben können intern gespeichert werden, sollten aber nicht automatisch öffentlich sichtbar sein.

---

# 31. Was bewusst nicht Teil des ersten Frontends ist

Nicht für Version 1 vorgesehen:

- soziale Profile
- Direktnachrichten
- Kommentare
- Follower
- Chat
- komplexe Benutzerkonten
- Schüler-Dashboard
- Push-Benachrichtigungen
- komplexes Gamification-System

Die Webseite bleibt primär:

> **eine Online-Zeitung.**

---

# 32. MVP – Zusammenfassung

## Öffentliche Website

- moderne Startseite
- klassische Zeitungsstruktur
- Top Story
- Rubriken
- Artikelseiten
- Autorenanzeige
- Herz-Funktion
- Suche
- Redaktion
- Über uns
- Mitmachen
- Artikel einreichen
- Pausenecke
- responsive Darstellung

## Redaktion

- zunächst nur Lehrkraft / Admin
- Artikel erstellen
- Artikel bearbeiten
- Artikel löschen
- Entwürfe
- Bilder hochladen
- Rubriken
- Top Story auswählen
- Artikelvorschau
- eingereichte Artikel prüfen
- eingereichte Artikel bearbeiten
- eingereichte Artikel veröffentlichen oder ablehnen

---

# 33. Technische Leitprinzipien für die spätere Backend-Konzeption

Das Backend ist noch nicht Teil dieses Konzepts.

Bei der späteren Backend-Planung sollten aber folgende Frontend-Anforderungen berücksichtigt werden.

## Inhalte

Das Backend benötigt mindestens Datenmodelle für:

- Artikel
- Rubriken
- Autoren
- Bilder / Medien
- eingereichte Artikel
- Herz-Reaktionen
- eventuell redaktionelle Einstellungen

## Artikel benötigen mindestens

- ID
- Titel
- Slug
- Teaser
- Artikeltext
- Titelbild
- Rubrik
- Autor
- Veröffentlichungsdatum
- Status
- Herz-Anzahl
- Featured / Top Story
- Erstellungsdatum
- Änderungsdatum

## Mögliche Artikelstatus

```text
draft
submitted
review
approved
published
rejected
archived
```

Für den MVP reichen eventuell:

```text
draft
published
```

plus separater Status für externe Einreichungen.

---

# 34. Anforderungen an das spätere Backend

Das Backend sollte ermöglichen:

- sichere Admin-Anmeldung
- CRUD für Artikel
- Medienverwaltung
- Rubrikenverwaltung
- Veröffentlichung / Zurückziehen
- Artikelvorschau
- Verarbeitung öffentlicher Artikeleinreichungen
- Herz-Funktion
- Suchfunktion
- Uploads
- spätere Erweiterung um Benutzer und Rollen

Wichtig:

> Die Backend-Architektur sollte die spätere Einführung von Schüleraccounts ermöglichen, ohne dass das System komplett neu aufgebaut werden muss.

---

# 35. Empfohlene Entwicklungsreihenfolge

## Phase 1 – Frontend

- Designsystem
- Navigation
- Startseite
- Artikelkarten
- Rubrikseite
- Artikelseite
- Autoren
- Pausenecke
- Artikel einreichen
- responsive Layouts

## Phase 2 – Backend MVP

- Datenbank
- Artikelverwaltung
- Admin-Login
- CMS
- Medienverwaltung
- Artikel veröffentlichen
- Einreichungsformular
- Herz-Funktion

## Phase 3 – Redaktionelle Erweiterungen

- Workflow
- Entwürfe
- Freigaben
- Rollen
- Schüleraccounts
- Änderungsanforderungen

## Phase 4 – Weitere Funktionen

Optional:

- Umfragen
- Quiz
- Newsletter
- saisonale Startseiten
- Statistiken
- automatische „Beliebt“-Sektionen
- Autorenprofile
- Redaktionstools

---

# 36. Zentrale Produktentscheidung

Die wichtigste Leitentscheidung lautet:

> Die Webseite ist zuerst eine **Zeitung** und kein soziales Netzwerk.

Die technischen und gestalterischen Entscheidungen sollten diesem Prinzip folgen.

---

# 37. Projektstand

Zum aktuellen Stand sind folgende Entscheidungen getroffen:

- Schule: **Aggertal-Gymnasium**
- aktueller Name: **Kaktus**
- Name kann sich später ändern
- öffentlich im Internet erreichbar
- Zielgruppe: Klasse 5 bis Abitur
- Schulfarben: Orange / Rot
- klassische Zeitungsstruktur
- Spaßrubrik vorhanden
- Autoren werden angezeigt
- Herz-Funktion vorgesehen
- externe Artikeleinreichungen möglich
- keine automatische Veröffentlichung
- zunächst keine Schüleraccounts
- Adminbereich zunächst primär für Lehrkraft
- spätere Schüleraccounts möglich
- Schülerartikel benötigen immer Freigabe
- Lehrkraft muss Artikel vor Veröffentlichung bearbeiten können

---

# 38. Ausgangspunkt für die Backend-Konzeption

Dieses Dokument beschreibt primär das gewünschte Frontend und den redaktionellen Workflow.

Im nächsten Schritt sollte daraus ein separates technisches Backend-Konzept entwickelt werden.

Dabei sollten insbesondere folgende Fragen entschieden werden:

1. Welche Backend-Technologie wird verwendet?
2. Welche Datenbank wird verwendet?
3. Wie werden Artikel gespeichert?
4. Welche CMS-/Editor-Lösung wird verwendet?
5. Wie funktioniert die Authentifizierung?
6. Wie werden Bilder gespeichert?
7. Wie wird die Herz-Funktion umgesetzt?
8. Wie werden öffentliche Artikeleinreichungen geschützt?
9. Wie funktioniert die Suche?
10. Wie wird das System deployed?
11. Wie werden Backups umgesetzt?
12. Wie wird die spätere Rollen- und Benutzerverwaltung vorbereitet?

Das Backend sollte sich konsequent an den in diesem Dokument definierten redaktionellen Abläufen orientieren.
