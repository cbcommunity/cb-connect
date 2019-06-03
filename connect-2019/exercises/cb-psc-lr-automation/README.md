# PSC Live Response Automation Example

This example was presented during CB Connect 2019 at the
"Exploring the Predictive Security Cloud APIs" session on June 4.

This script demonstrates how you can automate the Live Response
capability in the Carbon Black Predictive Security Cloud to
automatically collect additional context when a notification is
received.

## How it works

This script uses the Live Response capability to collect the following
information from a remote endpoint when a `THREAT` notification is
received for that endpoint:

1. The list of all running Windows services on the remote host
2. The Google Chrome browser history file for any currently logged-in users
   on the remote host

This example script polls for notifications using the PSC Notifications
API, then if one is received, retrieves the device ID for that alert
from the notification and passes the device ID to a Live Response
worker thread to collect those two data points.

The collected data is stored in memory and then available to analysts
through an embedded web server.

## Installation & Pre-Requisites

To use this script, you will need the following:

1. an API key of type "Live Response" in your PSC organization
2. an API key of type "SIEM" in your PSC organization
3. Python version 2.7+ or 3.5+
4. The `cbapi` Python module installed and configured

To learn how to create API keys in your PSC organization, visit the
[CB Developer Network website](https://developer.carbonblack.com) and
search for "CB Defense authentication" in the top right.

Once you have Python installed and the API keys created, you can then
configure this script. Run the following command in a Python command
prompt:

    pip install -r requirements.txt

This `pip install` command will install the required Python modules:
`cbapi` for accessing the PSC APIs, `Flask` for serving the web
front-end, and the `six` module to handle Python 2/3 compatibility.

Once `pip install` has completed, then proceed to add the API keys
you created in your organization to the configuration file for `cbapi`.
You can do this by creating a directory called `.carbonblack` (note
the beginning period) in your user's home directory (for example
`C:\Users\myusername` on Windows, or `/home/myusername` on Linux/macOS).
Inside that directory, create a file named `credentials.psc` and add
two profiles: one for your "Live Response" API key, and one for your
"SIEM" API key.

To use the script out of the box, name your Live Response API key
profile `default` and name your SIEM API key profile `siem`.

Your `.carbonblack/credentials.psc` file should look like the following:

    [default]
    url=https://api-prod05.conferdeploy.net
    token=SYDCCYZ86BAKGQD45XRJYR6W/SOAP56ZKZ7

    [siem]
    url=https://api-prod05.conferdeploy.net
    token=3A9CW66L9M2MFKQPWTA70PFD/DR8CKLRPUN

For more information on creating the configuration file, see the
[`cbapi` documentation](https://cbapi.readthedocs.io) page.

## Usage

Once the prerequisites have been installed and the credential file
created, then you can launch the script. Change directory into the
folder containing the `cb-psc-lr-automation` folder, and type:

    python cb-psc-lr-automation

You should see the python script launch and start the webserver on
port 7982. You can then connect to the webserver on the local machine
at http://localhost:7982/

Detailed usage can be retrieved by adding the `--help` command line
parameter:

    usage: cb-psc-lr-automation [-h] [--cburl CBURL] [--apitoken APITOKEN]
                                [--no-ssl-verify] [--profile PROFILE] [--verbose]
                                [--synthetic DEVICE_ID] [--poll POLL]
                                [--siemprofile SIEMPROFILE]

    Example CB PSC Live Response automation

    optional arguments:
      -h, --help            show this help message and exit
      --cburl CBURL         CB server's URL. e.g., http://127.0.0.1
      --apitoken APITOKEN   API Token for Carbon Black server
      --no-ssl-verify       Do not verify server SSL certificate.
      --profile PROFILE     profile to connect
      --verbose             enable debug logging
      --synthetic DEVICE_ID
                            Generate synthetic notifications with given Device ID
      --poll POLL           Poll interval for the Notifications API
      --siemprofile SIEMPROFILE
                            CB Profile for SIEM API key (required to poll for
                            notifications)

## Implementation

This orchestration example is subdivided into four parts. Each of the parts demonstrated
are modular, so you can swap each out for different functionality. The high level
components, implemented as Python modules, demonstrated here are:

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

There are comments in each of the Python modules to help understand the
implementation details.

## Debugging and Testing

An integral part of any integration is testing and debugging. This
script contains a simple way to test the Live Response capability
without the need to wait for a notification to appear on a given
endpoint. To run this script and force it to acquire Live Response
for a given device, use the `--synthetic` command line parameter,
followed by the device ID you'd like to use for testing. Consider
adding the `--verbose` flag to collect additional information as the
script runs as well.

An example successful run:

    python cb-psc-lr-automation --synthetic 21212 --poll 1 --profile lrprofile --verbose
    INFO:__main__:Starting
    DEBUG:cbapi.auth:Using file credential store
     * Serving Flask app "liveresponse" (lazy loading)
     * Environment: production
       WARNING: Do not use the development server in a production environment.
       Use a production WSGI server instead.
     * Debug mode: off
    INFO:actions:Starting worker <CollectContextWorker(Thread-3, started daemon 140422543394560)>
    INFO:actions:Starting worker <CollectContextWorker(Thread-4, started daemon 140422535001856)>
    INFO:actions:Starting worker <CollectContextWorker(Thread-5, started daemon 140422526609152)>
    INFO:actions:Starting worker <CollectContextWorker(Thread-6, started daemon 140422518216448)>
    INFO:actions:Starting worker <CollectContextWorker(Thread-7, started daemon 140422509823744)>
    INFO:__main__:Received THREAT notification for device_id 21212, enqueuing
    INFO:actions:Performing live response on 21212
    DEBUG:cbapi.connection:Sending HTTP POST /integrationServices/v3/cblr/session/21212 with {"sensor_id": 21212}
    INFO:werkzeug: * Running on http://0.0.0.0:7982/ (Press CTRL+C to quit)
    DEBUG:cbapi.connection:HTTP POST /integrationServices/v3/cblr/session/21212 took 0.171s (response 200)
    DEBUG:cbapi.connection:HTTP GET /integrationServices/v3/cblr/session/1:21212 took 0.155s (response 200)
    DEBUG:cbapi.live_response_api:{"check_in_timeout": 900, "sensor_id": 21212, ... }
    DEBUG:cbapi.connection:HTTP GET /integrationServices/v3/device/21212 took 0.023s (response 200)
    DEBUG:cbapi.connection:Sending HTTP POST /integrationServices/v3/cblr/session/1:21212/command with {"name": "create process", "object": "c:\\windows\\system32\\net.exe start", ... }
    DEBUG:cbapi.connection:HTTP POST /integrationServices/v3/cblr/session/1:21212/command took 0.123s (response 200)
    DEBUG:cbapi.connection:HTTP GET /integrationServices/v3/cblr/session/1:21212/command/0 took 0.062s (response 200)
    INFO:__main__:Received THREAT notification for device_id 21212, enqueuing
    INFO:datastore:Device ID 21212 already inflight
    DEBUG:cbapi.connection:HTTP GET /integrationServices/v3/cblr/session/1:21212/command/0 took 0.053s (response 200)
    ...

