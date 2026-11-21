# Task 03 – Multi-Stage Docker Containerization & Optimization

A lightweight Flask and PostgreSQL application using a multi-stage Docker
build, Docker Compose, health checks, persistent database storage, and
non-root container execution.

> **Reported results:** Application health is `healthy`, the database is
> `connected`, GET and POST API requests were successful, and the Flask
> container runs as `appuser` (UID 10001). The application image
> `rab-tech-task03:latest` is reported as **101 MB disk usage** and **24.8 MB
> content size**. Disk usage is below the **150 MB** target. These measurements
> are distinct; the 24.8 MB content size is not the 101 MB disk-usage figure.
> Results are the project results supplied for this submission.

## Project Overview

This internship project packages a Flask records dashboard and a PostgreSQL
database for containerized use. The browser dashboard displays application and
database status and records. A JSON API supports retrieving and creating
records. Docker Compose coordinates the application and database services,
including their configuration, health checks, private network, and database
volume.

## Problem Statement

An application and its database can be difficult to set up consistently across
machines when dependencies, configuration, and service startup are handled
manually. This project uses Docker and Compose to provide a reproducible
multi-service setup, separate build-only requirements from runtime files, and
make application and database health visible.

## Project Objectives

- Build a production-oriented Flask image with a multi-stage Dockerfile.
- Keep build-time tooling and package caches out of the final image.
- Run the web application with Gunicorn as a non-root user.
- Connect Flask to PostgreSQL using environment-based configuration.
- Support record retrieval and insertion through a web dashboard and API.
- Use Docker Compose health checks, service dependencies, and persistent
  database storage.
- Document verification and submission steps without claiming unverified
  results.

## Technologies

| Technology | Purpose |
| --- | --- |
| Python 3.12 Alpine | Application runtime and Docker base image |
| Flask | Dashboard and HTTP API |
| Gunicorn | Production WSGI server |
| psycopg 3 | PostgreSQL client |
| PostgreSQL 16 Alpine | Relational database |
| Docker | Image build and container runtime |
| Docker Compose | Multi-service configuration and orchestration |
| HTML and CSS | Dashboard presentation |

## System Architecture

```text
Browser / API client
        |
        | HTTP :5000
        v
Flask application served by Gunicorn (appuser, UID 10001)
        |
        | PostgreSQL protocol over the Compose private network
        v
PostgreSQL 16 ---- named volume: postgres_data
        ^
        |
   init.sql (first initialization of an empty database volume)
```

The app publishes port 5000 to the host. PostgreSQL is not published to a host
port; the app reaches it using the Compose service hostname `db`. The named
`postgres_data` volume stores database files independently of the app
container.

## Project Structure

```text
multi-stage-docker-project/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   └── database.py
├── templates/
│   └── index.html
├── static/
│   └── css/
│       └── style.css
├── submission/
│   ├── project-summary.md
│   ├── testing-report.md
│   └── docker-commands.md
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── init.sql
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md
```

## Multi-Stage Docker Build

The Dockerfile defines two Python 3.12 Alpine stages:

1. **`builder`** installs the pinned Python dependencies into `/install`.
2. **`production`** starts from a clean Python Alpine base and copies only the
   installed dependencies and application files needed at runtime.

The Compose build selects the `production` target. This keeps the production
image independent of builder-stage files and keeps the Docker build instructions
clear about the runtime stage.

## Docker Image Optimization

The image build is optimized by:

- Using the smaller Alpine Python base.
- Separating dependency installation from the runtime stage.
- Installing Python packages without retaining pip's download cache.
- Copying only the application package, templates, static assets, entry point,
  and installed dependencies into production.
- Excluding local and generated files from the build context with
  `.dockerignore`.

### Supplied image-size result

| Measurement | Reported value |
| --- | ---: |
| Image | `rab-tech-task03:latest` |
| Disk usage | **101 MB** |
| Content size | **24.8 MB** |
| Disk-usage target | **Below 150 MB** |
| Target status | **Met**, based on the reported 101 MB disk usage |

Disk usage and content size are different metrics. The 101 MB result is the
reported disk-usage value used for comparison with the 150 MB target; do not
describe the 24.8 MB content size as disk usage.

## Non-Root Security

The production Docker stage creates the `appuser` user and `app` group with
numeric ID 10001, assigns application files to that user, and sets
`USER appuser`. The supplied verification result is:

```text
uid=10001(appuser) gid=10001(app)
```

Database credentials are provided through environment variables rather than
hard-coded in the application. Keep real credentials in the local `.env` file
and never commit that file. `.env.example` is safe to commit because it uses a
placeholder password.

## PostgreSQL Integration

The app reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`
from its environment. In Compose, `DB_HOST` is the `db` service name. SQL
operations use psycopg's parameter binding. The `init.sql` file initializes the
records table and sample records when PostgreSQL initializes a new data
directory; it does not automatically rerun on an already-initialized volume.

## Docker Compose Configuration

The Compose file defines:

- `app`: Flask served by Gunicorn; exposes host port 5000 by default.
- `db`: PostgreSQL 16 Alpine, available internally to the app.
- `project_network`: private bridge network for inter-service communication.
- `postgres_data`: named volume for PostgreSQL persistence.
- Health checks and a dependency so the app waits for the database health
  check.

Compose service names are `app` and `db`; configured container names are
`flask_app` and `postgres_db`.

## Health Checks

PostgreSQL's check uses `pg_isready`. The app check calls
`http://127.0.0.1:5000/health`; the endpoint also tests database connectivity.
The supplied endpoint result is:

