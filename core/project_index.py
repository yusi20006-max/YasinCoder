import ast
import json
from pathlib import Path


class ProjectIndex:

    def __init__(self, root):

        self.root = Path(root)
        self.db = self.root / ".yc"

    def save(self, name, data):

        self.db.mkdir(exist_ok=True)

        with open(self.db / name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, name):

        path = self.db / name

        if not path.exists():
            return {}

        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def python_files(self):

        files = []

        for file in self.root.rglob("*.py"):

            if ".git" in file.parts:
                continue

            if "__pycache__" in file.parts:
                continue

            if ".yc" in file.parts:
                continue

            files.append(file)

        return sorted(files)

    def analyze(self, file):

        source = file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        tree = ast.parse(source)

        classes = []

        functions = []

        imports = []

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):

                classes.append(node.name)

            elif isinstance(node, ast.FunctionDef):

                functions.append(node.name)

            elif isinstance(node, ast.Import):

                for n in node.names:

                    imports.append(n.name)

            elif isinstance(node, ast.ImportFrom):

                imports.append(node.module)

        return {

            "file": str(file),

            "classes": classes,

            "functions": functions,

            "imports": imports,

            "lines": len(source.splitlines())

        }

    def build(self):

        result = []

        for file in self.python_files():

            try:

                result.append(

                    self.analyze(file)

                )

            except Exception:

                pass

        self.save("index.json", result)

        return result
