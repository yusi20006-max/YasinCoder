from project import list_files

class ProjectStats:

    def build(self):

        total_files=0
        total_lines=0

        for file in list_files():

            total_files+=1

            try:

                with open(file,"r",encoding="utf8") as f:

                    total_lines+=len(f.readlines())

            except:

                pass

        return {

            "files":total_files,

            "lines":total_lines

        }
