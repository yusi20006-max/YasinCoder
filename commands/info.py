from core.version import VERSION
from core.constants import SUPPORTED_COMMANDS

class InfoCommand:

    def run(self):

        return {

            "version":VERSION,

            "commands":SUPPORTED_COMMANDS

        }
