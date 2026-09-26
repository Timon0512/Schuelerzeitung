# Technisches Backend-Konzept – Schülerzeitung Aggertal-Gymnasium

Stand: 25. September 2026. Grundlage: `konzept_schuelerzeitung_aggertal_gymnasium.md`.

## 1. Entscheidung

**Ein Python-Projekt mit Django, serverseitig gerenderten Seiten und PostgreSQL.** Das öffentliche Frontend, die Formulare und der geschützte Redaktionsbereich laufen in derselben Anwendung. Django liefert Datenmodelle, Migrationen, Anmeldung, Berechtigungen, Formulare, CSRF-Schutz und einen Adminbereich. Eine separate REST-API, ein JavaScript-Frontend-Server, Redis und eine Job-Queue sind für den Start nicht nötig.

Das Redaktionsinterface nutzt Django Admin als technische Grundlage, erhält aber klare deutsche Bezeichnungen, gezielte Listenansichten und eigene Aktionen für Vorschau, Prüfung und Veröffentlichung. Der Standard-Admin allein erfüllt die gewünschte einfache Bedienung und echte Artikelvorschau noch nicht.

**Datenbank:** PostgreSQL ist von Beginn an die produktive Datenbank und läuft bereits direkt auf dem Homeserver, außerhalb von Docker. Die Schülerzeitung erhält dort eine eigene Datenbank und einen eigenen Datenbankbenutzer mit auf diese Datenbank begrenzten Rechten. Der Django-Container verbindet sich über den Hostnamen des Homeservers mit dieser Instanz. Verbindungsdaten kommen aus Umgebungsvariablen, nicht aus dem Image. Ein PostgreSQL-Container und ein PostgreSQL-Volume sind für dieses Deployment nicht erforderlich. Für eine spätere Übergabe an die Schule können Hostname und Zugangsdaten auf deren PostgreSQL-Instanz umgestellt werden.

## 2. Architektur und Projektstruktur

```text
Browser → HTTPS-Reverse-Proxy → Django-Container → PostgreSQL auf dem Homeserver
                                  ├── persistente Medienablage
                                  └── Admin / Redaktionsbereich
```

```text
config/          Einstellungen und URL-Routen
news/            Artikel, Rubriken, Autoren, Startseite, Suche
submissions/     öffentliche Einreichung und Prüfung
reactions/       Herz-Funktion
accounts/        eigene User-Klasse und spätere Rollen
templates/       öffentliche Seiten, Formulare, Vorschau
static/          CSS, JavaScript, Logos
media/           hochgeladene, geprüfte Bilder
```

Eine eigene User-Klasse (`AbstractUser`) **vor der ersten Migration** anlegen; zunächst gibt es nur Lehrkraft-/Redaktionskonten. Redaktionelle Autorennamen sind davon getrennt: Ein Artikel kann „Marie S.“ zeigen, ohne dass Marie ein Login besitzt.

## 3. Datenmodell

| Modell | Wichtige Felder | Zweck |
|---|---|---|
| `Category` | `name`, eindeutiger `slug`, `color`, `sort_order`, `is_active` | Rubriken und Pausenecke; feste Slugs für bekannte URLs |
| `Author` | `display_name`, eindeutiger `slug`, optionale Kurzbeschreibung, `is_public`, optional `user` | Öffentlicher Autorenname unabhängig vom späteren Login |
| `Article` | `title`, eindeutiger `slug`, `excerpt`, `body`, `category`, `author`, optional `hero_image`, `status`, `published_at`, `created_at`, `updated_at`, `featured`, `editor` | Redaktionell bearbeiteter Beitrag |
| `Submission` | `name`, `class_level`, `title`, `category`, `body`, optionale Datei, `status`, `submitted_at`, `reviewed_at`, `reviewed_by`, `editor_note`, optional `article` | Unveröffentlichte öffentliche Einsendung; interne Klassenangabe |
| `Media` | Datei, `alt_text`, Typ, Breite/Höhe, Größe, `created_at`, `uploaded_by` | Redaktionsbilder und Bildbeschreibungen |
| `Reaction` | `article`, `visitor_token_hash`, `created_at` | Eine anonyme Herz-Reaktion pro Browser/Artikel |
| `SiteSetting` | `publication_name`, `tagline`, `logo`, `school_name` | Umbenennung von „Kaktus“ ohne Codeänderung |

