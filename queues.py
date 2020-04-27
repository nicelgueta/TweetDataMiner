
from queue import Queue

class TweetQueue(Queue):
    ''' queue that the listener places tweets onto '''
    pass

class DBQueue(Queue):
    ''' queue that the saver places savable tweets onto for the DB listener to pick up'''
    pass
