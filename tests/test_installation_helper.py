"""Installation checks using temporary configuration and no real database."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from deploy import prepare_installation as setup


class InstallationHelperTests(unittest.TestCase):
    def test_secrets_are_generated_once_without_printing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "production.env"
            path.write_text("DJANGO_SECRET_KEY=\nPGPASSWORD=\nPGDATABASE=sz\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                setup.prepare_secrets(path)
                first = path.read_text(encoding="utf-8")
                setup.prepare_secrets(path)
            self.assertEqual(first, path.read_text(encoding="utf-8"))
            _, values = setup.read_config(path)
            for key in ("DJANGO_SECRET_KEY", "PGPASSWORD"):
                self.assertEqual(len(values[key]), 64)
                self.assertNotIn(values[key], output.getvalue())
            self.assertEqual(values["PGDATABASE"], "sz")

    def test_existing_secret_and_password_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "production.env"
            original = 'DJANGO_SECRET_KEY="existing-key"\nPGPASSWORD=existing-password\n'
            path.write_text(original, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                setup.prepare_secrets(path)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_existing_database_or_role_prevents_all_writes(self):
        with patch.object(setup, "read_config", return_value=("", {
            "PGHOST": "host.docker.internal", "PGDATABASE": "sz", "PGUSER": "sz_app", "PGPASSWORD": "test-only",
        })), patch.object(setup, "local_psql", return_value="database") as execute:
            with self.assertRaisesRegex(ValueError, "existiert bereits"):
                setup.create_database(Path("unused"))
            self.assertEqual(execute.call_count, 1)
            self.assertNotIn("CREATE", execute.call_args.args[1])

    def test_new_database_uses_restricted_role_and_quoted_password(self):
        with patch.object(setup, "read_config", return_value=("", {
            "PGHOST": "host.docker.internal", "PGDATABASE": "sz", "PGUSER": "sz_app", "PGPASSWORD": "test'only",
        })), patch.object(setup, "local_psql", return_value="") as execute, patch("builtins.input", return_value="sz"), contextlib.redirect_stdout(io.StringIO()):
            setup.create_database(Path("unused"))
            statements = "\n".join(call.args[1] for call in execute.call_args_list)
            self.assertIn("NOSUPERUSER NOCREATEDB NOCREATEROLE", statements)
            self.assertIn("'test''only'", statements)
            self.assertIn("scram-sha-256", statements)
            self.assertNotIn("DROP", statements)

    def test_duplicate_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "production.env"
            path.write_text("PGPASSWORD=one\nPGPASSWORD=two\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mehrfach"):
                setup.prepare_secrets(path)


if __name__ == "__main__":
    unittest.main()
