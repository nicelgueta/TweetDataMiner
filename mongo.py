# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.realpath('./project')) #add the src folder path for better importing
import pymongo
from bson.objectid import ObjectId
from config import C,X
from mongologger import MongoLogger
import pandas as pd
import operator


class BotDB(pymongo.database.Database):
    ''' Main DataBase wrapper for interacting with the MONGODB instance.
    Carries all same methods as mongo db class but with Bot-specfic methods for
    simpler kv retrieval and saving structured tabular data.

    Mandatory collections:
    .kvstore (this is a key value store to persist config changes)
    .logs (to persist logs on the db)

    '''

    def __init__(self):
        # ensure all data points only to the environment-specfic db
        mongo_uri = os.environ['MONGODB_URI']
        client = pymongo.MongoClient(mongo_uri)
        self.dbname = mongo_uri[-15:]
        super(BotDB, self).__init__(client, self.dbname)
        self.log = MongoLogger(objName='DATABASE', db=self, debug=True, logstodb=X['LOGS_TO_DB'])
        self.log.debug('Initialised db wrapper for MONGODB (%s) '%(self.dbname))


    def get_db_stats(self):
        return self.command('dbstats') #returns a dictionary

    def addkv(self, key, value):
        #add key value pair to the kvstore
        if not self.kvstore.find_one({'key': key}):
            return self.kvstore.insert_one({'key': key, 'value': value})
        else:
            print(key + ' already exists - use updatekv method')
            return False

    def getkv(self, key):
        #get value for a given key
        r = self.kvstore.find_one({'key': key})
        if not r:
            self.log.warn('key %s not found in database' % key)
            return False
        else:
            val = r['value']
        return val

    def delkv(self, key):
        #delete key value pair from the kvstore
        return self.kvstore.delete_one({'key': key})

    def updatekv(self, key, value):
        #update key value pair in the kvstore
        r = self.kvstore.update_one({'key': key}, {'$set': {'value': value}})
        return r


    def updatekv_from_config(self,C):
        #C = imported config dictionary
        # updates the kvstore from a given dictionary
        for key in C:
            value = C[key]
            if self.addkv(key,value): #add - returns none if already exists
                self.log.debug('Added new kv: %s=%s'%(key,value))
            else:
                self.updatekv(key,value)
                self.log.debug('Updated kv: %s=%s'%(key,value))
        return True

    def load_collection_as_table(self,collection,filter_criteria=[],as_df=False):

        '''generic method to take a entire collection stored in the db and load as a dataframe or array of dicts
        filter_criteria must be an array of dicts. Filter criteria in this case operates like a query in relational dbs
        Each Dict Format : {'field':'example_field','operator':'example_operator','value':'example_value'}
        eg=> {'field':'timestamp','operator':'gt','value':15028993}

        See operator module for full list of valid operator methods

        '''
        ret = []
        for document in self[collection].find():
            chuck_doc = False
            for filter_c in filter_criteria:
                operator_method = getattr(operator,filter_c['operator'])
                if not operator_method(document['field'],filter_c['value']):
                    chuck_doc = True
                    break
            if chuck_doc:
                continue
            else:
                ret.append(document)
        if as_df:
            return pd.DataFrame.from_records(ret)
        else:
            return ret

    def insert_table_to_collection(self, df, collection):

        '''generic method to save a df as an entire collection stored in the db '''

        dfDict = list(df.T.to_dict().values())
        if not self[collection].insert_many(dfDict):
            print('Error saving %s to database' % collection)
        else:
            return True


    def load_db_table(self, collection, tablename, createIfNew=False):

        '''generic method to take a json stored in the db and load as a dataframe '''

        dbdoc = self[collection].find_one({'docType': 'table', 'name': tablename})
        if not dbdoc and createIfNew:
            self.log.info("%s table doesn't exist it the database - creating from new" % tablename)
            self[collection].insert_one({'docType': 'table', 'name': tablename, 'table': []})
            # return empty frame
            return pd.DataFrame()
        df = pd.DataFrame.from_records(dbdoc['table'])
        return df

    def save_db_table(self, df, collection, tablename):

        '''generic method to take a dataframe and store it in the db as a single json object '''

        dfDict = list(df.T.to_dict().values())
        if not self[collection].update_one({'docType': 'table', 'name': tablename}, {'$set': {'table': dfDict}}):
            print('Error saving %s to database' % tablename)
        return


    def printLogs(self, html=True):
        ''' returns array of strings to print logs in HTML format - returns an array of html formatted strings. non_html parameter to print on terminal'''
        alllogs = self.logs.find()
        # make sure logs print in order
        loglist = [log for log in alllogs]
        lognos = [log['logNo'] for log in loglist]
        maxno = max(lognos)
        minno = min(lognos)
        ordered = []
        i = minno
        while i <= maxno:
            for log in loglist:
                if log['logNo'] == i:
                    ordered.append(log)
            i += 1
        ret = []
        for log in ordered:
            for line in log['logTxt']:
                if not html:
                    ret.append(line + '\n')
                else:
                    ret.append(line + '<br>')
        return ret


#create instance for importing - only one instance is required
DB = BotDB()
