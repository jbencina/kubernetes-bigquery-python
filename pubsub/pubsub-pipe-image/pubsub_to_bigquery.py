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
"""This script grabs tweets from a PubSub topic, and stores them in BiqQuery
using the BigQuery Streaming API.
"""

import base64
import datetime
import json
import os
import time

import utils

from google.api_core.exceptions import AlreadyExists
# Get the project ID and pubsub topic from the environment variables set in
# the 'bigquery-controller.yaml' manifest.
PROJECT_ID = os.environ['PROJECT_ID']
PUBSUB_TOPIC = os.environ['PUBSUB_TOPIC']
NUM_RETRIES = 3

def create_subscription(pubsub_sub, project_name, sub_name):
    """Creates a new subscription to a given topic."""
    print("using pubsub topic: {}".format(PUBSUB_TOPIC))
    path = pubsub_sub.subscription_path(project_name, sub_name)
    pubsub_sub.create_subscription(path, PUBSUB_TOPIC)

def pull_messages(pubsub_sub, project_name, sub_name):
    """Pulls messages from a given subscription."""
    BATCH_SIZE = 50
    subscription_path = pubsub_sub.subscription_path(project_name, sub_name)
    tweets = []

    try:
        resp = pubsub_sub.pull(subscription_path, max_messages=BATCH_SIZE)
    except Exception as e:
        print("Exception: {}".format(e))
        time.sleep(0.5)
        return

    receivedMessages = resp.received_messages
    if len(receivedMessages) > 0:
        ack_ids = []
        for msg in receivedMessages:
            tweets.append(
                base64.urlsafe_b64decode(msg.message.data)
            )
            ack_ids.append(msg.ack_id)
        pubsub_sub.acknowledge(subscription_path, ack_ids)
    return tweets

def write_to_bq(pubsub_sub, pubsub_pub, sub_name, bigquery):
    """Write the data to BigQuery in small chunks."""
    tweets = []
    CHUNK = 50 # The size of the BigQuery insertion batch.
    WAIT = 2 # Sleep time in seconds if no data

    while 1 > 0:
        while len(tweets) < CHUNK:
            twmessages = pull_messages(pubsub_sub, PROJECT_ID, sub_name)
            if twmessages:
                for res in twmessages:
                    try:
                        tweet = json.loads(res, encoding='utf8')
                    except Exception as bqe:
                        print(bqe)
                    
                    mtweet = utils.cleanup(tweet)
                    tweets.append(mtweet)
            else:
                print('sleeping...')
                time.sleep(WAIT)

        utils.bq_data_insert(bigquery, PROJECT_ID, os.environ['BQ_DATASET'],
                                os.environ['BQ_TABLE'], tweets)
        
        tweets = []

if __name__ == '__main__':
    topic_info = PUBSUB_TOPIC.split('/')
    topic_name = topic_info[-1]
    sub_name = "tweets-%s" % topic_name
    print("starting write to BigQuery....")

    bigquery = utils.create_bigquery_client()
    pubsub_pub = utils.create_pubsub_publisher_client()
    pubsub_sub = utils.create_pubsub_subscriber_client()
    try:
        create_subscription(pubsub_sub, PROJECT_ID, sub_name)
    except AlreadyExists:
        print('Subscription already exists')
    except Exception as e:
        print(e)
    write_to_bq(pubsub_sub, pubsub_pub, sub_name, bigquery)
    print('exited write loop')
