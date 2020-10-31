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

"""This file contains some utilities used for processing tweet data and writing
data to BigQuery
"""

import collections
import datetime
import time
import logging

import dateutil.parser
from google.cloud import bigquery, pubsub

NUM_RETRIES = 3

def create_bigquery_client():
    """Build the bigquery client."""
    return bigquery.Client()

def create_pubsub_publisher_client():
    """Build the pubsub client."""
    return pubsub.PublisherClient()

def create_pubsub_subscriber_client():
    """Build the pubsub subscriber client."""
    return pubsub.SubscriberClient()

def flatten(lst):
    """Helper function used to massage the raw tweet data."""
    for el in lst:
        if (isinstance(el, collections.Iterable) and
                not isinstance(el, str)):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def cleanup(data):
    """Do some data massaging."""
    if isinstance(data, dict):
        newdict = {}
        for k, v in data.items():
            if (k == 'coordinates') and isinstance(v, list):
                # flatten list
                newdict[k] = list(flatten(v))
            elif k == 'created_at' and v:
                newdict[k] = str(dateutil.parser.parse(v))
            elif v is False:
                newdict[k] = v
            else:
                if k and v:
                    newdict[k] = cleanup(v)
        return newdict
    elif isinstance(data, list):
        newlist = []
        for item in data:
            newdata = cleanup(item)
            if newdata:
                newlist.append(newdata)
        return newlist
    else:
        return data

def bq_data_insert(bq_client, project_id, dataset, table, tweets):
    """Insert a list of tweets into the given BigQuery table."""
    try:
        table_ref = bigquery.TableReference.from_string(
            table_id='{}.{}'.format(dataset, table),
            default_project=project_id
        )

        logging.info(f'BigQuery: Inserting {len(tweets)} records')
        # Try the insertion.
        response = bq_client.insert_rows_json(
            table=table_ref,
            json_rows=tweets,
            ignore_unknown_values=True,
            skip_invalid_rows=True
        )

        if response != []:
            logging.info(f'BigQuery: Insert Error - {response}')

        return response
    except Exception as e1:
        logging.error(f'BigQuery: General Error - {e1}')
