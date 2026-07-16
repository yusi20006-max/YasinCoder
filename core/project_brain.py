from core.project_index import ProjectIndex
from core.parser import Parser

class ProjectBrain:

    def __init__(self):

        self.index=ProjectIndex()

        self.parser=Parser()

    def build(self,project):

        result=[]

        files=self.index.scan(project)

        for item in files:

            try:

                with open(item["path"],"r",encoding="utf8") as f:

                    code=f.read()

                info=self.parser.parse(code)

                result.append({

                    "file":item["name"],

                    "path":item["path"],

                    "classes":info["classes"],

                    "functions":info["functions"]

                })

            except:

                pass

        return result
