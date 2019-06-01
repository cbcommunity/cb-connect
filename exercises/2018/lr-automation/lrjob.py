import logging
from tempfile import NamedTemporaryFile
import sqlite3


logger = logging.getLogger(__name__)


def get_context(session):
    try:
        logger.info("Gathering running services")
        running_services = session.create_process("c:\\windows\\system32\\net.exe start")
        logger.info("Gathering running processes")
        running_processes = session.list_processes()
    
        # get the current user
        users = set([proc['username'].split('\\')[-1]
                     for proc in running_processes if proc['path'].find('explorer.exe') != -1])

        browser_history = {}
        for user in users:
            logger.info("Gathering Chrome browser history for %s" % user)
            browser_history[user] = \
                session.get_file("c:\\users\\%s\\appdata\\local\\google\\chrome\\user data\\default\\history" % user)
    
        logger.info("LR done")
    except Exception as e:
        import traceback
    
        traceback.print_exc()
        return None, None
    else:
        return running_services, browser_history


def run_liveresponse(session):
    running_services, browser_history = get_context(session)

    for user in browser_history.keys():
        print("Last 10 URLs accessed by {0}:".format(user))
        with NamedTemporaryFile(delete=False) as tf:
            tf.write(browser_history[user])
            tf.close()
            db = sqlite3.connect(tf.name)
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            cur.execute(
                "SELECT url, title, datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), 'unixepoch') as last_visit_time FROM urls ORDER BY last_visit_time DESC")
            urls = [dict(u) for u in cur.fetchall()]

            for url in urls:
                print("{0} {1} {2}".format(url['last_visit_time'], url['url'], url['title']))

    print(running_services.decode('utf8'))