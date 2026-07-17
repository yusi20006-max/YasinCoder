from core.project_index import ProjectIndex


class ProjectStats:

    def __init__(self, root):

        self.index = ProjectIndex(root)

    def info(self):

        data = self.index.load("index.json")

        files = len(data)

        classes = 0

        functions = 0

        imports = 0

        lines = 0

        for item in data:

            classes += len(item["classes"])

            functions += len(item["functions"])

            imports += len(item["imports"])

            lines += item["lines"]

        return {

            "files": files,

            "classes": classes,

            "functions": functions,

            "imports": imports,

            "lines": lines

        }
