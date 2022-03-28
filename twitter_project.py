import requests
import os
import json
from dotenv import load_dotenv

#export 'BEARER_TOKEN'='<your_bearer_token>' >>> initially tried that syntax but didn't work, variables returned none
load_dotenv()  # take environment variables from .env.

bearer_token = os.environ.get("BEARER_TOKEN")
qb_user_token = os.environ.get("QB_USER_TOKEN")

#get request arguments query_params, headers and search_url
query_params = {
    'query': '#QuickBase OR #NoCode OR #LowCode OR #QBCommunitySummit',
    # https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference 
    'tweet.fields':'author_id,created_at,entities',
    # https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by-username-username
    'expansions':'author_id',
    'user.fields': 'username,id',
    #Twitter pagination from 10 to 100
    'max_results': 100,
}

# 2 endpoints available, "all" and "recent". All is only available for academic and research. I only have access to recent which gives me the most recent 7 days
# https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-all
# https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
search_url = "https://api.twitter.com/2/tweets/search/recent"

headers = {
    "Authorization": f"Bearer {bearer_token}"
}

#token to request the next page due to Twitter API pagination >> max 100/page min 10/page
#https://developer.twitter.com/en/docs/twitter-api/pagination
next_token = None

#dictionary to map userids to usernames
users = {}

#list of tweets
tweets = []

for i in range(5): #looping to get X number of tweets (more than 100)
    
    # next_token only used starting the second request 
    if i > 0:
        query_params['next_token'] = next_token
    
    # sending get request to twitter API
    response = requests.get(search_url, headers=headers, params=query_params)
    page = response.json()
    next_token = page['meta']['next_token']
    
    # upserting usernames to users dictionary
    for user in page['includes']['users']:
        userid = user['id']
        username = user['username']
        users[userid] = username
        
    # Reshaping the twitter data with the proper formatting for the Quickbase API
    for tweet in page['data']:
        tweet_id = tweet['id']
        tweet_text = tweet['text']
        tweet_created_at = tweet['created_at']
        tweet_author_id = tweet['author_id']
        
        #extracting tags and exception handling for when no hashtags are returned >> get 'hashtags', [] otherwise 
        tweet_hashtags = [hashtag['tag'] for hashtag in tweet['entities'].get('hashtags', [])]
        
        #twitter strips data after 140th character. resulting in incomplete records (in some cases not including the tags we're looking for),
        #although the original tweet includes the hashtags, hence them showing in the response in the first place!
        
        #filtering out records that don't include the tags in the response
        if "nocode" in tweet_hashtags or 'QuickBase' in tweet_hashtags or 'LowCode' in tweet_hashtags or'QBCommunitySummit' in tweet_hashtags:
            tweets.append({
                
                #'record ID#'
                '10': { #'11' for the copy of tweets table in QB
                    "value": tweet_id
                },
                
                #'Hashtags'
                '6': {
                    "value": tweet_hashtags
                },
                
                #'Twitter_Username'
                '7':{
                    "value": users.get(tweet_author_id, None)
                },
                
                #'Tweet_Content'
                '8': {
                    "value":tweet_text
                },
                
                #'Date'
                '9':{
                    "value": tweet_created_at.split("T")[0] # for date field in QB
                    #"value": tweet_created_at for date/time field in QB
                },
            })

body = {
    #"to": "br9e6snt2", #copy of tweets table in QB
    "to": "br9btjupe",
    "data": tweets,
}

qb_headers = {
    'QB-Realm-Hostname': 'team.quickbase.com',
    #same thing here, storing it here while working on the assignment..
    'Authorization': f'QB-USER-TOKEN {qb_user_token}'
}

r = requests.post(
        'https://api.quickbase.com/v1/records', 
        headers = qb_headers, 
        json = body
    )

upload = r.json()
upload



