#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
from mongo import DB
from tweepy import OAuthHandler
from tweepy import StreamListener, Stream
from config import X
from mongologger import MongoLogger
import json
from pandas.io.json import json_normalize
import datetime
import tweepy
import os
import unicodedata


#Variables that contains the user credentials to access Twitter API
consumer_key = os.environ['TWITTER_CONSUMER_KEY']
consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
access_token = os.environ['TWITTER_ACCESS_TOKEN']
access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']


class TweetListener(StreamListener):
    ''' main listener that will subscribe to twitter and place any relevant tweets on the queue for processing '''
    def  __init__(self,db,Q):
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.stream = Stream(auth, self)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        self._currentTableName = None
        self.db = db
        self.logger = MongoLogger('TweetListener',DB, debug=True)
        self.logger.debug('initialised TweetListener')
        self.Q = Q

    def on_data(self, data):
        tweet = json.loads(data)
        try:
            self.logger.debug('detected tweet - %s'%(tweet['id']))
        except KeyError:
            #abandon saving as not a real tweet- twitter api returned an error
            print(tweet)
            time.sleep(0.2)
            return True
        tweet = self.flatten_tweet(tweet)
        self.Q.put(tweet)
        self.logger.debug('Tweet - %s - placed on queue'%(tweet['id']))
        keep_streaming = self.db.getkv('streamLive') #boolean
        if not keep_streaming:
            self.logger.info('Live stream config is set to False - disconnecting from stream')
        return keep_streaming

    def on_error(self, status):
        print (status)

    def flatten_tweet(self,tweet):
        #normalise to flat structure
        tweet['text'] = unicodedata.normalize('NFKD', tweet['text']).encode('ascii','ignore')
        tweet = json_normalize(tweet)
        #swap point for underscore so can save to db as dictionary
        self.logger.debug('reformatting')
        tweet = {field.replace('.','_'):tweet[field][0] for field in tweet.columns}
        return tweet


    def listenTweets(self,keywords=[],people=[]):
        self.stream.filter(track=keywords,languages = ["en"])

    def searchTweets(self,querystr):
        cursor = tweepy.Cursor(self.api.search,q=querystr,lang="en",since="2018-04-01")
        for tweet in cursor.items():
            tweet = json.loads(json.dumps(tweet._json))
            tweet = self.flatten_tweet(tweet)
            self.Q.put(tweet)
            self.logger.debug('Tweet - %s - placed on queue'%(tweet['id']))
            keep_streaming = self.db.getkv('streamLive') #boolean
            if not keep_streaming:
                self.logger.info('Live stream config is set to False - disconnecting')
            return keep_streaming
        self.logger.debug('Search Complete')

if __name__ == '__main__':
    #main()
    main()
