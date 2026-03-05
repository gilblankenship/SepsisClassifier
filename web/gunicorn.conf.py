"""Gunicorn configuration for SepsisDx web application."""

import os

bind = "127.0.0.1:8081"
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
threads = int(os.environ.get("GUNICORN_THREADS", 4))
worker_class = "sync"

# ML training and SHAP can be slow
timeout = 300
keepalive = 5
graceful_timeout = 60

max_requests = 500
max_requests_jitter = 50

accesslog = "/var/log/sepsis-dx/gunicorn-access.log"
errorlog = "/var/log/sepsis-dx/gunicorn-error.log"
loglevel = "info"
proc_name = "sepsis-dx"

chdir = "/opt/sepsis-dx/web"
forwarded_allow_ips = "127.0.0.1"
