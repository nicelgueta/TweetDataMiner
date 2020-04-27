import os
#dependent config
permittedTweetColumns=['text','user_followers_count','user_location','timestamp_ms','geo','id']

#configs on DB
C = dict(
logCount=0,
totalTweetColumns=['contributors','coordinates','created_at','entities_hashtags','entities_symbols','entities_urls','entities_user_mentions','favorite_count','favorited','filter_level','geo','id','id_str','in_reply_to_screen_name',
'in_reply_to_status_id','in_reply_to_status_id_str','in_reply_to_user_id','in_reply_to_user_id_str','is_quote_status','lang','place','possibly_sensitive','quote_count','reply_count','retweet_count','retweeted','source','text','timestamp_ms',
'truncated','user_contributors_enabled','user_created_at','user_default_profile','user_default_profile_image','user_description','user_favourites_count','user_follow_request_sent','user_followers_count','user_following','user_friends_count','user_geo_enabled',
'user_id','user_id_str','user_is_translator','user_lang','user_listed_count','user_location','user_name','user_notifications','user_profile_background_color','user_profile_background_image_url','user_profile_background_image_url_https','user_profile_background_tile',
'user_profile_banner_url','user_profile_image_url','user_profile_image_url_https','user_profile_link_color','user_profile_sidebar_border_color','user_profile_sidebar_fill_color','user_profile_text_color','user_profile_use_background_image','user_protected',
'user_screen_name','user_statuses_count','user_time_zone','user_translator_type','user_url','user_utc_offset','user_verified'
]
)
# user configurable configs - defaults are in this config
V = dict(
streamLive=False,
collectionToStoreTweets='twoColl',
permittedTweetColumns=permittedTweetColumns,
tweetFiltersDict={col:{'value':None,'operator':'gt'} for col in permittedTweetColumns},
tweetKeywords=['Bitcoin','BTC'] #
)
#not openly on DB configs
X = dict(
appVersion='0.0.1',
LOGS_TO_DB=False,
noOfTweetWorkerThreads=4,
appUrl='https://url.url'
)
