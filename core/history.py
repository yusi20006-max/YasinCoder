import json
import os
from datetime import datetime

FILE="history.json"

class History:

    def __init__(self):

        if os.path.exists(FILE):

            with open(FILE,"r",encoding="utf8") as f:

                self.data=json.load(f)

        else:

            self.data=[]

            self.save()

    def add(self,command):

        self.data.append({

            "time":datetime.now().isoformat(),

            "command":command

        })

        self.save()

    def save(self):

        with open(FILE,"w",encoding="utf8") as f:

            json.dump(self.data,f,indent=4,ensure_ascii=False)

    def last(self,n=10):

        return self.data[-n:]
