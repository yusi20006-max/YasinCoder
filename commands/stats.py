from core.project_stats import ProjectStats


class StatsCommand:

    def run(self):

        stats = ProjectStats(".")

        info = stats.info()

        print()

        print("Project Statistics")

        print("------------------")

        print("Files      :", info["files"])

        print("Classes    :", info["classes"])

        print("Functions  :", info["functions"])

        print("Imports    :", info["imports"])

        print("Lines      :", info["lines"])
