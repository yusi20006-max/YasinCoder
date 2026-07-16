from project import list_files

class FileSearch:

    def search(self,text):

        result=[]

        for file in list_files():

            try:

                with open(file,"r",encoding="utf8") as f:

                    code=f.read()

                if text.lower() in code.lower():

                    result.append(file)

            except:

                pass

        return result
