import time

class Cache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl

    def set(self, key, value):
        self.cache[key] = (value, time.time())

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def clear(self):
        self.cache.clear() 