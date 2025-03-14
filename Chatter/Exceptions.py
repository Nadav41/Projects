class DateError(Exception):
    def __init__(self,time_tup, date_tup):
        self.date = [str(i) for i in date_tup]
        self.time = [str(i) for i in time_tup]

    def __str__(self):
        return f"Invalid date."