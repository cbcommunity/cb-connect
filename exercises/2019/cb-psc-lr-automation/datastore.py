import threading
import logging
from six.moves.queue import Queue
from collections import defaultdict


log = logging.getLogger(__name__)


class DataStore(object):
    def __init__(self):
        self.live_response_results = defaultdict(dict)
        self.live_response_lock = threading.Lock()

        self.work_queue = Queue()
        self.work_queue_lock = threading.Lock()
        self.work_queue_inflight = {}

    def update_result(self, device_id, results):
        with self.live_response_lock:
            self.live_response_results[device_id].update(results)

    def get_result(self, device_id):
        with self.live_response_lock:
            res = self.live_response_results.get(device_id, {})

        return res

    def devices_available(self):
        with self.live_response_lock:
            res = self.live_response_results.keys()

        return res

    def enqueue_work(self, device_id):
        with self.work_queue_lock:
            if device_id in self.work_queue_inflight:
                log.info("Device ID {} already inflight".format(device_id))
                return

            self.work_queue.put(device_id)
            self.work_queue_inflight[device_id] = True

    def dequeue_work(self):
        work_item = self.work_queue.get()
        return work_item

    def work_done(self, device_id):
        with self.work_queue_lock:
            self.work_queue.task_done()
            del(self.work_queue_inflight[device_id])

    def dump_info(self):
        with self.live_response_lock:
            for device_id in self.live_response_results:
                print(self.live_response_results[device_id])
