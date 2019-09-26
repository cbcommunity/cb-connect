from flask import Flask, render_template
from tempfile import NamedTemporaryFile
import sqlite3
import threading
from six.moves.urllib.parse import urlsplit, urlunsplit
import os


def get_flask_server(datastore):
    current_path = os.path.dirname(os.path.abspath(__file__))
    flask_server = Flask('liveresponse', template_folder=os.path.join(current_path, "templates"))

    @flask_server.route('/', methods=['GET', 'POST'])
    def index():
        return render_template("index.html", sensors=datastore.devices_available())

    @flask_server.route('/sensor_result/<device_id>')
    def sensor_result(device_id):
        device_id = int(device_id)
        results = datastore.get_result(device_id)
        return render_template('sensor_result.html', results=results, sensor_id=device_id)

    @flask_server.route('/browser_history/<device_id>')
    def browser_history(device_id):
        device_id = int(device_id)
        results = datastore.get_result(device_id)
        if 'browser_history' in results and len(results["browser_history"].keys()) > 0:
            user = list(results["browser_history"])[0] # pick the first user
            browser_history = results["browser_history"][user]
            with NamedTemporaryFile(delete=False) as tf:
                tf.write(browser_history)
                tf.close()
                db = sqlite3.connect(tf.name)
                db.row_factory = sqlite3.Row
                cur = db.cursor()
                cur.execute("""SELECT url, title,
                               datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), 'unixepoch') as last_visit_time
                               FROM urls ORDER BY last_visit_time DESC""")
                urls = [dict(u) for u in cur.fetchall()]

                for url in urls:
                    (scheme, netloc, _, _, _) = urlsplit(url["url"])
                    url["favicon"] = urlunsplit((scheme, netloc, "favicon.ico", "", ""))

                return render_template('browser_history.html', urls=urls)

        return render_template('no_such_result.html')

    t = threading.Thread(target=flask_server.run, args=['0.0.0.0', 7982])
    t.daemon = True
    return t
