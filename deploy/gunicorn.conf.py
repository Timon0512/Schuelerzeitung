bind = "0.0.0.0:8000"
workers = 2
worker_class = "gthread"
threads = 4
timeout = 60
graceful_timeout = 60
worker_tmp_dir = "/tmp"
accesslog = None  # Do not log query strings, visitor IPs or submission content.
errorlog = "-"
capture_output = False
# Django alone interprets the explicitly enabled, proxy-overwritten header.
forwarded_allow_ips = ""
