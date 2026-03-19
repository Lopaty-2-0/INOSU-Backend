from app import redis_client
import json
import redis

def set_cache(cache_key, data):
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        return None
    
    redis_client.setex(cache_key, 60, json.dumps(data))

def get_cache(cache_key):
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        return None
    
    data = redis_client.get(cache_key)

    if not data:
        return None
    
    return json.loads(data)
    