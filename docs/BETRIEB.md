# Betrieb und Wiederherstellung

Paket 7 bereitet den Betrieb vor. Keine öffentliche Inbetriebnahme freigegeben.
Die Befehle dieses Dokuments sind für Bash auf dem späteren Linux-Host bestimmt
und wurden dort noch nicht ausgeführt. PostgreSQL bleibt der bestehende Hostdienst.

## Installation und Updates

Voraussetzungen: Docker mit Compose ab 2.30 (rohes env_file), HTTPS-Reverse-Proxy
auf dem Host, eigene PostgreSQL-Datenbank und Zugang. Container-Port 8000 bindet
ausschließlich an 127.0.0.1. Keine Freigabe von 5432, keine DB-Container.
`PGHOST=host.docker.internal` bezeichnet den Host; localhost im Container wäre falsch.
Der Betreiber beschränkt PostgreSQL-Listener, Firewall und pg_hba.conf auf den
tatsächlichen Containerzugang und diese Datenbank. Bei TLS Zertifikate prüfen;
für entfernte Datenbanken `verify-full` mit passender CA/Hostname verwenden.

Runtime-Rolle: LOGIN, CONNECT auf eigene DB, USAGE auf ihr Schema, SELECT/INSERT/
UPDATE/DELETE auf Anwendungstabellen und USAGE/SELECT auf Sequenzen. Kein SUPERUSER,
CREATEDB, CREATEROLE oder Zugriff auf andere Anwendungen. Migrationen mit separater
Eigentümerrolle ausführen; deren Default Privileges müssen neue Tabellen/Sequenzen
für die Runtime-Rolle freigeben. Testrolle nur auf entbehrliche Testziele berechtigen.

```bash
cp deploy/production.env.example deploy/production.env
chmod 600 deploy/production.env
# Werte mit lokalem Editor setzen; einen zufälligen SECRET_KEY erzeugen.
install -d -m 750 var/private
sudo chown 10001:10001 var/private
docker compose --env-file deploy/compose.env -f compose.production.yaml build
docker compose --env-file deploy/compose.env -f compose.production.yaml config --quiet
docker compose --env-file deploy/compose.env -f compose.production.yaml run --rm web python manage.py check --deploy
```

`DJANGO_ENV=production` und DEBUG=false werden von Compose erzwungen. Hosts ohne
Schema/Port, CSRF-Origins mit https:// und gegebenenfalls Port setzen, keine Wildcards.
HSTS zunächst 0; nach geprüftem HTTPS inklusive Zertifikatserneuerung auf 31536000
erhöhen. Keine automatische Subdomain- oder Preload-Freigabe. Ein bewusstes HSTS=0
verursacht vor dieser Freigabe eine Warnung bei `check --deploy`. Auch mit positivem
HSTS-Alter bleiben W005 (Subdomains) und W021 (Preload) bewusst sichtbar; eine Prüfung
mit `--fail-level WARNING` endet deshalb mit Fehlercode. Diese beiden Optionen erst
nach separater Domainfreigabe aktivieren, Warnungen nicht pauschal unterdrücken.

`deploy/nginx.conf.example` ist eine anzupassende Vorlage, keine installierte
Serverkonfiguration. Unbekannte Hosts im globalen Default-vhost ablehnen. TLS endet
an diesem Proxy. Er überschreibt Host, X-Forwarded-Proto und X-Forwarded-For;
`DJANGO_TRUST_PROXY_PROTO=true` darf nur mit diesem abgeschotteten Zugriff gelten.
`TRUSTED_PROXY_NETWORKS` enthält ausschließlich die tatsächlich beobachteten
unmittelbaren Proxy-Peers (Docker-NAT beachten), nie pauschal alle privaten Netze.
Bei weiteren vorgeschalteten Proxies Vertrauenskette neu prüfen. Bodylimit 11 MiB,
Zeitlimits und Loginlimit sind enthalten. Loginlimit zählt auch GETs; bei vielen
Nutzern hinter derselben Schul-IP sorgfältig dimensionieren. Kein Request-Body-
Logging. Nginx-Fehlerlogs können IPs/Pfade enthalten: Zugriff und Rotation begrenzen.

Öffentliche CSS/JS/Schriften werden aus dem Image exportiert. Uploads werden nie
in dieses Verzeichnis kopiert und nie per Proxy-Alias freigegeben:

