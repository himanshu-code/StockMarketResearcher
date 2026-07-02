import json
import logging
from functools import wraps
import redis
from config.settings import get_settings

logger=logging.getLogger(__name__)
settings=get_settings()

_redis_client=None

def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        _redis_client=redis.Redis.from_url(settings.redis_url,decode_responses=True)
        _redis_client.ping()
        logger.info("[Redis] Connected to cloud cache")
        return _redis_client
    except Exception as e:
        logger.error("[Redis] Connect failed: %s",e)
        _redis_client=None
        return None

def redis_cache(ttl_seconds:int=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):            
            client=get_redis_client()
            if not client:
                return func(*args,**kwargs)
            key=f"yfinance:{func.__name__}:{':'.join(str(a).strip().upper() for a in args)}"
            try:
                cached=client.get(key)
                if cached:
                    logger.info("[Redis] Cache hit for %s",key)
                    data=json.loads(cached)
                    from inspect import signature
                    return_type =signature(func).return_annotation
                    if return_type and hasattr(return_type,"model_validate"):
                        return return_type.model_validate(data)
                    return data
            except Exception as e:
                logger.warning("[Redis] Cache read failed for %s: %s",key,e)
            result=func(*args,**kwargs)
            try:
                serialized=result.model_dump_json() if hasattr(result,"model_dump_json") else json.dumps(result)
                client.setex(key,ttl_seconds,serialized)
                logger.info("[Redis] Stored cache for %s",key)
            except Exception as e:
                logger.warning("[Redis] Cache write failed for %s: %s",key,e)
            return result
        return wrapper
    return decorator
    

            
