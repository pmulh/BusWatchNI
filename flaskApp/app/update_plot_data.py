import pandas as pd
import os
from google.cloud import storage

# Set up google cloud stuff (requires environment variable GOOGLE_APPLICATION_CREDENTIALS
# to have been set - see https://cloud.google.com/docs/authentication/getting-started)
storage_client = storage.Client()
bucket_name = os.environ['BUCKET_NAME']
bucket = storage_client.get_bucket(bucket_name)

# For local testing
if os.environ['HOME'] == '/home/peter':
    data_dir = os.environ['HOME'] + '/Codes/python/BusWatchNI/data/'
else:
    data_dir = os.environ['HOME'] + '/BusWatchNI/data/'

for blob in storage_client.list_blobs(bucket, prefix='Data_for_BusWatchNI/DataForPlots'):
    # print(blob.name)
    output_filename = blob.name.split('/')[-1]
    # print(output_filename)
    data = pd.read_csv('gs://' + bucket_name + '/' + blob.name)
    data.to_csv(data_dir + output_filename)
