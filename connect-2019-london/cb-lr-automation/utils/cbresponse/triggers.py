import threading
import time
import json
import logging

log = logging.getLogger(__name__)


def process_notification(notification):
    # Retrieve device ID from the notification body
    # optionally this function could determine if our notification 'meets the threshold'
    #  to trigger a live response action.
    try:
        device_id = int(notification["sensor_id"])
        log.info("Received THREAT notification for sensor_id {}, enqueuing".format(device_id))
        return device_id
    except:
        return None


# TODO: clean up and create a proper listener class that integrates with the event forwarder output
class NotificationListener(threading.Thread):
    def __init__(self, datastore, poll_interval=30):
        threading.Thread.__init__(self)

        self.datastore = datastore
        self.poll_interval = poll_interval
        self.daemon = True

    def run(self):
        while True:
            for notification in self.cb.notification_listener(self.poll_interval):
                device_id = process_notification(notification)
                if device_id:
                    self.datastore.enqueue_work(device_id)
                    self.datastore.update_result(device_id, {"notification": notification, "timestamp": time.time()})


# TODO: add a "real" notification for synthetic testing purposes
class SyntheticNotificationGenerator(threading.Thread):
    TEST_EVENT_CONTENT = """{ }"""

    def __init__(self, device_id, datastore, poll_interval=30):
        threading.Thread.__init__(self)

        self.device_id = device_id
        self.datastore = datastore
        self.poll_interval = poll_interval
        self.daemon = True

        self.test_event_content = json.loads(self.TEST_EVENT_CONTENT)
        self.test_event_content["sensor_id"] = int(device_id)

    def run(self):
        while True:
            device_id = process_notification(self.test_event_content)
            if device_id:
                self.datastore.enqueue_work(device_id)
                self.datastore.update_result(device_id, {"notification": self.test_event_content,
                                                         "timestamp": time.time()})
            time.sleep(self.poll_interval)
