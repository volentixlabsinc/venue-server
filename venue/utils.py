
import rncryptor
import base64
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


#------------------------------------
# Encryption and decryption functions
#------------------------------------

def encrypt_data(data, password):
    cryptor = rncryptor.RNCryptor()
    encrypted_data = cryptor.encrypt(data, password)
    encoded_data = base64.b64encode(encrypted_data)
    return encoded_data.decode('utf-8')
    
def decrypt_data(data, password):
    cryptor = rncryptor.RNCryptor()
    decoded_data = base64.b64decode(data)
    decrypted_data = cryptor.decrypt(decoded_data, password)
    return decrypted_data