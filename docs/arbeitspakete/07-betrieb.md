# Paket 7 — Betriebsfähigkeit und Gesamtabnahme

## Kopierbarer Prompt

Lies PRODUCT.md, Backend-Konzept und Übergaben. Erstelle Dockerfile und produktive Compose-Konfiguration für Django ohne PostgreSQL-Container. Nutze die konfigurierbare Verbindung zum vorhandenen PostgreSQL-Dienst auf dem Host, persistente Medien sowie getrennte öffentliche und private Medienauslieferung. Dokumentiere Reverse-Proxy-Anforderungen, HTTPS, sichere Cookies, vertrauenswürdige Hosts/Origins, begrenzte DB-Rechte, Migrationen und namentliche Administrationskonten. Erstelle Backup-/Restore-Befehle für Datenbank und Medien mit gemeinsamer Sicherungskennung und dokumentierter Konsistenzstrategie. Prüfe Restore in einer isolierten Testumgebung, sofern nötiger Zugang vorhanden ist; andernfalls ausdrücklich ungeprüft kennzeichnen. Keine echten Serveränderungen oder öffentliche Inbetriebnahme in diesem Paket. Führe Gesamtabnahme einschließlich Rechte, Medienzugriff und responsiver Bedienung durch. Dokumentiere Startblocker: Schultexte, Aufbewahrungsfristen, Namens-/Bildfreigaben, Domain-/Proxy-Konfiguration und erfolgreicher Restore-Test. Erstelle kurze deutsche Bedienungsanleitung für die Lehrkraft.

## Abnahme

- Reproduzierbarer Build und dokumentierte Startbefehle, keine Geheimnisse im Repository.
- Private Medien auch über Proxy nicht öffentlich; keine Datenbankport-Freigabe ins Internet.
- Backup-/Restore-Nachweis oder expliziter offener Prüfpunkt; keine vorgetäuschte Betriebsbereitschaft.
- Lehrkraft kann anhand der Anleitung Einreichung prüfen, Artikel bearbeiten und veröffentlichen.
