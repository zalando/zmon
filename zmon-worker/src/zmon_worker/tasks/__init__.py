
import logging

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('celery.worker.job').setLevel(logging.DEBUG)