```text
application: healthy
database: connected
status: ok
```

## Persistent Docker Volumes

PostgreSQL stores its data in the Compose named volume `postgres_data`. The
volume survives `docker compose down`, which removes containers and the
network. Do **not** use `docker compose down -v` during normal testing: `-v`
removes the named volume and can delete database records. Volume persistence
across a restart should be tested separately before claiming that specific
behavior as verified.

## API Documentation

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Renders the dashboard and current database records. |
| `GET` | `/health` | Returns application/database health; reports HTTP 503 if PostgreSQL is unavailable. |
| `GET` | `/api/records` | Returns records as JSON. |
| `POST` | `/api/records` | Creates a record from a JSON `name` field. |
| `POST` | `/records` | Creates a record from the dashboard form. |

The API requires a non-empty name of at most 120 characters. For the JSON API,
send `Content-Type: application/json`.

The supplied results report that GET successfully returned saved records and
POST successfully inserted a new record.

## Installation Requirements

- Git.
- Docker Engine or Docker Desktop with Docker Compose v2.
- PowerShell (commands below use PowerShell syntax).
- A local `.env` file with a private PostgreSQL password.

For local development without Docker, Python 3.12 and a reachable PostgreSQL
server are also required.

## Setup Instructions

Open PowerShell in the project root and create `.env` from the safe template if
it does not already exist. This command preserves an existing `.env`:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env`, replacing `POSTGRES_PASSWORD` with a strong private password.
`POSTGRES_DB`, `POSTGRES_USER`, and `APP_PORT` have example values in
`.env.example`. The `.env` file is ignored by Git; keep `.env.example` in the
repository.

## Build and Run

From the project root:

```powershell
docker --version
docker compose version
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

Open [http://localhost:5000](http://localhost:5000) for the dashboard. Use
`docker compose logs` to inspect service output. Stop the containers without
deleting the database volume using:

```powershell
docker compose down
```

## Testing Instructions

Check application health and retrieve records:

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/api/records
```

Insert a record:

```powershell
Invoke-RestMethod -Uri http://localhost:5000/api/records `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"name":"My Docker Record"}'
```

Verify the app process identity and list Docker volumes:

```powershell
docker exec flask_app id
docker volume ls
```

The supplied test results report healthy application/database status, successful
GET and POST requests, and UID 10001 execution. Compose status and database
volume persistence are not reported as tested in the accompanying
[testing report](submission/testing-report.md).

## Docker Image Size Verification

List the application image and its displayed disk usage:

```powershell
docker image ls rab-tech-task03:latest
```

To inspect Docker's image size in bytes and compare to 150,000,000 bytes:

```powershell
$bytes = [int64](docker image inspect rab-tech-task03:latest --format '{{.Size}}')
"{0:N2} MB (decimal), {1:N2} MiB" -f ($bytes / 1000000), ($bytes / 1048576)
if ($bytes -lt 150000000) { "PASS: below 150 MB" } else { "FAIL: at least 150 MB" }
```

The supplied result is **101 MB disk usage**, below the target of 150 MB.
Content size was separately reported as **24.8 MB**. Retain the output from
your own image measurement if your instructor requires fresh evidence.

## Screenshots Checklist

Capture real screenshots manually; no screenshots are generated by this
project's documentation. Save them in a repository location such as
`screenshots/` if appropriate, and ensure they contain no secrets.

1. Docker Desktop running.
2. Docker image build completed successfully.
3. Docker Compose containers running.
4. Flask dashboard open in a browser.
5. Health endpoint response.
6. GET API response.
7. POST API response.
8. Non-root user verification showing UID 10001.
9. Docker image listing showing 101 MB disk usage.
10. Docker volume listing.

## GitHub Repository Instructions

Suggested repository name:

```text
multi-stage-docker-containerization
```

Suggested GitHub repository description:

> A lightweight Flask and PostgreSQL application using multi-stage Docker
> builds, Docker Compose, health checks, persistent volumes, and non-root
> container execution.

Create a new, empty repository on GitHub with the suggested name. In PowerShell,
from the project root, inspect the Git status and ensure `.env` is ignored
before staging:

```powershell
git status --short
git check-ignore .env
git add .
git status --short
git commit -m "Document Docker project for internship submission"
git branch -M main
git remote -v
```

If no remote is configured, add your own repository URL, then push:

```powershell
git remote add origin https://github.com/<YOUR-USERNAME>/multi-stage-docker-containerization.git
git push -u origin main
```

If a remote already exists, verify it with `git remote -v` and use the correct
URL rather than adding a duplicate. Never stage or push `.env`, passwords,
tokens, or other secrets. The repository description is set on GitHub when you
create or edit the repository; the suggested text above is ready to copy.

## Submission Documentation

- [Project summary](submission/project-summary.md)
- [Testing report](submission/testing-report.md)
- [Docker commands](submission/docker-commands.md)

## Conclusion

The project provides a Flask/PostgreSQL application packaged with a multi-stage
Docker build and Docker Compose. The supplied results report successful health,
database, API, non-root, and image-size checks. Use the testing report to
distinguish those results from Compose and volume checks that still need
evidence before they are claimed as passed.
