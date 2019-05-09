#!/usr/bin/env bash
echo "login a docker"
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
export REPO=tfm-diego-heroku
docker pull paberlo/alpine-scikit-django-jdk8:latest

echo "login a heroku"
#prueba 1:https://stackoverflow.com/questions/39554697/script-heroku-login-in-a-ci-environment
#prueba 2: echo "$HEROKU_PASSWORD" | docker login -u "$HEROKU_USERNAME" --password-stdin registry.heroku.com
docker login --username=_ --password=$HEROKU_API_KEY registry.heroku.com
export TAG=web
docker build -f $TRAVIS_BUILD_DIR/Dockerfile-heroku-web -t $REPO/$TAG .
docker tag $REPO/$TAG:latest registry.heroku.com/tfm-diego/$TAG
docker push registry.heroku.com/tfm-diego/$TAG

export TAG=worker
docker build -f $TRAVIS_BUILD_DIR/Dockerfile-worker -t $REPO/$TAG .
docker tag $REPO/$TAG:latest registry.heroku.com/tfm-diego/$TAG
docker push registry.heroku.com/tfm-diego/$TAG
heroku container:release web --app tfm-diego