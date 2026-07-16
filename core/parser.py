import ast

class Parser:

    def parse(self,code):

        tree=ast.parse(code)

        classes=[]
        functions=[]

        for node in ast.walk(tree):

            if isinstance(node,ast.ClassDef):

                classes.append(node.name)

            elif isinstance(node,ast.FunctionDef):

                functions.append(node.name)

        return {

            "classes":classes,

            "functions":functions

        }
