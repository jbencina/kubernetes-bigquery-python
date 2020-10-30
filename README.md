# Overview
This project builds a scalable flow to capture real-time Twitter data using a stack of:
- Google Kubernetes
- Google PubSub
- Google BigQuery (Streaming)
- Google Cloud Build & Container Registry
- Python libraries (Tweepy & Google Cloud SDK)

Originally forked from https://github.com/GoogleCloudPlatform/kubernetes-bigquery-python. This fork adds enhancements to the original Google repo which has not been updated in some time:
- Updated `bigquery-setup/schema.json` to latest available schema found in Twitter API docs
- Moved keyword terms to `twitter-stream.yaml` under the field `TWKEYWORDS` to allow for adjustment without rebuild
- Updated script to use latest Google SDK Python library and avoid oauth2 library issues + Python 3.x

# Instructions
This repo uses a guided bash script for easier setup.

## Prerequisite: Install Google Cloud SDK
Prior to running, ensure that your local instance of Google Cloud SDK is properly configured for your project. https://cloud.google.com/sdk/install. This includes:
- Installing the SDK
- Authenticating to your account
- Adding your project

Additionally, you will need a valid Google Cloud project that is set up with payment information or has an active free trial.
## Prerequisite: Obtain Twitter development API keys
Head over to https://developers.twitter.com and create a new application to obtain the following keys & tokens:
1. API key
2. API secret key
3. Access token
4. Access token secet

Put all 4 items in their own line, in this order, in a file called `twitter.key`. This file will be parsed in sequence by the setup script to populate values.

## Step 1: Using the guided script
The bash script will walk you through each step in an optional approach to create all of the necessary resources on Google Cloud platform. Each step is optional if you already have a resource created.

1. Launch the script using `sh make-environment.sh` and enter your GCP project id. This will update the gcloud sdk for you.
```bash
sh make-environment.sh
GCP Project ID: jbencina-144002
Updated property [core/project].
```

2. Next, you are prompted to create a container image. If you do not already have one, press Y and enter the tag name. This will build and upload to Google Container Registry.
```bash
Build new Google Container Image? (Y/n): y
Image tag: v1
# Lots of output as build progresses. You should see the final line containing something like gcr.io/yourproject-12345/pubsub_bq:v1  SUCCESS
```
3. Next, create a BigQuery dataset & table. This automatically uses the schema specified under `bigquery-setup/schema.json`
```bash
Create Google BigQuery table? (Y/n): Y
BQ Dataset Name: testds
BQ Table Name: testtable
Dataset 'yourproject-12345:testds' successfully created.
Table 'yourproject-12345:testds.testtable' successfully created.
```

4. Next, create the PubSub topic. This will show an error if the topic is new because it will try to delete an existing one under the same name first.
```bash
Create Google PubSub Topic? (Y/n): Y
PubSub Topic Name: mytopic
ERROR: Failed to delete topic [projects/jbencina-144002/topics/mytopic]: Resource not found (resource=mytopic).
ERROR: (gcloud.pubsub.topics.delete) Failed to delete the following: [mytopic].
Created topic [projects/jbencina-144002/topics/mytopic].
```

5. Next, create the Kubernetes cluster by supplying a name. This uses small instances to help minimize cost. 2 nodes is generally fine unless you see some performance impact.
```bash
Create Google Kubernetes Cluster? (Y/n): Y
Cluster Name: test
Number of nodes (2 recommended): 2
# Lots of output. Should show success after 2-3 minutes to start up cluster
```

6. Lastly, the script will create the `bigquery-controller.yaml` and `twitter-stream.yaml` file for you. If you skipped any of the previous steps, you will be prompted for the input. Otherwise, prior entries are recycled.
```bash
Number of PubSub -> BQ Nodes (2 recommended): 1
Keywords to track (Comma separated): test,topic
```
You are now ready to push the flow to kubernetes

## Step 2: Deploy to Kubernetes

Simply run `sh deploy-environment.sh` to upload the data to Kubernetes. You can check the current status on the GCP Cloud Console or by running `kubectl get pods  -o wide` from the CLI. If this takes more than a few minutes, you may have to try deleting the workflows & redeploying or possibly recreating the cluster.

```bash
sh push-environment.sh
deployment.apps/bigquery-controller created
deployment.apps/twitter-stream created
NAME                                   READY   STATUS              RESTARTS   AGE   IP       NODE                                  NOMINATED NODE   READINESS GATES
bigquery-controller-xxx   0/1     ContainerCreating   0          1s    <none>   gke-test-default-pool-xxx  <none>           <none>
twitter-stream-xxx         0/1     ContainerCreating   0          1s    <none>   gke-test-default-pool-xxx   <none>           <none>
```
## Validate results

Assuming all workflows are running you should start seeing new data loading into BigQuery

```bash
bq query 'select COUNT(*) FROM dataset.tablename'

+-------+
|  f0_  |
+-------+
| 16400 |
+-------+
```

# Querying the data

There are a few important caveats to the data collected
1. There are likely duplicate entries in BigQuery. This is because multiple workers may grab the same message. Dedup on Tweet ID
2. Most Tweets are retweets. Filter for unique with `retweeted_status.id IS NULL`
3. Tweets over 140 characters are truncated with `...`. These are typically retweets but some original tweets may also exceed the limit. Use `extended_tweet.full_text` to capture the full tweet.
4. The data has many instances of Unicode

Follow the Twitter API guide for the most detailed field explainations https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/overview/tweet-object

## Sample Query

This is a sample query focusing on the core elements of the data

```sql
SELECT
  created_at,
  id,
  user.name,
  retweeted_status.id IS NOT NULL is_retweet,
  retweeted_status.text AS retweeted_text,
  COALESCE(extended_tweet.full_text, text) AS text
FROM `dataset.tablename`
LIMIT 1000;
```