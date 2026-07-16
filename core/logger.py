from datetime import datetime

class Logger:

    def info(self,msg):
        print("[INFO]",datetime.now(),msg)

    def warn(self,msg):
        print("[WARN]",datetime.now(),msg)

    def error(self,msg):
        print("[ERROR]",datetime.now(),msg)
