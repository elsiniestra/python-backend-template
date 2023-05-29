FROM python:3.11-slim-bullseye@sha256:1cd45c5dad845af18d71745c017325725dc979571c1bbe625b67e6051533716c as python-base

RUN apt -y update && \
    apt install -y --no-install-recommends build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

FROM python-base as container-base

ENV TINI_VERSION v0.19.0

ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

ARG USER_NAME=app
ENV USER_NAME=${USER_NAME}
ARG USER_UID=1000
ARG PASSWD=password

RUN useradd -m -s /bin/bash -u $USER_UID $USER_NAME && \
    gpasswd -a $USER_NAME sudo && \
    echo "${USER_NAME}:${PASSWD}" | chpasswd && \
    echo "${USER_NAME} ALL=(ALL) ALL" >> /etc/sudoers

RUN mkdir /app
RUN chown -R ${USER_NAME}:${USER_NAME} /app
WORKDIR /app

COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock
COPY ./deployment/entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh
USER $USER_NAME


FROM container-base as app-base

ENV POETRY_VERSION 1.4.2
ENV PATH $PATH:/home/${USER_NAME}/.local/bin
RUN export PYTHONUNBUFFERED=1 && \
    curl -sSL https://install.python-poetry.org | python - && \
    poetry config virtualenvs.in-project true && \
    poetry check && poetry export --no-interaction -o requirements.txt --without-hashes  && \
    pip install -U pip && \
    pip --no-cache-dir install -r requirements.txt

ENV PATH=/app/.venv/bin:$PATH

COPY ./src ./src
COPY alembic.ini .
COPY ./migrations ./migrations
COPY ./configs ./configs
COPY ./graphdata ./graphdata

EXPOSE 8000

CMD ["./entrypoint.sh"]
