import threading
import logging
from six.moves.queue import Queue
from collections import defaultdict


log = logging.getLogger(__name__)


class DataStore(object):
    """A simple object to track two things: the queue of devices we will be interrogating
    to collect Live Response results, and a database of the results we receive from those
    devices.

    The interface to this object is simple: use the ``enqueue_work()`` function to add
    a device ID into the list of devices to operate upon. If the device is already in the
    queue, this function returns immediately so as to avoid making multiple simultaneous
    requests to the same device.

    Worker threads can "pick up" work by calling ``dequeue_work()`` which sleeps until a
    work item is ready. Once a work item is ready, the device ID is returned.

    Once results are received from the remote device, the worker thread calls the
    ``update_result()`` function to add information to the result database for that device
    ID.

    The ``work_done()`` function should then be called to signal that the Live Response
    session is complete (whether it was successful or not). The device ID is removed from
    the list of devices being operated upon, so future calls to ``enqueue_work()`` with
    the same device ID will cause a new Live Response session for that device ID.

    Results can be consumed through the ``devices_available()`` method, which will return
    a list of all device IDs with results available in the database, and the
    ``get_result()`` method which will return the dictionary of detailed information for
    a given device ID.
    """

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
            res = list(self.live_response_results.keys())

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
