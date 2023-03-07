import time

import redis

redis_host = "eya-prod.enujjj.ng.0001.cnw1.cache.amazonaws.com.cn"
redis_port = 6379
redis_db = 8


# key : 键, value: 值, expired: 过期时间
def add(key: str, value: str, expired: int):
    add_result = False
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    if expired != -1:
        add_result = redis_conn.setex(key, expired, value)
    else:
        add_result = redis_conn.set(key, value)
    redis_conn.close()
    return add_result


def exists(key: str):
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    exist = redis_conn.exists(key)
    redis_conn.close()
    return exist


def delete_key(key: str):
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    delete_result = redis_conn.delete(key)
    redis_conn.close()
    return delete_result
