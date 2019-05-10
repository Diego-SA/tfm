#como el código hay que meterlo en los 2, se construyen ambos con el script
docker build -f Dockerfile-web -t tfm-diego-web .
docker build -f Dockerfile-worker -t tfm-diego-worker .
