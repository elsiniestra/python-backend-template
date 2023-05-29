PROJECT_NAME={python-backend-template}# TODO: cookiecutter
DOCKER_COMPOSE_COMMAND=docker compose
ENV_FILE=./.env

# Development
.PHONY: run-local
run-local:
	uvicorn --factory --reload src.main:api --host 0.0.0.0 --port 8000

# Docker (local)
LOCAL_COMPOSE=${DOCKER_COMPOSE_COMMAND} -p ${PROJECT_NAME} -f deployment/docker-compose.local.yml --env-file ${ENV_FILE}

.PHONY: compose-up-local
compose-up-local:
	${LOCAL_COMPOSE} up -d --build --remove-orphans

.PHONY: compose-up-no-app-local
compose-up-no-app-local:
	${LOCAL_COMPOSE} up -d postgres traefik redis-stack

.PHONY: compose-down-local
compose-down-local:
	${LOCAL_COMPOSE} down

.PHONY: compose-restart-local
compose-restart-local:
	compose-down-local compose-up-local


# Docker (development)
DEV_COMPOSE=${DOCKER_COMPOSE_COMMAND} -p ${PROJECT_NAME} -f deployment/docker-compose.dev.yml --env-file ${ENV_FILE}

.PHONY: compose-up-dev
compose-up-dev:
	APP_VERSION=${APP_VERSION} ${DEV_COMPOSE} up -d --build --remove-orphans

.PHONY: compose-up-no-app-dev
compose-up-no-app-dev:
	${DEV_COMPOSE} up -d postgres redis-stack

.PHONY: compose-down-dev
compose-down-dev:
	${DEV_COMPOSE} down


.PHONY: compose-restart-dev
compose-restart-dev:
	compose-down-local compose-up-dev


# Docker (production)
PROD_COMPOSE=${DOCKER_COMPOSE_COMMAND} -p ${PROJECT_NAME} -f deployment/docker-compose.prod.yml --env-file ${ENV_FILE}

.PHONY: compose-up-prod
compose-up-prod:
	${PROD_COMPOSE} up -d --build  --remove-orphans

.PHONY: compose-down-prod
compose-down-prod:
	${PROD_COMPOSE} down


# Helpers
.PHONY: add-superadmin-user
add-superadmin-user:
	python src/cli.py --username admin --first-name Admin --last-name Admin --email test@email.com  --password password --role superadmin

.PHONY: lint
lint:
	black . --diff
	isort . --check-only --diff
	flake8 .
	mypy .

.PHONY: format
format:
	black .
	isort .

.PHONY: prepare
prepare:
	git config core.hooksPath .gitconfig/hooks

.PHONY: create-ssl-certificate
create-ssl-certificate:
	/bin/sh deployment/create-ssl-certificate.sh