# Overview
This project builds a scalable flow to capture real-time Twitter data using a stack of:
- Google Kubernetes
- Google PubSub
- Google BigQuery
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

# Instructions
Prior to running, ensure that your local instance of Google Cloud SDK is properly configured for your project. https://cloud.google.com/sdk/install. This includes:
- Installing the SDK
- Authenticating to your account
- Adding your project

Additionally, you will need a valid Google Cloud project that is set up with payment information or has an active free trial.

## Building Docker image
This step is needed the first time you run this project as the one available from Google does not contain any of the enhancements in this repository.
1. Navigate to `pubsub/pubsub-pipe-image`
2. Run the command below to initiate the Google Cloud Build process for the Docker image which will run in Kubernetes. Increment the version number if future modifications are performed which require a new build
```
gcloud builds submit --tag gcr.io/[PROJECT_ID]/pubsub_bq:v1 .
```

## Create a PubSub topic
The PubSub topic will act as a buffer to accept streaming updates from the Twitter API and give us some time to ingest into BigQuery
```
gcloud pubsub topics create <your-topic-name>
```

## Create BigQuery table
1. Create the BigQuery dataset if it does not already exist
```
bq mk <your-dataset-name>
```
2. Create the BigQuery table using the schema file
```
bq mk -t <your-dataset-name>.<your-table-name> bigquery-setup/schema.json
```
This repo includes a `bigquery-setup/make_schema.py` file that enables the modular construction of the BigQuery schema file. The Twitter API contains some recursive elements where objects like retweeted_status contain the entire Tweet object again. This makes working on a single schema file confusing and error prone. Instead, you can edit the individual JSON files which are combined to build up a master `schema.json` file.

## Updating YAML
1. Edit `twitter-stream.py` to update the Twitter API settings, PubSub topic, and tracking keyword.
2. Edit `bigquery-controller.yaml` to update the destination BigQuery settings

In both steps, ensure you've supplied the updated image path from the prior step. You can increase the number of BigQuery replicas as needed but do not add more than one twitter-stream pod.

## Launching Pods
1. Run the following to create a Kubernetes cluster to run the application. This cluster will have API access to PubSub and BigQuery. Substitute your project ID below. If you've added more than one replica for each of the pods, increase the total cluster size here.
```
gcloud beta container --project "[PROJECT_ID]" clusters create "standard-cluster-1" --zone "us-east1-b" --no-enable-basic-auth --cluster-version "1.13.7-gke.8" --machine-type "n1-standard-1" --image-type "COS" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/bigquery","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/pubsub","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --num-nodes "2" --enable-cloud-logging --enable-cloud-monitoring --enable-ip-alias --network "projects/[PROJECT_ID]/global/networks/default" --subnetwork "projects/[PROJECT_ID]/regions/us-east1/subnetworks/default" --default-max-pods-per-node "110" --addons HorizontalPodAutoscaling,HttpLoadBalancing --enable-autoupgrade --enable-autorepair
```

2. Launch the pods
```
kubectl create -f bigquery-controller.yaml
kubectl create -f twitter-stream.yaml
```
3. Monitor the status of your pods via the Google Cloud Kubernetes UI or by typing
```
kubectl get pods  -o wide
```