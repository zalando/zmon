
class ConnectionPool(object):
    def __init__(self,redis_conn,cass_conn):
        self.redis_conn = redis_conn
        self.cassandra_conn = cass_conn

    def disconnect(self):
        if self.redis_conn != None:
            self.redis_conn.connection_pool.disconnect()

# pipeline support is basic, commands are issued immediatly changing redis semantics and latency/performance
class WrapperPipeline(object):

    def __init__(self, wrapper, redis_write, cass_write, cass_read, redis_conn, cass_conn):
        self.wrapper = wrapper
        
        self.redis_conn = redis_conn
        self.cassandra_conn = cass_conn

        self.redis_p = redis_conn.pipeline()
        self.cass_p = self.cassandra_conn.pipeline()

        self.redis_write = redis_write
        self.cass_write = cass_write
        self.cass_read = cass_read

        self.cass_results = []
        self.redis_results = []

    def delete(self, key):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.delete(key))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.delete(key))
        else:
            self.cass_results.append(None)

    def smembers(self, key):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.smembers(key))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.smembers(key))
        else:
            self.cass_results.append(None)

    def sadd(self, key, value):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.sadd(key,value))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.sadd(key,value))
        else:
            self.cass_results.append(None)


    def srem(self, key, value):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.srem(key,value))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.srem(key,value))
        else:
            self.cass_results.append(None)

    def hgetall(self, key):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.hgetall(key))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.hgetall(key))
        else:
            self.cass_results.append(None)

    def hset(self, key, hash_key, value):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.hset(key, hash_key, value))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.hset(key, hash_key, value))
        else:
            self.cass_results.append(None)

    def hdel(self, key, hash_key):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.hdel(key, hash_key))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.hdel(key,hash_key))
        else:
            self.cass_results.append(None)

    def hkeys(self, key):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.hkeys(key))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.hkeys(key))
        else:
            self.cass_results.append(None)

    def incrby(self,key,value):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.incrby(key, value))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.incrby(key, value))
        else:
            self.cass_results.append(None)

    def set(self,key,value):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.set(key, value))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.set(key, value))
        else:
            self.cass_results.append(None)

    def get(self,key):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.get(key))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.get(key))
        else:
            self.cass_results.append(None)

    def lrange(self, key, a, b):
        if self.redis_write:
            self.redis_results.append(self.redis_conn.lrange(key, a, b))
        else:
            self.redis_results.append(None)

        if self.cass_write:
            self.cass_results.append(self.cassandra_conn.lrange(key, a, b))
        else:
            self.cass_results.append(None)


    def execute(self):
        if self.cass_read:
            return self.cass_results

        return self.redis_results



class RedisWrapper(object):

    def __init__(self, redis_conn, cass_conn, enable_redis_write=True, enable_cassandra_write=True, enable_cassandra_read=False):
        self.redis_conn = redis_conn
        self.cassandra_conn = cass_conn

        self.cass_read = enable_cassandra_read
        self.cass_write = enable_cassandra_write
        self.redis_write = enable_redis_write

        self.connection_pool = ConnectionPool(self.redis_conn, self.cassandra_conn)

    def getCassandraConnection(self):
        return self.cassandra_conn

    def getRedisConnection(self):
        return self.redis_conn

    def smembers(self, key):
        if self.cass_read:
            members = self.cassandra_conn.smembers(key)
        else:
            members = self.redis_conn.smembers(key)

        return members

    def rpush(self, key, *values):
        if self.redis_write:
            self.redis_conn.rpush(key, *values)

    def lpush(self, key, *values):
        if self.redis_write:
            self.redis_conn.lpush(key, *values)

    def ltrim(self,key, a, b):
        if self.redis_write:
            self.redis_conn.ltrim(key, a, b)

    def lrange(self,key,a,b):
        if self.cass_read:
            return self.cassandra_conn.lrange(key, a, b)
        else:
            return self.redis_conn.lrange(key, a, b)            

    def sadd(self, key, value):
        if self.redis_write:
            r = self.redis_conn.sadd(key, value)

        if self.cass_write:
            c = self.cassandra_conn.sadd(key, value)

        if self.redis_write:
            return r
        else:
            return c

    def srem(self, key, value):
        if self.redis_write:
            r = self.redis_conn.srem(key, value)

        if self.cass_write:
            c = self.cassandra_conn.srem(key, value)

        if self.redis_write:
            return r
        else:
            return c        

    def hgetall(self, key):
        if self.cass_read:
            return self.cassandra_conn.hgetall(key)
        else:
            return self.redis_conn.hgetall(key)

    def hset(self, key, hash_key, value):
        if self.redis_write:
            r = self.redis_conn.hset(key, hash_key, value)

        if self.cass_write:
            c = self.cassandra_conn.hset(key, hash_key, value)

        if self.redis_write:
            return r
        else:
            return c



    def hdel(self, key, hash_key):
        if self.redis_write:
            r = self.redis_conn.hdel(key, hash_key)

        if self.cass_write:
            c = self.cassandra_conn.hdel(key, hash_key)

        if self.redis_write:
            return r
        else:
            return c

    def hkeys(self, key):
        if self.cass_read:
            return self.cassandra_conn.hkeys(key)
        return self.redis_conn.hkeys(key)

    def set(self, key,value):
        if self.redis_write:
            r = self.redis_conn.set(key,value)

        if self.cass_write:
            c = self.cassandra_conn.set(key,value)

        if self.redis_write:
            return r
        else:
            return c

    def get(self, key):
        if self.cass_read:
            return self.cassandra_conn.get(key)

        return self.redis_conn.get(key)

    def delete(self, key):
        if self.redis_write:
            r = self.redis_conn.delete(key)

        if self.cass_write:
            c = self.cassandra_conn.delete(key)

        if self.redis_write:
            return r
        else:
            return c


    def pipeline(self):
        return WrapperPipeline(self, self.redis_write, self.cass_write, self.cass_read, self.redis_conn, self.cassandra_conn)

    # todo fix return value if redis is disabled
    def incrby(self, key, value):
        r = None
        if self.redis_write:
            r = self.redis_conn.incrby(key, value)

        if self.cass_write:
            self.cassandra_conn.incrby(key, value)

        return r
