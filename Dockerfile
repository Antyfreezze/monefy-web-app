# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster
WORKDIR /app
COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

ENV DROPBOX_TOKEN=YOUR_DROPBOX_TOKEN
ENV DROPBOX_PATH=YOUR_DROPBOX_PATH
ENV DROPBOX_APP_SECRET=YOUR_DROPBOX_APP_SECRET
COPY . .
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
# available to provide options as host, port, autoreload, debug, access logs
CMD ["python3", "run.py"]
