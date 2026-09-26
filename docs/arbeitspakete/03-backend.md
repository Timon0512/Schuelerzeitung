# Paket 3 — Backend-Grundlage und Inhaltsmodell

## Kopierbarer Prompt

Lies PRODUCT.md, beide Konzepte und die Übergabe; prüfe die Designfreigabe. Implementiere die Django-Struktur mit config, news, submissions, reactions und accounts. Lege eine eigene AbstractUser-Klasse vor der ersten Migration an. Konfiguriere PostgreSQL über Umgebungsvariablen: vorhandener Dienst auf dem Server, keine DB-Container, getrennte Entwicklungs- und Testdatenbank. Nutze keine Produktionsdatenbank für Tests und ändere bestehende Serverdatenbanken nicht ungefragt. Implementiere Category, Author, Article, Submission, Media, Reaction und SiteSetting gemäß Backend-Konzept; ergänze Artikel-Medien-Zuordnungen für Textbilder und Slugweiterleitungen. Erzeuge Gruppen Redaktion und Veröffentlichung. Kapsle öffentliche Sichtbarkeit zentral, inklusive Medien und Autorenseiten. Sichere genau höchstens einen Aufmacher transaktional und gegen konkurrierende Änderungen; ohne gesetzten Aufmacher dient der neueste öffentliche Artikel als Startseitenaufmacher. Datum wird bei erstmaliger Veröffentlichung gesetzt. Ergänze wiederholbar ladbare fiktive Demodaten sowie eine Startanleitung. Richte eine funktionsfähige Projektumgebung ein; die ursprüngliche .venv war nicht startbar und darf nicht ungeprüft vorausgesetzt werden. Noch keine gestalteten öffentlichen Seiten.

## Abnahme

- Migrationen auf leerer Testdatenbank, Modellconstraints, Sichtbarkeitsregeln und Rollen geprüft.
- Tests dürfen nicht auf Produktionsdatenbank laufen; fehlende Testverbindung ist ein expliziter Blocker, kein stiller SQLite-Fallback.
- Demodaten wiederholbar; öffentliche und private Medien getrennt.
