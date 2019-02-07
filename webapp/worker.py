import os

import redis
from rq import Worker, Queue, Connection

print("iniciando en GLOBAL el  worker")
if os.name == 'nt':  # Windows
    worker_conn = redis.from_url(os.getenv('REDISTOGO_URL', 'redis://localhost:6379/'))
elif os.getenv('LOCAL') == 'true':  # linux (local docker compose)
    worker_conn = redis.from_url('redis://redis:6379/')
else:  # heroku
    worker_conn = redis.from_url(os.environ.get("REDIS_URL"))


listen = ['high', 'default', 'low']


if __name__ == '__main__':
    print("iniciando en main el worker")
    with Connection(worker_conn):
        print('Ejecutando proceso background')
        worker = Worker(map(Queue, listen))
        worker.work()
        print(worker.log)
