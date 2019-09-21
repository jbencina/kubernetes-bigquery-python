#!/usr/bin/env python
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

import json

def create_schema():
    """Creates BigQuery schema by assembling entities represented in JSON"""
    mappings = {}

    # Load the base entities from JSON
    for e in ['tweet', 'user', 'entities', 'extended_entities', 'extended_tweet']:
        with open('{}.json'.format(e), 'r') as f:
            mappings[e] = json.load(f)

    # Append the sub entities to the Tweet entity
    for e in ['user', 'entities', 'extended_entities']:
        mappings['tweet'].append(mappings[e])
        
    base_tweet = mappings['tweet'][:]

    # Retweets and quotes are full Tweet objects but do not recursively
    # contain themselves
    for e in ['retweeted_status', 'quoted_status']:
        ent = {
            'name': e,
            'type': 'RECORD',
            'mode': 'NULLABLE',
            'fields': base_tweet
        }
        mappings['tweet'].append(ent)

    # Build the extended_tweet object
    mappings['extended_tweet']['fields'].append(mappings['entities'])
    mappings['extended_tweet']['fields'].append(mappings['extended_entities'])
    mappings['tweet'].append(mappings['extended_tweet'])
        
    # Save the file as a BQ schema file
    with open('schema.json', 'w') as f:
        f.write(json.dumps(mappings['tweet'], indent=2))

if __name__ == '__main__':
    create_schema()