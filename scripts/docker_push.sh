#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker push jan104/poescraper

if [[ -n $1 ]]; then
    docker push jan104/poescraper:$1
fi