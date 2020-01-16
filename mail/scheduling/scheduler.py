import threading
import time
from datetime import datetime


def scheduled_jobs():
    # Do some stuff
    # Offload the blocking job to a new thread

    t = threading.Thread(target=some_fn, args=(), kwargs={})
    t.setDaemon(True)
    t.start()

    return True


def some_fn():
    while True:
        print(datetime.now())
        # if condition:
        #     return
        # else:
        #     time.sleep(interval in seconds)
        time.sleep(5)
