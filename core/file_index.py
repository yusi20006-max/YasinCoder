from project import list_files

class FileIndex:

    def build(self):

        index={}

        for file in list_files():

            name=file.split("/")[-1]

            index[name]=file

        return index
