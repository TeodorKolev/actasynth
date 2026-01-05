"""Gunicorn configuration for production deployment"""

import multiprocessing
import os

# Server Socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker Processes
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevent memory leaks)
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "agentops-studio"

# Server Mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"


def on_starting(server):
    """Called just before the master process is initialized"""
    server.log.info("Starting AgentOps Studio")


def on_reload(server):
    """Called when a worker is reloaded"""
    server.log.info("Reloading workers")


def when_ready(server):
    """Called just after the server is started"""
    server.log.info("Server is ready. Workers: %s", workers)


def on_exit(server):
    """Called just before the server is shut down"""
    server.log.info("Shutting down AgentOps Studio")