Für `Article.status` reichen im MVP `draft`, `published`, `archived`. Für `Submission.status` reichen `new`, `in_review`, `rejected`, `converted`. Einreichungen bleiben grundsätzlich eigene Datensätze. Bei „In Artikel übernehmen“ wird ein **Entwurf** angelegt und verknüpft; niemals unmittelbar ein veröffentlichter Artikel.

`featured=True` darf nur bei einem veröffentlichten Artikel gesetzt werden; die Aktion „Als Aufmacher setzen“ entfernt den bisherigen Aufmacher in derselben Datenbanktransaktion. Die Veröffentlichung setzt `published_at` nur beim erstmaligen Veröffentlichen; für die sichtbare Reihenfolge zählt dieses Datum. Slugs werden beim Anlegen vorgeschlagen, nach Veröffentlichung aber möglichst stabil gehalten; bei einer Änderung wird eine Weiterleitung benötigt.

## 4. Artikelinhalt und Editor

Der Admin erhält einen einfachen visuellen Rich-Text-Editor mit Absätzen, Zwischenüberschriften, Fett/Kursiv, Listen und Links. Der konkrete Editor ist eine austauschbare UI-Komponente. **Erlaubte HTML-Elemente und Attribute werden serverseitig auf eine feste Liste begrenzt**; Skripte, eingebettete Inhalte und beliebige Styles sind nicht erlaubt. Alternativ können strukturierte Blöcke gespeichert werden, falls später komplexe Magazinelemente gebraucht werden. Für das MVP reicht bereinigtes HTML im `body`.

Eine Vorschau zeigt auch Entwürfe in der echten Artikelseiten-Vorlage. Die Vorschau-URL ist nur nach Admin-Anmeldung erreichbar und wird nicht indexiert; Kenntnis einer URL allein erteilt keinen Zugriff. Für noch nicht gespeicherte Editoränderungen kann die Vorschau per geschütztem POST gerendert werden.

## 5. Öffentliche Seiten und Datenzugriff

| Route | Backend-Verhalten |
|---|---|
| `/` | Genau ein gewählter Aufmacher, aktuelle Beiträge und Rubrikenbereiche; nur veröffentlichte Artikel |
| `/artikel` | Paginierte Liste, neueste zuerst |
| `/rubrik/<slug>` | Veröffentlichte Artikel dieser Rubrik |
| `/artikel/<slug>` | Veröffentlichter Beitrag, Autor, Bild, Herz-Zahl und passende Artikel |
| `/autoren`, `/autor/<slug>` | Nur öffentlich freigegebene Autorendarstellungen und deren veröffentlichte Artikel; Autorenseite optional |
| `/suche?q=...` | Treffer in Titel, Teaser, Text, Autor und Rubrik; nur veröffentlichte Artikel, paginiert |
| `/artikel-einreichen` | Formular per GET und POST; Einsendung bleibt intern |
| `/mitmachen`, `/ueber-uns` | Zunächst gepflegte Textseiten oder einfache Templates |
| `/admin/` | Geschützte redaktionelle Verwaltung |

Für die Suche genügt zunächst eine Datenbankabfrage mit `icontains` und `Q` über die genannten Felder. Text aus HTML für die Suche als Klartext speichern oder extrahieren. Suchbegriffe begrenzen und Ergebnisse paginieren. Bei wachsendem Bestand kann die Suche auf PostgreSQL-Volltextsuche mit geeigneter deutscher Sprachkonfiguration und Index umgestellt werden; ein externer Suchdienst ist nicht nötig.

Der öffentliche Bereich liest ausschließlich `status=published` **und** `published_at <= jetzt`. Diese Regel gilt auch für Suche, Autorenseiten, verwandte Artikel und Bildzuordnungen. Zugriff auf Medien aus unveröffentlichten Einsendungen erfolgt nur über eine geschützte Admin-Route, nicht über eine öffentliche `/media/`-URL.

## 6. Redaktioneller Ablauf

