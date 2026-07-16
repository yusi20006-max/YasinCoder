import json
import os

class JsonDB:

    def __init__(self,file):

        self.file=file

        if os.path.exists(file):

            self.data=json.load(open(file))

        else:

            self.data={}

    def save(self):

        json.dump(

            self.data,

            open(self.file,"w"),

            indent=4,

            ensure_ascii=False

        )
