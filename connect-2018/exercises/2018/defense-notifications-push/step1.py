#!/usr/bin/env python

# Subscribe to notifications on Cb Defense and push them to your mobile phone via
# Pushover: https://pushover.net

# Step 1: basic authentication to Cb Defense and ability to pull Notifications

import sys
from cbapi.example_helpers import get_cb_defense_object, build_cli_parser


def main():
    parser = build_cli_parser("Push notifications to mobile phone")

    # Parse command line arguments and retrieve Cb Defense API credentials
    args = parser.parse_args()
    cb = get_cb_defense_object(args)

    # Note that the following is essentially an infinite loop - it will keep asking for notifications from
    # the Cb Defense server every 30 seconds forever...
    for notification in cb.notification_listener(interval=30):
        print(notification)


if __name__ == '__main__':
    sys.exit(main())