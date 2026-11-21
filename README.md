# Task 03 — Multi-Stage Docker Containerization

A small Flask dashboard backed by PostgreSQL. It displays application and database
status, lists database records, and lets a user add a record. Docker Compose runs
the application and database on a private bridge network with health checks and
persistent database storage.

> **Image-size result:** Not measured in the authoring workspace because Docker is
> not installed there. Build and measure it in Docker-enabled Linux (for example,
> GitHub Codespaces) using the commands in [Image optimization and measurement](#image-optimization-and-measurement).
> Do not report the under-150-MB target as achieved until that measurement passes.

## Objectives

- Demonstrate a multi-stage Python Docker build and a small runtime image.
- Run Gunicorn as a dedicated, non-root user.
- Connect Flask to PostgreSQL using environment-based credentials.
- Use parameterized SQL for record insertion and retrieval.
- Provide Compose health checks, service ordering, a private network, and a named database volume.

## Technologies

Python 3.12, Flask, Gunicorn, PostgreSQL 16, psycopg 3, Docker, Docker Compose,
HTML, and CSS.

## Architecture

The browser sends requests to the Flask/Gunicorn service on port 5000. Flask
uses psycopg to connect to the PostgreSQL service over the Compose-only
`project_network`. PostgreSQL stores its data in `postgres_data`; the SQL
initialization script creates and seeds the `records` table when the database
volume is first initialized.

```text
Browser ── HTTP :5000 ──> Flask + Gunicorn ── private network ──> PostgreSQL
                                  │                                 │
                          app health check                   postgres_data
                                                                    │
                                                           init.sql on first start
```

## Project structure and file purposes

```text
multi-stage-docker-project/
├── app/
│   ├── __init__.py          # Flask package marker
│   ├── routes.py            # Dashboard, health, and records API routes
│   └── database.py          # PostgreSQL connection and query helpers
├── templates/
│   └── index.html           # Responsive dashboard markup
├── static/
│   └── css/
│       └── style.css        # Dashboard styling
├── app.py                   # Flask application factory and WSGI entry point
├── requirements.txt         # Python runtime dependencies
├── Dockerfile               # Builder and minimal runtime stages
├── docker-compose.yml       # App, database, network, checks, and volume
├── init.sql                 # Creates and seeds the PostgreSQL table
├── .dockerignore            # Files excluded from the Docker build context
├── .gitignore               # Local secrets and generated files excluded from Git
├── .env.example             # Safe-to-copy environment variable template
└── README.md                # Setup, run, test, and submission guide
```

## Configuration and security

The Compose file requires `POSTGRES_PASSWORD`; it does not supply a default
password. Database name and user default to `projectdb` and `projectuser`.
Credentials are passed to the app as environment variables rather than placed
in source code. The database port is not published to the host. The web
container runs as UID/GID `10001`, and the Docker health check tests the app's
database-aware `/health` endpoint.

### Prepare the environment file

In PowerShell, from the project directory:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env` and set `POSTGRES_DB=projectdb`, `POSTGRES_USER=projectuser`, and a
private `POSTGRES_PASSWORD`. `APP_PORT=5000` selects the local web port. If
`.env` already exists, preserve it and check/update those values rather than
overwriting it. Never commit `.env`; `.gitignore` excludes it. The example
password in `.env.example` is only a placeholder and must be replaced.

## Run the Python application locally

This option requires a locally installed PostgreSQL server. The authoring
Windows workspace does not have Docker, so this is not the recommended way to
run the full stack.

1. Create a PostgreSQL database/user and apply `init.sql` to the `projectdb`
   database as that user.
2. In PowerShell, create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Configure the local connection and start Flask:

   ```powershell
   $env:DB_HOST = "127.0.0.1"
   $env:DB_PORT = "5432"
   $env:DB_NAME = "projectdb"
   $env:DB_USER = "projectuser"
   $env:DB_PASSWORD = "your-local-password"
   python app.py
   ```

4. Open `http://127.0.0.1:5000`. Stop the development server with `Ctrl+C`.

The development server is for local learning only. In Compose, Gunicorn serves
the application.

## Run with Docker Compose

Docker must be available in the terminal where these commands run. Since it is
not installed in the authoring Windows environment, use the Codespaces
instructions below or another Docker-enabled Linux host.

```sh
docker --version
docker compose version
docker compose build
docker compose up -d
docker compose ps
```

Open the forwarded port 5000, or `http://localhost:5000` when running on a
machine with local Docker. Compose waits until PostgreSQL's health check passes
before starting the app. Initial database creation runs `init.sql`; PostgreSQL
does not rerun it on an already-initialized data volume.

Stop and remove the containers/network while preserving records:

```sh
docker compose down
```

**Warning:** `docker compose down -v` deletes the named `postgres_data` volume
and all records stored in it. Use it only when you intentionally want to reset
the database.

## HTTP endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Dashboard with app/database status and recent records |
| `GET` | `/health` | JSON health status; HTTP 503 when PostgreSQL is unavailable |
| `GET` | `/api/records` | JSON list of up to 100 newest records |
| `POST` | `/api/records` | Add a record using a JSON `name` field |
| `POST` | `/records` | Add a record from the dashboard form |

Names are trimmed, required, and limited to 120 characters. SQL values use
psycopg parameters, not string interpolation. Database errors are logged by the
app and returned as a clear unavailable status without exposing connection
details.

## Testing guide

Commands below use PowerShell where noted. JSON data and IDs in the example
outputs are illustrative; generated IDs and timestamps vary.

### 1. Check Python and run the Python application

```powershell
python --version
python -m pip install -r requirements.txt
python app.py
```

Expected: Python reports its version, pip finishes successfully, and Flask
prints that it is serving on port 5000. The local PostgreSQL service must be
running with the environment variables configured, or the dashboard will show
the database as unavailable.

### 2. Test the Flask homepage

In a second terminal:

```powershell
(Invoke-WebRequest http://127.0.0.1:5000/).StatusCode
```

Expected: `200`; the HTML contains the “Container Dashboard” title and status
cards.

### 3. Test the health endpoint

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Expected when PostgreSQL is reachable:

```text
status       application database
------       ----------- --------
ok           healthy     connected
```

When the database is unavailable, the endpoint responds with HTTP 503 and JSON
showing `"status": "degraded"` and `"database": "unavailable"`.

### 4. Check PostgreSQL connectivity and seed records

With Compose running:

```powershell
docker compose exec db psql -U projectuser -d projectdb -c "SELECT id, name FROM records ORDER BY id;"
```

Expected: a query result containing the two sample records from `init.sql`.
If you changed the configured database/user in `.env`, use those values in the
command. This command also confirms that the app's database schema is available.

### 5. Insert a record through the API

```powershell
$body = @{ name = "Test record" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:5000/api/records -Method Post -ContentType "application/json" -Body $body
```

Expected: a JSON `record` with a generated integer `id`, `"name": "Test record"`,
and a `created_at` timestamp. The HTTP status is 201.

### 6. Retrieve records

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/records
```

Expected: a `records` array containing the sample records and the newly added
record. Invalid or missing names return HTTP 400; database failures return 503.

### 7. Build the Docker image

```powershell
docker compose build
```

Expected: both build stages complete and the Compose app image is created. The
final stage should not contain compiler/build packages or pip's download cache.

### 8. Start Docker Compose

```powershell
docker compose up -d
```

Expected: the app and database containers start; the app waits for the database
health check.

### 9. Check container status

```powershell
docker ps
docker compose ps
```

Expected: database and app services are listed. After their health checks pass,
the Compose status should show `healthy`.

### 10. Check container health

```powershell
$appId = docker compose ps -q app
docker inspect --format='{{.State.Health.Status}}' $appId
$dbId = docker compose ps -q db
docker inspect --format='{{.State.Health.Status}}' $dbId
```

Expected: `healthy` for each service. The app check calls `/health`, which also
checks the database.

### 11. Verify persistent volume behavior

Add a record using test 5, then run:

```powershell
docker compose down
docker compose up -d
Invoke-RestMethod http://127.0.0.1:5000/api/records
```

Expected: the record remains in the API result. The named database volume
survives `docker compose down`.

### 12. Verify non-root execution

```powershell
docker compose exec app id
```

Expected: UID and GID are `10001` (the named user/group may also be printed).
The app must not report UID 0.

### 13. Inspect the image and measure its size

```powershell
docker image ls rab-tech-task03
$bytes = [int64](docker image inspect rab-tech-task03:latest --format '{{.Size}}')
"{0:N2} MB (decimal), {1:N2} MiB" -f ($bytes / 1000000), ($bytes / 1048576)
if ($bytes -lt 150000000) { "PASS: below 150 MB" } else { "FAIL: at least 150 MB" }
```

Expected: the inspection prints a byte count and a measurement. Only report
the target as met if the final line is `PASS`. Docker's `.Size` is the summed
uncompressed image-layer size; it is not the compressed download size.

### Useful Docker commands

| Command | What it does |
| --- | --- |
| `docker --version` | Shows the Docker Engine CLI version |
| `docker compose version` | Shows the Compose plugin version |
| `docker compose build` | Builds the app image |
| `docker compose up -d` | Starts services in the background |
| `docker ps` | Lists running containers |
| `docker compose ps` | Shows this project's containers and health |
| `docker image ls` | Lists local images and their displayed sizes |
| `docker compose logs -f` | Follows service logs; press `Ctrl+C` to stop following |
| `docker compose down` | Stops/removes containers and network; keeps database volume |
| `docker compose down -v` | Also deletes the database volume and its stored data |
| `docker inspect <container>` | Shows detailed container configuration and health state |

## Image optimization and measurement

The Dockerfile has two stages. The **builder** installs the pinned Python
dependencies into a temporary prefix. The **runtime** starts from a clean,
lightweight `python:3.12-slim-bookworm` base and copies only those installed
dependencies and the files required to serve the app. It does not copy source
control, local environments, tests, pip cache, or compiler tools. The runtime
process uses an unprivileged user.

The slim Python image provides the required interpreter and standard runtime
libraries without the larger collection of tools included in a general-purpose
OS image. The final image is measured after building with `docker image inspect`
as shown in test 13. If it is 150 MB or larger:

1. Check the installed dependencies and remove unused packages from
   `requirements.txt`.
2. Check `docker history rab-tech-task03:latest` for large layers.
3. Keep build-only tools in the builder stage and avoid copying caches or
   development files into the runtime stage.
4. Rebuild and remeasure; do not estimate or substitute the base-image size for
   the final image size.

**Measured result for this submission:** Not measured yet. Docker is unavailable
in the authoring workspace. Run test 13 in a Docker-enabled environment and
record the actual output here before making an image-size claim.

## Use GitHub Codespaces for Docker

Docker is not installed in the Windows authoring environment. You can run the
Docker commands in a Linux GitHub Codespace:

1. Push this project to a GitHub repository using the commands below.
2. On GitHub, open the repository and select **Code → Codespaces → Create
   codespace on main**. Wait for the browser-based VS Code editor to finish
   starting.
3. Open the integrated terminal. Run `docker --version` and `docker compose
   version` to check availability. If Docker is unavailable, use a supported
   Linux VM/cloud development environment that provides Docker Engine and the
   Compose plugin.
4. Create/edit `.env` in the Codespace terminal (copy `.env.example` if there is
   no `.env`), and set a private password. Do not commit the file.
5. Run the Compose build/start commands. In VS Code, open the **Ports** tab and
   open forwarded port 5000 to view the dashboard.
6. To connect from desktop VS Code, install the GitHub Codespaces extension,
   sign into GitHub, then run **Codespaces: Connect to Codespace** from the
   Command Palette.

Codespaces and other cloud environments may incur charges and have their own
resource limits; stop/delete the Codespace when finished.

## GitHub setup and submission

Create an empty GitHub repository first. In the project directory, run the
following in PowerShell, replacing the URL with your repository's HTTPS URL:

```powershell
git init
git add .
git status --short
git commit -m "Build Flask PostgreSQL Docker project"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPOSITORY>.git
git push -u origin main
```

Review `git status --short` before committing and ensure `.env` is not listed.
Use `git remote -v` to confirm the repository URL.

### Academic submission checklist

- [ ] GitHub repository link is accessible to the instructor.
- [ ] Complete source code and required project structure are present.
- [ ] Dockerfile demonstrates the builder/runtime stages and non-root user.
- [ ] Compose file includes both services, health checks, network, and volume.
- [ ] PostgreSQL schema and sample data are included.
- [ ] Successful Docker build logs are captured.
- [ ] `docker compose ps` or `docker inspect` shows healthy containers.
- [ ] `docker compose exec app id` verifies non-root execution.
- [ ] Image size proof is captured from `docker image inspect`.
- [ ] Application dashboard and record insertion/retrieval screenshots are captured.

### Screenshots checklist

- [ ] Dashboard showing Flask and PostgreSQL statuses.
- [ ] Dashboard showing sample and newly added records.
- [ ] Compose services in healthy state.
- [ ] Non-root UID/GID output.
- [ ] Image-size measurement and pass/fail output.
