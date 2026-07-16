import os
import shutil
from datetime import datetime


class BackupManager:

    def backup(self,path):

        if not os.path.exists(path):

            return False

        name=path+"."+datetime.now().strftime("%Y%m%d%H%M%S")+".bak"

        shutil.copy2(path,name)

        return name
