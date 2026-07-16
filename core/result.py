class Result:

    def __init__(self,success=True,message="",data=None):

        self.success=success

        self.message=message

        self.data=data

    def to_dict(self):

        return {
            "success":self.success,
            "message":self.message,
            "data":self.data
        }
