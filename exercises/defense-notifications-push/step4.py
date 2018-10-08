#!/usr/bin/env python

# Subscribe to notifications on Cb Defense and push them to your mobile phone via
# Pushover: https://pushover.net

# Step 4: Add automated action based on notification

import sys
from cbapi.example_helpers import get_cb_defense_object, build_cli_parser
from os.path import join, expanduser
import requests


# TODO: Define how you would like to summarize a THREAT notification
def summarize_threat(notification):
    """Summarize a THREAT notification type. An example of a THREAT notification:
    {
      "eventTime": 1534474673973,
      "eventDescription": "[jason-splunk-test-alert] [Confer has detected a threat against your company.]
     [https://defense-eap01.conferdeploy.net#device/5798/incident/2TP5H0LB] [The application chrome.exe i
    nvoked another application (software_reporter_tool.exe).] [Incident id: 2TP5H0LB] [Threat score: 3] [
    Group: Restrictive_Windows_Workstation] [Email: jgarman+po@carbonblack.com] [Name: WIN-IA9NQ1GN8OI] [
    Type and OS: WINDOWS Windows 8 x64] [Severity: Monitored]\n",
      "ruleName": "jason-splunk-test-alert",
      "threatInfo": {
        "indicators": [
          {
            "applicationName": "chrome.exe",
            "indicatorName": "RUN_ANOTHER_APP",
            "sha256Hash": "268a0463d7cb907d45e1c2ab91703e71734116f08b2c090e34c2d506183f9bca"
          }
        ],
        "summary": "The application chrome.exe invoked another application (software_reporter_tool.exe)."
    ,
        "score": 3,
        "time": 1534474724976,
        "incidentId": "2TP5H0LB"
      },
      "url": "https://defense-eap01.conferdeploy.net/investigate?s[searchWindow]=ALL&s[c][DEVICE_ID][0]=5
    798&s[c][INCIDENT_ID][0]=2TP5H0LB",
      "deviceInfo": {
        "externalIpAddress": "70.106.213.105",
        "deviceHostName": null,
        "groupName": "Restrictive_Windows_Workstation",
        "deviceVersion": "Windows 8 x64",
        "targetPriorityType": "MEDIUM",
        "deviceName": "WIN-IA9NQ1GN8OI",
        "internalIpAddress": "192.168.109.131",
        "email": "jgarman+po@carbonblack.com",
        "deviceType": "WINDOWS",
        "targetPriorityCode": 0,
        "deviceId": 5798
      },
      "type": "THREAT"
    }
    """
    return notification.get("threatInfo", {}).get("summary", None)


def main():
    parser = build_cli_parser("Push notifications to mobile phone")
    parser.add_argument("pushoverkey", help="API key for pushover (will read from ~/.pushover if this isn't set)")
    parser.add_argument("userkey", help="User key for pushover (to control the destination of your notifications)",
                        nargs=1)

    # Parse command line arguments and retrieve Cb Defense API credentials
    args = parser.parse_args()
    cb = get_cb_defense_object(args)

    # Get the API key for Pushover
    if args.pushoverkey:
        pushoverkey = args.pushoverkey
    else:
        # Read from ~/.pushover
        homedir = expanduser("~")
        pushoverkey = open(join(homedir, ".pushover"), "r").readline().strip()

    for notification in cb.notification_listener(interval=30):
        if notification.get("type") == "THREAT":
            summary = summarize_threat(notification)

            # Send summary to pushover to notify our on-call team
            requests.post("https://api.pushover.net/1/messages.json", json={
                "token": pushoverkey,
                "user": args.userkey,
                "message": summary
            })

            print("Sent notification {0} to phones!".format(summary))


if __name__ == '__main__':
    sys.exit(main())