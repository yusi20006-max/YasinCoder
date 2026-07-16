import os
import shutil

class FileManager:

    def exists(self,path):
        return os.path.exists(path)

    def read(self,path):
        with open(path,"r",encoding="utf8") as f:
            return f.read()

    def write(self,path,data):
        with open(path,"w",encoding="utf8") as f:
            f.write(data)

    def backup(self,path):

        if os.path.exists(path):
            shutil.copy2(path,path+".bak")