```bash
install -d var/static-export
cid=$(docker create kaktus:local)
docker cp "$cid:/app/staticfiles/." var/static-export/
docker rm "$cid"
sudo install -d /srv/kaktus/static
sudo cp -a var/static-export/. /srv/kaktus/static/
# Für jedes Release passende statische Dateien exportieren.
```

Die Medienablage `var/private` bleibt persistent und nur UID 10001 zugänglich.
`/medien/<UUID>` prüft öffentliche Zuordnung, `/redaktion/medien/<UUID>` Anmeldung
und Rechte, `/zeitungslogo` die explizite Logoauswahl. Kein Proxy-/CDN-Cache auf
Anwendungsrouten; Rücknahmen müssen beim nächsten Request wirken. Downloads lassen
sich nicht zurückrufen. Proxy hat keinen Zugriff auf den privaten Medienordner nötig.

Vor Updates: Wartung, Sicherung gemäß unten; altes Image samt Releasekennung behalten.
Keine Migration im Container-Entrypoint. Mit separat geschützter env-Datei der
Migrationsrolle (gleiche DB, nicht einchecken):

```bash
KAKTUS_ENV_FILE=/sicher/migration.env docker compose --env-file deploy/compose.env -f compose.production.yaml run --rm web python manage.py migrate --plan
KAKTUS_ENV_FILE=/sicher/migration.env docker compose --env-file deploy/compose.env -f compose.production.yaml run --rm web python manage.py migrate --noinput
docker compose --env-file deploy/compose.env -f compose.production.yaml run --rm web python manage.py createsuperuser
docker compose --env-file deploy/compose.env -f compose.production.yaml up -d web
```

Mindestens zwei namentliche Konten für Vertretung, keine gemeinsamen Passwörter.
Staff plus Gruppe Veröffentlichung für Lehrkräfte; Superuser nur für vertrauenswürdige
Kontenverwaltung. Keine Demodaten in Produktion. Funktionsprüfung zunächst nur intern.
Ein Code-Rollback ist nach Schemaänderungen nicht automatisch möglich: kompatible
Migration prüfen oder vollständiges Sicherungspaar wiederherstellen.

## Konsistente Sicherung

Täglich und vor Updates. PostgreSQL-Client passend zur Serverversion auf dem Host
installieren. Zugang über geschützte PGSERVICE-/PGPASSFILE-Dateien (chmod 600), keine
Passwörter in Befehlen. `kaktus_backup` muss die vollständige eigene DB lesen können.
Backupordner außerhalb des Repositories, verschlüsselte Kopie auf anderem System;
Zugriff, Fristen und Löschung auch für Sicherungen schulisch festlegen.

Strategie: Wartungsseite am Proxy, alle App-Instanzen stoppen, keine laufenden
Management-/Lösch-/Migrationsjobs oder anderen Schreiber zulassen. Erst nach Ende
aller Requests DB-Dump und Medienarchiv erstellen. Bis Abschluss bleibt Schreibstopp.
Das PostgreSQL-Datenverzeichnis wird nicht kopiert. Folgendes als ein Bash-Skript
mit Fehlerabbruch ausführen; bei Fehler bleibt die Anwendung bewusst gestoppt:

```bash
set -euo pipefail
umask 077
# Wartungsseite aktivieren, Jobs und sämtliche weiteren Schreiber stoppen.
docker compose --env-file deploy/compose.env -f compose.production.yaml stop web
id="$(date -u +%Y%m%dT%H%M%SZ)-$(openssl rand -hex 4)"
backup="/sicher/backups/$id"
mkdir -p "$backup"
PGSERVICE=kaktus_backup pg_dump --format=custom --no-owner --no-acl --file="$backup/database.dump"
tar -C var/private -czf "$backup/media.tar.gz" .
PGSERVICE=kaktus_backup psql -XAt -c 'SHOW server_version' > "$backup/postgresql-version.txt"
docker image inspect kaktus:local --format '{{.Id}}' > "$backup/image-id.txt"
printf '%s\n' "$id" > "$backup/backup-id.txt"
(cd "$backup" && sha256sum database.dump media.tar.gz postgresql-version.txt image-id.txt backup-id.txt > SHA256SUMS)
touch "$backup/COMPLETE"
# Verschlüsselt extern kopieren und Prüfsummen dort kontrollieren.
docker compose --env-file deploy/compose.env -f compose.production.yaml start web
# Erst nach Funktionsprüfung Wartungsseite entfernen.
```

Nur Ordner mit COMPLETE und gültigen Prüfsummen verwenden. Image/Quellstand und
geschützte Konfiguration separat sichern. Ein Dump ist ohne Restore-Test kein Nachweis.

