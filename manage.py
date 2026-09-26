import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if len(sys.argv) > 1 and sys.argv[1] in {"migrate", "runserver", "createsuperuser", "load_demo", "dbshell", "flush"}:
        from config.db_safety import require_database_configuration
        require_database_configuration()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
