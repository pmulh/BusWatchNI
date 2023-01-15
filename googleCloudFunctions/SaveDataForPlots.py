from google.cloud import storage
import pandas as pd
from datetime import datetime
from datetime import timedelta
from google.cloud import logging as cloudlogging
import logging
from os import path, remove, environ
import json
import numpy as np
import branca.colormap as branca_cm

def SaveDataForPlots_main(event, context):
    lg_client = cloudlogging.Client()
    lg_client.setup_logging(log_level=logging.INFO)
    storage_client = storage.Client()
    bucket_name = environ.get('BUCKET_NAME')
    bucket = storage_client.bucket(bucket_name)

    # Get the newly created combined dataset
    filename = 'Data_for_BusWatchNI/combined_reduced_daily_data_15aug2022_onwards.csv.bz2'
    for blob in storage_client.list_blobs(bucket, prefix=filename):
        # logging.info(blob.name)
        # Specify dtypes to help with memory usage
        data = pd.read_csv('gs://' + bucket_name + '/' + blob.name,
                           dtype={'ServiceName':'category', 'DestinationName': 'category',
                                  'LinesQueryGroup':'category','IsCancelled':'category'})

    # Create DateTime columns from individual Date and Time columns
    data['ActualDepartureDateTime'] = pd.to_datetime(data['ActualDepartureDate'] + ' ' + 
                                                      data['ActualDepartureTime'], format='%d/%m/%Y %H:%M')
    data['PlannedDepartureDateTime'] = pd.to_datetime(data['PlannedDepartureDate'] + ' ' + 
                                                      data['PlannedDepartureTime'], format='%d/%m/%Y %H:%M')
    data['PlannedDepartureDate'] = pd.to_datetime(data['PlannedDepartureDate'], format='%d/%m/%Y')

    # The difference of two datetime columns returns a datetime.timedelta object
    # Convert into minutes using astype
    data['ActPlanDeptTimeDiffMins'] = ((data.ActualDepartureDateTime - data.PlannedDepartureDateTime)
                                        .astype('timedelta64[m]'))

    # Some more new columns
    data['PlannedDepartureHour'] = data['PlannedDepartureDateTime'].dt.hour
    # A handful of departures with departure times between 2 and 3 am appeared on 2022-22-10; drop these for now
    data = data[data.PlannedDepartureHour > 4].copy()
    data['DayOfWeek'] = data['PlannedDepartureDateTime'].dt.day_of_week
    data['WeekdayOrWeekend'] = np.where(data['DayOfWeek'] < 5, 'Weekday', 'Weekend')
    data['PlannedDepartureTime15MinBuckets'] = data['PlannedDepartureDateTime'].dt.floor('15min').dt.time
    # E.g., 05:10 rounded down to 05:00, 05:17 to 05:15, etc
    data['PlannedDepartureTime30MinBuckets'] = data['PlannedDepartureDateTime'].dt.floor('30min').dt.time

    # To enable easier grouping by bus routes
    # First use split to separate out, e.g., 'Bus 1a' or 'Glider G2' (taking the second part)
    data['Service'] = data['ServiceName'].apply(lambda x: x.split(' ')[1])
    # Then go a step futher and drop the letter (in the case of buses) or the number (for gliders)
    data['Line'] = data['Service'].apply(lambda x: x[0:-1])
    # IsCancelled is a mix of nulls, 'True', and 'False'. Create a binary indicator version for use later
    data['IsCancelledInt'] = np.where(data['IsCancelled'] == 'True', 1, 0)

    # Drop unneeded columns
    data = data.drop(columns=['QueryDateUnix', 'PlannedDepartureTime', 'ActualDepartureDate', 'ActualDepartureTime',
                              'LinesQueryGroup'])

    summary_table = create_summary_table_row(data, 'SinceRecordsBegan')

    for lookback in ['SinceRecordsBegan', 'TwelveWeeks', 'FourWeeks', 'TwoWeeks', 'OneWeek']:
        # If lookback == 'SinceRecordsBegan', continue with full data
        if lookback == 'TwelveWeeks':
            data = data[data['PlannedDepartureDateTime'] > (datetime.now() - timedelta(weeks=12))].copy()
        elif lookback == 'FourWeeks':
            data = data[data['PlannedDepartureDateTime'] > (datetime.now() - timedelta(weeks=4))].copy()
        elif lookback == 'TwoWeeks':
            data = data[data['PlannedDepartureDateTime'] > (datetime.now() - timedelta(weeks=2))].copy()
        elif lookback == 'OneWeek':
            data = data[data['PlannedDepartureDateTime'] > (datetime.now() - timedelta(weeks=1))].copy()
        #logging.info(data.PlannedDepartureDate.unique())

        if lookback != 'SinceRecordsBegan':
            summary_table = pd.concat([summary_table, create_summary_table_row(data, lookback)]).reset_index(drop=True)

        # Count the cancellations first, then filter down to just non-cancellations for remainder of functions
        create_CancellationCountBy_GroupbyVars_csv(data, bucket, ['Line'], 'Line_' + lookback)
        data_noCancellations = data[data.IsCancelledInt == 0].copy()

        # All routes considered together
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['PlannedDepartureDate'], 'Date_' + lookback,
                                      incl_rolling_avg=True)
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['DayOfWeek'], 'DayOfWeek_' + lookback)
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['PlannedDepartureTime30MinBuckets', 'WeekdayOrWeekend'],
                                      'TimeOfDay30MinBuckets_WeekdayOrWeekend_' + lookback)
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['PlannedDepartureTime15MinBuckets', 'WeekdayOrWeekend'],
                                      'TimeOfDay15MinBuckets_WeekdayOrWeekend_' + lookback)
        create_PercDelaysBy_GroupbyVars_csv(data_noCancellations, bucket, ['PlannedDepartureDate'], 'Date_' + lookback,
                                            incl_rolling_avg=True)

        # Split out by line (1, 2, 3, ..., G)
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['Line', 'PlannedDepartureDate'], 'Line_Date_' + lookback)
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['Line', 'DayOfWeek'], 'Line_DayOfWeek_' + lookback)
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['Line', 'PlannedDepartureTime30MinBuckets', 'WeekdayOrWeekend'],
                                      'Line_TimeOfDay30MinBuckets_WeekdayOrWeekend_' + lookback)
        create_PercDelaysBy_GroupbyVars_csv(data_noCancellations, bucket, ['Line', 'PlannedDepartureDate'], 'Line_Date_' + lookback)

        # Split out by line but not by Date/DayOfWeek/etc
        create_MeanBy_GroupbyVars_csv(data_noCancellations, bucket, ['Line'], 'Line_' + lookback)
        create_PercDelaysBy_GroupbyVars_csv(data_noCancellations, bucket, ['Line'], 'Line_' + lookback)

        # Basic count of delays
        create_DelayDistribution_csv(data_noCancellations, bucket, lookback)

        # Data for Folium plots
        create_FoliumData_csv(data_noCancellations, bucket, 'AllLines_' + lookback)

    output_file = 'Data_for_BusWatchNI/DataForPlots/SummaryTable.csv'
    blob = bucket.blob(output_file)
    blob.upload_from_string(summary_table.to_csv(index=False), content_type='text/csv')

    return

