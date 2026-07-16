class FileReader:

    def read(self,path):

        with open(path,"r",encoding="utf8") as f:

            return f.read()
