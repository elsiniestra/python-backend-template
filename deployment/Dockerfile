FROM python:3.11-slim-bullseye@sha256:1cd45c5dad845af18d71745c017325725dc979571c1bbe625b67e6051533716c as python-base

ENV PYTHONUNBUFFERED=1

RUN apt -y update && \
    apt install -y --no-install-recommends build-essential curl wkhtmltopdf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


FROM python-base as poetry-export

ENV PATH=$PATH:/root/.local/bin POETRY_VERSION=1.4.2
RUN curl -sSL https://install.python-poetry.org | python -
COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock
RUN poetry export --no-interaction -o /requirements.txt --without-hashes --only main


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

COPY --from=poetry-export /requirements.txt /app/requirements.txt
RUN pip --no-cache-dir install -r /app/requirements.txt

COPY ./deployment/entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    chown -R ${USER_NAME}:${USER_NAME} /app && \
    chmod -R 755 /app

USER $USER_NAME


FROM container-base as app-base

COPY --chown=$USER_NAME:USER_NAME ./src ./src
COPY --chown=$USER_NAME:USER_NAME alembic.ini .
COPY --chown=$USER_NAME:USER_NAME ./migrations ./migrations
COPY --chown=$USER_NAME:USER_NAME ./configs ./configs
COPY --chown=$USER_NAME:USER_NAME ./graphdata ./graphdata
COPY --chown=$USER_NAME:USER_NAME ./assets ./assets

EXPOSE 8000

CMD ["./entrypoint.sh"]
