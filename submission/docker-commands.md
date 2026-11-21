# Docker Commands

Run commands from the project root. Before starting Compose, ensure a local
`.env` file exists and contains a private `POSTGRES_PASSWORD`. Never commit
`.env`.

| Command | What it does |
| --- | --- |
| `docker --version` | Displays the Docker CLI/Engine version. |
| `docker compose version` | Displays the Docker Compose plugin version. |
| `docker run hello-world` | Runs Docker's hello-world image to check basic image execution and registry access. |
| `docker compose config` | Renders and validates the Compose configuration with environment substitutions. |
| `docker compose build` | Builds the application image using the Dockerfile's production target. |
| `docker compose up -d` | Creates and starts the app and PostgreSQL services in the background. |
| `docker compose ps` | Shows this Compose project's services, state, and health. |
| `docker compose logs` | Displays logs from the Compose services. Add `-f` to follow logs. |
| `docker compose logs web` | Displays logs for a service named `web`; this project names the service `app`, so use `docker compose logs app` here. |
| `docker compose logs db` | Displays PostgreSQL service logs. |
| `docker image ls` | Lists local Docker images and their displayed disk usage. |
| `docker exec flask_app id` | Prints the running identity inside the app container; expected supplied identity is UID/GID 10001. |
| `docker volume ls` | Lists Docker volumes, including the project database volume if it exists. Listing a volume alone does not verify data persistence. |
| `docker compose down` | Stops and removes this project's containers and network while preserving named volumes and database data. |

The Compose service is called `app`, while its configured container name is
`flask_app`; use `docker compose logs app` for service logs and
`docker exec flask_app id` for the container identity.

## API checks

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/api/records
Invoke-RestMethod -Uri http://localhost:5000/api/records `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"name":"My Docker Record"}'
```

Do not use `docker compose down -v` during normal testing: `-v` removes named
volumes and can delete the persisted PostgreSQL data.
