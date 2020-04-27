# -*- coding: utf-8 -*-
import time
import numpy
def save_from_queue_to_db_table(DBqueue,db,collection):
    ''' processes 50 items and saves them to the DB. Doing it every 50 items in case  of dyno outage '''
    db.log.debug('started db queue worker')
    time.sleep(3)
    while True:
        db.log.debug('DBqueue size: %i'%DBqueue.qsize())
        while not DBqueue.empty():
            item_to_save = DBqueue.get()
            #encoding bug
            for key in item_to_save:
                if isinstance(item_to_save[key], numpy.generic):
                    item_to_save[key] = numpy.asscalar(item_to_save[key])
            db.log.debug('db queue worker processing item id: %s'%item_to_save['id'])
            try:
                db.log.debug(str(item_to_save['id'])+' - Object to save- '+str(item_to_save))
            except UnicodeEncodeError:
                db.log.debug('UNICODE ENCODE ERROR - ABANDONING TWEET')
                break
            db[collection].insert_one(item_to_save)
            db.log.debug(str(item_to_save['id'])+' - sucessfully saved')
        else:
            db.log.debug('DBqueue size: %i'%DBqueue.qsize())
            db.log.debug('DBqueue empty')
            time.sleep(1)
        if not db.getkv('streamLive'):
            db.log.debug('Stream is off - db worker will close')
            break
    db.log.debug('db worker completed')
