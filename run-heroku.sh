#LA PRIMERA VEZ HAY QUE LOGUEARSE TANTO EN HEROKU COMO EL REGISTRO
#heroku login
#heroku container:login
docker tag tfm-diego-heroku:latest registry.heroku.com/tfm-diego/web
docker push registry.heroku.com/tfm-diego/web

docker tag tfm-diego-worker:latest registry.heroku.com/tfm-diego/worker
docker push registry.heroku.com/tfm-diego/worker

heroku container:release web worker -a tfm-diego
#heroku container:release web -a tfm-diego

echo "Ahora ve a https://tfm-diego.herokuapp.com/main/"