## Restore nur in isoliertem Ziel

**Offener Prüfpunkt: echter Restore bisher nicht nachgewiesen.** Benötigt werden eine
ausdrücklich freigegebene leere DB mit Suffix `_restore_test`, separater DB-Benutzer,
frischer Medienordner, passender PostgreSQL-Client und isolierte Anwendung ohne
öffentlichen Zugang. Für Abnahme ausschließlich fiktive Daten sichern; reale
Sicherungen enthalten private Einsendungen und gehören nicht in Entwickler-Testläufe.
Kein `--clean`, keine automatische Löschung/Neuanlage bestehender Datenbanken.

```bash
set -euo pipefail
umask 077
backup=/sicher/backups/BEKANNTE-SICHERUNGSKENNUNG
test -f "$backup/COMPLETE"
(cd "$backup" && sha256sum -c SHA256SUMS)
# PGSERVICE kaktus_restore_test muss auf das freigegebene leere Ziel zeigen.
target=$(PGSERVICE=kaktus_restore_test psql -XAt -c 'SELECT current_database()')
case "$target" in *_restore_test) ;; *) echo 'Falsches Restore-Ziel'; exit 1;; esac
tables=$(PGSERVICE=kaktus_restore_test psql -XAt -c "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
test "$tables" = 0
PGSERVICE=kaktus_restore_test pg_restore --exit-on-error --single-transaction --no-owner --no-acl --dbname="service=kaktus_restore_test" "$backup/database.dump"
restore_media=/sicher/restore/BEKANNTE-SICHERUNGSKENNUNG/private
mkdir -p "$(dirname "$restore_media")"
mkdir "$restore_media"  # Muss neu sein; vorhandener Ordner führt zum Abbruch.
# Nur eigenes, geprüftes Archiv; Inhalt vor Extraktion kontrollieren.
tar -tzf "$backup/media.tar.gz"
tar --no-same-owner --no-same-permissions -xzf "$backup/media.tar.gz" -C "$restore_media"
sudo chown -R 10001:10001 "$restore_media"
```

Isolierte Compose-Kopie mit anderem Projektname, Port und diesem Medienpfad verwenden;
env-Datei ausschließlich auf Restore-DB richten. Zuerst das gesicherte Image starten,
keine neuen Migrationen vor Bestandsvergleich. Kontenzahl, Artikelstatus, Zuordnungen,
Einsendungen und Dateiprüfsummen mit fiktivem Ausgangsbestand vergleichen. Anmeldung,
Entwurfsvorschau, öffentliche Bilder, private Bildsperre und Rücknahme prüfen.
Sicherungskennung, Server-/Imageversion, Zeiten, Befehle und Ergebnisse protokollieren.
Fehlende Datei oder unzugängliches Konto bedeutet fehlgeschlagene Abnahme.

## Startfreigabe und laufender Betrieb

- Schulisch bestätigte Impressums-/Datenschutztexte statt Platzhaltern.
- Bestätigte Aufbewahrungsfristen für Einsendungen, Herzen, Logs und Backups.
- Namens-/Bildfreigaben und bewusst gewählte Autorendarstellungen.
- Echte Domain, Zertifikatserneuerung, Hosts/Origins, Proxyvertrauen und DB-Firewall geprüft.
- Erfolgreicher isolierter Restore und vollständige PostgreSQL-/Redaktionsabnahme.
- Lehrkraft prüft mit der [Bedienungsanleitung](LEHRKRAFT.md) auf Smartphone/Desktop.

Löschung zunächst mit `python manage.py purge_interactions` im Container vorschauen;
`--execute` nur nach bestätigten Fristen. Kein Zeitplan wird automatisch eingerichtet.
Zusätzlich abgelaufene Django-Sitzungen mit `python manage.py clearsessions` entfernen.
Betreiber plant Wartung/Backups, überwacht Erreichbarkeit, Speicher, DB-Verbindung,
Backupalter und Zertifikatsablauf und testet Wiederherstellung regelmäßig.
Abhängigkeiten gezielt aktualisieren, locken, testen und Image neu bauen.
Die Basisimages sind per Registry-Digest fixiert. Für jede weitere Freigabe
deren Registry-Digests dokumentieren/fixieren und das gebaute Releaseimage archivieren.

Grundlagen: [Django Proxy-/Sicherheitseinstellungen](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header),
[uv im Container](https://docs.astral.sh/uv/guides/integration/docker/).

