#!/usr/bin/env python

import sys

from cbapi.example_helpers import build_cli_parser, get_cb_defense_object
from cbapi.psc.defense import *


def main():

    cb = CbDefenseAPI(profile="default")

    #List of devices to move
    deviceNames = ["Stark", "Targaryen", "greyjoy", "lannister.cbenglab.com"]

    #Policy to move to
    destPolicy = "sm-detection"

    for d in deviceNames:
        devices = list(cb.select(Device).where("hostNameExact:{0}".format(d)))
        #print("Pre-Test: {0:9} {1:40s}".format(devices[0].deviceId, devices[0].name, devices[0].policyName))
        if len(devices) > 0 :
            devices[0].policyName = destPolicy
            devices[0].save()
            print("Moved device id {0} (hostname {1}) into policy {2}.".format(devices[0].deviceId, devices[0].name, destPolicy))
        else:
            print("Device {0} not found.".format(d))

if __name__ == "__main__":
    sys.exit(main())