### Functions to aggregate data and save out csvs
def create_summary_table_row(df, label):
    df_noCancellations = df[df.IsCancelledInt == 0].copy()
    row = {'TimePeriod': label,
           'Count': df.shape[0],
           'CountExclCancelled': df_noCancellations.shape[0],
           'OriginIdNunique': df.OriginId.nunique(),
           'CancelledCount': df[df.IsCancelledInt == 1].shape[0],
           'MinDeptDate': df['PlannedDepartureDate'].min().strftime('%d/%m/%Y'),
           'MaxDeptDate': df['PlannedDepartureDate'].max().strftime('%d/%m/%Y'),
           'ServiceNameNunique': df.ServiceName.nunique(),
           'ActPlanDeptTimeDiffMinsMeanInclCancelled': df.ActPlanDeptTimeDiffMins.mean(),
           'ActPlanDeptTimeDiffMinsLte5CountDivFullCountInclCancelled': df[df.ActPlanDeptTimeDiffMins <= 5].shape[0] / df.shape[0],
           'ActPlanDeptTimeDiffMinsMean': df_noCancellations.ActPlanDeptTimeDiffMins.mean(),
           'ActPlanDeptTimeDiffMinsLte5CountDivFullCount': df_noCancellations[df_noCancellations.ActPlanDeptTimeDiffMins <= 5].shape[0] / df_noCancellations.shape[0]
          }
    return(pd.DataFrame(row, index=[0]))

