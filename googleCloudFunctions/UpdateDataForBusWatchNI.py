from google.cloud import storage
import pandas as pd
from datetime import datetime
from datetime import timedelta
from google.cloud import logging as cloudlogging
import logging
from os import path, remove, environ
import json

def UpdataDataForBusWatchNI_main(event, context):
    lg_client = cloudlogging.Client()
    lg_client.setup_logging(log_level=logging.INFO)
    storage_client = storage.Client()
    bucket_name = environ.get('BUCKET_NAME')
    bucket = storage_client.bucket(bucket_name)

    # Get yesterday's data
    yesterday = (datetime.now() - timedelta(days = 1))
    date_prefix = yesterday.strftime('%Y') + '/' + yesterday.strftime('%m') + '/' + yesterday.strftime('%Y%m%d') + '.csv.bz2' 
    filename = 'QueryNextServiceAPI_data/' + date_prefix
    for blob in storage_client.list_blobs(bucket, prefix=filename):
        logging.info(blob.name)
        yesterdays_data = pd.read_csv('gs://' + bucket_name + '/' + blob.name)

    # Rerun of filtering done before, but now only keeping the most recent record (rather than a handful of recent records)

    # For each OriginId-ServiceName-DestinationName-PlannedDepartureDate grouping, sort the records with the group
    # by QueryDateUnix and assign a number, with 0 being the most recent record we have (the last query for that
    # particular departure), 1 being the 2nd most recent, etc (also grouping by LinesQueryGroup, although this
    # shouldn't make a difference due to the filtering applied in the loop above)
    yesterdays_data['QueryDateRank'] = (yesterdays_data.groupby(['OriginId', 'ServiceName', 'DestinationName', 'PlannedDepartureDate',
                                                                'PlannedDepartureTime', 'LinesQueryGroup'])['QueryDateUnix']
                                        .rank(method='first', ascending=False) - 1)
    # Only keep most the most recent query result for each OriginId-ServiceName-DestinationName-PlannedDepartureDate grouping
    yesterdays_data = yesterdays_data[yesterdays_data.QueryDateRank == 0]
    yesterdays_data = yesterdays_data.drop(columns=['QueryDateRank', 'SysPlannedDepartureDate',
                                       'SysActualDepartureDate', 'TransportMode', 'OccupancyStatus'])
    #logging.info(yesterdays_data.shape)

    # Get previous data (produced by this script yesterday)
    date_prefix = yesterday.strftime('%Y') + '/' + yesterday.strftime('%m') + '/' + yesterday.strftime('%Y%m%d') + '.csv.bz2' 
    filename = 'Data_for_BusWatchNI/combined_reduced_daily_data_15aug2022_onwards.csv.bz2'
    for blob in storage_client.list_blobs(bucket, prefix=filename):
        logging.info(blob.name)
        data = pd.read_csv('gs://' + bucket_name + '/' + blob.name)

    # Concat yesterdays data to existing data
    data = pd.concat([data, yesterdays_data], sort=False, ignore_index=True).drop_duplicates()
    logging.info(data.shape)

    del yesterdays_data
 
    # Get list of OriginIds to keep data for for each line
    global stops
    with open('OriginIds_to_query_by_line_20220910.txt', 'r') as input_file:
        stops = json.load(input_file)
    # Filter down to the OriginIds specified above
    data['intended_originId_for_this_line'] = data.apply(check_if_intended_originId, axis=1)
    data = data[data.intended_originId_for_this_line == 1].drop(columns='intended_originId_for_this_line')

    # Write out updated data
    root = path.dirname(path.abspath(__file__))
    tmp_file_name = 'combined_reduced_daily_data_15aug2022_onwards.csv.bz2'
    file_path = '/tmp/' + tmp_file_name
    data.to_csv(path.join(root, file_path), index=False)

    logging.info(f"Updating: {filename}")
    blob = bucket.blob(filename)
    blob.upload_from_filename(path.join(root, file_path))
    remove(file_path)

    return

def check_if_intended_originId(row):
    if row.OriginId in stops[row.ServiceName]:
        return(1)
    else:
        return(0)
