class Report:

    def build(self,title,items):

        out=[]

        out.append(title)

        out.append("="*40)

        for item in items:

            out.append(str(item))

        return "\\n".join(out)
