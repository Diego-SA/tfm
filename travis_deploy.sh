#!/usr/bin/env bash
echo "login a docker"
echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
export REPO=tfm-diego-heroku
docker pull paberlo/alpine-scikit-django-jdk8:latest

echo "login a heroku. ignorar el warning porque lo que se usa es el HEROKU API KEY, encriptado."
#crear en Settings de la app en la web  deheroku la variable HEROKU_API_KEY con la salida del comando en local 'heroku auth:token'
docker login --username=_ --password=$HEROKU_API_KEY registry.heroku.com
export TAG=web
docker build -f $TRAVIS_BUILD_DIR/Dockerfile-heroku-web -t $REPO/$TAG .
docker tag $REPO/$TAG:latest registry.heroku.com/tfm-diego/$TAG
docker push registry.heroku.com/tfm-diego/$TAG

export TAG=worker
docker build -f $TRAVIS_BUILD_DIR/Dockerfile-worker -t $REPO/$TAG .
docker tag $REPO/$TAG:latest registry.heroku.com/tfm-diego/$TAG
docker push registry.heroku.com/tfm-diego/$TAG
heroku container:release web worker --app tfm-diego