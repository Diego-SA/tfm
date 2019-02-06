#!/usr/bin/env bash
docker stack deploy -c docker-compose.yml tfm
echo "al terminar no olvides ejecutar 'docker stack rm tfm'"