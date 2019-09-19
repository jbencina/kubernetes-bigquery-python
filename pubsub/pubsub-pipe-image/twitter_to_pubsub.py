#!/usr/bin/env python
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This script uses the Twitter Streaming API, via the tweepy library,
to pull in tweets and publish them to a PubSub topic.
"""

import base64
import datetime
import os
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

import utils

# Get your twitter credentials from the environment variables.
# These are set in the 'twitter-stream.json' manifest file.
consumer_key = os.environ['CONSUMERKEY']
consumer_secret = os.environ['CONSUMERSECRET']
access_token = os.environ['ACCESSTOKEN']
access_token_secret = os.environ['ACCESSTOKENSEC']

PUBSUB_TOPIC = os.environ['PUBSUB_TOPIC']
NUM_RETRIES = 3

def publish(pubsub_pub, pubsub_topic, data_lines):
    """Publish to the given pubsub topic."""
    for line in data_lines:
        pub = base64.urlsafe_b64encode(line.encode('utf-8'))
        pubsub_pub.publish(pubsub_topic, pub)

class StdOutListener(StreamListener):
    """A listener handles tweets that are received from the stream.
    This listener dumps the tweets into a PubSub topic
    """
    count = 0
    twstring = ''
    tweets = []
    batch_size = 50
    pubsub_pub = utils.create_pubsub_publisher_client()

    def write_to_pubsub(self, tw):
        publish(self.pubsub_pub, PUBSUB_TOPIC, tw)

    def on_data(self, data):
        """What to do when tweet data is received."""
        self.tweets.append(data)
        if len(self.tweets) >= self.batch_size:
            self.write_to_pubsub(self.tweets)
            self.tweets = []
        self.count += 1

        if (self.count % 1000) == 0:
            print('count is: {} at {}'.format(
                self.count, datetime.datetime.now())
            )
        return True

    def on_error(self, status):
        print(status)

if __name__ == '__main__':
    print('....')
    listener = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, listener)

    keywords = [s.strip() for s in os.environ['TWKEYWORDS'].split(',')]
    languages = os.environ['TWKEYWORDS']
    stream.filter(track=keywords, languages=languages)
