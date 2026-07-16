from project import list_files

class SearchCommand:

    def run(self,keyword):

        result=[]

        for file in list_files():

            try:

                with open(file,"r",encoding="utf8") as f:

                    text=f.read()

                if keyword.lower() in text.lower():

                    result.append(file)

            except:

                pass

        return result
