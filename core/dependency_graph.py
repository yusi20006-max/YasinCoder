from project import list_files
from core.code_parser import CodeParser

class DependencyGraph:

    def build(self):

        parser=CodeParser()

        graph={}

        for file in list_files():

            try:

                with open(file,"r",encoding="utf8") as f:

                    code=f.read()

                graph[file]=parser.parse(code)["imports"]

            except:

                graph[file]=[]

        return graph
