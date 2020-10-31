read -p "GCP Project ID: " PROJECT_ID
gcloud config set project ${PROJECT_ID}

read -p "Build new Google Container Image? (Y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]
then
    read -p "Image tag: " TAG_ID
    gcloud builds submit pubsub/pubsub-pipe-image --tag gcr.io/${PROJECT_ID}/pubsub_bq:${TAG_ID}
fi

read -p "Create Google BigQuery table? (Y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]
then
    read -p "BQ Dataset Name: " BQ_DATASET
    read -p "BQ Table Name: " BQ_TABLE

    bq mk ${BQ_DATASET}
    bq mk -t ${BQ_DATASET}.${BQ_TABLE} bigquery-setup/schema.json
fi

read -p "Create Google PubSub Topic? (Y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]
then
    read -p "PubSub Topic Name: " TOPIC_NAME
    gcloud pubsub topics delete ${TOPIC_NAME}
    gcloud pubsub subscriptions delete tweets-${TOPIC_NAME}
    gcloud pubsub topics create ${TOPIC_NAME}
fi

read -p "Create Google Kubernetes Cluster? (Y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]
then
    read -p "Cluster Name: " CLUSTER_NAME
    read -p "GCP Zone (eg. us-west2-a, us-central1-b, or us-east1-b): " CLUSTER_ZONE
    read -p "Number of nodes (2 recommended): " NUM_NODES
    gcloud beta container --project ${PROJECT_ID} clusters create ${CLUSTER_NAME} --zone ${CLUSTER_ZONE} --no-enable-basic-auth --cluster-version "1.16.13-gke.401" --machine-type "e2-small" --image-type "COS" --disk-type "pd-standard" --disk-size "10" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" --num-nodes ${NUM_NODES} --enable-stackdriver-kubernetes --enable-ip-alias --network "projects/${PROJECT_ID}/global/networks/default" --subnetwork "projects/${PROJECT_ID}/regions/${CLUSTER_ZONE%-*}/subnetworks/default" --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0
    gcloud container clusters get-credentials ${CLUSTER_NAME} -z ${CLUSTER_ZONE}
fi

if [[ -z $BQ_TABLE ]]
then 
    read -p "BQ Dataset Name: " BQ_DATASET
    read -p "BQ Table Name: " BQ_TABLE
fi

if [[ -z $TOPIC_NAME ]]
then 
    read -p "PubSub Topic Name: " TOPIC_NAME
fi

if [[ -z $TAG_ID ]]
then 
    read -p "Image tag: " TAG_ID
fi

read -p "Number of PubSub -> BQ Nodes (2 recommended): " NUM_REPLICA
read -p "Keywords to track (Comma separated): " TW_KEYWORDS
read -p "Languages to track ('en' suggested): " TW_LANGUAGES

sed -e "s/\${bq_table}/${BQ_TABLE}/" -e "s/\${bq_dataset}/${BQ_DATASET}/" -e "s/\${tag_id}/${TAG_ID}/" -e "s/\${num_replica}/${NUM_REPLICA}/" -e "s/\${project_id}/${PROJECT_ID}/" -e "s/\${topic_name}/${TOPIC_NAME}/" pubsub/bigquery-controller-template.yaml > bigquery-controller.yaml

IFS=$'\n' read -d '' -r -a secrets < twitter.key

sed -e "s/\${tag_id}/${TAG_ID}/" -e "s/\${project_id}/${PROJECT_ID}/" -e "s/\${topic_name}/${TOPIC_NAME}/" -e "s/\${tw_key}/${secrets[0]}/" -e "s/\${tw_secret}/${secrets[1]}/" -e "s/\${tw_token}/${secrets[2]}/" -e "s/\${tw_token_sec}/${secrets[3]}/" -e "s/\${tw_keywords}/${TW_KEYWORDS}/" -e "s/\${tw_languages}/${TW_LANGUAGES}/" pubsub/twitter-stream-template.yaml > twitter-stream.yaml