from google.cloud import storage
import pandas as pd
from datetime import datetime
from datetime import timedelta
from google.cloud import logging as cloudlogging
import logging
from os import path, remove, environ
import smtplib, ssl # For emailing summary information

def CombineDailyNextServiceAPIData_main(event, context):
    lg_client = cloudlogging.Client()
    lg_client.setup_logging(log_level=logging.INFO)
    storage_client = storage.Client()
    bucket_name = environ.get('BUCKET_NAME')
    bucket = storage_client.bucket(bucket_name)

    yesterday = (datetime.now() - timedelta(days = 1))
    query_date = yesterday.strftime('%d/%m/%Y')
    date_prefix = yesterday.strftime('%Y') + '/' + yesterday.strftime('%m') + '/' + yesterday.strftime('%Y%m%d')
    base_prefix = 'QueryNextServiceAPI_data/' + date_prefix
    
    # Define bus names on each line, to use later to filter down to only keep rows
    # for buses we intended to query (e.g. the 1 and 2 routes from the 1_2 function call,
    # the 3,4,5s for the 3_4_5 call, etc)
    metro1  = ['Bus 1'  + letter for letter in ['a', 'c', 'd', 'e', 'f', 'g', 'j']]
    metro2  = ['Bus 2'  + letter for letter in ['a', 'b', 'c', 'd', 'e', 'g', 'h', 'j', 'k', 'm']]
    metro3  = ['Bus 3'  + letter for letter in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j']]
    metro4  = ['Bus 4'  + letter for letter in ['c', 'd', 'e']]
    metro5  = ['Bus 5'  + letter for letter in ['a', 'b', 'c']]
    metro6  = ['Bus 6'  + letter for letter in ['a', 'c', 'd', 'e']]
    metro7  = ['Bus 7'  + letter for letter in ['a', 'b', 'c', 'd', 'e', 'g', 'h']]
    metro8  = ['Bus 8'  + letter for letter in ['a', 'b', 'c', 'd']]
    metro9  = ['Bus 9'  + letter for letter in ['a', 'b', 'c', 'e', 'f', 'g', 'h', 'j', 'k']]
    metro10 = ['Bus 10' + letter for letter in ['a', 'b', 'f', 'g', 'h', 'j', 'k', 'm', 'p', 'x']]
    metro11 = ['Bus 11' + letter for letter in ['a', 'b', 'c', 'd', 'e', 'f', 'g']]
    metro12 = ['Bus 12' + letter for letter in ['a', 'b', 'c']]
    glider  = ['Glider G1', 'Glider G2']
    metro_1_2 = metro1 + metro2
    metro_3_4_5 = metro3 + metro4 + metro5
    metro_6_7 = metro6 + metro7
    metro_8_9 = metro8 + metro9
    metro_10_11_12 = metro10 + metro11 + metro12
    valid_lines = {'1_2': metro_1_2, '3_4_5': metro_3_4_5, '6_7': metro_6_7,
                   '8_9': metro_8_9, '10_11_12': metro_10_11_12, 'Glider': glider}

    dfs = []
    for lines in ['1_2', '3_4_5', '6_7', '8_9', '10_11_12', 'Glider']:
        prefix = base_prefix  + '/' + lines + '/'
        logging.info(prefix)
        for blob in storage_client.list_blobs(bucket, prefix=prefix):
            csv_path = 'gs://' + bucket_name + '/' + blob.name
            df = pd.read_csv(csv_path)
            # Filter out rows for buses we didn't intend to query
            df = df[df.ServiceName.isin(valid_lines[lines])]
            df['LinesQueryGroup'] = lines
            # Filter out any records for departures that were planned for tomorrow
            # (not filtering out those that were planned for today but actually happened post midnight)
            df = df[df['PlannedDepartureDate'] == query_date]
            dfs.append(df)

    #logging.info(f"{len(dfs)}")
    del df
    merged_df = pd.concat(dfs, sort=False, ignore_index=True)
    del dfs

    # For each OriginId-ServiceName-DestinationName-PlannedDepartureDate grouping, sort the records with the group
    # by QueryDateUnix and assign a number, with 0 being the most recent record we have (the last query for that
    # particular departure), 1 being the 2nd most recent, etc (also grouping by LinesQueryGroup, although this
    # shouldn't make a difference due to the filtering applied in the loop above)
    merged_df['QueryDateRank'] = (merged_df.groupby(['OriginId', 'ServiceName', 'DestinationName', 'PlannedDepartureDate',
                                                    'PlannedDepartureTime', 'LinesQueryGroup'])['QueryDateUnix']
                                .rank(method='first', ascending=False) - 1)

    # Only keep most a couple of results for each OriginId-ServiceName-DestinationName-PlannedDepartureDate grouping
    # Roughly the most recent, and the query from 10, 20, 30 and 40 minutes before the last query time
    merged_df = merged_df[merged_df.QueryDateRank.isin([0, 5, 10, 15, 20])]
    merged_df = merged_df.drop(columns=['QueryDateRank'])
    #logging.info(f"{merged_df.shape}")

    # Email summary of yesterday's data 
    # 
    # (actual emailing is done right at the end of the function, in case of errors
    # (want to make sure merged_df gets saved out ok first))
    # Some setup
    port = 465
    context = ssl.create_default_context()
    # EMAIL_ADDRESS and EMAIL_APP_PASSWORD environment variables should have been set in Function configuration
    email_address = environ.get('EMAIL_ADDRESS')

    # Create some new variables to use in summary email
    merged_df['PlannedDepartureHour'] = merged_df['PlannedDepartureTime'].apply(lambda x: x.split(':')[0])
    # First split is to separate, e.g., 'Bus 1a'; then indexing is to drop the letter part. Then pad
    # out to two digits so Lines appear in order when sorted
    merged_df['Line'] = merged_df['ServiceName'].apply(lambda x: x.split(' ')[1][0:-1].zfill(2))
    # Similar, but more granular, since we don't drop the letter part
    merged_df['Service'] = merged_df['ServiceName'].apply(lambda x: x.split(' ')[1].zfill(3))

    email_text = """Subject: Data Collection Summary: """ + yesterday.strftime('%d/%m/%Y') + """

    Yesterdays merged_df shape: """ + str(merged_df.shape) + """
    \nNumber of unique ServiceNames = """ + str(merged_df.ServiceName.nunique()) + """
    \nNumber of unique Services = """ + str(merged_df.Service.nunique()) + """
    \nNumber of unique Lines = """ + str(merged_df.Line.nunique()) + """
    \nNumber of unique OriginIds = """ + str(merged_df.OriginId.nunique()) + """
    \nBreakdown by PlannedDepartureHour: \n""" + merged_df.groupby('PlannedDepartureHour').QueryDateUnix.count().sort_index().to_string() + """
    \nBreakdown by LineGroup: \n""" + merged_df.groupby('LinesQueryGroup').QueryDateUnix.count().sort_index().to_string() + """
    \nBreakdown by Line: \n""" + merged_df.groupby('Line').QueryDateUnix.count().sort_index().to_string() + """
    \nBreakdown by Service: \n""" + merged_df.groupby('Service').QueryDateUnix.count().sort_index().to_string() + """
    \n"""

    # Drop the three columns created for email summary
    merged_df = merged_df.drop(columns=['PlannedDepartureHour', 'Line', 'Service'])

    # Save out data
    root = path.dirname(path.abspath(__file__))
    tmp_file_name = yesterday.strftime('%Y%m%d') + '.csv.bz2'
    file_path = '/tmp/' + tmp_file_name
    merged_df.to_csv(path.join(root, file_path), index=False)
    del merged_df

    gcs_filename = base_prefix + '.csv.bz2'
    logging.info(f"{gcs_filename}")
    blob = bucket.blob(gcs_filename)
    blob.upload_from_filename(path.join(root, file_path))
    remove(file_path)
   
    # Send email summary of yesterday's data
    with smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) as server:
       server.login(email_address, environ.get('EMAIL_APP_PASSWORD'))
       server.sendmail(email_address, email_address, email_text)

    return
