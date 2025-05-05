import os
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = ["localhost"]

if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
