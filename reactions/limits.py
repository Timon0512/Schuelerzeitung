import hashlib
import hmac
import ipaddress
from datetime import datetime, timezone as dt_timezone
from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from .models import RateLimitWindow


def client_ip(request):
    networks = [ipaddress.ip_network(value.strip()) for value in settings.TRUSTED_PROXY_NETWORKS]
    def parse(value):
        try:
            return ipaddress.ip_address(value.strip())
        except ValueError:
            return None
    def trusted(address):
        return address is not None and any(address in network for network in networks)
    address = parse(request.META.get("REMOTE_ADDR", ""))
    if trusted(address) and request.META.get("HTTP_X_FORWARDED_FOR"):
        # Walk from the trusted nearest hop; never trust a client-supplied leftmost value.
        chain = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
        for value in reversed(chain):
            if not trusted(address):
                break
            address = parse(value)
            if address is None:
                return "unknown"
    return str(address) if address else "unknown"


def window_key(ip, scope, window):
    return hmac.new(settings.SECRET_KEY.encode(), f"rate:{scope}:{window}:{ip}".encode(), hashlib.sha256).hexdigest()


@transaction.atomic
def consume_attempt(request, scope):
    seconds = getattr(settings, scope.upper() + "_RATE_SECONDS")
    limit = getattr(settings, scope.upper() + "_RATE_LIMIT")
    now = timezone.now()
    window = int(now.timestamp()) // seconds
    expires = datetime.fromtimestamp((window + 1) * seconds, tz=dt_timezone.utc)
    RateLimitWindow.objects.filter(expires_at__lte=now).delete()
    key = window_key(client_ip(request), scope, window)
    # One PostgreSQL upsert avoids a lookup/delete race when a window expires.
    # Saturate rejected counters so sustained abuse cannot overflow the column.
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO reactions_ratelimitwindow (key, expires_at, attempts) VALUES (%s, %s, 1) "
            "ON CONFLICT (key) DO UPDATE SET attempts = LEAST(reactions_ratelimitwindow.attempts + 1, %s) "
            "RETURNING attempts", [key, expires, limit + 1])
        attempts = cursor.fetchone()[0]
    return attempts <= limit, max(1, int((expires - now).total_seconds()) + 1)
