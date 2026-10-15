# Schülerzeitung installieren

Sie erhalten die Schülerzeitung als fertiges Programmpaket. Die Zeitung startet leer; die Lehrkraft legt Artikel und Bilder später neu an. Es werden keine bisherigen Inhalte übertragen.

Diese Anleitung gilt für einen Linux-Server. Die PostgreSQL-Installation in Schritt 4 gilt konkret für Ubuntu/Debian mit dem üblichen Dienst auf Port 5432. Für andere Systeme muss dieser Schritt angepasst werden. Auf dem Schulserver wurde die Anleitung noch nicht ausgeführt.

## 1. Das Paket auf den Server kopieren

Sie erhalten vom Entwickler:

- `sz-image.tar`: das fertig verpackte Programm mit dem internen Namen `sz:local`.
- `compose.installation.yaml`: die Startanweisung für das Programm.
- den Ordner `deploy` mit der vorbereiteten `production.env`, dem Skript `prepare_installation.py`, der Datei `compose.env` und der Vorlage `nginx.conf.example`.
- diese Anleitung, `BETRIEB.md` und `LEHRKRAFT.md`.

Kopieren Sie alles in einen eigenen Ordner, beispielsweise `~/schuelerzeitung`. Dieser darf nicht im öffentlich abrufbaren Ordner der bestehenden Homepage liegen. `sz-image.tar` bleibt als Datei liegen; sie muss nicht entpackt werden.

Öffnen Sie das Befehlsfenster auf dem Server und wechseln Sie in diesen Ordner:

```bash
cd ~/schuelerzeitung
```

Alle folgenden Befehle werden hier ausgeführt. Führen Sie die Befehle einzeln aus. Bei einem Fehler stoppen Sie beim betroffenen Schritt.

## 2. Die benötigten Programme prüfen

Docker startet die verpackte Zeitung. PostgreSQL speichert Artikel und Konten. Python führt das mitgelieferte Einrichtungsskript aus.

```bash
docker --version
docker compose version
python3 --version
```

Es müssen Versionsangaben erscheinen. Compose muss mindestens Version 2.30 haben, Python mindestens Version 3.8.

