

class Logger():

    log_file = r"./experiment.log"

    def __init__(self, log_file: str):
        self.log_file = log_file

    def log(self, message: str):
        with open(self.log_file, 'a') as f:
            f.write(f"{message}\n")

    def set_log_file(self, log_file: str):
        self.log_file = log_file


