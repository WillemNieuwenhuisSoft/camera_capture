import logging

logging.basicConfig(
    filename='camera_capture.log',
    filemode='a',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
logFormatter = logging.Formatter(
    "[%(levelname)s]  %(message)s")
logFormatter.datefmt = "%Y-%m-%d %H:%M:%S"
ch = logging.StreamHandler()
ch.setFormatter(logFormatter)
ch.setLevel(logging.INFO)
log.addHandler(ch)
