from .webui import get_flask_server

import time
import logging


log = logging.getLogger(__name__)


class LiveResponseOrchestrator(object):
    def __init__(self, cb, get_lr_session, context_worker_cls, datastore):
        self.context_worker_cls = context_worker_cls
        self.datastore = datastore
        self.get_lr_session = get_lr_session
        self.cb = cb

    def start(self):
        # Start the flask web server
        web = get_flask_server(self.datastore)
        web.start()

        # Start five threads to listen for work and do the Live Response
        for i in range(5):
            worker_thread = self.context_worker_cls(self.cb, self.get_lr_session, self.datastore)
            worker_thread.start()

        # Sleep forever so our worker threads do all the work in the background. Listen for a keyboard
        #  interrupt to exit cleanly
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # uncomment below to dump out the current state of the database:
            # self.datastore.dump_info()
            return
