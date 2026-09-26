# Arbeitspakete und Übergaben

Die Prompts sind für separate, nacheinander bearbeitete Aufgaben im selben Projekt gedacht. Alle Entscheidungen stehen in PRODUCT.md. Die beiden ursprünglichen Konzeptdateien bleiben unverändert. Erst nach Auswahl und Freigabe der Mockups beginnt die Implementierung.

| Paket | Voraussetzung | Prompt | Status |
|---|---|---|---|
| 1 Entscheidungen und Impeccable | Konzepte gelesen | [01](01-projektgrundlage.md) | Abgeschlossen; Installationsnachweis siehe Übergabe |
| 2 Bild-Mockups | Paket 1 | [02](02-designmockups.md) | Abgeschlossen; Option A und acht Detailansichten freigegeben; DESIGN.md verbindlich |
| 3 Backend-Grundlage | Paket 2 freigegeben; DB-Verbindung | [03](03-backend.md) | Implementiert; PostgreSQL-Abnahme blockiert, Entwicklungs-/Testverbindung fehlt |
| 4 Redaktion und Medien | Paket 3 | [04](04-redaktion.md) | Implementiert; lokale Prüfungen bestanden, PostgreSQL- und vollständige Admin-Abnahme mangels DB offen |
| 5 Öffentliches Frontend | Paket 4; Designfreigabe | [05](05-frontend.md) | Implementiert; Offline-/Browserprüfungen bestanden, PostgreSQL-Abnahme mangels Verbindung offen |
| 6 Öffentliche Interaktionen | Paket 5 | [06](06-interaktionen.md) | Implementiert; 25 Offline-Tests und Browserprüfung bestanden, PostgreSQL-Abnahme bis zur Bestätigung des Testziels offen |
| 7 Betrieb und Gesamtabnahme | Paket 6 | [07](07-betrieb.md) | Implementiert; lokale Betriebsprüfung, PostgreSQL-/Restore-/Schulabnahme noch offen |

## Gemeinsamer Auftrag für jede Aufgabe

Lies PRODUCT.md, diesen Paketprompt, beide Konzepte im Projektroot und die vorhandenen Übergaben. Inspiziere den tatsächlichen Projektstand, statt einen früheren Zustand anzunehmen. Setze nur das jeweilige Paket um. Bewahre fremde Änderungen. Verwende keine Produktivdaten für Tests. Dokumentiere tatsächlich ausgeführte Prüfungen, ihre Ergebnisse und nicht geprüfte Punkte. Aktualisiere Paketstatus und docs/arbeitspakete/UEBERGABE.md. Starte kein Folgepaket automatisch.

## Übergabeformat

- Erreichtes Ergebnis und relevante Dateien
- Exakte Start-/Testbefehle mit Ergebnissen
- Offene Entscheidungen oder externe Voraussetzungen
- Nächstes Paket und dessen Einstiegspunkt
- Dokumentierte Designfreigabe, falls vorhanden
