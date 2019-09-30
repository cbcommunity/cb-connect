import threading
import logging
import time
import os
from cbapi.psc.defense.models import Device
from cbapi.live_response_api import LiveResponseError

import uuid


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

    def __init__(self, cb, get_lr_session, datastore):
        threading.Thread.__init__(self)

        self.datastore = datastore
        self.get_lr_session = get_lr_session
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

    def run_psrecon(self, session):
        run_id = str(uuid.uuid4())
        COMMAND_LINE = "powershell c:\\psrecon\\psrecon.ps1"
        maximum_time = 300                      # max time in seconds before giving up

        log.info("Running psrecon - run ID {0}".format(run_id))

        try:
            session.create_directory("c:\\psrecon")
        except LiveResponseError as e:
            if e.win32_error == 0x800700B7:     # Directory already exists
                pass
            else:
                log.exception("Error creating c:\\psrecon directory")
                return None

        try:
            session.delete_file("c:\\psrecon\\psrecon.ps1")
        except LiveResponseError as e:
            if e.win32_error == 0x80070002:     # File not found
                pass
            else:
                log.exception("Error deleting existing psrecon.ps1 file")
                return None

        try:
            current_path = os.path.dirname(os.path.abspath(__file__))
            session.put_file(open(os.path.join(current_path, "files", "psrecon.ps1"), "rb"),
                             "c:\\psrecon\\psrecon.ps1")
        except Exception:
            log.exception("Could not upload psrecon powershell script")
            return None

        try:
            session.create_directory("c:\\psrecon\\{0}".format(run_id))
        except Exception:
            log.exception("Could not create c:\\psrecon\\{0} directory".format(run_id))
            return None

        try:
            session.create_process(COMMAND_LINE, wait_for_output=False,
                                   wait_for_completion=False,
                                   remote_output_file_name="c:\\psrecon\\{0}\\output.txt".format(run_id),
                                   working_directory="c:\\psrecon\\{0}".format(run_id))
        except Exception:
            log.exception("Could not launch psrecon")
            return None

        still_running = True
        start_time = time.time()
        current_time = start_time

        while still_running and current_time - start_time < maximum_time:
            try:
                listing = session.list_processes()
                if COMMAND_LINE not in [proc["command_line"] for proc in listing]:
                    still_running = False
                else:
                    time.sleep(2)
            except:
                pass


        try:
            listing = session.list_directory("c:\\psrecon\\{0}\\psrecon*".format(run_id))
        except LiveResponseError as e:
            log.exception("Could not find PSRecon output directory")
            return None
        else:
            output_file_name = listing[0]["filename"]

        try:
            psrecon_data = session.get_file("c:\\psrecon\\{0}\\{1}\\{1}.html".format(run_id, output_file_name))
        except Exception:
            log.exception("Could not retrieve file")
            return None
        else:
            return psrecon_data


    def process_task(self, device_id):
        log.info("Performing live response on {}".format(device_id))
        session = self.get_lr_session(self.cb, device_id)

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

        psrecon_data = self.run_psrecon(session)

        log.info("Live Response complete")
        session.close()

        # Update the database with the results from our Live Response session
        self.datastore.update_result(device_id,
                                    {
                                        "browser_history": browser_history,
                                        "running_services": running_services.decode('utf8'),
                                        "psrecon_report": psrecon_data,
                                        "lr_timestamp": time.time()
                                    })
