import hashlib
import json
import os

CACHE_DIR="cache"

os.makedirs(CACHE_DIR,exist_ok=True)

class Cache:

    def path(self,key):

        h=hashlib.md5(key.encode()).hexdigest()

        return os.path.join(CACHE_DIR,h+".json")

    def save(self,key,data):

        with open(self.path(key),"w",encoding="utf8") as f:

            json.dump(data,f,indent=4,ensure_ascii=False)

    def load(self,key):

        p=self.path(key)

        if not os.path.exists(p):

            return None

        with open(p,"r",encoding="utf8") as f:

            return json.load(f)
