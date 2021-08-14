FROM python:3.9-slim as base

WORKDIR /tmp/deps

RUN pip install pipenv
COPY Pipfile* ./
RUN PIP_USER=1 PIP_IGNORE_INSTALLED=1 \
  pipenv install --system --deploy --ignore-pipfile

WORKDIR /app
RUN rm -rf /tmp/deps

COPY src/* ./

ENTRYPOINT [ "python", "/app/main.py" ]
