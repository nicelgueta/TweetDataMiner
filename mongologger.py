import time
import datetime

def readabledate(unixdate):
    date =  datetime.datetime.fromtimestamp(float(unixdate)).strftime('%Y-%m-%d %H:%M:%S:%f')
    return date

class MongoLogger(object):
    ''' very basic logger to send logs to a mongo db and print to stdout
    debug level is just printed to the console. Info, warning and critical is
    both saved to the .logs collection (if LOGS_TO_DB=True) in the mongo db and printed to console
    '''

    def __init__(self, objName, db, debug=False, logstodb=False):
        if type(logstodb) != bool:
            raise TypeError('logstodb not recognised as Boolean')
        self._db = db
        self.logdb = db.logs
        self._debug = debug
        if logstodb:
            self.logCount = int(db.getkv('logCount'))
        else:
            self.logCount = 0
        self.logObj = objName
        self.logstodb = logstodb

    def _addLogStr(self, string):
        query = {'logNo': self.logCount}
        logdoc = self.logdb.find_one(query)
        logarr = logdoc['logTxt']
        logarr.append(string)
        self.logdb.update_one(query, {'$set': {'logTxt': logarr}})

    def _write(self, message, level, only_print=False):
        msg = '[%s - %s - %s] - %s' % (self.logObj, readabledate(time.time()), level, message)
        print(msg)
        if not only_print:
            if self.logstodb:
                if self._isNewLog():
                    self._addNewLog()
                self._addLogStr(msg)

    def warn(self, message):
        level = 'WARNING'
        self._write(message, level)

    def info(self, message):
        level = 'INFO'
        self._write(message, level)

    def debug(self, message):
        if self._debug:
            level = 'DEBUG'
            self._write(message, level, only_print=True)

    def critical(self, message, exception_traceback=False):
        level = 'CRITICAL'
        self._write(message, level)
        if exception_traceback:
            exception_traceback = exception_traceback.replace('\n', '<br>')
            self._write(message=exception_traceback, level=level)
        # raise BittrexApiError(message)

    def _isNewLog(self):
        query = {'logNo': self.logCount}
        logdoc = self.logdb.find_one(query)
        if not logdoc:  # no log found
            return True
        if logdoc['dateCreatedTimestamp'] < (time.time() - 18000):  # less than 5 hours previous
            return True
        else:
            return False

    def _addNewLog(self):
        self.logCount += 1
        self._db.updatekv('logCount', self.logCount)  # records the log count in the kv
        logdoc = {'logNo': self.logCount, 'logTxt': [], 'dateCreated': readabledate(time.time()), 'dateCreatedTimestamp': time.time()}
        self.logdb.insert_one(logdoc)
