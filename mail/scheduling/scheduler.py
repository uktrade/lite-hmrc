import datetime
import threading
import time

from conf.settings import POLL_INTERVAL


def scheduled_job():
    # Do some stuff
    # Offload the blocking job to a new thread

    t = threading.Thread(target=some_fn, args=(True,))
    t.setDaemon(True)
    t.start()

    return True


def some_fn(x):
    while x:
        from mail.routing_controller import check_and_route_emails

        print("I'm tyring to connect", datetime.datetime.now())
        try:
            check_and_route_emails()
        except Exception as e:
            print(e)
        print("I'm all good", datetime.datetime.now())
        # if condition:
        #     return
        # else:
        #     time.sleep(interval in seconds)
        # return 0
        time.sleep(POLL_INTERVAL)
