import hashlib


def create_dht(ids):
    dht = {i: None for i in ids}

    def get():
        return dht

    def clear():
        for i in dht:
            dht[i] = None

    def _mk_put_fns():
        def put(key, value):
            dht[key] = value

        return map(lambda i: lambda v: put(i, v), ids)
      
    return get, _mk_put_fns()
