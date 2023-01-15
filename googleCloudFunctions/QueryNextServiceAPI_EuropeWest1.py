import requests
import json
from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
from google.cloud import storage
from google.cloud import logging as cloudlogging
from random import shuffle
import logging
from os import environ
import pandas as pd

def QueryNextServiceAPI_EuropeWest1_main(event, context):
    # Set up logging and storage clients
    lg_client = cloudlogging.Client()
    lg_client.setup_logging(log_level=logging.INFO)
    storage_client = storage.Client()
    bucket_name = environ.get('BUCKET_NAME')
    bucket = storage_client.bucket(bucket_name)

    # Start of url for POST request
    translink_url = 'https://www.translink.co.uk/JourneyPlannerApi/GetJourneyResults'

    # Just for testing
    # event['attributes'] = {}
    # event['attributes']['lines'] = '1_2'

    stops_1a = [10004031, 10003955, 10012548, 10004129, 10006349, 10002952, 10006600, 10003517, 10009289, 10009233]
    stops_1c = [10004031, 10003955, 10012548, 10004129, 10006349, 10002952, 10006600, 10009748, 10009289, 10009233]
    stops_1d = [10004031, 10003955, 10011157, 10004129, 10006349, 10002952, 10006600, 10009748, 10009325, 10009329]
    stops_1e = [10004031, 10003955, 10012548, 10004129, 10006349, 10002952, 10006600, 10008820, 10011876, 10011875]
    stops_1f = [10004031, 10003955, 10012548, 10004129, 10006349, 10002952, 10006600, 10006595, 10008804, 10007202]
    stops_1g = [10004031, 10003955, 10012548, 10004129, 10006349, 10002952, 10006600, 10006595, 10009295]
    stops_1j = [10004031, 10003955, 10012548, 10004129, 10006349, 10002952, 10006600, 10006579]

    stops_2a = [10004031, 10003955, 10011184, 10005773, 10006815, 10012378, 10006600, 10003522, 10009309, 10009299]
    stops_2b = [10004031, 10003955, 10011184, 10005773, 10006815, 10006808, 10002946, 10006588, 10009309, 10009299]
    stops_2c = [10004031, 10003955, 10011184, 10005773, 10006815, 10012369, 10012365, 10009230, 10012285, 10012294]
    stops_2d = [10004031, 10003955, 10011184, 10005773, 10006815, 10006808, 10012365, 10009230, 10012285, 10012294]
    stops_2e = [10004031, 10003955, 10011184, 10005773, 10006815, 10012369, 10012365, 10009230, 10012285, 10012294]
    stops_2g = [10004031, 10003955, 10011184, 10005773, 10006815, 10012369, 10012303, 10007260, 10012285, 10012294]
    stops_2h = [10004031, 10003955, 10011184, 10005773, 10006815, 10012369, 10010603, 10012365, 10010623]
    stops_2j = [10003962, 10003955, 10011162, 10011185, 10004131, 10006352, 10002501]
    stops_2k = [10003962, 10003955, 10011162, 10011185, 10011159, 10011190, 10005361, 10005364]
    stops_2m = [10003962, 10003955, 10011162, 10011185, 10011159, 10011190, 10005361, 10006815, 10012378, 10006808]

    stops_3a = [10003969, 10012547, 10002149, 10002136, 10012624, 10011624, 10011616, 10002965, 10007790, 10007787]
    stops_3b = [10003969, 10012547, 10012618, 10010133, 10011531, 10011626, 10002965, 10007790, 10007787]
    stops_3c = [10003969, 10012547, 10012618, 10010133, 10011624, 10003000, 10007782, 10007787, 10007784]
    stops_3d = [10003969, 10012547, 10012618, 10010133, 10011624, 10003000, 10007790, 10007173, 10007784]
    stops_3e = [10003969, 10012547, 10012618, 10010133, 10011624, 10002976, 10002992, 10002990, 10007787, 10007784]
    stops_3f = [10003969, 10012547, 10002149, 10011531, 10002974, 10002977, 10002987, 10012032, 10011407, 10005838]
    stops_3g = [10003969, 10012547, 10002149, 10011531, 10002974, 10002977, 10002987, 10011416, 10005838]
    stops_3h = [10003969, 10012547, 10012618, 10010133, 10011531, 10002974, 10002977, 10002987, 10011416, 10011407]
    stops_3j = [10003969, 10012547, 10012618, 10010133, 10011531, 10011626, 10002965, 10007782, 10007787, 10007784]

    stops_4c = [10003969, 10012547, 10012618, 10010129, 10003155, 10002028, 10011019, 10012034, 10005822, 10012499]
    stops_4d = [10003969, 10012547, 10012618, 10010129, 10003155, 10002028, 10011019, 10012034, 10005822, 10005838]
    stops_4e = [10003969, 10012547, 10012618, 10010129, 10003155, 10002028, 10002033, 10011024, 10007687, 10007686]

    stops_5a = [10003969, 10012547, 10012614, 10004016, 10002140, 10004780, 10003773, 10003223, 10003225, 10007686]
    stops_5b = [10012547, 10004016, 10002150, 10010136, 10003148, 10003781, 10003773, 10003223, 10003225, 10007686]
    stops_5c = [10003969, 10012547, 10012618, 10002140, 10004780, 10003773, 10003779, 10007697, 10006421, 10006368]

    stops_6a = [10003969, 10012618, 10004789, 10004764, 10004776, 10007697, 10006419, 10006421]
    stops_6c = [10003969, 10003994, 10008467, 10010150, 10006422, 10009906, 10009897, 10003013, 10002854, 10002863]
    stops_6d = [10003969, 10003999, 10012424, 10010826, 10009906, 10009897, 10003003, 10010496, 10010494]
    stops_6e = [10003969, 10003999, 10012424, 10010674, 10010677, 10010826, 10004788, 10009907, 10006368]

    stops_7a = [10003988, 10003949, 10003174, 10008467, 10010150, 10006422, 10009907, 10003405, 10006367, 10003410]
    stops_7b = [10003988, 10003949, 10003174, 10008467, 10010150, 10006422, 10009907, 10006368, 10006367, 10003410]
    stops_7c = [10003988, 10003942, 10003174, 10010156, 10010820, 10006422, 10009907, 10003405, 10006367, 10003410]
    stops_7d = [10003988, 10003949, 10003174, 10010156, 10004788, 10006422, 10009907, 10006368, 10006367, 10003410]
    stops_7e = [10003988, 10003994, 10003966, 10008467, 10001216, 10010820, 10007697, 10003779, 10003223, 10004786]
    stops_7g = [10003988, 10003942, 10003177, 10008467, 10001216, 10010820, 10004786, 10003223, 10003224, 10007686]
    stops_7h = [10003988, 10003942, 10008467, 10001216, 10004784, 10003223, 10007686, 10012023, 10005799, 10011416]

    stops_8a = [10003958, 10003980, 10003173, 10011543, 10011550, 10008845, 10008839, 10012164, 10012163, 10006267]
    stops_8b = [10003958, 10003980, 10003173, 10008838, 10008847, 10008845, 10008839, 10012164, 10012163, 10006267]
    stops_8c = [10003958, 10003980, 10003173, 10008838, 10008847, 10008839, 10012163, 10001173, 10007812, 10007808]
    stops_8d = [10003958, 10003980, 10003173, 10010503, 10011543, 10011550, 10011544]

    stops_9a = [10003958, 10003980, 10003173, 10012443, 10012440, 10006280, 10006274, 10006051, 10006042, 10005036]
    stops_9b = [10003958, 10003980, 10003173, 10012443, 10012444, 10012440, 10002609, 10006280, 10006285, 10011671]
    stops_9c = [10003958, 10003980, 10012443, 10012440, 10006280, 10011671, 10006268, 10006051, 10006042, 10005036]
    stops_9e = [10003958, 10003980, 10003171, 10011890, 10011887, 10011888, 10006225, 10012434, 10000123]
    stops_9f = [10003980, 10003171, 10011890, 10011879, 10011893, 10006225, 10012434, 10002612, 10000123]
    stops_9g = [10003958, 10003980, 10011890, 10006225, 10012434, 10001168, 10001183, 10001173, 10007808, 10007812]
    stops_9h = [10003958, 10003980, 10003171, 10011890, 10011887, 10006235, 10006236, 10011893, 10011879]
    stops_9j = [10003958, 10003980, 10011890, 10006251, 10009110, 10006228, 10001168, 10001183, 10007808, 10007812]
    stops_9k = [10003958, 10003175, 10003171, 10011890, 10011887, 10006235, 10006251, 10009110]

    stops_10a = [10004008, 10003941, 10006241, 10006212, 10009067, 10001190, 10001183, 10007808, 10007812]
    stops_10b = [10004008, 10003941, 10006241, 10006212, 10009067, 10001190, 10001183, 10001172, 10007008, 10003861]
    stops_10f = [10003941, 10006241, 10006212, 10009067, 10001165, 10007008, 10011588, 10010214, 10007839, 10007842]
    stops_10g = [10003941, 10006256, 10006241, 10006212, 10009067, 10001190, 10001183, 10007811, 10011588]
    stops_10h = [10004008, 10003941, 10006241, 10006212, 10009067, 10001165, 10007008, 10011585, 10011581, 10006269]
    stops_10j = [10004008, 10003941, 10006241, 10012099, 10012102, 10001165, 10007008, 10011588, 10000206, 10012120]
    stops_10k = [10004008, 10003982, 10006213, 10012099, 10012102, 10001165, 10007008, 10011588, 10000206, 10012120]
    stops_10m = [10004008, 10003982, 10006238, 10006231, 10006213, 10011251, 10012473, 10001454, 10010007, 10010016]
    stops_10p = [10004008, 10006238, 10006213, 10011251, 10012476, 10012473, 10001454, 10010003, 10002510, 10002502]
    stops_10x = [10004008, 10006043, 10007802, 10011588, 10010214, 10007836, 10007835, 10009340, 10007842]

    stops_11a = [10003939, 10004004, 10012777, 10011052, 10011054, 10001448, 10001446, 10002506, 10002512, 10002504]
    stops_11b = [10003939, 10004004, 10012777, 10011052, 10011054, 10012476, 10011246, 10011254, 10011253]
    stops_11c = [10003939, 10004004, 10012777, 10011052, 10011054, 10012469, 10008082]
    stops_11d = [10003939, 10004004, 10012777, 10011052, 10011054, 10012469, 10008082, 10011246, 10011254, 10011253]
    stops_11e = [10003939, 10003955, 10003950, 10011041, 10011051, 10001448, 10001446, 10008087, 10008095, 10008093]
    stops_11f = [10003939, 10003955, 10003950, 10011041, 10011051, 10001448, 10001446, 10008087, 10008095, 10008093]
    stops_11g = [10003939, 10004004, 10012777, 10011052, 10011054, 10001448, 10001446, 10002506, 10012762]

    stops_12a = [10000057, 10003955, 10003950, 10004105, 10010003, 10002510, 10002502]
    stops_12b = [10000057, 10003955, 10003950, 10011041, 10010017, 10010000, 10010003, 10002510, 10002502]
    stops_12c = [10000057, 10003955, 10003950, 10004105, 10010003, 10002512, 10008087, 10008094, 10012760]

    stops_g1 = [10007836, 10007811, 10001190, 10006216, 10003941, 10012547, 10002146, 10002028, 10011422, 10000211]
    stops_g2 = [10011899, 10003999, 10011901, 10005769, 10011918, 10012547, 10003939, 10003962]

    if event['attributes']['lines'] == '1_2':
        # logging.info('1_2')
        originIds = (stops_1a + stops_1c + stops_1d + stops_1e + stops_1f + stops_1g + stops_1j +
                     stops_2a + stops_2b + stops_2c + stops_2d + stops_2e + stops_2g + stops_2h + stops_2j + stops_2k + stops_2m)

    elif event['attributes']['lines'] == '3_4_5':
        # logging.info('3_4_5')
        originIds = (stops_3a + stops_3b + stops_3c + stops_3d + stops_3e + stops_3f + stops_3g +  stops_3h + stops_3j +
                     stops_4c + stops_4d + stops_4e +
                     stops_5a + stops_5b + stops_5c)

    elif event['attributes']['lines'] == '6_7':
        # logging.info('6_7')
        originIds = (stops_6a + stops_6c + stops_6d + stops_6e + 
                     stops_7a + stops_7b + stops_7c + stops_7d + stops_7e + stops_7g + stops_7h)

    elif event['attributes']['lines'] == '8_9':
        # logging.info('8_9')
        originIds = (stops_8a + stops_8b + stops_8c + stops_8d +
                     stops_9a + stops_9b + stops_9c + stops_9e + stops_9f + stops_9g + stops_9h + stops_9j + stops_9k)

    elif event['attributes']['lines'] == '10_11_12':
        # logging.info('10_11_12')
        originIds = (stops_10a + stops_10b + stops_10f + stops_10g + stops_10h + stops_10j + stops_10k + stops_10m + stops_10p + stops_10x +
                     stops_11a + stops_11b + stops_11c + stops_11d + stops_11e + stops_11f + stops_11g +
                     stops_12a + stops_12b + stops_12c)

    elif event['attributes']['lines'] == 'Glider':
        # logging.info('Glider')
        originIds = (stops_g1 + stops_g2)

    originIds = list(set(originIds))
    # Shuffle the originIds each time the function is called, in case there's some advantage/disadvantage for a stop if it's
    # queried earlier/later
    shuffle(originIds)

    dfs = []
    error_originIds = []
    error_queryTimes = []
    error_count = 0
    for originId in originIds:
        # Updated version to account for daylight savings
        dtnow = datetime.now(ZoneInfo("Europe/London"))
        current_date_unix = int(dtnow.timestamp())
        current_time = (dtnow).strftime('%Y-%m-%d %H:%M')

        payload = {'OriginId': str(originId), 'DepartureOrArrivalDate': current_time, 'IsParkAndRideRequest': 'false'}

        try:
            raw_data = requests.post(url = translink_url, data = payload, verify = True)
        except:
            logging.warning(f'Error with requests.post for id {originId}')

        if raw_data.status_code != 200:
            logging.warning(f'Status code {raw_data.status_code} for id {originId}')
            error_count = error_count + 1
            error_originIds.append(originId)
            error_queryTimes.append(current_date_unix)
            continue
        if 'Result' not in raw_data.json() or (raw_data.json()['Result'] is None):
            logging.warning(f'Json data for id {originId} has no Result key')
            error_count = error_count + 1
            error_originIds.append(originId)
            error_queryTimes.append(current_date_unix)
            continue
        if 'Departures' not in raw_data.json()['Result'] or (raw_data.json()['Result']['Departures'] is None):
            logging.warning(f'Json data for id {originId} has no Departures key')
            error_count = error_count + 1
            error_originIds.append(originId)
            error_queryTimes.append(current_date_unix)
            continue
        if len(raw_data.json()['Result']['Departures']) < 1:
            logging.warning(f'Json data for id {originId} has length < 1')
            error_count = error_count + 1
            error_originIds.append(originId)
            error_queryTimes.append(current_date_unix)
            continue

        df = pd.json_normalize(raw_data.json()['Result']['Departures'])
        df['QueryDateUnix'] = current_date_unix
        df['OriginId'] = int(originId)
        dfs.append(df[['QueryDateUnix', 'OriginId', 'ServiceName', 'DestinationName',
            'SysPlannedDepartureDate', 'SysActualDepartureDate', 'TransportMode', 'OccupancyStatus',
            'PlannedDepartureDate', 'PlannedDepartureTime', 'ActualDepartureDate', 'ActualDepartureTime',
            'IsCancelled']])

    if error_count > 0:
        logging.warning(f"Lines: {event['attributes']['lines']}; Total error count: {error_count} originIds had errors")

    full_df = pd.concat(dfs)

    # Updated version to handle daylight savings
    dtnow = datetime.now(ZoneInfo("Europe/London"))
    datetime_short = dtnow.strftime('%Y%m%d_%H%M%S')
    output_prefix = dtnow.strftime('%Y') + '/' + dtnow.strftime('%m') + '/' + dtnow.strftime('%Y%m%d')
    output_file = 'QueryNextServiceAPI_data/' + output_prefix + '/' + event['attributes']['lines'] + '/' + datetime_short + '.csv'

    blob = bucket.blob(output_file)
    blob.upload_from_string(full_df.to_csv(index=False), content_type='text/csv')

    # If there were errors, write out a dataframe with the OriginIds that had errors, and the
    # times at which they were queried
    if (len(error_originIds) > 0):
        error_df = pd.DataFrame(data={'OriginId': error_originIds, 'QueryDateUnix': error_queryTimes})
        error_output_file = 'QueryNextServiceAPI_errors/' + output_prefix + '/' + event['attributes']['lines'] + '/' + datetime_short + '_errorIDs.csv'
        blob = bucket.blob(error_output_file)
        blob.upload_from_string(error_df.to_csv(index=False), content_type='text/csv')
