# Overview
This project builds a scalable flow to capture real-time Twitter data using a stack of:
- Google Kubernetes
- Google PubSub
- Google BigQuery (Streaming)
- Google Cloud Build & Container Registry
- Python libraries (Tweepy & Google Cloud SDK)

Originally forked from https://github.com/GoogleCloudPlatform/kubernetes-bigquery-python. This fork adds enhancements to the original Google repo which has not been updated in some time. It contains an updated schema for the BigQuery table which matches the latest Twitter API and also updates the code to Python 3 with the latest libraries.

# Changes

## Major Changes
- Updated `bigquery-setup/schema.json` to latest available schema found in Twitter API docs (**As of 2019-09-15**)
- Moved keyword terms to `twitter-stream.yaml` under the field `TWKEYWORDS`
- Updated script to use latest Google SDK Python library and avoid oauth2 library issues

## Minor Changes
- Updated code to Python 3
- Removed redis subdirectory
- Removed Google documentation and added this documentation

# Setup Instructions
Prior to running, ensure that your local instance of Google Cloud SDK is properly configured for your project. https://cloud.google.com/sdk/install. This includes:
- Installing the SDK
- Authenticating to your account
- Adding your project

Additionally, you will need a valid Google Cloud project that is set up with payment information or has an active free trial.

## Create the Docker image
This step is needed the first time you run this project as the one available from Google does not contain any of the enhancements in this repository. Choose any version tag you'd like for your project.

```bash
cd pubsub/pubsub-pipe-image
gcloud builds submit --tag gcr.io/[PROJECT_ID]/pubsub_bq:v1
```

## Create a PubSub topic
The PubSub topic will act as a buffer to accept streaming updates from the Twitter API and give us some time to ingest into BigQuery

```bash
gcloud pubsub topics create <your-topic-name>
```

## Create BigQuery table
Create the BigQuery table + dataset using the supplied schema file
```bash
bq mk <your-dataset-name>
bq mk -t <your-dataset-name>.<your-table-name> bigquery-setup/schema.json
```

This repo includes a `bigquery-setup/make_schema.py` file that enables the modular construction of the BigQuery schema file. You can edit the individual JSON files which are combined to build up a master `schema.json` file.

## Updating YAML
1. Edit `twitter-stream.py` to update the Twitter API settings, PubSub topic, Docker image, and tracking keyword.
2. Edit `bigquery-controller.yaml` to update the destination BigQuery settings and Docker image

## Create Kubernetes cluster

Create the Kubernetes cluster using the following template. Don't forget to substitute **[PROJECT_ID]** with your own project ID. Change the region as necessary. You can also create this in the UI.

```bash
gcloud beta container --project "[PROJECT_ID]" clusters create "cluster-debate-clone-1" --zone "us-west1-b" --no-enable-basic-auth --cluster-version "1.15.12-gke.20" --machine-type "e2-medium" --image-type "COS" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" --max-pods-per-node "110" --num-nodes "3" --enable-stackdriver-kubernetes --enable-ip-alias --network "projects/[PROJECT_ID]/global/networks/default" --subnetwork "projects/[PROJECT_ID]/regions/us-west1/subnetworks/default" --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade
```

## Launch the Kubenetes workflow

First register the Kubernetes cluster once live and then submit the two worflow YAML files.

```bash
cd pubsub
gcloud container clusters get-credentials [CLUSTER_NAME]
kubectl create -f bigquery-controller.yaml
kubectl create -f twitter-stream.yaml
```
Monitor the status of your pods via the Google Cloud Kubernetes UI or by typing
```
kubectl get pods  -o wide
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