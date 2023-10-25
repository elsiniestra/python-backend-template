# Python Backend Template

# Features
- ✨REST API project inspired by Clean Architecture
- ✨The project based on FastAPI, Pydantic 2.0, Postgres/SA 2.0, RedisStack, Celery 
- ✨Fully asynchronous application
- ✨JWT authentication and role-based access using graph-based IAM
- ✨SSO authentication (Microsoft, Google, GitHub)
- ✨S3 and Sentry integrations
- ✨Fully covered by flake8, mypy, blake, and isort
- ✨Dev environment using docker-compose and traefik (including SSL certificates generation) 
- ✨CI workflow on Github Actions including linting and image building

# Things to improve
- Cookiecutter implementation
- Refactor redisgraph module (forked from https://github.com/RedisGraph/redisgraph-bulk-loader)
- Move from FastAPI DI to `python-dependency-injector` to get rid of `providers` entity
- Add `.editorconfig` rules for non-IJ editors 
- Add deviceID field in JWT body
- Fix mypy errors related to SA2.0 and Pydantic 

# How to run

### Install the dependencies

1. Install `poetry`
2. Run this command in the command line: `poetry install`

### Setup

For the initial setup, environment variables must be filled in the `.env' file in the root of the project:

| Variable                  | Type     | Description                                         | Mandatory?            |
|---------------------------|----------|-----------------------------------------------------|-----------------------|
| `ADMIN_USERNAME`          | `string` | Username used for the admin user                    | yes                   |
| `ADMIN_PASSWORD`          | `string` | Password used for the admin user                    | yes                   |
| `POSTGRES_USER`           | `string` | Postgres User                                       | yes                   |
| `POSTGRES_PASSWORD`       | `string` | Postgres Password                                   | yes                   |
| `POSTGRES_HOST`           | `string` | Postgres Host                                       | yes                   |
| `POSTGRES_PORT`           | `int`    | Postgres Port                                       | yes                   |
| `POSTGRES_DB`             | `string` | Postgres DB name                                    | yes                   |
| `REDIS_HOST`              | `string` | Redis Host                                          | yes                   |
| `REDIS_PORT`              | `int`    | Redis Port                                          | yes                   |
| `IAM_GRAPH_NAME`          | `string` | Redis Graph used for IAM                            | yes                   |
| `GRAPH_DATA_PATH`         | `string` | Path to the graph migrations (nodes, relationships) | yes                   |
| `ALLOW_ORIGINS`           | `string` | CORS Allow Origins                                  | yes                   |
| `ALLOW_METHODS`           | `string` | CORS Allow Methods                                  | yes                   |
| `ALLOW_HEADERS`           | `string` | CORS Allow Headers                                  | yes                   |
| `ALLOW_CREDENTIALS`       | `bool`   | CORS Allow Credentials                              | yes                   |
| `PRODUCTION`              | `bool`   | Production mode                                     | no (default: `false`) |
| `TESTING`                 | `bool`   | Testing mode                                        | no (default: `false`) |
| `SECRET_KEY`              | `string` | JWT secret key                                      | yes                   |
| `S3_BUCKET`               | `string` | S3 Bucket                                           | no                    |
| `S3_ENDPOINT`             | `string` | S3 Endpoint                                         | no                    |
| `S3_ACCESS_KEY`           | `string` | S3 Access Key                                       | no                    |
| `S3_SECRET_KEY`           | `string` | S3 Secret Key                                       | no                    |
| `S3_REGION`               | `string` | S3 Region                                           | no                    |
| `S3_REPLACE_DOMAIN`       | `string` | S3 custom domain                                    | no                    |
| `APP_NAME`                | `string` | App name used for Traefik                           | no                    |
| `APP_HOST`                | `string` | App host used for Traefik                           | no                    |
| `SENTRY_DSN`              | `string` | Sentry DSN                                          | no                    |
| `TRACES_SAMPLE_RATE`      | `int`    | Sentry Traces Sample Rate                           | no (default: `1.0`)   |
| `GOOGLE_CLIENT_ID`        | `string` | Google Client ID (SSO)                              | no                    |
| `GOOGLE_CLIENT_SECRET`    | `string` | Google Client Secret (SSO)                          | no                    |
| `GOOGLE_REDIRECT_URI`     | `string` | Google Redirect URI (SSO)                           | no                    |
| `MICROSOFT_CLIENT_ID`     | `string` | Microsoft Client ID (SSO)                           | no                    |
| `MICROSOFT_CLIENT_SECRET` | `string` | Microsoft Client Secret (SSO)                       | no                    |
| `MICROSOFT_REDIRECT_URI`  | `string` | Microsoft Redirect URI (SSO)                        | no                    |
| `MICROSOFT_TENANT`        | `string` | Microsoft Tenant (SSO)                              | no                    |
| `GITHUB_CLIENT_ID`        | `string` | Github Client ID (SSO)                              | no                    |
| `GITHUB_REDIRECT_URI`     | `string` | Github Redirect URI (SSO)                           | no                    |


An example can be seen in the file `.env.example`

### Launch

Use the `Makefile` commands to run the backend locally or in the docker.

### Documentation

OpenAPI documentation can be opened at `0.0.0.0:8000/docs`.
