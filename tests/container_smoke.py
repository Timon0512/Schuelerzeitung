"""Run inside the built Linux image, --network none; no database required."""
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import urllib.error

assert os.getuid() == 10001
assert not Path('/app/.env').exists()
assert Path('/app/staticfiles/news/public.css').is_file()
process = subprocess.Popen(['gunicorn', '--config', 'deploy/gunicorn.conf.py', 'config.wsgi:application'])
try:
    for attempt in range(50):
        try:
            request = urllib.request.Request('http://127.0.0.1:8000/admin/login/',
                headers={'Host': 'zeitung.example.invalid', 'X-Forwarded-Proto': 'https'})
            with urllib.request.urlopen(request, timeout=10) as response:
                assert response.status == 200
                assert 'Secure' in response.headers.get('Set-Cookie', '')
                assert b'csrfmiddlewaretoken' in response.read()
            break
        except (urllib.error.URLError, TimeoutError):
            if process.poll() is not None or attempt == 49:
                raise
            time.sleep(0.1)
    # Private media must redirect anonymous visitors before any database lookup.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request('http://127.0.0.1:8000/redaktion/medien/12345678-1234-1234-1234-123456789abc',
        headers={'Host': 'zeitung.example.invalid', 'X-Forwarded-Proto': 'https'})
    try:
        opener.open(request)
        raise AssertionError('Anonymous private-media request succeeded')
    except urllib.error.HTTPError as error:
        assert error.code == 302 and '/admin/login/' in error.headers['Location']
    print('Non-root Gunicorn, static assets, secret exclusion, HTTPS login and private-media gate passed.')
finally:
    process.terminate()
    process.wait(timeout=15)
