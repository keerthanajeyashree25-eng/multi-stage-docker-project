# Project Summary

## Task 03 – Multi-Stage Docker Containerization & Optimization

### Overview

This project packages a Python Flask records application and PostgreSQL database
for local and containerized use. Docker Compose coordinates the services, while
the Flask dashboard and JSON API provide record creation, retrieval, and health
information.

### Objectives

- Demonstrate a multi-stage Docker build for a Python application.
- Keep build-time dependencies out of the production image.
- Connect Flask to PostgreSQL using environment-based configuration.
- Run the web process as a dedicated non-root user.
- Provide health checks and persistent database storage through Compose.
- Document build, run, test, and GitHub submission steps.

### Technologies

Python 3.12 Alpine, Flask, Gunicorn, psycopg 3 with its binary extra,
PostgreSQL 16 Alpine, Docker, Docker Compose, HTML, and CSS.

### Architecture

The browser or API client connects to the Flask/Gunicorn service on port 5000.
The app connects to PostgreSQL over the Compose private bridge network. A named
Docker volume stores PostgreSQL data, and `init.sql` initializes the records
table when the database volume is first created.

### Main Features

- Flask dashboard displaying application/database status and records.
- `GET /api/records` to retrieve records.
- `POST /api/records` to create a record.
- `GET /health` checks application and database availability.
- Compose-managed database initialization, service dependencies, and health checks.

### Security Features

- The app container runs as `appuser` with UID 10001, not as root.
- Database credentials are configured through environment variables.
- `.env` is ignored by Git; `.env.example` contains only placeholder values.
- SQL parameters are used for database operations.
- PostgreSQL is available to the app through the internal Compose network.

### Optimization Techniques

- A multi-stage Dockerfile separates dependency installation from runtime.
- The production stage uses `python:3.12-alpine`.
- Only the installed Python dependencies and application files are copied into
  the production stage.
- Pip is instructed not to retain a package download cache.
- The reported final application image disk usage is 101 MB, below the 150 MB
  target. Its separately reported content size is 24.8 MB; these are distinct
  image-size measurements.

### Conclusion

The project demonstrates a containerized Flask/PostgreSQL application with a
multi-stage build, a non-root app process, health checks, and persistent
database storage. The supplied test results report healthy application and
database status, successful GET and POST API requests, and a 101 MB application
image disk usage.
