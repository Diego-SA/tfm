
from prueba_redis.counters import count_words_at_url
from redis import Redis
from rq import Queue



if __name__ == '__main__':

    q = Queue(connection=Redis())
    # will return None when the job is not yet finished,
    # or a non-None value when the job has finished
    # (assuming the job has a return value in the first place, of course).
    result = q.enqueue(
        count_words_at_url, 'http://nvie.com')
    print(result)
