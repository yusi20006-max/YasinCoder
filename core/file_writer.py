class FileWriter:

    def write(self,path,data):

        with open(path,"w",encoding="utf8") as f:

            f.write(data)