Falls Docker fehlt, verwenden Sie die offizielle Installationsanleitung für [Ubuntu](https://docs.docker.com/engine/install/ubuntu/) oder [Debian](https://docs.docker.com/engine/install/debian/), einschließlich des dort beschriebenen Compose-Plugins. Die Installation hängt von der Betriebssystemversion ab.

Falls Python auf Ubuntu/Debian fehlt:

```bash
sudo apt update
sudo apt install python3
```

Die Docker-Befehle setzen voraus, dass Ihr Serverkonto Docker verwenden darf. Bei „permission denied“ richten Sie den Zugang gemäß [Docker-Nachinstallation für Linux](https://docs.docker.com/engine/install/linux-postinstall/) ein.

## 3. Die mitgelieferte Einstellungsdatei vorbereiten

Der Entwickler liefert `deploy/production.env`, vorbereitet auf Grundlage seiner `.env`. 

**Nur diese zwei Geheimniswerte werden neu erzeugt:**

| Feld | Bedeutung |
|---|---|
| `DJANGO_SECRET_KEY` | Ein geheimer Schlüssel, den die Website intern benötigt. |
| `PGPASSWORD` | Das Passwort des neuen Datenbankbenutzers. |

Diese beiden Felder sind bei Lieferung leer. Führen Sie aus:

```bash
python3 deploy/prepare_installation.py secrets
```

Das Skript füllt die leeren Felder automatisch und schützt die Datei vor dem Lesen durch andere Benutzer. Die Werte werden nicht angezeigt. Bei erneutem Aufruf bleiben vorhandene Werte unverändert.

**Bei einem bereits vorhandenen Datenbankbenutzer:** Tragen Sie dessen vorhandenes Passwort zuvor bei `PGPASSWORD` ein. Das Skript behält es bei. Es ändert keine Passwörter in einer bestehenden Datenbank.

Die anderen Einstellungen müssen zum Schulserver passen. Sie werden nicht zufällig erzeugt. Der Entwickler soll sie soweit bekannt vorab eintragen. Kontrollieren Sie insbesondere die Internetadresse und die Datenbankverbindung. Die Adresse des Entwickler-PCs passt nicht zum öffentlichen Schulserver.

Sie können die Datei mit dem Texteditor öffnen, beispielsweise:

```bash
nano deploy/production.env
```

Bei nano: **Strg+O**, dann **Enter** zum Speichern, **Strg+X** zum Schließen. Die Datei muss vertraulich bleiben und mitgesichert werden.

## 4. PostgreSQL und eine neue Datenbank einrichten, falls nötig

Wenn bereits eine **eigene leere PostgreSQL-Datenbank für die Schülerzeitung** mit passendem Benutzer vorhanden ist, entfällt das Anlegen. Der Benutzer muss darin Tabellen anlegen und bearbeiten dürfen. Verwenden Sie weder die Datenbank der bestehenden Homepage noch den PostgreSQL-Administrator als Benutzer der Zeitung.

### 4a. PostgreSQL installieren, falls es fehlt

Auf Ubuntu/Debian:

```bash
sudo apt update
sudo apt install postgresql postgresql-client
sudo systemctl enable --now postgresql
```

Wenn PostgreSQL schon installiert ist, lassen Sie diesen Teil aus. Das folgende Skript verwendet den lokalen Standarddienst auf Port 5432.

### 4b. Datenbank und Benutzer automatisch anlegen

Die vorbereitete Einstellungsdatei muss eigene, freie Namen für Datenbank und Benutzer enthalten, beispielsweise `sz` und `sz_app`. Für PostgreSQL auf demselben Server verwendet die Anwendung `host.docker.internal` und Port `5432`.

```bash
sudo -v
python3 deploy/prepare_installation.py database
```

Bei `sudo` wird gegebenenfalls Ihr Serverpasswort abgefragt. Das Skript zeigt die vorgesehenen Namen. Geben Sie den angezeigten Datenbanknamen erneut ein, um die Erstellung zu starten.

Es erstellt eine leere Datenbank und einen eigenen Benutzer mit dem Passwort aus der Einstellungsdatei. Dieser darf die Tabellen seiner Datenbank anlegen und ändern. Er bekommt keine PostgreSQL-Verwaltungsrechte und darf keine weiteren Datenbanken oder Benutzer anlegen.

Wenn Datenbank oder Benutzer bereits existiert, stoppt das Skript ohne Änderungen. Es überschreibt und löscht nichts. Bei einem Fehler während der Erstellung können Teile bereits angelegt sein; das Skript weist darauf hin. Diese vor einem erneuten Versuch prüfen.

Das Skript ist für PostgreSQL auf diesem Linux-Server vorgesehen. Eine entfernte Datenbank legen Sie über deren eigene Verwaltung an.

### 4c. Den Zugriff der Anwendung auf PostgreSQL erlauben

Die Anwendung läuft innerhalb von Docker. PostgreSQL muss Verbindungen von dort annehmen. Diese Einstellungen betreffen den Server und werden deshalb nicht automatisch überschrieben.

Laden Sie das Programm und legen Sie seinen Bilderordner an:

```bash
docker image load --input sz-image.tar
install -d -m 750 var/private
sudo chown 10001:10001 var/private
docker compose --env-file deploy/compose.env -f compose.installation.yaml create web
docker network inspect sz_default
docker compose --env-file deploy/compose.env -f compose.installation.yaml run --rm web python -c "import socket; print(socket.gethostbyname('host.docker.internal'))"
```

Beim Laden muss `sz:local` genannt werden. In der Netzwerkausgabe finden Sie `Subnet`, den Netzwerkbereich der Anwendung. Der letzte Befehl zeigt die Adresse, unter der die Anwendung den Datenbankserver auf diesem Rechner erreicht. Notieren Sie beide Werte. Verwenden Sie die tatsächlichen Werte, nicht die Beispiele unten.

Zeigen Sie die Dateipfade der PostgreSQL-Einstellungen an:

```bash
sudo -u postgres psql -X -c 'SHOW config_file;'
sudo -u postgres psql -X -c 'SHOW hba_file;'
```

Öffnen Sie die erste angezeigte Datei mit `sudo nano DATEIPFAD`. Ergänzen Sie bei `listen_addresses` die Adresse aus dem letzten Befehl. Beispiel:

```text
listen_addresses = 'localhost,172.20.0.1'
```

Ersetzen Sie die Beispieladresse. Behalten Sie weitere Adressen bei, die vorhandene Anwendungen benötigen. Falls vor der Einstellung ein `#` steht, entfernen Sie dieses Zeichen.

Öffnen Sie die zweite Datei. Ergänzen Sie eine Regel für die Zeitung. Beispiel bei Datenbank `sz`, Benutzer `sz_app` und Subnet `172.20.0.0/16`:

```text
hostssl sz sz_app 172.20.0.0/16 scram-sha-256
```

Ersetzen Sie Namen und Subnet. Eine frühere passende Regel hat Vorrang; berücksichtigen Sie deshalb die vorhandene Reihenfolge. Lassen Sie die Regeln anderer Anwendungen bestehen.

Dieses Beispiel benötigt verschlüsselte PostgreSQL-Verbindungen und die vorbereitete Einstellung `PGSSLMODE=require`. Prüfen Sie:

```bash
sudo -u postgres psql -X -c 'SHOW ssl;'
```

Die Ausgabe muss `on` sein. Bei `off` muss zuerst PostgreSQL mit einem passenden Zertifikat für verschlüsselte Verbindungen eingerichtet werden. Bei entfernten Datenbanken müssen zusätzlich Zertifikatsprüfung und Servername passend eingerichtet sein.

Übernehmen Sie anschließend die Änderungen:

```bash
sudo systemctl restart postgresql
```

Der Neustart unterbricht kurz die Verbindungen aller Anwendungen, die diesen PostgreSQL-Dienst nutzen. Planen Sie ihn entsprechend ein. Falls die Firewall den Zugriff blockiert, erlauben Sie nur den benötigten Docker-Zugriff auf Port 5432. Öffnen Sie diesen Port nicht allgemein zum Internet.

## 5. Den leeren Bilderordner vorbereiten

Falls Sie Schritt 4c ausgelassen haben, führen Sie jetzt aus:

```bash
docker image load --input sz-image.tar
install -d -m 750 var/private
sudo chown 10001:10001 var/private
```

Beim Laden muss `sz:local` genannt werden. Der Ordner `var/private` ist zunächst leer. Hier speichert die Anwendung die Bilder, die die Lehrkraft später hochlädt. Der Ordner liegt außerhalb des Programms, damit neue Bilder bei Programmupdates erhalten bleiben. **Es werden keine alten Bilder übertragen.**

Die Zahlen `10001:10001` geben der Anwendung Zugriff auf ihren Speicherordner. Dieser Ordner darf nicht direkt als öffentlicher Downloadordner angeboten werden.

## 6. Die leeren Tabellen anlegen

Eine neue Datenbank braucht Tabellen für Artikel, Benutzerkonten und Bilder. Die Anwendung legt sie mit diesem Befehl an:

```bash
docker compose --env-file deploy/compose.env -f compose.installation.yaml run --rm web python manage.py migrate --noinput
```

Die ausgeführten Schritte erscheinen mit `OK`. Der technische Befehl heißt `migrate`, **überträgt hier aber keine alten Artikel oder Bilder**. Ohne diese Tabellen kann die Zeitung keine neuen Inhalte speichern.

Bei Verbindungsfehlern prüfen Sie Schritt 4c und die Datenbankangaben. Bei fehlenden Rechten prüfen Sie den vorgesehenen Datenbankbenutzer.

## 7. Das Verwaltungskonto anlegen

```bash
docker compose --env-file deploy/compose.env -f compose.installation.yaml run --rm web python manage.py createsuperuser
```

Geben Sie Benutzername, E-Mail-Adresse und ein eigenes starkes Passwort ein. Bei der Passworteingabe sind keine Zeichen sichtbar; das ist normal. Dieses Konto ist für die verantwortliche Kontenverwaltung vorgesehen. Für die Lehrkraft legen Sie später ein persönliches Redaktionskonto an.

## 8. Das Programm prüfen und starten

```bash
docker compose --env-file deploy/compose.env -f compose.installation.yaml run --rm web python manage.py check --deploy
```

Fehler müssen vor dem Start behoben werden. Die Erstkonfiguration kann Warnungen zur späteren HSTS-Festlegung ausgeben; diese Einstellung wird nach der HTTPS-Prüfung gesetzt. Die Warnungen zu HSTS-Subdomains und Preload sind laut `BETRIEB.md` bewusst vorgesehen.

Starten Sie anschließend das Programm:

```bash
docker compose --env-file deploy/compose.env -f compose.installation.yaml up -d web
docker compose --env-file deploy/compose.env -f compose.installation.yaml ps
```

`web` muss als laufend angezeigt werden. Das Programm ist zunächst nur innerhalb des Servers erreichbar.

## 9. Die Internetadresse einrichten

Richten Sie eine eigene Adresse ein, beispielsweise `zeitung.schulname.de`, und verbinden Sie sie mit dem Schulserver. Die neue Adresse benötigt HTTPS mit automatischer Zertifikatserneuerung.

Der vorhandene Webserver muss Anfragen für diese Adresse an `127.0.0.1:8002` weiterreichen. Richten Sie zunächst einen beschränkten Zugang für die Prüfung ein. Der genaue Einrichtungsweg hängt von der bestehenden Serververwaltung ab.

Bei Nginx können Sie `deploy/nginx.conf.example` als Vorlage verwenden. Passen Sie Internetadresse und Zertifikatspfade an. Ändern Sie **beide Weiterleitungen von Port `8000` auf `8002`**. Überschreiben Sie nicht die bestehende Homepage-Konfiguration.

Die Weiterleitung muss HTTPS-Information und Besucheradresse korrekt weitergeben. Dazu müssen die vorbereiteten Einstellungen `DJANGO_TRUST_PROXY_PROTO` und `TRUSTED_PROXY_NETWORKS` passen. Letztere enthält die Adresse des tatsächlich unmittelbar vorgeschalteten Webservers, nicht pauschal das gesamte Docker-Netz. Details stehen in `BETRIEB.md`.

Bei Verwendung der Nginx-Vorlage kopieren Sie außerdem die Darstellungsdateien aus dem Programm:

```bash
install -d var/static-export
container_id=$(docker create sz:local)
docker cp "$container_id:/app/staticfiles/." var/static-export/
docker rm "$container_id"
sudo install -d /srv/kaktus/static
sudo cp -a var/static-export/. /srv/kaktus/static/
```

Der Pfad `/srv/kaktus/static` entspricht der vorhandenen Nginx-Vorlage. Sie können ihn umbenennen, wenn Sie den Pfad dort ebenfalls ändern. Hier liegen Gestaltung und Schriften, keine alten Artikelbilder. Bei Programmupdates müssen diese Darstellungsdateien ebenfalls erneuert werden.

Prüfen Sie die geänderte Nginx-Konfiguration mit `sudo nginx -t`. Laden Sie sie nur nach erfolgreicher Prüfung. Die Einrichtung von Internetadresse und Zertifikat hängt von Ihrem Server ab.

Nach Änderungen an der Einstellungsdatei übernehmen Sie diese mit:

```bash
docker compose --env-file deploy/compose.env -f compose.installation.yaml up -d --force-recreate web
```

Nach geprüfter HTTPS-Verbindung und Zertifikatserneuerung setzen Sie den vorgesehenen HSTS-Wert gemäß `BETRIEB.md` und übernehmen die Änderung erneut.

## 10. Die Zeitung ausprobieren

Prüfen Sie auf Computer und Smartphone:

1. Die Startseite erscheint mit Gestaltung und Schriften.
2. Anmeldung unter `https://IHRE-ADRESSE/admin/` funktioniert.
3. Ein erfundener Testartikel lässt sich als Entwurf speichern und in der Vorschau öffnen.
4. Ein neu hochgeladenes Testbild erscheint in der Vorschau.
5. Nach dem Veröffentlichen erscheint der Artikel für Besucher.
6. Nach dem Zurückziehen ist der Artikel für Besucher wieder gesperrt. Bilder, die ausschließlich zu diesem Artikel gehören, sind ebenfalls gesperrt.
7. Einsendungen funktionieren und bleiben im geschützten Bereich.
8. Herzen lassen sich setzen und wieder entfernen.

Legen Sie persönliche Redaktionskonten für die Lehrkraft und eine Vertretung an. Die Bedienung steht in `LEHRKRAFT.md`.

## 11. Sicherungen und öffentlichen Start vorbereiten

Richten Sie tägliche Sicherungen von **Datenbank und Bilderordner zusammen** ein, einschließlich einer geschützten Kopie auf einem anderen System. Sichern Sie auch die Einstellungsdatei. Prüfen Sie mit erfundenen Daten, ob sich die Zeitung wiederherstellen lässt.

Die technischen Sicherungsbefehle in `BETRIEB.md` müssen für dieses Paket auf `compose.installation.yaml` und `sz:local` angepasst werden. Verwenden Sie sie nicht unverändert mit der alten Startkonfiguration.

Vor der öffentlichen Freigabe:

- Datenbankprüfung, Funktionsprüfung und Wiederherstellungstest erfolgreich abschließen. Im bisherigen Betriebsdokument sind Prüfungen noch als offen beschrieben.
- Die von der Schule bestätigten Impressums- und Datenschutztexte einsetzen.
- Aufbewahrungsfristen festlegen und regelmäßige Löschaufgaben einrichten.
- Verantwortliche für Konten, Sicherungen und Programmupdates festhalten.

Danach den beschränkten Zugang aufheben.

## 12. Den Link auf der Schulhomepage setzen

Fügen Sie in der gewohnten Homepage-Verwaltung einen Link ein:

- **Linktext:** Schülerzeitung
- **Ziel:** die neue vollständige Adresse, beispielsweise `https://zeitung.schulname.de`

Speichern oder veröffentlichen Sie die Änderung und testen Sie den Link.

## Wenn etwas nicht funktioniert

| Beobachtung | Prüfen |
|---|---|
| Datenbankfehler | Stimmen Verbindung und Passwort? Ist Schritt 4c abgeschlossen? |
| Die Seite zeigt „502“ | Läuft `web`? Zeigt die Weiterleitung auf Port `8002`? |
| Die Seite leitet ständig weiter | Stimmen HTTPS-Weiterleitung und Anwendungseinstellungen? |
| Gestaltung fehlt | Sind die Darstellungsdateien vorhanden und vom Webserver erreichbar? |
| Anmeldung oder Speichern wird abgewiesen | Stimmen Internetadresse und HTTPS-Einstellungen? |
| Bilder lassen sich nicht hochladen | Hat die Anwendung Zugriff auf `var/private`? Ist das Bild höchstens 10 MB groß? |

Letzte Programmmeldungen anzeigen:

```bash
docker compose --env-file deploy/compose.env -f compose.installation.yaml logs --tail=80 web
```

Meldungen vertraulich behandeln und persönliche Angaben oder Zugangsdaten vor dem Weitergeben entfernen.
