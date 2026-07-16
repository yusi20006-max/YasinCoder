import os

class ProjectIndex:

    def __init__(self):
        self.files=[]

    def scan(self,project):

        self.files=[]

        for root,dirs,files in os.walk(project):

            dirs[:]=[d for d in dirs if not d.startswith(".")]

            for file in files:

                if file.endswith(".py"):

                    self.files.append({

                        "name":file,

                        "path":os.path.join(root,file)

                    })

        return self.files

    def names(self):

        return [x["name"] for x in self.files]

    def find(self,name):

        for item in self.files:

            if item["name"]==name:

                return item

        return None
