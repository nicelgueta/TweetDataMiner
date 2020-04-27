from flask import Flask, redirect
from flask.json import jsonify
from mongologger import MongoLogger
from mongo import DB
from queues import TweetQueue,DBQueue
from tweetsaver import TweetSaver
from tweetlistener import TweetListener
from threading import Thread
from db_queue_worker import save_from_queue_to_db_table
import time
from config import X
import datetime
import requests

import logging
logging.basicConfig(level=logging.DEBUG)

class MiningBot(object):

    def __init__(self):
        self.logger = MongoLogger('MiningBot',DB, debug=True)
        self.q = TweetQueue()
        self.listener = TweetListener(DB,self.q)
        self.saver = TweetSaver(self.q,DB)
        self.dbq = DBQueue()

    def listenForCommand(self):
        while not DB.getkv('streamLive'):
            self.logger.debug('Currently sleeping. Awaiting command to initiate %s'%datetime.datetime.fromtimestamp(time.time()))
            time.sleep(5)
            #keep alive to stop Heroku putting us to sleep
            requests.get(X['appUrl']+'keepalive')
        else:
            self.logger.debug('streamLive set to TRUE - Bot Initiating')
            self.startBot()
            #keep hanging to prevent creating infinite instances
            while DB.getkv('streamLive'):
                time.sleep(5)
                #keep alive to stop Heroku putting us to sleep
                requests.get(X['appUrl']+'keepalive')
            else:
                self.logger.debug('streamLive set to FALSE - Bot shutting down')
                self.listenForCommand()

    def startBot(self):
        #run necessary threads
        self.s1 = Thread(target=self.saver.process_tweets_from_queue,args=(4,self.q,self.dbq))
        self.s1.start()
        self.l1 = Thread(target=self.listener.listenTweets,args=(DB.getkv('tweetKeywords'),))
        self.l1.start()
        time.sleep(10)
        self.d1 = Thread(target=save_from_queue_to_db_table,args=(self.dbq,DB,DB.getkv('collectionToStoreTweets')))
        self.d1.start()


#API defs
class MainApp(Flask):
    ''' class wrapper to automatically start the Miner Bot '''
    def __init__(self,name='MiningBotApp'):
        super(MainApp,self).__init__(name)
        self.miner = MiningBot()
        bot = Thread(target=self.miner.listenForCommand)
        bot.start()

app = MainApp()

@app.route('/keepalive')
def keepalive():
    return jsonify({'currentTime':datetime.datetime.fromtimestamp(time.time())})

@app.route('/')
def index():
    status = 'Off' if not DB.getkv('streamLive') else 'Currently Running'
    return '''
        <title>Mining Bot</title>
        <h1>Mining Bot Homepage</h1>
        <body>
            <p>The bot runs in the background, all interactions should be through the local console...</p>
            <br><br>
            <p>Happy Mining!</p>
            <br>
            <p>Current Status: '''+status+'''</p>
        </body>
        '''

if __name__ == '__main__':
    app.run()
