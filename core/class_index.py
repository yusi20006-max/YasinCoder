from project import list_files
from core.code_parser import CodeParser

class ClassIndex:

    def build(self):

        parser=CodeParser()

        result={}

        for file in list_files():

            try:

                code=open(file,"r",encoding="utf8").read()

                data=parser.parse(code)

                result[file]=data["classes"]

            except:

                result[file]=[]

        return result
