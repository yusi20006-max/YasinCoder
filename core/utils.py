import os

def read(path):

    with open(path,"r",encoding="utf8") as f:

        return f.read()

def write(path,data):

    with open(path,"w",encoding="utf8") as f:

        f.write(data)

def project_name(path):

    return os.path.basename(path)