1. Eine Schülerin oder ein Schüler sendet das Formular ab. Die Anwendung speichert die Einsendung mit `new` und zeigt lediglich eine Empfangsbestätigung.
2. Die Lehrkraft sieht neue Einsendungen im Admin, öffnet Text und zulässige Anhänge, markiert sie als `in_review` oder lehnt sie ab.
3. „Als Entwurf übernehmen“ kopiert den Beitrag in `Article(status=draft)`. Die ursprüngliche Einreichung bleibt zur Nachvollziehbarkeit erhalten. Vorname, Nachname und Klasse werden **nicht automatisch** als öffentliche Autorendaten übernommen.
4. Die Lehrkraft prüft Namensdarstellung, Bilder, Rechte, Rubrik und Text, bearbeitet den Entwurf und öffnet die Vorschau.
5. Nur eine Person mit `can_publish_article` darf veröffentlichen. Beim Zurückziehen wechselt der Status auf `draft` oder `archived`; öffentliche Listen und URL liefern den Beitrag dann nicht mehr aus.

Eigene Adminaktionen: „Vorschau“, „Als Entwurf übernehmen“, „Veröffentlichen“, „Zurückziehen“, „Als Aufmacher setzen“. Anstelle eines öffentlichen Löschens bevorzugt archivieren; endgültiges Löschen nur für ausdrücklich berechtigte Admins.

## 7. Anmeldung und Berechtigungen

- Django-Session-Login mit sicheren Passwort-Hashes, CSRF-Schutz und HTTPS-only-Cookies im Produktivbetrieb.
- Keine öffentliche Registrierung und keine Schüleraccounts im MVP.
- Mindestens zwei namentlich zugeordnete Administrationskonten für Vertretung; keine geteilten Passwörter.
- Gruppe `Redaktion`: Entwürfe und Einreichungen bearbeiten. Gruppe `Veröffentlichung`: zusätzlich Artikel freigeben und Aufmacher festlegen. Eine kleine Schule kann zunächst beide Rechte der Lehrkraft geben.
- Admin-Login gegen wiederholte Anmeldeversuche begrenzen; optional 2FA ergänzen, wenn die Schule den Betrieb übernimmt.

Später erhält ein Schüleraccount nur Zugriff auf eigene Entwürfe. Die Freigabe wird als Berechtigungsprüfung auf Serverebene durchgesetzt, nicht nur durch ausgeblendete Buttons. Eine spätere Statuskette `draft → submitted → in_review → approved → published` kann dann ergänzt werden.

## 8. Öffentliche Einsendungen und Uploads

Das Formular fragt nur erforderliche Angaben ab; Klasse/Jahrgang ist intern. Keine Veröffentlichung von Kontaktdaten. Zweck, Sichtbarkeit, Aufbewahrung und notwendige Einwilligungen für Namen/Bilder werden vor Inbetriebnahme mit der Schule abgestimmt. Die Checkbox „selbst geschrieben“ ersetzt keine Prüfung von Rechten an Bildern oder personenbezogenen Aussagen.

Für den Start empfiehlt sich **Text plus optional ein Bild**, statt beliebiger Dateianhänge. Nur JPEG, PNG und WebP nach tatsächlichem Dateityp akzeptieren, Dateigröße und Bildmaße begrenzen, Bild dekodieren und als frische Datei speichern (entfernt problematische Metadaten). SVG, HTML, ausführbare Dateien und PDF-Uploads im öffentlichen Formular zunächst ausschließen. Bilder von Einreichungen bleiben privat; erst geprüfte Medien werden in die öffentliche Ablage übernommen. Alt-Text bei veröffentlichten Bildern erfassen.

Schutz des öffentlichen POST-Endpunkts: CSRF, serverseitige Validierung, begrenzte Feldlängen, Rate-Limit pro IP/Zeitraum, unsichtbares Honeypot-Feld und Begrenzung der Request-Größe. Bei tatsächlichem Spam kann ein CAPTCHA nachgerüstet werden. Einreichungen nie als HTML ausführen oder ungeprüft veröffentlichen.

## 9. Herz-Funktion

`POST /artikel/<slug>/herz` ist der einzige Schreibendpunkt für Besucher. Der Server setzt ein zufälliges, langlebiges SameSite-Cookie und speichert davon nur einen Hash. Ein Unique-Constraint auf `(article, visitor_token_hash)` verhindert doppelte Herzen aus demselben Browser. Optionaler zweiter Klick entfernt die Reaktion. Der sichtbare Zähler wird aus der Tabelle gezählt oder bei Bedarf zwischengespeichert.

Ohne Login ist **eine Person über verschiedene Browser hinweg nicht eindeutig identifizierbar**. Die Funktion ist daher eine informelle Beliebtheitsanzeige, keine verlässliche Abstimmung. Kein öffentliches Besucherprofil, keine IP-Adresse dauerhaft für Herzen speichern. Rate-Limit schützt vor einfachem Missbrauch. „Beliebt diese Woche“ kann nach Herzen aus einem definierten Zeitraum sortiert werden; redaktionelle Gewichtung bleibt möglich.

