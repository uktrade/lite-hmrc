import threading
import time
from datetime import datetime

import schedule as schedule


# class Scheduler(object):
#     """
#     A scheduler used to schedule a job defined in mail.scheduling.jobs
#     """
#
#     def __init__(self, interval: int):
#         """interval: the length of time in seconds paused between runs"""
#         self.interval = interval
#
#     def add_job(self, job: object):
#         """add a job to this scheduler"""
#         schedule.every(self.interval).seconds.do(job)
#
#     def run(self):
#         while True:
#             schedule.run_pending()
#             time.sleep(1)


# def run_continuously(self, interval=5):
#     """Continuously run, while executing pending jobs at each elapsed
#     time interval.
#     @return cease_continuous_run: threading.Event which can be set to
#     cease continuous run.
#     Please note that it is *intended behavior that run_continuously()
#     does not run missed jobs*. For example, if you've registered a job
#     that should run every minute and you set a continuous run interval
#     of one hour then your job won't be run 60 times at each interval but
#     only once.
#     """
#
#     cease_continuous_run = threading.Event()
#
#     class ScheduleThread(threading.Thread):
#         @classmethod
#         def run(cls):
#             while not cease_continuous_run.is_set():
#                 self.run_pending()
#                 time.sleep(interval)
#
#     continuous_thread = ScheduleThread()
#     continuous_thread.setDaemon(True)
#     continuous_thread.start()
#     return cease_continuous_run
#
#
# schedule.Scheduler.run_continuously = run_continuously


def shut_down(params):
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
