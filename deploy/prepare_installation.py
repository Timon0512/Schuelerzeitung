"""Linux installation helper; no Django, Docker or third-party Python imports.

Run from the package root. Never imports settings or reads the development .env.
Database mode uses the local PostgreSQL administrator via sudo and psql.
"""

import argparse
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile


ENV_PATH = Path("deploy/production.env")


def read_config(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("deploy/production.env muss eine normale, vorhandene Datei sein.")
    text = path.read_text(encoding="utf-8-sig")
    values = {}
    for line in text.splitlines():
        match = re.match(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=(.*)$", line)
        if match:
            key, value = match.groups()
            if key in values:
                raise ValueError("Eine Einstellung steht mehrfach in der Datei: " + key)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key] = value
    return text, values


def prepare_secrets(path):
    text, values = read_config(path)
    changed = []
    for key in ("DJANGO_SECRET_KEY", "PGPASSWORD"):
        if values.get(key):
            continue
        value = secrets.token_hex(32)
        pattern = re.compile(r"^\s*(?:export\s+)?" + key + r"\s*=.*$", re.MULTILINE)
        if key in values:
            text = pattern.sub(key + "=" + value, text, count=1)
        else:
            text = text.rstrip("\n") + "\n" + key + "=" + value + "\n"
        changed.append(key)
    if changed:
        handle, temporary = tempfile.mkstemp(prefix=".production-", dir=path.parent)
        try:
            os.chmod(temporary, 0o600)
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as output:
                output.write(text)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    else:
        path.chmod(0o600)
    print("Neue Werte gespeichert: " + ", ".join(changed) if changed else "Vorhandene Geheimnisse bleiben unverändert.")
    print("Die Datei ist nur für ihren Besitzer lesbar. Geheimnisse werden nicht angezeigt.")


def sql_literal(value):
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ValueError("Das Datenbankpasswort muss in einer Zeile stehen.")
    return "'" + value.replace("'", "''") + "'"


def local_psql(database, statement):
    result = subprocess.run(
        ["sudo", "-u", "postgres", "psql", "-X", "-w", "-qAt", "--host=/var/run/postgresql", "--port=5432", "--set=ON_ERROR_STOP=1", "--dbname=" + database],
        input="SET standard_conforming_strings = on;\n" + statement,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        # PostgreSQL errors may echo a statement containing a password.
        raise RuntimeError("PostgreSQL hat den Schritt abgelehnt. Zugang, Rechte und Serverprotokoll lokal prüfen. Es werden keine Fehlermeldungen mit möglichen Passwörtern ausgegeben.")
    return result.stdout.strip()


def create_database(path):
    _, values = read_config(path)
    database, user, password = (values.get(key, "") for key in ("PGDATABASE", "PGUSER", "PGPASSWORD"))
    for name in (database, user):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name):
            raise ValueError("PGDATABASE und PGUSER benötigen einfache Namen: kleine Buchstaben, Ziffern und Unterstriche.")
        if name in {"postgres", "template0", "template1", "public"} or name.startswith("pg_"):
            raise ValueError("Für die Schülerzeitung einen eigenen Namen verwenden.")
    if not password:
        raise ValueError("Zuerst den Aufruf mit secrets ausführen.")
    if values.get("PGHOST") not in {"host.docker.internal", "127.0.0.1", "localhost"}:
        raise ValueError("Dieses Skript erstellt nur Datenbanken im lokalen PostgreSQL-Dienst. Für eine entfernte Datenbank die dortige Verwaltung verwenden.")
    if values.get("PGPORT", "5432") != "5432":
        raise ValueError("Dieses Skript unterstützt den lokalen Standarddienst auf Port 5432.")
    existing = local_psql("postgres", "SELECT 'database' FROM pg_database WHERE datname=" + sql_literal(database) + ";\nSELECT 'user' FROM pg_roles WHERE rolname=" + sql_literal(user) + ";")
    if existing:
        raise ValueError("Datenbank oder Benutzer existiert bereits. Nichts geändert. Vorhandenen Zugang prüfen oder neue, freie Namen wählen.")
    print("Neue lokale Datenbank: " + database + "; neuer Benutzer: " + user)
    print("Der Benutzer erhält Tabellenrechte in seiner Datenbank, aber keine PostgreSQL-Verwaltungsrechte.")
    if input("Zum Anlegen den Datenbanknamen erneut eingeben: ").strip() != database:
        raise ValueError("Abgebrochen. Nichts geändert.")
    # Names are strictly validated above; values are quoted, never shell-interpolated.
    local_psql("postgres", 'SET password_encryption = \'scram-sha-256\';\nCREATE ROLE "' + user + '" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD ' + sql_literal(password) + ";")
    try:
        local_psql("postgres", 'CREATE DATABASE "' + database + '" OWNER "' + user + '" TEMPLATE template0 ENCODING \'UTF8\';')
        local_psql("postgres", 'REVOKE ALL ON DATABASE "' + database + '" FROM PUBLIC;')
        local_psql(database, 'REVOKE CREATE ON SCHEMA public FROM PUBLIC;\nGRANT USAGE, CREATE ON SCHEMA public TO "' + user + '";')
    except (RuntimeError, OSError):
        print("Ein Teil der Einrichtung kann bereits angelegt sein. Es wird nichts gelöscht. Vor einem neuen Versuch den lokalen Zustand prüfen.")
        raise
    print("Datenbank und Benutzer angelegt. Die Netzwerkverbindung aus Docker muss anschließend separat eingerichtet und geprüft werden.")


def main():
    parser = argparse.ArgumentParser(description="Vorbereitung der Schülerzeitungs-Installation")
    parser.add_argument("step", choices=("secrets", "database"))
    args = parser.parse_args()
    try:
        if args.step == "secrets":
            prepare_secrets(ENV_PATH)
        else:
            create_database(ENV_PATH)
    except (ValueError, RuntimeError, OSError) as error:
        parser.exit(1, "Einrichtung gestoppt: " + str(error) + "\n")


if __name__ == "__main__":
    main()
