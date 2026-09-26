# KAKTUS — verbindlicher Produktkontext

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Django, serverseitige Templates, PostgreSQL auf bestehendem Server; durch den Nutzer bestätigtes Backend-Konzept. JavaScript nur für gezielte progressive Erweiterungen und den lokal gebündelten Editor.

Stand: 25.09.2026. Quelle: beide Konzeptdateien im Root und die vom Nutzer bestätigte Planung. Dieses Dokument hat bei Widersprüchen Vorrang; danach gilt das Backend-Konzept.

## Zweck und Zielgruppe

Öffentliche Schülerzeitung des Aggertal-Gymnasiums: Schülerinnen und Schüler von Klasse 5 bis Abitur, daneben Lehrkräfte, Eltern und Ehemalige. Besucher sollen Nachrichten entdecken, Artikel lesen und eigene Beiträge einreichen können. Redaktionelle Bedienung muss ohne HTML- oder Technikkenntnisse möglich sein. Sprache: Deutsch, direkte und verständliche Ansprache. Eine Zeitung, kein soziales Netzwerk.

## Verbindliche Entscheidungen

- Aktueller Name KAKTUS; Name, Untertitel und Branding austauschbar. logo.jpg ist ergänzendes Schullogo, nicht das Hauptlogo der Zeitung. Bildquelle ist nur 202 × 249 Pixel groß: nicht als große Grafik hochskalieren.
- Klassische journalistische Hierarchie: ein Aufmacher, weitere aktuelle Nachrichten, Rubriken, Pausenecke weiter unten. Orange und Rot verbinden die Gestaltung; jugendlich, aber nicht kindlich.
- Vor Frontend-Code: drei Startseitenrichtungen als PNG mit Desktop- und Mobilansicht vorlegen. Nutzer wählt eine Richtung. Anschließend Detailmockups erstellen und freigeben lassen. Keine Richtung stillschweigend auswählen.
- Django mit serverseitigen Templates, eigener User-Klasse vor erster Migration, PostgreSQL und angepasstem deutschsprachigem Django-Admin. Kein separater Frontend-Server, keine REST-API, kein Redis und keine Job-Queue für den Start.
- PostgreSQL läuft bereits als Dienst auf dem Server, außerhalb von Docker. Auch Entwicklung nutzt diese Instanz mit separaten Entwicklungs- und Testdatenbanken. Keine Produktionsdaten für Tests; keine bestehenden Serverdatenbanken ungefragt verändern. Keine Datenbankcontainer.
- Redaktion und Veröffentlichung sind getrennte Berechtigungsgruppen ab Version 1. Keine öffentliche Registrierung und keine Schüleraccounts.
- Artikel enthalten Titel, Teaser, Rubrik, Autor, Titelbild und Textbilder mit Alt-Text und optionaler Bildunterschrift. Tiptap wird lokal gebündelt; keine Cloud-Editor-Abhängigkeit. HTML serverseitig bereinigen.
- Autorennamen werden redaktionell festgelegt. Redaktionsübersicht und öffentliche einzelne Autorenseiten gehören zur ersten Version. Klassenangaben bleiben intern.
- Öffentliche Einreichung: Name, Klasse/Jahrgang, Titel, Rubrik, Klartext, Urheberschaftsbestätigung, optional ein Bild. Keine automatische Veröffentlichung; Übernahme erzeugt einen Entwurf und keine automatischen öffentlichen Autorendaten.
- Bilder: JPEG, PNG, WebP; maximal 10 MB und 25 Megapixel. Dekodieren, Metadaten entfernen und neu speichern. Keine SVG-, PDF- oder sonstigen Dateianhänge im öffentlichen Formular.
- Herzen ohne Login: zufälliges Browser-Cookie, nur Hash speichern, Eindeutigkeit je Browser/Artikel; erneuter Klick entfernt Herz. Keine Identifikation einer Person über verschiedene Browser.
- „Beliebt diese Woche“: höchstens fünf öffentliche Artikel nach bestehenden Herzen aus den letzten sieben Tagen; bei Gleichstand neuestes Veröffentlichungsdatum zuerst. Keine Null-Herz-Einträge.
- Pausenecke zunächst normale Artikel. Kein Quiz, keine Umfragen, Kommentare, Nachrichten, Follower oder Newsletter.
- Deployment vorbereiten, tatsächliche Inbetriebnahme separat. Django im Container, bestehendes PostgreSQL auf dem Host, persistente Medien, HTTPS-Reverse-Proxy.

