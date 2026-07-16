import json
import os


FILE="tasks.json"


class TaskManager:

    def __init__(self):

        if os.path.exists(FILE):

            self.tasks=json.load(open(FILE))

        else:

            self.tasks=[]


    def add(self,text):

        self.tasks.append({

            "task":text,

            "done":False

        })

        self.save()


    def save(self):

        json.dump(

            self.tasks,

            open(FILE,"w"),

            indent=4,

            ensure_ascii=False

        )


    def all(self):

        return self.tasks
