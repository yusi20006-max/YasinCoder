from core.project_index import ProjectIndex


class IndexCommand:

    def run(self):

        index = ProjectIndex(".")

        data = index.build()

        print()

        print("Project indexed successfully.")

        print("")

        print("Files :", len(data))
