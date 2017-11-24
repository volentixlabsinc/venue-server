import json
import redis

class RedisTemp(object):
    
    def __init__(self, namespace):
        self.rconn = redis.StrictRedis(db=2)
        if len(namespace.split()) > 1:
            raise Exception('Namespace should not contain spaces')
        else:
            self.namespace = namespace
            
    def generate_key(self, key):
        return 'temp__' + key + '__' + self.namespace
    
    def store(self, key, value):
        key = self.generate_key(key)
        json_value = json.dumps(value)
        return self.rconn.set(key, json_value)
        
    def retrieve(self, key):
        key = self.generate_key(key)
        value = self.rconn.get(key)
        if value:
            return json.loads(value.decode('utf-8'))
        else:
            return value
        
    def remove(self, key):
        key = self.generate_key(key)
        return self.rconn.delete(key)