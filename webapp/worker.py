import os

import redis
from rq import Worker, Queue, Connection
from urllib.parse import urlparse

listen = ['high', 'default', 'low']

# Si redis esta instalado en nuestro propio entorno haria que cambiar la direccion

#redis_url = os.getenv('REDISTOGO_URL', 'redis://172.17.0.2:6379/')

# en HEROKU coge la dirección de una variable propia de entorno
#redis_url = redis.from_url(os.environ.get("REDIS_URL"))
if os.name == 'nt':# Windows
    redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379/')
    worker_conn = redis.from_url(redis_url)

else: worker_conn = redis.from_url('redis://redis:6379/') #linux (docker container)


if __name__ == '__main__':


    print("worker: antes de with Connection")
    with Connection(worker_conn):
        print('Ejecutando proceso background')
        worker = Worker(map(Queue, listen))
        worker.work()
        print(worker.log)
