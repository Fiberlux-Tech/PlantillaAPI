# Gunicorn Configuration File
# Production settings for PlantillaAPI

import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker Processes
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests to avoid all workers restarting at once
timeout = 120
keepalive = 5

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"  # Changed from debug to info for production
capture_output = True

# Process Naming
proc_name = "plantillaapi"

# Server Mechanics
daemon = False  # Managed by systemd
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
# keyfile = None
# certfile = None