# Count the number of cancelled departures
def create_CancellationCountBy_GroupbyVars_csv(data, bucket, groupby_vars, suffix):
    # Only considering data where we have a non-null value for IsCancelled (which should be all records from mid-Dec 2022)
    # Create two columns: count_True (number of cancellations), count_False (number of not cancelled departures)
    temp = pd.merge(data[data.IsCancelled == 'True'].groupby(groupby_vars)['ActPlanDeptTimeDiffMins'].agg(['count']).reset_index(),
                    data[data.IsCancelled == 'False'].groupby(groupby_vars)['ActPlanDeptTimeDiffMins'].agg(['count']).reset_index(),
                    on=groupby_vars, how='outer', suffixes=['_True', '_False'])
    temp['cancellation_percentage'] = 100*round(temp['count_True'] / (temp['count_True'] + temp['count_False']), 3)

    output_file = 'Data_for_BusWatchNI/DataForPlots/CancellationCountBy_' + suffix + '.csv'
    blob = bucket.blob(output_file)
    blob.upload_from_string(temp.to_csv(index=False), content_type='text/csv')
    return()

# Average delay by ...
def create_MeanBy_GroupbyVars_csv(data, bucket, groupby_vars, suffix, incl_rolling_avg=False):
    plot_df = data.groupby(groupby_vars).ActPlanDeptTimeDiffMins.agg(['mean', 'count', 'min', q10, q25, q50, q75, q90, 'max']).reset_index()

    if incl_rolling_avg:
        # 7-day rolling average of delay
        daily = data.groupby('PlannedDepartureDate')['ActPlanDeptTimeDiffMins'].agg(['count', 'sum', 'mean'])
        rolling = daily.rolling(7).sum()
        rolling_avg = pd.DataFrame(rolling['sum']/rolling['count']).reset_index().rename(columns={0: 'rolling_avg_7day'})
        plot_df = pd.merge(plot_df, rolling_avg, on='PlannedDepartureDate', how='left')
    output_file = 'Data_for_BusWatchNI/DataForPlots/MeanBy_' + suffix + '.csv'
    blob = bucket.blob(output_file)
    blob.upload_from_string(plot_df.to_csv(index=False), content_type='text/csv')
    return()

# % of departures within a certain delay time, per...
def create_PercDelaysBy_GroupbyVars_csv(data, bucket, groupby_vars, suffix, incl_rolling_avg=False):
    plot_df = data.groupby(groupby_vars).ActPlanDeptTimeDiffMins.agg([delay_lte2Mins_perc, delay_lte3Mins_perc, delay_lte5Mins_perc,
                                                                      delay_lte7Mins_perc, delay_lte10Mins_perc,
                                                                      delay_lte15Mins_perc]).reset_index()

    if incl_rolling_avg:
        daily = data.groupby(groupby_vars).ActPlanDeptTimeDiffMins.agg(['count', delay_lte2Mins_count, delay_lte3Mins_count,
                                                                        delay_lte5Mins_count, delay_lte7Mins_count,
                                                                        delay_lte10Mins_count, delay_lte15Mins_count])
        rolling = daily.rolling(7).sum()
        rolling['rolling_perc_lte2Mins'] = rolling['delay_lte2Mins_count'] / rolling['count']
        rolling['rolling_perc_lte3Mins'] = rolling['delay_lte3Mins_count'] / rolling['count']
        rolling['rolling_perc_lte5Mins'] = rolling['delay_lte5Mins_count'] / rolling['count']
        rolling['rolling_perc_lte7Mins'] = rolling['delay_lte7Mins_count'] / rolling['count']
        rolling['rolling_perc_lte10Mins'] = rolling['delay_lte10Mins_count'] / rolling['count']
        rolling['rolling_perc_lte15Mins'] = rolling['delay_lte15Mins_count'] / rolling['count']

        plot_df = pd.merge(plot_df, rolling[['rolling_perc_lte2Mins', 'rolling_perc_lte3Mins', 'rolling_perc_lte5Mins',
                                             'rolling_perc_lte7Mins', 'rolling_perc_lte10Mins', 'rolling_perc_lte15Mins']],
                        on='PlannedDepartureDate', how='left')
        
    output_file = 'Data_for_BusWatchNI/DataForPlots/PercDelaysBy_' + suffix + '.csv'
    blob = bucket.blob(output_file)
    blob.upload_from_string(plot_df.to_csv(index=False), content_type='text/csv')
    return(plot_df)

