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
    elif "maturita" in loadedData:
        loadedData["maturita"] = maturita_load(loadedData["maturita"])
    elif "users" in loadedData:
        loadedData["users"] = user_load(loadedData["users"])
    elif "evaluators" in loadedData:
        loadedData["evaluators"] = user_load(loadedData["evaluators"])

    return loadedData

def user_load(data):
    if not "createdAt" in data and not "updatedAt" in data:
        for d in data:
            d["createdAt"] = datetime.fromisoformat(d["createdAt"])

            if "updatedAt" in d:
                d["updatedAt"] = datetime.fromisoformat(d["updatedAt"])
    else:
        data["createdAt"] = datetime.fromisoformat(data["createdAt"])

        if "updatedAt" in data:
            data["updatedAt"] = datetime.fromisoformat(data["updatedAt"])

    return data

def user_save(data):
    if not "createdAt" in data and not "updatedAt" in data:
        for d in data:
            d["createdAt"] = d["createdAt"].isoformat()

            if "updatedAt" in d:
                d["updatedAt"] = d["updatedAt"].isoformat()
    else:
        data["createdAt"] = data["createdAt"].isoformat()
        
        if "updatedAt" in data:
            data["updatedAt"] = data["updatedAt"].isoformat()

    return data

def maturita_save(data):
    if not "startDate" in data and not "endDate" in data:
        for d in data:
            d["startDate"] = d["startDate"].isoformat()
            d["endDate"] = d["endDate"].isoformat()
    else:
        data["startDate"] = data["startDate"].isoformat()
        data["endDate"] = data["endDate"].isoformat()

    return data

def maturita_load(data):
    if not "startDate" in data and not "endDate" in data:
        for d in data:
            d["startDate"] = datetime.fromisoformat(d["startDate"])
            d["endDate"] = datetime.fromisoformat(d["endDate"])
    else:
        data["startDate"] = datetime.fromisoformat(data["startDate"])
        data["endDate"] = datetime.fromisoformat(data["endDate"])

    return data

def table_load(data):
    for d in data:
        if "objector" in d and d["objector"]:
            d["objector"] = user_load(d["objector"])

        d["guarantor"] = user_load(d["guarantor"])
        d["user"] = user_load(d["user"])
    
    return data


def table_save(data):
    for d in data:
        if "objector" in d and d["objector"]:
            d["objector"] = user_save(d["objector"])
            
        d["guarantor"] = user_save(d["guarantor"])
        d["user"] = user_save(d["user"])
    
    return data