# Paket 4 — Redaktion, Editor und Medien

Stand 26.09.2026: implementiert. Systemcheck, 13 datenbankfreie Tests und isolierter Editor-Browsertest bestanden. 14 PostgreSQL-Tests vorhanden, mangels freigegebener Testverbindung nicht ausgeführt. Vollständige Admin-Abnahme bleibt offen; Details in [UEBERGABE.md](UEBERGABE.md).

## Kopierbarer Prompt

Lies PRODUCT.md, DESIGN.md, Backend-Konzept und Übergabe. Implementiere den vereinfachten deutschen Django-Admin mit klaren Listen, Filtern und Aktionen. Integriere Tiptap lokal gebündelt für Absätze, Zwischenüberschriften, Hervorhebungen, Listen, Links und kontrollierte interne Bildauswahl; keine Cloud- oder kostenpflichtigen Funktionen. Ein Build-Werkzeug darf statische Editor-Dateien erzeugen, ein laufender Frontend-Server ist nicht erforderlich. Bereinige HTML serverseitig mit einer Positivliste einschließlich sicherer Linkprotokolle und interner Bildreferenzen. Implementiere Bilddekodierung, Neuencodierung, Alt-Texte und Bildunterschriften. Kontrolliere den Zugriff auf private Medien serverseitig; Kenntnis einer URL reicht nicht. Übernahme einer Einsendung erzeugt idempotent einen verknüpften Entwurf; Name und Klasse werden nicht automatisch öffentliche Autorendaten. Implementiere Veröffentlichen, Zurückziehen, Aufmacherwahl und Rechteprüfung auf allen Schreibwegen. Bereite die geschützte Vorschau einschließlich ungespeicherter Änderungen per POST vor. Paket 5 verbindet sie mit der finalen öffentlichen Artikelvorlage.

## Abnahme

- Direkte Requests ohne Freigaberecht scheitern; Standardformular kann Rechte nicht umgehen.
- XSS, unsichere Links und fremde/private Bildreferenzen abgewehrt.
- Zweite Übernahme erzeugt keinen zweiten Artikel; Klassenangabe bleibt intern.
- Vorschau nur authentifiziert und ohne Indexierung; zurückgezogene Medien geschützt, soweit nicht anderweitig öffentlich verwendet.
