# Task 06 - Cloud Infrastructure Deployment & Monitoring Capstone

This capstone extends the existing Flask/PostgreSQL application; it does not
replace it with a new application.

> **Deployment status:** The local Docker Compose stack has been built and
> verified with PostgreSQL, Prometheus, and Grafana. The Google Cloud project,
> billing, Cloud Run deployment, and Cloud Monitoring uptime check are **not
> verified as complete**. No Cloud Run URL is available. The cloud setup is
> paused because billing has not been enabled; no paid cloud resource was
> created as part of this work.

## Architecture

### Verified local architecture

```text
Browser / API client --> Flask + Gunicorn :5000 --> PostgreSQL
                               ^
                               | /metrics
                         Prometheus :9090
                               ^
                               | Prometheus data source
                            Grafana :3000
```

Docker Compose connects all four services on the project network. PostgreSQL,
Prometheus, and Grafana use named volumes. Prometheus and Grafana host ports
bind to `127.0.0.1`; they are intended for local use. PostgreSQL is not
published to a host port.

### Planned Google Cloud architecture (not deployed)

```text
Browser --> Cloud Run Flask service --> Cloud SQL for PostgreSQL
                    |
                    +--> Cloud Monitoring uptime check and alert

Local Docker Compose Prometheus/Grafana --> local app only
```

Cloud Run instances are stateless and their writable filesystem is disposable.
Do not run the persistent database or a production Prometheus TSDB on the
Cloud Run filesystem. Cloud Monitoring is the selected production uptime and
alerting path; the Prometheus/Grafana stack in this repository is for local
scraping and dashboards. Cloud SQL data persists outside Cloud Run.

The app's `/metrics` endpoint is available to callers of the app service. If
the Cloud Run service is made public, `/metrics` is public too unless
endpoint-level protection is added. The metrics use route templates rather
than user-supplied paths and contain aggregate counts, durations, and health.

## Local Docker Compose: app, database, Prometheus, Grafana

Run these commands in **PowerShell or the VS Code terminal**, from the
repository root. Docker Desktop must be running with Linux containers enabled.

For a fresh clone only, create the ignored local environment file without
overwriting an existing one:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Set a private `POSTGRES_PASSWORD` and `GRAFANA_ADMIN_PASSWORD` in `.env`. Do not
use the placeholder values from `.env.example`, commit `.env`, or share these
values. The local Grafana username defaults to `admin`.

Validate, build, and start the services:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Open:

