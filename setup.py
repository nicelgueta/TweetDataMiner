
from config import C,V,X
from pprint import pprint
import pandas as pd
from subprocess import Popen
import os
import sys

''' SETUP SCRIPT - THIS IS USED TO SETUP A HEROKU INSTANCE TO RUN A TWITTER MINER

'''

def first_run(db,true_first=False):
    ''' set up the Bot from new - whole DB is wiped and replaced with new data

    '''
    #set up core attributes from the config file
    for collection in db.collection_names():
        pprint(db.command('collstats',collection))
    if not true_first:
        c = input('\n\nWARNING - process will wipe the existing database (%s)\nEnter "Y" if you wish to proceed else cancel: '% (db.dbname))
        if c.lower() == 'y':
            pass
        else:
            print('Exiting..')
            return
    assert setup_core_attributes(db,C,V)
    print('Database setup completed')
    return


def setup_core_attributes(db,C,V):
    ''' function used only once when setting up the Bot for the first time
    Resets entire key-value store and pulls new kvs from supplied config file
    Only adds core data - kvstore'''
    #reset db
    print('Dropping all existing collections')
    for collection in db.collection_names(include_system_collections=False):
        db.drop_collection(collection)
    #add new config values - only for user configs - system configs must require a release
    print('Adding reference kvstore configurations')
    for key in C:
        value = C[key]
        print('%s:%s'%(key,value))
        db.addkv(key,value)
    print('Adding user-configurable kvstore configurations')
    for key in V:
        value = V[key]
        print('%s:%s'%(key,value))
        db.addkv(key,value)
    print('success')
    return True

def update_core_attributes(db,C,V,overwrite=False):
    ''' used to update KVs that don't already exist '''
    existing_k = [doc['key'] for doc in db.kvstore.find()]
    print('Updating reference kvstore configurations')
    for key in C:
        if not overwrite:
            if key in existing_k:
                continue
        value = C[key]
        print('%s:%s'%(key,value))
        if not db.addkv(key,value):
            db.updatekv(key,value)
    print('Updating user-configurable kvstore configurations')
    for key in V:
        if not overwrite:
            if key in existing_k:
                continue
        value = V[key]
        print('%s:%s'%(key,value))
        if not db.addkv(key,value):
            db.updatekv(key,value)

def check_y_n(question):
    a = input(question)
    if a not in ['y','Y','n','N']:
        print('not valid response - try again..')
        check_y_n(question)
    else:
        if a in ['Y','y']:
            return True
        else:
            return False
def check_valid(question,responses):
    a = input(question+' %s'%responses)
    if a not in responses:
        print('not valid response - try again..')
        check_valid(question,responses)
    else:
        return a
def main(no_prompt=False):
    print('Running application environment and database setup..')
    print('_'*30)
    if no_prompt:
        create_env_bat()
        from mongo import DB
        first_run(DB,true_first=True)
        print('Setup script completed')
        return
    if check_y_n('\nSet HEROKU environment variables? (any existing variables will be overwritten) (y/n) '):
        batchfile = 'heroku_env_setup.bat'
        if y:
            run_bat(batchfile)

    if check_y_n('\nStart full DB setup? (NB> anything in the existing db will be wiped) (y/n)'):
        first_run(db)
        print('Setup script completed')
        return
    if check_y_n('\nUpdate DB kvstore? (y/n)'):
        update_core_attributes(db,C,V)

    print('Setup script completed')

def create_env_bat():
    appname = input('Enter name of Heroku app to use: ')
    print('-'*20+'\n'+'Twitter security keys will be safely stored as heroku config variables to avoid storing them in any open file \n\n')
    TWITTER_CONSUMER_KEY = input('Paste TWITTER_CONSUMER_KEY: ')
    TWITTER_CONSUMER_SECRET = input('Paste TWITTER_CONSUMER_SECRET: ')
    TWITTER_ACCESS_TOKEN = input('Paste TWITTER_ACCESS_TOKEN: ')
    TWITTER_ACCESS_TOKEN_SECRET = input('Paste TWITTER_ACCESS_TOKEN_SECRET: ')
    ist_str = ('@ECHO OFF\n'+
    'ECHO Creating MONGO DB Instance for %s\n'%appname+
    'heroku addons:create mongolab:sandbox -a %s\n'%appname+
    'ECHO Setting Heroku Environment variables\n'+
    'heroku config:set TWITTER_CONSUMER_KEY=%s -a %s\n'%(TWITTER_CONSUMER_KEY,appname)+
    'heroku config:set TWITTER_CONSUMER_SECRET=%s -a %s\n'%(TWITTER_CONSUMER_SECRET,appname)+
    'heroku config:set TWITTER_ACCESS_TOKEN=%s -a %s\n'%(TWITTER_ACCESS_TOKEN,appname)+
    'heroku config:set TWITTER_ACCESS_TOKEN_SECRET=%s -a %s\n'%(TWITTER_ACCESS_TOKEN_SECRET,appname)+
    'heroku config:get MONGODB_URI > temp.txt\n'+
    'ECHO HEROKU ENVIRONMENT SETUP COMPLETED\n'+
    'ECHO The Mining Bot is now ready to be deployed to the Heroku platform\n'+
    'pause\n'+
    'ECHO Deploying Application to HEROKU cloud\n'+
    'git init\n'+
    'heroku git:remote -a %s\n'%appname+
    'git add .\n'+
    'git commit -m "Deployment to heroku cloud using setup"\n'+
    'git push heroku master\n')
    with open('temp.bat','w') as f:
        f.write(ist_str)
        f.close()
    run_bat('temp.bat')
    #get MONGO URI
    with open('temp.txt','r') as f:
        mongo_uri = f.readline().rstrip('\n')
        os.environ['MONGODB_URI'] = mongo_uri
    ist_str = ('@ECHO OFF\n'+
    'ECHO Setting Mongo URI to local environment variable to enable console DB connection to %s\n'%appname+
    'ECHO setx MONGODB_URI %s\n'%mongo_uri+
    'ECHO set MONGODB_URI=%s\n'%mongo_uri+
    'ECHO Completed\n'+
    'ECHO Cleaning up temp files...'
    )
    with open('temp.bat','w') as f:
        f.write(ist_str)
        f.close()
    run_bat('temp.bat')
    #clean up
    os.remove('temp.bat')
    os.remove('temp.txt')



def run_bat(batchfile):
    p = Popen(batchfile, cwd=os.getcwd())
    stdout, stderr = p.communicate()

if __name__ == '__main__':
    no_prompt=True if sys.argv[1] == '-nope' else False
    main(no_prompt)
