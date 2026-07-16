import json
import os

FILE="memory.json"


class Memory:

    def __init__(self):

        if os.path.exists(FILE):

            self.data=json.load(open(FILE))

        else:

            self.data={

                "history":[],

                "last_file":"",

                "project":""

            }

            self.save()


    def save(self):

        json.dump(

            self.data,

            open(FILE,"w"),

            indent=4,

            ensure_ascii=False

        )


    def add(self,text):

        self.data["history"].append(text)

        self.save()


    def set_file(self,file):

        self.data["last_file"]=file

        self.save()


    def get(self):

        return self.data
