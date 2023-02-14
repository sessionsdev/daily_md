class DateHeaderNotFoundError(Exception):
    def __init__(self, date):
        self.message = f"Header for {date} was not found."

        super().__init__(self.message)