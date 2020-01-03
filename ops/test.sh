#!/usr/bin/env bash

set -ex


REPOSITORY=eyeem-overpass
IMAGE_TAG=testing-latest


docker build --no-cache --target test -f Dockerfile -t $REPOSITORY:$IMAGE_TAG .

docker run --rm $REPOSITORY:$IMAGE_TAG

docker rmi $REPOSITORY:$IMAGE_TAG