## Öffentliche Schnittstellen

GET /, /artikel, /rubrik/<slug>, /artikel/<slug>, /autoren, /autor/<slug>, /suche?q=..., /mitmachen, /ueber-uns, /impressum, /datenschutz.
GET und POST /artikel-einreichen; POST /artikel/<slug>/herz. Redaktion unter /admin/.
Keine fachliche REST-API. Sichere interne Upload- und Vorschau-Routen ergänzen den Admin.

Öffentliche Inhalte müssen status=published und published_at <= jetzt erfüllen. Das gilt für alle Listen, Suche, Autoren, verwandte Artikel, Sitemap und Medienzugriff. Ein zurückgezogener Beitrag ist sofort nicht mehr öffentlich. Medien bleiben nur zugänglich, wenn sie noch von einem anderen öffentlichen Artikel verwendet werden. Private Medien niemals direkt durch den Proxy ausliefern.

## Abnahme und Startblocker

- Unberechtigte können auch durch direkte Requests nicht veröffentlichen. Entwürfe und Einsendungen einschließlich Bilder bleiben privat.
- Vorschau nutzt dieselbe Artikelvorlage wie die öffentliche Seite und erfordert Anmeldung. Ungespeicherte Änderungen dürfen geschützt per POST angezeigt werden.
- Einreichung lässt sich einmalig in einen Entwurf übernehmen, bearbeiten, prüfen und veröffentlichen. Slugänderungen veröffentlichter Artikel benötigen Weiterleitungen, die keine zurückgezogenen Artikel offenlegen.
- Smartphone und Desktop, Tastaturbedienung, lesbare Kontraste, sinnvolle Fokuszustände und verständliche Fehlermeldungen prüfen.
- Datenbank und Medien gemeinsam sichern; Wiederherstellung nur als geprüft ausweisen, wenn sie tatsächlich in isolierter Umgebung erfolgreich war.
- Vor öffentlichem Start: schulisch bestätigte Impressums-/Datenschutztexte, Aufbewahrungsfristen, Namens-/Bildfreigaben, Domain-/Proxy-Konfiguration und erfolgreicher Restore-Test. Keine erfundenen rechtlichen Texte als final ausgeben.
- Löschbefehl mit Vorschau und konfigurierbarer Frist; ohne bestätigte Frist keine automatische Löschung.

## Arbeitsweise und Übergaben

Sieben Arbeitspakete nacheinander, jeweils in separater Aufgabe mit Zugriff auf dieses Projekt. Keine automatische Erstellung neuer Aufgaben ohne ausdrücklichen Nutzerauftrag. Prompts und Abnahmekriterien: docs/arbeitspakete/README.md.
Jede Aufgabe prüft den aktuellen Stand, schützt fremde Änderungen und schreibt eine kurze Übergabe mit geänderten Dateien, Befehlen, Ergebnissen und Blockern. Abnahme und Designfreigaben nicht erfinden. Geheimnisse gehören in lokale Umgebungsvariablen, nie in Dokumentation oder Versionsverwaltung.

## Noch erforderliche Eingaben

1. Option A „Klassische Zeitung“ und alle acht Detailmockups wurden freigegeben („Option A gefällt uns am besten“; „Ja das sieht gut aus.“). DESIGN.md ist verbindlich. Keine weitere Designfreigabe erforderlich.
2. Für Paket 3: erreichbare Datenbankverbindung und getrennte Entwicklungs-/Testdatenbank. Keine Passwörter im Chat erforderlich.
3. Vor Inbetriebnahme: die oben genannten Schul- und Betriebsangaben.
