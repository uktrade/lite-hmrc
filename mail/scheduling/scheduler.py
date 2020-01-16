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
        # Do the job, get result in res
        # If the job is done, return. Or sleep the thread for 2 seconds before trying again.
        print(datetime.now())
        time.sleep(5)