def create_DelayDistribution_csv(data, bucket, suffix):
    delay_counts = pd.DataFrame(data['ActPlanDeptTimeDiffMins'].value_counts()).reset_index()
    delay_counts = delay_counts.rename(columns={'index': 'ActPlanDeptTimeDiffMins',
                                                'ActPlanDeptTimeDiffMins': 'count'})
    output_file = 'Data_for_BusWatchNI/DataForPlots/DelayDistribution_' + suffix + '.csv'
    blob = bucket.blob(output_file)
    blob.upload_from_string(delay_counts.to_csv(index=False), content_type='text/csv')
    return()

def create_FoliumData_csv(data, bucket, suffix):
    mean_by_originId = data.groupby(['OriginId'])['ActPlanDeptTimeDiffMins'].agg(['count', 'mean'])
    stop_info = pd.read_csv('20221002_CombineStopInfo.csv')
    z = pd.merge(mean_by_originId, stop_info, on='OriginId', how='left')
    z['Name'] = z['Name'].fillna('')
    z_noNullLatLongs = z[~z.Latitude_mean.isnull()].copy()

    # Some stops have more than one name (e.g. names in Irish and English).
    # For these cases, combine the names (in alphabetical order) with a linebreak between them
    names_per_OriginId = z_noNullLatLongs.groupby('OriginId')['Name'].agg(['unique']).reset_index()
    names_per_OriginId['names_sorted'] = names_per_OriginId.unique.apply(lambda x: sorted(x))
    names_per_OriginId['names_sorted_final'] = names_per_OriginId.names_sorted.apply(lambda x: '<br>'.join(x))
    names_per_OriginId = names_per_OriginId.drop(columns=['unique', 'names_sorted'])
    z_noNullLatLongs = pd.merge(z_noNullLatLongs.drop(columns='Name'), names_per_OriginId,
                                on='OriginId', how='left').drop_duplicates()

    # Combine all ServiceNames for each OriginId into a single string
    #
    # Drop 'Bus' part of ServiceName, and pad out e.g. '1a' to '01a' so sorting works better
    data['Route'] = data['ServiceName'].apply(lambda x: x.split(' ')[1].zfill(3))
    routes_per_OriginId = data.groupby('OriginId')['Route'].agg(['unique']).reset_index()
    routes_per_OriginId['routes_sorted'] = routes_per_OriginId.unique.apply(lambda x: sorted(x))
    # Drop the '0' added above
    routes_per_OriginId['routes_sorted2'] = routes_per_OriginId['routes_sorted'].apply(lambda x: [y.lstrip('0') for y in x])
    routes_per_OriginId['routes_sorted_final'] = routes_per_OriginId.routes_sorted2.apply(lambda x: ' '.join(x))
    routes_per_OriginId = routes_per_OriginId.drop(columns=['unique', 'routes_sorted', 'routes_sorted2'])

    z2 = pd.merge(z_noNullLatLongs, routes_per_OriginId, on='OriginId', how='left')
    # z2['TooltipText'] = (z2['OriginId'].astype('str') + 
    z2['TooltipText'] = ('<b>Stop Name(s):</b> ' + z2['names_sorted_final'] +
                         '<br><b>Routes:</b> ' + z2['routes_sorted_final'] +
                         '<br><b>Departures Recorded:</b> ' + z2['count'].astype('str') +
                         '<br><b>Average Delay:</b> ' + round(z2['mean'], 1).astype('str') + ' minutes')

    # Define colours for markers based on mean delay
    colourmap = branca_cm.LinearColormap(colors=['orange','blue'], vmin=0.5, vmax=7)
    colourmapAlt = branca_cm.LinearColormap(colors=['green','red'], vmin=0.5, vmax=7)
    # TODO: Currently have hardcoded min and max here, based on rough estimates of 5th and 95th percentiles
    # of mean delay (as of end of Sept 2022); may want to have these limits automatically calculated
    z2['MarkerColour'] = z2['mean'].apply(lambda x: colourmap(x))
    z2['MarkerColourAlt'] = z2['mean'].apply(lambda x: colourmapAlt(x))

    output_file = 'Data_for_BusWatchNI/DataForPlots/DataForFolium_' + suffix + '.csv'
    blob = bucket.blob(output_file)
    blob.upload_from_string(z2.to_csv(index=False), content_type='text/csv')

    return()


