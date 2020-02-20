import datetime
import threading
import time


def scheduled_job():
    # Do some stuff
    # Offload the blocking job to a new thread

    t = threading.Thread(target=some_fn, args=(True,))
    t.setDaemon(True)
    t.start()

    return True


def some_fn(x):
    while x:
        # check_and_route_emails()
        print("I'm all good", datetime.datetime.now())
        # if condition:
        #     return
        # else:
        #     time.sleep(interval in seconds)
        # return 0
        time.sleep(15)
