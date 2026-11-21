# Testing Report

This report distinguishes results supplied for this project from checks that
were not evidenced. “Not verified” does not mean a test failed.

| Test | Expected result | Result | Evidence / notes |
| --- | --- | --- | --- |
| Docker installation | Successful | Not separately verified | Docker image results were supplied, but no installation/version output was included. |
| Docker hello-world | Successful | Not verified | No hello-world run output was supplied. |
| Docker image build | Successful | Successful (supplied) | The `rab-tech-task03:latest` application image and its reported size were supplied. |
| Flask application | Running | Successful (supplied) | Project was reported as implemented and running successfully. |
| PostgreSQL connection | Connected | Successful (supplied) | Health result reports `database: connected`. |
| GET API | Successful | Successful (supplied) | `GET /api/records` was reported to return saved records. |
| POST API | Successful | Successful (supplied) | `POST /api/records` was reported to insert a record. |
| Health endpoint | Healthy | Successful (supplied) | Reported values: application `healthy`, database `connected`, status `ok`. |
| Non-root execution | UID 10001 | Successful (supplied) | Reported identity: `uid=10001(appuser) gid=10001(app)`. |
| Image size | 101 MB disk usage | Successful (supplied) | Reported for `rab-tech-task03:latest`. This is disk usage, not content size. |
| Image size target | Below 150 MB | Successful (supplied) | The reported 101 MB disk usage is below the target. |
| Docker Compose configuration validation | Configuration is valid | Successful (validated during this update) | `docker compose config --services` parsed the configuration and listed `db` and `app`. |
| Docker Compose services/status | Services start and report healthy | Not verified in this report | No Compose status output was supplied for this report. |
| Persistent-volume retention | Data remains after container recreation | Not verified | No persistence test result was supplied. |

## Supplied image measurements

- Image: `rab-tech-task03:latest`
- Disk usage: **101 MB**
- Content size: **24.8 MB**
- Target: **below 150 MB**

Disk usage and content size are different reported measurements; this report
does not substitute one for the other.

## Evidence to capture before submission

Capture genuine terminal/browser screenshots for the items in the root
[README screenshots checklist](../README.md#screenshots-checklist). Do not use
mocked or fabricated output.
