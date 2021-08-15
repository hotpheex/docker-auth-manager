#!/bin/bash
CREDS="${1}"
touch "${HOME}/.docker/config.json"
docker build . -t docker-auth-manager
docker run --rm -v "${HOME}/.docker/config.json:/.docker/config" \
    -e DOCKER_CREDS="${CREDS}" \
    -e REFRESH_THRESHOLD=50 \
    -e SCHEDULE_MINS=1 \
        docker-auth-manager
