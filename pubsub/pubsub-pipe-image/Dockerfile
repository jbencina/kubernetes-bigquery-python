FROM python:3

RUN pip3 install --upgrade pip
RUN pip3 install tweepy==3.9.0
RUN pip3 install --upgrade google-api-python-client==1.12.5
RUN pip3 install --upgrade google-cloud-pubsub==2.1.0
RUN pip3 install --upgrade google-cloud-bigquery==2.2.0
RUN pip3 install python-dateutil

ADD twitter_to_pubsub.py /twitter_to_pubsub.py
ADD pubsub_to_bigquery.py /pubsub_to_bigquery.py
ADD controller.py /controller.py
ADD utils.py /utils.py

CMD python3 controller.py