## 10. Betrieb, Backup und Datenschutz

- Django läuft als Container hinter einem HTTPS-Reverse-Proxy. PostgreSQL läuft als bereits installierter Dienst direkt auf demselben Homeserver; Docker Compose startet **keinen** Datenbankcontainer. Statische Dateien liefert der Proxy aus, hochgeladene Medien liegen in einem persistent eingebundenen Ordner des Homeservers. Die PostgreSQL-Daten liegen im vom installierten PostgreSQL-Dienst verwalteten Datenverzeichnis, ebenfalls außerhalb des Django-Containers.
- Der Django-Container erreicht den Homeserver über einen ausdrücklich konfigurierten Hostnamen beziehungsweise eine Host-Gateway-Adresse, nicht über `localhost` im Container. PostgreSQL lauscht auf der dafür nötigen Schnittstelle; `pg_hba.conf` erlaubt nur die erforderliche Verbindung des Containers. Port 5432 wird nicht öffentlich ins Internet freigegeben. Bei einer späteren Migration auf einen anderen Server werden Netzwerkzugang und verschlüsselte Datenbankverbindung neu geprüft.
- Produktive Einstellungen per Umgebungsvariablen: `SECRET_KEY`, `DEBUG=False`, erlaubte Hosts, HTTPS-Weiterleitung, sichere Cookies, vertrauenswürdige CSRF-Origins. Abhängigkeiten mit festen Versionen und Sicherheitsupdates pflegen.
- Tägliches konsistentes Backup von Datenbank **und** Medien, außerhalb desselben Servers aufbewahren. Die PostgreSQL-Datenbank mit `pg_dump` sichern (einschließlich Schema und Daten), Medienverzeichnis separat sichern und die zueinander gehörenden Sicherungen gemeinsam kennzeichnen. Version des Datenbankservers, Wiederherstellung mit `pg_restore` bzw. `psql` und regelmäßige Restore-Tests dokumentieren. Das Kopieren des laufenden PostgreSQL-Datenverzeichnisses allein ist kein verlässlicher logischer Backup-Prozess.
- Nachvollziehbare Admin-Änderungen und Fehlerprotokolle, aber keine unnötigen personenbezogenen Inhalte in Logs. Aufbewahrungsfristen für abgelehnte Einsendungen, Klassenangaben und Medien festlegen; Löschung technisch vorsehen.
- Öffentliche Artikel für Suchmaschinen freigeben; Entwürfe, Admin, Einsendungen und Vorschau technisch sperren. Datenschutz- und Impressumsseiten vor Veröffentlichung mit der Schule abstimmen.

## 11. Umsetzungsreihenfolge und Abnahme

1. Django-Projekt, eigene User-Klasse, Einstellungen, Datenbankmigrationen, Admin-Login.
2. Rubriken, Autoren, Artikel und öffentliche Seiten einschließlich Aufmacher und Suche.
3. Redaktioneller Editor, private Vorschau und Veröffentlichung mit Rechteprüfung.
4. Öffentliches Einsendungsformular, private Bildablage und Übernahme als Entwurf.
5. Herz-Funktion, Schutz vor Spam, Medienverarbeitung und Branding-Einstellungen.
6. Deployment, Backup/Wiederherstellung und Prüfung mit einer Lehrkraft auf Smartphone und Desktop.

**Wichtige Abnahmekriterien:** Eine Einreichung ist öffentlich nirgends sichtbar; auch ihre Bilder nicht. Eine Lehrkraft kann Text und Autorendarstellung vor der Veröffentlichung ändern. Entwürfe erscheinen in keiner öffentlichen Abfrage. Die Vorschau entspricht der Artikelseite. Ein zurückgezogener Artikel verschwindet sofort. Ein unberechtigtes Konto kann nicht veröffentlichen. Nach einem Restore sind Artikel, Konten und Medien vollständig vorhanden.

## 12. Spätere Erweiterungen

Schüleraccounts mit eigenem Dashboard und Freigabeprozess; redaktionelle Revisionen; Umfragen/Quiz mit eigener Moderation; differenzierte Statistiken; PostgreSQL-Volltextsuche bei wachsendem Artikelbestand. Diese Funktionen gehören bewusst nicht zum MVP.
