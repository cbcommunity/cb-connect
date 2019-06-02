#!/usr/bin/env python

import threading
import time
import json


TEST_EVENT_CONTENT = """{
  "url": "https://defense-dev01.cbdtest.io/investigate?s[searchWindow]=ALL&s[c][DEVICE_ID][0]=358141&s[c][INCIDENT_ID][0]=VJRFGCHC",
  "deviceInfo": {
    "deviceName": "WIN-BTB0KQ5OFF4",
    "deviceHostName": null,
    "deviceId": 358141,
    "targetPriorityType": "MEDIUM",
    "externalIpAddress": "104.207.192.98",
    "deviceType": "WINDOWS",
    "email": "againor",
    "internalIpAddress": "192.168.184.138",
    "groupName": "Standard",
    "targetPriorityCode": 0,
    "deviceVersion": "Windows 8.1 x64"
  },
  "eventDescription": "[devr-siem-notifications] [Carbon Black has detected a threat against your company.] [https://defense-dev01.cbdtest.io#device/358141/incident/VJRFGCHC] [The application CrossProductSystemTest.exe acted as a network server.] [Incident id: VJRFGCHC] [Threat score: 3] [Group: Standard] [Email: againor] [Name: WIN-BTB0KQ5OFF4] [Type and OS: WINDOWS Windows 8.1 x64] [Severity: Monitored]\\n",
  "threatInfo": {
    "summary": "The application CrossProductSystemTest.exe acted as a network server.",
    "indicators": [
      {
        "sha256Hash": "37fec82d9e18c251b76bcfd5a2b88e12974c5b44862e2a6900b8a1f71b76183f",
        "indicatorName": "FIXED_PORT_LISTEN",
        "applicationName": "CrossProductSystemTest.exe"
      },
      {
        "sha256Hash": "37fec82d9e18c251b76bcfd5a2b88e12974c5b44862e2a6900b8a1f71b76183f",
        "indicatorName": "UNKNOWN_APP",
        "applicationName": "CrossProductSystemTest.exe"
      }
    ],
    "score": 3,
    "incidentId": "VJRFGCHC",
    "time": 1544686632744
  },
  "eventTime": 1544646521656,
  "ruleName": "devr-siem-notifications",
  "type": "THREAT"
}
"""


class NotificationListener(threading.Thread):
    def __init__(self, cb, callbackfunc, poll_interval=30):
        threading.Thread.__init__(self)

        self.cb = cb
        self.callbackfunc = callbackfunc
        self.poll_interval = poll_interval
        self.daemon = True

    def run(self):
        while True:
            for notification in self.cb.notification_listener(self.poll_interval):
                self.callbackfunc(notification)


class SyntheticNotificationListener(threading.Thread):
    def __init__(self, device_id, callbackfunc, poll_interval=30):
        threading.Thread.__init__(self)

        self.device_id = device_id
        self.callbackfunc = callbackfunc
        self.poll_interval = poll_interval
        self.daemon = True

        self.test_event_content = json.loads(TEST_EVENT_CONTENT)
        self.test_event_content["deviceInfo"]["deviceId"] = int(device_id)

    def run(self):
        while True:
            self.callbackfunc(self.test_event_content)
            time.sleep(self.poll_interval)
