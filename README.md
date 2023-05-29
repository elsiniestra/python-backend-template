# Python Backend Template

# Features
- ✨REST API project inspired by Clean Architecture
- ✨JWT authentication and role-based access using graph-based IAM
- ✨S3 integration
- ✨Fully covered by flake8, mypy, blake, and isort
- ✨Dev environment using docker-compose and traefik (including SSL certificates generation) 
- ✨CI workflow on Github Actions including linting and image building

# Things to improve
- Cookiecutter implementation
- Tests examples
- Refactor redisgraph module (forked from https://github.com/RedisGraph/redisgraph-bulk-loader)
- Move from FastAPI DI to `python-dependency-injector` to get rid of `providers` entity
- Add `.editorconfig` rules for non-IJ editors 
- Add deviceID field in JWT body
- Refactor current S3 integration to the asynchronous one
- Fix mypy errors related to SA2.0 and Pydantic 

# How to run

### Install the dependencies

1. Install `poetry`
2. Run this command in the command line: `poetry install`

### Setup

For a basic startup without the ability to load a photo, 2 environment variables must be filled in the `.env' file in the root of the project:
- `ADMIN_PASSWORD`: the admin password
- `DB_URL`: URL for the database connection (PostgreSQL)

An example can be seen in the file `.env.example`

### Launch

Use the `Makefile` commands to run the backend locally or in the docker.

### Documentation

OpenAPI documentation can be opened at `0.0.0.0:8000/docs`.
