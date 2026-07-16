from core.project_stats import ProjectStats
from core.project_tree import ProjectTree
from config import PROJECT_PATH

class ProjectReport:

    def build(self):

        stats=ProjectStats().build()

        tree=ProjectTree().build(PROJECT_PATH)

        return {

            "stats":stats,

            "tree":tree

        }
