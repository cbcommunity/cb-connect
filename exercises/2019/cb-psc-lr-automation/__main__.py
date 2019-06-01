from notifications import NotificationListener, SyntheticNotificationListener
from actions import CollectContextWorker
from datastore import DataStore
from webapi import get_flask_server

from cbapi.example_helpers import get_cb_defense_object, build_cli_parser
from six.moves.queue import Queue

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
            notification_thread = SyntheticNotificationListener(self.args.synthetic, self.process_notification,
                                                                poll_interval=poll_interval)
        else:
            notification_thread = NotificationListener(self.cb, self.process_notification, poll_interval=poll_interval)

        # Start five threads to listen for work and do the Live Response
        for i in range(5):
            worker_thread = CollectContextWorker(self.cb, self.datastore)
            worker_thread.start()

        notification_thread.start()
        try:
            time.sleep(100)
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
    parser = build_cli_parser("Example CB PSC Live Response automation")
    parser.add_argument("--synthetic", help="Generate synthetic notifications with given Device ID",
                        metavar="DEVICE_ID")
    parser.add_argument("--poll", help="Poll interval for the Notifications API", type=int, default=30)
    args = parser.parse_args()

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    log.info("Starting")

    orchestrator = LiveResponseOrchestrator(args)

    orchestrator.start()

if __name__ == '__main__':
    sys.exit(main())