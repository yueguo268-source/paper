import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('SERVER_PORT', '5000')}"
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 2000
timeout = 180
keepalive = 10

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

proc_name = "survey_app"

max_requests = 1000
max_requests_jitter = 50
preload_app = True

limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
