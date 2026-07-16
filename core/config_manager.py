import json
import os

CONFIG_FILE="config.json"

class ConfigManager:

    def __init__(self):

        if os.path.exists(CONFIG_FILE):

            self.data=json.load(open(CONFIG_FILE))

        else:

            self.data={}

    def get(self,key,default=None):

        return self.data.get(key,default)

    def set(self,key,value):

        self.data[key]=value

        json.dump(self.data,open(CONFIG_FILE,"w"),indent=4)
