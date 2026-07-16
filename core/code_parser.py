import ast

class CodeParser:

    def parse(self,code):

        tree=ast.parse(code)

        result={

            "classes":[],

            "functions":[],

            "imports":[]

        }

        for node in ast.walk(tree):

            if isinstance(node,ast.ClassDef):

                result["classes"].append(node.name)

            elif isinstance(node,ast.FunctionDef):

                result["functions"].append(node.name)

            elif isinstance(node,ast.Import):

                for i in node.names:

                    result["imports"].append(i.name)

            elif isinstance(node,ast.ImportFrom):

                if node.module:

                    result["imports"].append(node.module)

        return result
