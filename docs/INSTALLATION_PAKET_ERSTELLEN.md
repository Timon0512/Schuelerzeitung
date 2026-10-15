# Übergabepaket vorbereiten (für den Projektentwickler)

Die Empfängeranleitung ist `INSTALLATION_EINFACH.md`. Sie verwendet die gesonderte Startdatei `compose.installation.yaml` und erwartet das Image `sz:local` in `sz-image.tar`. Die bisherige Entwicklungs- und Produktionskonfiguration bleibt verfügbar.

## Image und Dateien

Das fertige, für den Zielserver passende Linux-Image unter dem neuen Namen bauen oder ein vorhandenes Release entsprechend markieren. Beispiel für ein bereits geprüftes Image:

```text
docker image tag kaktus:local sz:local
docker image save --output sz-image.tar sz:local
```

Nicht ungeprüft einen veralteten lokalen Build exportieren. Architektur des Zielservers beachten. Die Image-Datei ist noch nicht durch diese Dokumentationsänderung gebaut oder exportiert worden.

Zusätzlich zum Image bereitstellen:

- `compose.installation.yaml`
- `deploy/production.env` (vorbereitet wie unten)
- `deploy/prepare_installation.py`
- `deploy/compose.env` (für dieses Paket leer, höchstens Kommentare; keine alten KAKTUS-Einstellungen übernehmen)
- `deploy/nginx.conf.example`
- `docs/INSTALLATION_EINFACH.md`, `docs/LEHRKRAFT.md`, `docs/BETRIEB.md`
- Releasekennung, Image-ID und Prüfsummen der gelieferten Dateien

Das Image enthält weder Datenbankinhalte noch Medien oder Geheimnisse. Die bisherige `.dockerignore` schließt Umgebungsdateien aus.

## Eine Einstellungsdatei für den Empfänger

Die eigene `.env` darf als Grundlage dienen. Eine bearbeitete **Kopie** als `deploy/production.env` liefern; die eigene Datei nicht verändern. Geheimnisse nicht ins Repository aufnehmen.

Nur `DJANGO_SECRET_KEY` und bei einem neuen Datenbankbenutzer `PGPASSWORD` leer lassen. Das Skript erzeugt leere Werte neu. Platzhalter wie `replace-with-...` sind nicht leer und werden vom Skript nicht ersetzt. Bei einem vorhandenen Benutzer ist dessen tatsächliches Passwort notwendig; kein neues generieren.

Außerdem die bestehenden Werte auf den Zielserver anpassen, soweit bekannt:

- Produktionsmodus und Debug aus. Compose erzwingt diese Werte zusätzlich.
- Echte Domain und HTTPS-Origin; unbekannte Zielwerte vor Übergabe klären oder als einzutragende Angaben kennzeichnen.
- Eigene neue Datenbank und Benutzer, etwa `sz` / `sz_app`; Entwicklerverbindungen nicht mitgeben.
- Bei lokalem PostgreSQL `PGHOST=host.docker.internal`, `PGPORT=5432`, `PGSSLMODE=require`, wenn dessen TLS eingerichtet ist.
- Bei entferntem PostgreSQL geprüfte Serveradresse, Zertifikatsprüfung und passende CA-Konfiguration verwenden.
- Proxyvertrauen nur passend zur tatsächlichen Umgebung eintragen. Keine pauschalen privaten Netze freigeben.
- Aufbewahrungsfristen erst nach schulischer Festlegung aktivieren. Testdatenbankwerte und nur für Entwicklung benötigte Angaben entfernen.

Der Empfänger verwendet **eine einzige** Datei. Der Anwendungsbenutzer erhält bei der vereinfachten Variante Eigentum an der eigenen Datenbank und Tabellenrechte, aber keine PostgreSQL-Verwaltungsrechte. Das unterscheidet sich bewusst von der strengeren Trennung zwischen Runtime- und Migrationsbenutzer in `BETRIEB.md`.

## Bekannte Anpassungen der technischen Betriebsanleitung

`BETRIEB.md` beschreibt weiterhin das bisherige Setup. Für das neue Paket dessen Befehle auf `compose.installation.yaml`, Compose-Projekt `sz` und Image `sz:local` übertragen. Vor allem Backup-/Restore-Kommandos vor Übergabe passend ausformulieren und prüfen. Keine zweite Geheimnisdatei erforderlich.

Die Nginx-Vorlage verwendet bisher Port 8000, die Startdatei bindet an 8002. Beide `proxy_pass`-Einträge auf 8002 ändern. Domain, Zertifikate und vertrauenswürdige Proxy-Adresse bleiben serverabhängig. Der bestehende statische Pfad `/srv/kaktus/static` ist nur ein Pfad; für eine Umbenennung auch den Alias in Nginx ändern.

Das Hilfsskript legt nur lokale Datenbank und Benutzer an. Es installiert PostgreSQL nicht und verändert weder Firewall noch dessen Listener- oder Zugriffsregeln. Es löscht keine bestehenden Objekte. Eine echte Abnahme auf dem Zielserver mit Sicherungs-/Wiederherstellungstest bleibt notwendig.
