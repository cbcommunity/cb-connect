import threading
import logging
import time
from cbapi.psc.defense import *


log = logging.getLogger(__name__)


class CollectContextWorker(threading.Thread):
    def __init__(self, cb, datastore):
        threading.Thread.__init__(self)

        self.datastore = datastore
        self.cb = cb
        self.daemon = True

    def run(self):
        log.info("Starting worker {}".format(self))
        while True:
            device_id = self.datastore.dequeue_work()
            try:
                self.process_task(device_id)
            except Exception as e:
                log.exception("Error processing task {}".format(device_id))
            finally:
                self.datastore.work_done(device_id)

    def process_task(self, device_id):
        log.info("Performing live response on {}".format(device_id))
        dev = self.cb.select(Device, device_id)
        session = dev.lr_session()

        # we have a live response session - let's collect some data
        running_services = session.create_process("c:\\windows\\system32\\net.exe start")
        running_processes = session.list_processes()

        # get the current user
        users = set([proc['username'].split('\\')[-1]
                     for proc in running_processes if proc['path'].find('explorer.exe') != -1])

        log.info("There are {0} users logged in to device {1}: {2}".format(len(users), device_id,
                                                                           ", ".join(list(users))))

        browser_history = {}
        for user in users:
            log.info("Gathering Chrome browser history for %s" % user)
            browser_history[user] = \
                session.get_file("c:\\users\\%s\\appdata\\local\\google\\chrome\\user data\\default\\history" % user)

        log.info("Live Response complete")
        session.close()

        self.datastore.update_result(device_id,
                                    {
                                        "browser_history": browser_history,
                                        "running_services": running_services.decode('utf8'),
                                        "lr_timestamp": time.time()
                                    })
