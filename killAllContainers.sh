#stop all running containers
docker stop $(docker ps -a -q)
#kill stopped containers
docker rm $(docker ps -a -q)