- App dashboard: [http://localhost:5000](http://localhost:5000)
- App health: [http://localhost:5000/health](http://localhost:5000/health)
- Prometheus targets: [http://localhost:9090/targets](http://localhost:9090/targets)
- Grafana: [http://localhost:3000](http://localhost:3000)

Sign in to Grafana as `admin`; the password is the local value in `.env`. The
provisioned **Flask Application Monitoring** dashboard is under the
**Application** folder. It shows total HTTP requests, request rate, application
uptime, HTTP error rate, p95 response time, and application health.

The Prometheus configuration is
[monitoring/prometheus/prometheus.yml](monitoring/prometheus/prometheus.yml).
Grafana provisioning is in
[monitoring/grafana/provisioning](monitoring/grafana/provisioning), and the
dashboard definition is
[monitoring/grafana/dashboards/application-dashboard.json](monitoring/grafana/dashboards/application-dashboard.json).

Useful local checks:

```powershell
Invoke-RestMethod http://localhost:5000/health
(Invoke-RestMethod http://localhost:5000/api/records).records.Count
(Invoke-WebRequest -UseBasicParsing http://localhost:5000/metrics).Content
```

In Prometheus, the target job is `flask_app` and its target is `app:5000`.
`docker compose down` stops containers but preserves the named volumes. Do not
use `docker compose down -v` unless you intend to delete the database and
monitoring data.

## Application endpoints and metrics

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Flask records dashboard |
| `GET` | `/health` | Application and PostgreSQL health; returns 503 when PostgreSQL is unavailable |
| `GET` | `/api/records` | List records as JSON |
| `POST` | `/api/records` | Create a record from a JSON `name` |
| `POST` | `/records` | Create a record from the dashboard form |
| `GET` | `/metrics` | Prometheus exposition endpoint |

Prometheus metrics include `http_requests_total`,
`http_request_duration_seconds`, `http_errors_total`, `application_health`,
and `application_start_time_seconds`. Route labels use Flask route templates
to avoid high-cardinality values from user input. `/metrics` requests are not
included in the HTTP request counters.

## Environment variables

| Variable | Local use | Cloud Run use |
| --- | --- | --- |
| `POSTGRES_DB` | Compose PostgreSQL database name; defaults to `projectdb` | Not used for the managed database |
| `POSTGRES_USER` | Compose PostgreSQL user; defaults to `projectuser` | Not used for the managed database |
| `POSTGRES_PASSWORD` | Local PostgreSQL password in ignored `.env` | Use a separate Secret Manager secret |
| `APP_PORT` | Host port mapped to the app; defaults to `5000` | Not used; Cloud Run supplies `PORT` |
| `PORT` | Container listener; defaults to `5000` | Cloud Run supplies its configured container port |
| `DB_HOST` | Compose sets this to `db` | Cloud SQL socket path: `/cloudsql/PROJECT:REGION:INSTANCE` |
| `DB_PORT` | Compose sets this to `5432` | PostgreSQL default `5432` |
| `DB_NAME`, `DB_USER` | Compose copies the PostgreSQL settings into the app | Non-secret Cloud SQL database/user settings |
| `DB_PASSWORD` | Compose copies `POSTGRES_PASSWORD` into the app | Reference a Secret Manager version; do not put the password in an image or command |
| `GRAFANA_ADMIN_USER` | Optional local Grafana username; defaults to `admin` | Not used |
| `GRAFANA_ADMIN_PASSWORD` | Local Grafana password in ignored `.env` | Not used |
| `PROMETHEUS_PORT`, `GRAFANA_PORT` | Optional host ports; defaults are `9090` and `3000` | Not used |
| `PROMETHEUS_MULTIPROC_DIR` | Internal Gunicorn metrics directory in the app image | Internal to each Cloud Run instance |

The `.env` file is ignored by both Git and Docker build context. `.env.example`
contains placeholders only. Cloud Run's service identity needs the Cloud SQL
Client role for an attached Cloud SQL instance and Secret Manager Secret
Accessor for the database password secret.

## Google Cloud preparation and cost boundary

The Google Cloud project and deployment are not complete. Before continuing,
review the current [Google Cloud Free Trial terms](https://cloud.google.com/free)
and [Cloud SQL pricing](https://cloud.google.com/sql/pricing). A Cloud SQL
PostgreSQL free-trial instance is available for 30 days to eligible users, but
requires billing to be enabled; data transfer over the public internet,
cross-region data transfer, and final-backup storage can still incur charges.
After the trial, an unupgraded instance stops serving requests. Free-tier
eligibility and pricing can change. No billing account or cloud resource is
created by these instructions.

When the account/project and cost approval are ready, the deployment sequence
is:

1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install),
   sign in, and select the intended project.
2. Review costs and explicitly approve billing before enabling APIs or creating
   Cloud SQL, Artifact Registry, Secret Manager, Cloud Run, or monitoring
   resources.
3. Use a Cloud SQL instance in the same region as Cloud Run, attach it to the
   Cloud Run service, and grant the runtime service account Cloud SQL Client.
   Apply [init.sql](init.sql) to the Cloud SQL database once; Cloud SQL does not
   run the Docker PostgreSQL initialization script automatically.
4. Store `DB_PASSWORD` in Secret Manager and grant the runtime identity access.
5. Build and push the existing application image to Artifact Registry, then
   deploy it to Cloud Run. Cloud Run sets `PORT`; the container honors it.
6. Use Cloud Monitoring to create an HTTPS uptime check for `/health` and an
   alert policy. Review any monitoring charges before creating the check.
7. Verify the Cloud Run URL and database health. Do not report the service or
   uptime alert as live until both are actually tested.

Cloud SQL connection details are documented in Google's
[Cloud Run connection guide](https://cloud.google.com/sql/docs/postgres/connect-run).
Cloud Run stores secrets through
[Secret Manager integration](https://cloud.google.com/run/docs/configuring/services/secrets).
The local Prometheus/Grafana stack does not scrape the deployed Cloud Run
service.

### Account, project, and CLI commands

Creating a Google account/project is separate from creating billable services.
An eligible new customer can review the
[Google Cloud Free Trial](https://cloud.google.com/free); enrollment can require
a billing account and payment method. Since billing is currently deferred for
this project, do not continue through any billing prompt.

After you have an account and decide to create an empty project, run in
PowerShell. Replace the ID with a globally unique value:

```powershell
$PROJECT_ID = 'replace-with-a-unique-project-id'
gcloud projects create $PROJECT_ID --name="Docker Cloud Capstone 2026"
gcloud config set project $PROJECT_ID
gcloud --version
```

`gcloud projects create` creates a project only; it does not deploy the app.
If the command asks for billing or the account lacks permission, stop and
resolve that decision before proceeding. To authorize the CLI, run
`gcloud init` and finish Google sign-in in the browser. Do not share credentials
or authentication codes.

### Build, push, and deploy template

**Do not run this block until billing/cost approval is complete** and the
project, APIs, Artifact Registry repository, Cloud SQL instance, Secret Manager
secret, and runtime service-account permissions are ready. These commands have
not been executed. Artifact Registry storage, Cloud Run usage, Cloud SQL
networking, and monitoring may incur charges.

Run in PowerShell from the repository root, replacing every placeholder:

```powershell
$PROJECT_ID = 'YOUR_PROJECT_ID'
$REGION = 'YOUR_REGION'
$REPOSITORY = 'containers'
$SERVICE = 'flask-records'
$INSTANCE_NAME = 'YOUR_CLOUD_SQL_INSTANCE'
$INSTANCE_CONNECTION_NAME = $PROJECT_ID + ':' + $REGION + ':' + $INSTANCE_NAME
$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/flask-records:task06"

# Run only after billing approval.
gcloud services enable run.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com monitoring.googleapis.com --project $PROJECT_ID
gcloud artifacts repositories create $REPOSITORY --location=$REGION --repository-format=docker --project=$PROJECT_ID
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
docker build -t $IMAGE .
docker push $IMAGE
```

Before deploying, apply `init.sql` to the Cloud SQL database once using Cloud
SQL Studio or another approved PostgreSQL client. Attach the Cloud SQL instance
to the Cloud Run service and use a runtime service account with Cloud SQL Client
and Secret Manager Secret Accessor roles. Create the `db-password` secret in
Secret Manager; never put its value in this file or a command.

```powershell
gcloud run deploy $SERVICE `
  --image=$IMAGE `
  --region=$REGION `
  --port=8080 `
  --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME `
  --set-env-vars="DB_HOST=/cloudsql/$INSTANCE_CONNECTION_NAME,DB_PORT=5432,DB_NAME=projectdb,DB_USER=projectuser" `
  --set-secrets="DB_PASSWORD=db-password:1" `
  --min=0 `
  --max=2 `
  --allow-unauthenticated

$SERVICE_URL = gcloud run services describe $SERVICE --region=$REGION --format="value(status.url)"
Invoke-RestMethod "$SERVICE_URL/health"
```

`--allow-unauthenticated` makes the service public, including `/metrics`; omit
it if the app should require Cloud Run IAM authentication. Decide whether
public metrics are acceptable before deploying. To configure deployed uptime,
create a Cloud Monitoring HTTPS uptime check for `$SERVICE_URL/health` and an
alert policy in the Google Cloud Console. Check current Monitoring pricing
before creating that check.

## Verification results

Verified locally during this update:

- `docker compose config --quiet` passed.
- All four Compose services started; the Flask and PostgreSQL health checks
  report healthy.
- `GET /health` reported `status=ok`, application healthy, and database
  connected.
- `GET /api/records` succeeded.
- Prometheus reported the `flask_app` target as `up` and returned request,
  rate, uptime, latency, health, and error-rate query results.
- Grafana health returned OK and its provisioned dashboard was present with
  six panels. A zero-error interval displayed 0% rather than no data.
- The image was also tested with `PORT=8080`; the dashboard returned HTTP 200.

Not verified: Cloud Run deployment, a public application URL, Cloud SQL in
Google Cloud, or Cloud Monitoring uptime checks/alerts. These remain pending;
no cloud deployment is claimed.

## Screenshots checklist

Capture genuine screenshots without passwords, access tokens, or billing
details:

1. `docker compose ps` showing app, database, Prometheus, and Grafana.
2. App dashboard and `/health` response.
3. Prometheus `/targets` showing `flask_app` as `UP`.
4. Grafana dashboard with populated panels.
5. A Cloud Run service URL and successful `/health` only after a real deployment.
6. Cloud Monitoring uptime check and alert only after they are configured.

## Previous Task 03 documentation

The sections below retain the original Docker-containerization notes and
historical supplied test results.

> **Historical reported results:** Application health was reported as
> `healthy`, the database as `connected`, GET and POST API requests as
> successful, and the Flask container as `appuser` (UID 10001). The application
> image `rab-tech-task03:latest` was reported as **101 MB disk usage** and
> **24.8 MB content size**. These measurements are distinct; those results were
> supplied for the earlier Task 03 submission and are not new cloud results.

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
│   ├── metrics.py
│   ├── routes.py
│   └── database.py
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       │   └── application-dashboard.json
│       └── provisioning/
│           ├── dashboards/
│           │   └── application.yml
│           └── datasources/
│               └── prometheus.yml
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
├── gunicorn.conf.py
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
