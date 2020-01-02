FROM python:3.8-slim AS base

COPY . /app

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIPENV_VENV_IN_PROJECT 1
RUN pip install pipenv && \
    pipenv install --deploy -d

FROM base AS test
WORKDIR /app
CMD pipenv run pytest
