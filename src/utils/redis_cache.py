from app import redis_client
import json
import redis
from datetime import datetime

def set_cache(cache_key, data):
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        return None
    
    if "tasks" in data:
        data["tasks"] = table_save(data["tasks"])
    if "maturita" in data:
        data["maturita"] = maturita_save(data["maturita"])
    if "users" in data:
        data["users"] = user_save(data["users"])
    if "evaluators" in data:
        data["evaluators"] = user_save(data["evaluators"])
    
    redis_client.setex(cache_key, 60, json.dumps(data))

def get_cache(cache_key):
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        return None
    
    data = redis_client.get(cache_key)

    if not data:
        return None
    
    loadedData = json.loads(data)
    
    if "tasks" in loadedData:
        loadedData["tasks"] = table_load(loadedData["tasks"])
    if "maturita" in loadedData:
        loadedData["maturita"] = maturita_load(loadedData["maturita"])
    if "users" in loadedData:
        loadedData["users"] = user_load(loadedData["users"])
    if "evaluators" in loadedData:
        loadedData["evaluators"] = user_load(loadedData["evaluators"])

    return loadedData

def user_load(data):
    for d in data:
        d["createdAt"] = datetime.fromisoformat(d["createdAt"])
        d["updatedAt"] = datetime.fromisoformat(d["updatedAt"])

    return data

def user_save(data):
    for d in data:
        d["createdAt"] = d["createdAt"].isoformat()
        d["updatedAt"] = d["updatedAt"].isoformat()

    return data

def maturita_save(data):
    for d in data:
        d["startDate"] = d["startDate"].isoformat()
        d["endDate"] = d["endDate"].isoformat()

    return data

def maturita_load(data):
    for d in data:
        d["startDate"] = datetime.fromisoformat(d["startDate"])
        d["endDate"] = datetime.fromisoformat(d["endData"])

    return data

def table_load(data):
    for d in data:
        d["guarantor"] = user_load(d["guarantor"])
        d["objector"] = user_load(d["objector"])
        d["user"] = user_load(d["user"])
    
    return data


def table_save(data):
    for d in data:
        d["guarantor"] = user_save(d["guarantor"])
        d["objector"] = user_save(d["objector"])
        d["user"] = user_save(d["user"])
    
    return data