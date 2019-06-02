import threading
import logging
import time
from cbapi.psc.defense.models import Device


log = logging.getLogger(__name__)


class CollectContextWorker(threading.Thread):
    """The CollectContextWorker is an example Worker thread that establishes a
    Live Response session with a remote device, retrieves context from the device,
    and adds that context to the datastore.

    This example implementation retrieves:

    1. The list of all running Windows services on the remote host
    2. The Google Chrome browser history file for any currently logged-in users
       on the remote host

    This is implemented as a Python thread, that sits and waits for jobs to appear
    in the datastore queue (see the ``datastore.py`` file for more information on
    the datastore). Multiple workers can be created in parallel in order to process
    multiple concurrent requests. Once results have been retrieved from the
    remote system, the results are stored back into the datastore so the web
    front-end can interpret and display back to the user."""

    def __init__(self, cb, datastore):
        threading.Thread.__init__(self)

        self.datastore = datastore
        self.cb = cb
        self.daemon = True

    def run(self):
        log.debug("Starting worker {}".format(self))
        while True:
            device_id = self.datastore.dequeue_work()
            try:
                self.process_task(device_id)
            except Exception as e:
                log.exception("Error processing task {}".format(device_id))
            finally:
                self.datastore.work_done(device_id)

    def retrieve_chrome_history(self, session, username):
        log.info("Gathering Chrome browser history for %s" % username)
        try:
            history_file = \
                session.get_file("c:\\users\\%s\\appdata\\local\\google\\chrome\\user data\\default\\history"
                                 % username)
            return history_file
        except Exception:
            log.exception("Could not retrieve Chrome history for {0}".format(username))
            return None

    def process_task(self, device_id):
        log.info("Performing live response on {}".format(device_id))
        dev = self.cb.select(Device, device_id)
        session = dev.lr_session()

        # We have a live response session - let's collect some data
        running_services = session.create_process("c:\\windows\\system32\\net.exe start")
        running_processes = session.list_processes()

        # get the list of currently logged-in users
        users = set([proc['username'].split('\\')[-1]
                     for proc in running_processes if proc['path'].find('explorer.exe') != -1])

        log.info("There are {0} users logged in to device {1}: {2}".format(len(users), device_id,
                                                                           ", ".join(list(users))))

        # Retrieve the Chrome browser history file for all logged-in users
        # - we split the actual retrieval for the history into its own function in case we receive
        #   an exception. (perhaps the user doesn't have a Chrome history file?)
        browser_history = {}
        for user in users:
            log.info("Gathering Chrome browser history for %s" % user)
            history_file = self.retrieve_chrome_history(session, user)
            if history_file:
                # If we retrieved a Chrome browser history file for the user, just store
                #  the whole thing in our database
                browser_history[user] = history_file

        log.info("Live Response complete")
        session.close()

        # Update the database with the results from our Live Response session
        self.datastore.update_result(device_id,
                                    {
                                        "browser_history": browser_history,
                                        "running_services": running_services.decode('utf8'),
                                        "lr_timestamp": time.time()
                                    })
