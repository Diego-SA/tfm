import os

import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

# Si redis esta instalado en nuestro propio entorno haria que cambiar la direccion
#redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379/')
redis_url = os.getenv('REDISTOGO_URL', 'redis://172.17.0.2:6379/')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        print('Ejecutando proceso background')
        worker = Worker(map(Queue, listen))
        worker.work()