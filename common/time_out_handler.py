import signal


def handler(signum, frame):
     print 'timeout'
     exit()
