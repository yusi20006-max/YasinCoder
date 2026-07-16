import os
import platform

class Environment:

    def info(self):

        return {

            "platform":platform.system(),

            "python":platform.python_version(),

            "cwd":os.getcwd()

        }
