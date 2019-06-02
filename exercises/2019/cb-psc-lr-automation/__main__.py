#!/usr/bin/env python

"""
This script demonstrates how to automate a Live Response action when a notification
is received on a given device.

To follow along, start at the ``main()`` function at the bottom of this file, then
trace through the ``LiveResponseOrchestrator.start()`` method.

This script demonstrates how you can implement a simple orchestration capability
with the Carbon Black Predictive Security Cloud. This orchestration example is
subdivided into four parts. Each of the parts demonstrated
are modular, so you can swap out for different functionality. The high level
modules demonstrated here are:

``actions`` - Implements the Live Response worker; change this out if you want to
adjust the data that you want to collect on the remote endpoint.

``triggers`` - Provides two implementations of a 'trigger' mechanism: one
will poll the PSC Notifications API to trigger on any alert/incident notification,
and the other will generate testing notifications to trigger on a specific device
ID.

``datastore`` - Implements a simple in-memory database to store the results of
the retrieved Live Response data. Change this out if you want to persist the data
into an external database.

``webapi`` - Provides the web front-end to view the results stored in the database.
"""

from actions import CollectContextWorker
from triggers import NotificationListener, SyntheticNotificationGenerator
from datastore import DataStore
from webapi import get_flask_server

from cbapi.example_helpers import get_cb_defense_object, build_cli_parser

import sys
import logging
import time


log = logging.getLogger(__name__)


class LiveResponseOrchestrator(object):
    def __init__(self, args):
        self.args = args
        self.cb = get_cb_defense_object(args)
        self.datastore = DataStore()

    def start(self):
        poll_interval = self.args.poll

        # Start the flask web server
        web = get_flask_server(self.datastore)
        web.start()

        # Start the thread to listen to notifications
        if self.args.synthetic:
            notification_thread = SyntheticNotificationGenerator(self.args.synthetic, self.datastore,
                                                                 poll_interval=poll_interval)
        else:
            notification_thread = NotificationListener(self.cb, self.datastore, poll_interval=poll_interval)
        notification_thread.start()

        # Start five threads to listen for work and do the Live Response
        for i in range(5):
            worker_thread = CollectContextWorker(self.cb, self.datastore)
            worker_thread.start()

        # Sleep forever so our worker threads do all the work in the background. Listen for a keyboard
        #  interrupt to exit cleanly
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.datastore.dump_info()
            return

    def process_notification(self, notification):
        # Retrieve device ID from the notification body
        device_id = int(notification["deviceInfo"]["deviceId"])
        log.info("Received THREAT notification for device_id {}, enqueuing".format(device_id))
        self.datastore.enqueue_work(device_id)
        self.datastore.update_result(device_id, {"notification": notification, "timestamp": time.time()})


def main():
    # First we create a command line parser to collect our configuration.
    # We use the built in ``build_cli_parser`` in ``cbapi.example_helpers`` to build
    #  the basic command line parser, then augment with a few parameters specific to
    #  this script.
    parser = build_cli_parser("Example CB PSC Live Response automation")
    parser.add_argument("--synthetic", help="Generate synthetic notifications with given Device ID",
                        metavar="DEVICE_ID")
    parser.add_argument("--poll", help="Poll interval for the Notifications API", type=int, default=30)
    parser.add_argument("--siemprofile", help="CB Profile for SIEM API key (required to poll for notifications)",
                        default="siem")
    args = parser.parse_args()

    log.info("Starting")

    orchestrator = LiveResponseOrchestrator(args)
    orchestrator.start()

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    sys.exit(main())