### Custom functions for use in agg function
## Percentiles
# 10th Percentile
def q10(x):
    return x.quantile(0.1)

# 25th Percentile
def q25(x):
    return x.quantile(0.25)

# 50th Percentile
def q50(x):
    return x.quantile(0.5)

# 75th Percentile
def q75(x):
    return x.quantile(0.75)

# 90th Percentile
def q90(x):
    return x.quantile(0.9)

## Mean with outliers excluded
def mean_excl_gt60mins(x):
    x = x[x <= 60]
    return sum(x) / len(x)

def mean_excl_gt120mins(x):
    x = x[x <= 120]
    return sum(x) / len(x)

def mean_excl_gt60mins_and_lt0mins(x):
    x = x[x <= 60]
    x = x[x >= 0]
    return sum(x) / len(x)

def mean_excl_gt120mins_and_lt0mins(x):
    x = x[x <= 120]
    x = x[x >= 0]
    return sum(x) / len(x)

## For calculating % of departures within certain delay times
def delay_lte2Mins_perc(x):
    total_rows = len(x)
    delay_lte2Mins_perc = 100 * len(x[x <= 2]) / total_rows
    return(delay_lte2Mins_perc)

def delay_lte3Mins_perc(x):
    total_rows = len(x)
    delay_lte3Mins_perc = 100 * len(x[x <= 3]) / total_rows
    return(delay_lte3Mins_perc)

def delay_lte5Mins_perc(x):
    total_rows = len(x)
    delay_lte2Mins_perc = 100 * len(x[x <= 5]) / total_rows
    return(delay_lte2Mins_perc)

def delay_lte7Mins_perc(x):
    total_rows = len(x)
    delay_lte2Mins_perc = 100 * len(x[x <= 7]) / total_rows
    return(delay_lte2Mins_perc)

def delay_lte10Mins_perc(x):
    total_rows = len(x)
    delay_lte2Mins_perc = 100 * len(x[x <= 10]) / total_rows
    return(delay_lte2Mins_perc)

def delay_lte15Mins_perc(x):
    total_rows = len(x)
    delay_lte2Mins_perc = 100 * len(x[x <= 15]) / total_rows
    return(delay_lte2Mins_perc)

def delay_lte2Mins_count(x):
    temp = len(x[x <= 2])
    return(temp)

def delay_lte3Mins_count(x):
    temp = len(x[x <= 3])
    return(temp)

def delay_lte5Mins_count(x):
    temp = len(x[x <= 5])
    return(temp)

def delay_lte7Mins_count(x):
    temp = len(x[x <= 7])
    return(temp)

def delay_lte10Mins_count(x):
    temp = len(x[x <= 10])
    return(temp)

def delay_lte15Mins_count(x):
    temp = len(x[x <= 15])
    return(temp)