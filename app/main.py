import json
import logging
import os
import sys
import time

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

# Settings come from environment variables, with a safe default for each.
APP_NAME = os.environ.get("APP_NAME", "maright-app")
GREETING = os.environ.get("GREETING", "Hello from Mission Control")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
READY_AFTER_SECONDS = float(os.environ.get("READY_AFTER_SECONDS", "5"))


class JsonFormatter(logging.Formatter):
    """Write every log line as one line of JSON, so a computer can read it."""

    def format(self, record):
        return json.dumps({
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "app": APP_NAME,
            "message": record.getMessage(),
        })


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log = logging.getLogger(APP_NAME)
log.addHandler(handler)
log.setLevel(LOG_LEVEL)
log.propagate = False

REQUESTS = Counter("app_requests_total", "Requests answered, by path", ["path"])
STARTED = time.time()

app = FastAPI(title=APP_NAME)
log.info("starting up")


@app.get("/")
def home():
    REQUESTS.labels(path="/").inc()
    log.info("home page served")
    return {"app": APP_NAME, "message": GREETING}


@app.get("/health")
def health():
    REQUESTS.labels(path="/health").inc()
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response):
    REQUESTS.labels(path="/ready").inc()
    if time.time() - STARTED < READY_AFTER_SECONDS:
        response.status_code = 503
        return {"status": "starting"}
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
