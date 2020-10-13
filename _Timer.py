import threading

class Timer1(threading.Timer): 
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()