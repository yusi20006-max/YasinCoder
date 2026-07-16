import os

class ProjectTree:

    def build(self,path):

        result=[]

        for root,dirs,files in os.walk(path):

            dirs[:]=sorted(dirs)

            files=sorted(files)

            level=root.replace(path,"").count(os.sep)

            result.append({

                "level":level,

                "path":root,

                "dirs":dirs,

                "files":files

            })

        return result
