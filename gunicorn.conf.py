"""Gunicorn hooks for Prometheus multiprocess metrics."""

import os

from prometheus_client import multiprocess


def on_starting(server):
    metrics_directory = os.environ["PROMETHEUS_MULTIPROC_DIR"]
    for entry in os.scandir(metrics_directory):
        if entry.is_file(follow_symlinks=False):
            os.unlink(entry.path)


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
