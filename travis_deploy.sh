#!/usr/bin/env bash
echo "$HEROKU_API_KEY" | docker login -u "$HEROKU_USERNAME" --password-stdin registry.heroku.com
docker login -u $DOCKER_USER -p $DOCKER_PASS
export REPO=tfm-diego-heroku
docker pull paberlo/alpine-scikit-django-jdk8:latest

export TAG=web
docker build -f $TRAVIS_BUILD_DIR/Dockerfile-heroku-web -t $REPO/$TAG .
docker tag $REPO/$TAG:latest registry.heroku.com/tfm-diego/$TAG
docker push registry.heroku.com/tfm-diego/$TAG

export TAG=worker
docker build -f $TRAVIS_BUILD_DIR/Dockerfile-worker -t $REPO/$TAG .
docker tag $REPO/$TAG:latest registry.heroku.com/tfm-diego/$TAG
docker push registry.heroku.com/tfm-diego/$TAG
heroku container:release web --app tfm-diego