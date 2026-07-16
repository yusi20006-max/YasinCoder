import os
from config import PROJECT_PATH

def list_files():

    result=[]

    for root,dirs,files in os.walk(PROJECT_PATH):

        dirs[:]=[d for d in dirs if not d.startswith(".")]

        for file in files:

            if file.endswith(".py"):

                result.append(os.path.join(root,file))

    return sorted(result)


def find_file(name):

    for file in list_files():

        if os.path.basename(file)==name:

            return file

    return None


def read_file(name):

    path=find_file(name)

    if path is None:

        return None

    with open(path,"r",encoding="utf8") as f:

        return f.read()


def project_info():

    files=list_files()

    return {

        "project":PROJECT_PATH,

        "count":len(files),

        "files":files

    }
