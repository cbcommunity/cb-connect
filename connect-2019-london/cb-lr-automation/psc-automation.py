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

import logging
import sys
import time

from cbapi.example_helpers import get_cb_defense_object, build_cli_parser
from cbapi.psc.defense import CbDefenseAPI, Device

from utils.actions import CollectContextWorker
from utils.datastore import DataStore
from utils.psc.triggers import NotificationListener, SyntheticNotificationGenerator
from utils.orchestrator import LiveResponseOrchestrator

log = logging.getLogger(__name__)


def get_lr_session_psc(cb, device_id):
    sensor = cb.select(Device, device_id)
    return sensor.lr_session()


def main():
    # First we create a command line parser to collect our configuration.
    # We use the built in ``build_cli_parser`` in ``cbapi.example_helpers`` to build
    #  the basic command line parser, then augment with a few parameters specific to
    #  this script.
    parser = build_cli_parser("Example CB PSC & Response Live Response automation")
    parser.add_argument("--synthetic", help="Generate synthetic notifications with given Device ID",
                        metavar="DEVICE_ID")
    parser.add_argument("--poll", help="Poll interval for the Notifications API", type=int, default=30)
    parser.add_argument("--siemprofile", help="CB Profile for SIEM API key (required to poll for notifications)",
                        default="siem")
    args = parser.parse_args()

    log.info("Starting")

    datastore = DataStore()

    # Start the thread to listen to notifications
    if args.synthetic:
        notification_thread = SyntheticNotificationGenerator(args.synthetic, datastore,
                                                             poll_interval=args.poll)
    else:
        siem_cb = CbDefenseAPI(profile=args.siemprofile)
        notification_thread = NotificationListener(siem_cb, datastore, poll_interval=args.poll)
    notification_thread.daemon = True
    notification_thread.start()

    cb = get_cb_defense_object(args)

    orchestrator = LiveResponseOrchestrator(cb, get_lr_session_psc, CollectContextWorker, datastore)
    orchestrator.start()

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    sys.exit(main())