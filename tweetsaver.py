from threading import Thread
import time
import operator
from mongologger import MongoLogger

class TweetSaver(object):
    ''' helper to process a tweet from the tweet queue and place on the db queue '''
    def __init__(self,tweetQueue,db):
        self.db = db
        self.logger = MongoLogger('Tweet Saver', db=db, debug=True)
        self.logger.debug('initialised Tweet Saver')

    def _process_tweets_from_queue(self,tweetQueue,DBqueue):
        while not tweetQueue.empty() or self.db.getkv('streamLive'):
            self.logger.debug('Current of items remaining on the Tweet Queue: %i'%tweetQueue.qsize())
            tweet = tweetQueue.get()
            self.logger.debug('tweet - %s - taken from queue'%tweet['id'])
            if not self.checkNumericalTweetFilters(tweet,self.db.getkv('tweetFiltersDict')):
                self.logger.debug('tweet - %s - failed filter criteria'%tweet['id'])
                pass
            else:
                #save tweet
                self.logger.debug('tweet - %s - passed filter criteria'%tweet['id'])
                self.saveTweet(tweet,DBqueue)

            tweetQueue.task_done()
            self.logger.debug('tweet - %s - marked as complete on queue'%tweet['id'])
        tweetQueue.join()

    def process_tweets_from_queue(self,num_threads,tweetQueue,DBqueue):
        self.logger.debug('creating %i worker threads'%num_threads)
        for i in range(num_threads):
            worker = Thread(target=self._process_tweets_from_queue, args=(tweetQueue,DBqueue))
            worker.setDaemon(True)
            worker.start()
            self.logger.debug('started tweet worker %i '%i)

    def saveTweet(self,tweet,DBqueue):
        #save tweet
        new_tweet = self.trimTweetFields(tweet)
        #add to DB queue for processing to DB
        DBqueue.put(new_tweet)
        self.logger.debug('tweet - %s - placed on db queue'% tweet['id'])

    def checkNumericalTweetFilters(self,tweet,filters_dict):
        ''' filters_dict must be a dictionary with the field name as the key and the value as the filter condition
        for this implementation only > and < are valid filter types
        Returns False if tweet does not match filter criteria else True '''
        ret = True
        for f in filters_dict:
            if not filters_dict[f]['value']:
                continue
            else:
                operator_method = getattr(operator,filters_dict[f]['operator'])
                if not operator_method(tweet[f],filters_dict[f]['value']):
                    self.logger.debug('Tweet found - filtered out because - %s value: %s is not %s %s'%(f,tweet[f],filters_dict[f]['operator'],filters_dict[f]['value']))
                    ret = False
                else:
                    continue
        return ret


    def trimTweetFields(self,tweet):
        ''' removes fields not specified in the config to save space '''
        new_tweet = {}
        permittedTweetColumns = self.db.getkv('permittedTweetColumns')
        # using column iteration instead of append in case some columns are missing
        for col in tweet:
            #check is only what user configed to see
            if col not in permittedTweetColumns:
                continue
            new_tweet[col] = tweet[col]
        return new_tweet
