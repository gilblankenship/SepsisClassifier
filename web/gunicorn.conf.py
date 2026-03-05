"""Gunicorn configuration for SepsisDx on Jetson AGX Thor."""

import os

# Server socket — unique port per app on the Jetson
# vitalmatch.ai=8080, patent-man.com=8081, sepsis-dx.com=8082
bind = "127.0.0.1:8082"
backlog = 256

# Workers: 2 workers for ML inference/training concurrency
workers = int(os.environ.get("GUNICORN_WORKERS", 2))
threads = int(os.environ.get("GUNICORN_THREADS", 4))
worker_class = "gthread"

# ML training and SHAP explanations can be slow
timeout = 300
graceful_timeout = 30
keepalive = 5

# Memory leak protection
max_requests = 500
max_requests_jitter = 50

# Logging
accesslog = "/var/log/sepsis-dx/gunicorn-access.log"
errorlog = "/var/log/sepsis-dx/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "sepsis-dx"

# Working directory
chdir = "/opt/sepsis-dx/web"

# Security — only trust nginx proxy headers
forwarded_allow_ips = "127.0.0.1"
