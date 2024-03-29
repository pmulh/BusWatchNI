from flask import send_file, render_template
import pandas as pd
import numpy as np
import altair as alt
from app import app
import folium
from datetime import datetime, time
from datetime import timedelta
import os

# For local testing
if app.config['HOME'] == '/home/peter':
    data_dir = app.config['HOME'] + '/Codes/python/BusWatchNI/data/'
    static_dir = app.config['HOME'] + '/Codes/python/BusWatchNI/flaskApp/app/static/'
else:
    data_dir = app.config['HOME'] + '/BusWatchNI/data/'
    static_dir = app.config['HOME'] + '/BusWatchNI/flaskApp/app/static/'


############################################################################
################################## About ###################################
############################################################################
@app.route('/about')
def about():
    return(render_template('about.html', title='About'))



############################################################################
################################### Data ###################################
############################################################################

###########################################################
# Get size of each "monthly data" file to show on Data page
###########################################################
MonthlyDownloadFileSizes = {}
for month in ['2022_08', '2022_09', '2022_10', '2022_11', '2022_12',
              '2023_01', '2023_02', '2023_03', '2023_04', '2023_05']:
    MonthlyDownloadFileSizes[month] = {}
    extension = '.csv.bz2'
    MonthlyDownloadFileSizes[month][extension] = int(round(os.path.getsize(data_dir + 'monthlyData_' + month +
                                                                           extension) / (1024*1024), 0))
    MonthlyDownloadFileSizes[month][extension] = str(MonthlyDownloadFileSizes[month][extension]) + ' MB'

@app.route('/data')
def data():
    return(render_template('data_details.html', title='Data',
                           MonthlyDownloadFileSizes=MonthlyDownloadFileSizes))

@app.route('/download/<filename>')
def download_file(filename):
    # Basic way to track the number of downloads of each file
    download_history = pd.read_csv(data_dir + 'DownloadHistory.csv')
    new_row = pd.DataFrame({'Date': datetime.now().strftime('%Y-%m-%d'),
                            'Time':datetime.now().strftime('%H:%M:%S'),
                            'Filename': filename},index=[0])
    download_history = pd.concat([download_history, new_row]).reset_index(drop=True)
    download_history.to_csv(data_dir + 'DownloadHistory.csv', index=False)

    path = data_dir + filename
    return send_file(path, as_attachment=True)

@app.route('/download_compressed/<month>')
def download_monthly_data_compressed(month):
    # Basic way to track the number of downloads of each file
    download_history = pd.read_csv(data_dir + 'DownloadHistory.csv')
    new_row = pd.DataFrame({'Date': datetime.now().strftime('%Y-%m-%d'),
                            'Time':datetime.now().strftime('%H:%M:%S'),
                            'Filename': 'monthlyData_' + month + '.csv.bz2'},index=[0])
    download_history = pd.concat([download_history, new_row]).reset_index(drop=True)
    download_history.to_csv(data_dir + 'DownloadHistory.csv', index=False)

    path = data_dir + 'monthlyData_' + month + '.csv.bz2'
    return send_file(path, as_attachment=True)



############################################################################
################################# Homepage #################################
############################################################################
lines_list = ['1','2','3','4','5','6','7','8','9','10','11','12','G']

#############################################################################################
# Data for Summary box at top of homepage ("Since XX/XX/XXXX, data has been collected on...")
#############################################################################################
HighLevelSummary = pd.read_csv(data_dir + 'SummaryTable.csv')
HighLevelSummary['MeanDelay'] = round(HighLevelSummary['ActPlanDeptTimeDiffMinsMean'], 1)
HighLevelSummary['PercLt5Mins'] = round((100 * HighLevelSummary['ActPlanDeptTimeDiffMinsLte5CountDivFullCount']), 0).astype(int)
HighLevelSummary['CancellationPerc'] = round(100*HighLevelSummary['CancelledCount'] / HighLevelSummary['Count'],0).astype(int)
HighLevelSummary['Count'] = HighLevelSummary['Count'].map('{:,.0f}'.format) # Add a , every 1,000
HighLevelSummary['CancelledCount'] = HighLevelSummary['CancelledCount'].map('{:,.0f}'.format) # Add a , every 1,000
HighLevelSummary = HighLevelSummary.set_index('TimePeriod')


#########################
# "Summary by Route" card
#########################
def make_summary_table(line_filter=None):
    if line_filter:
        grouping_col = 'Service'
        if line_filter == '1':
            services = ['1a', '1c', '1d', '1e', '1f', '1g', '1j']
        elif line_filter == '2':
            services = ['2a', '2b', '2c', '2d', '2e', '2g', '2h', '2j', '2k', '2m']
        elif line_filter == '3':
            services = ['3a', '3b', '3c', '3d', '3e', '3f', '3g', '3h', '3j']
        elif line_filter == '4':
            services = ['4c', '4d', '4e']
        elif line_filter == '5':
            services = ['5a', '5b', '5c']
        elif line_filter == '6':
            services = ['6a', '6c', '6d', '6e']
        elif line_filter == '7':
            services = ['7a', '7b', '7c', '7d', '7e', '7g', '7h']
        elif line_filter == '8':
            services = ['8a', '8b', '8c', '8d']
        elif line_filter == '9':
            services = ['9a', '9b', '9c', '9e', '9f', '9g', '9h', '9j', '9k']
        elif line_filter == '10':
            services = ['10a', '10b', '10f', '10g', '10h', '10j', '10k', '10m', '10p', '10x']
        elif line_filter == '11':
            services = ['11a', '11b', '11c', '11d', '11e', '11f', '11g']
        elif line_filter == '12':
            services = ['12a', '12b', '12c']
        elif line_filter == 'G':
            services = ['G1', 'G2']
    else:
        grouping_col = 'Line'

    #
    MeanBy_Group_OneWeek = pd.read_csv(data_dir + 'MeanBy_' + grouping_col + '_OneWeek.csv')
    MeanBy_Group_TwoWeeks = pd.read_csv(data_dir + 'MeanBy_' + grouping_col + '_TwoWeeks.csv')
    MeanBy_Group_FourWeeks = pd.read_csv(data_dir + 'MeanBy_' + grouping_col + '_FourWeeks.csv')
    MeanBy_Group_TwelveWeeks = pd.read_csv(data_dir + 'MeanBy_' + grouping_col + '_TwelveWeeks.csv')
    MeanBy_Group_SinceRecordsBegan = pd.read_csv(data_dir + 'MeanBy_' + grouping_col + '_SinceRecordsBegan.csv')
    #
    PercDelaysBy_Group_OneWeek = pd.read_csv(data_dir + 'PercDelaysBy_' + grouping_col + '_OneWeek.csv')
    PercDelaysBy_Group_TwoWeeks = pd.read_csv(data_dir + 'PercDelaysBy_' + grouping_col + '_TwoWeeks.csv')
    PercDelaysBy_Group_FourWeeks = pd.read_csv(data_dir + 'PercDelaysBy_' + grouping_col + '_FourWeeks.csv')
    PercDelaysBy_Group_TwelveWeeks = pd.read_csv(data_dir + 'PercDelaysBy_' + grouping_col + '_TwelveWeeks.csv')
    PercDelaysBy_Group_SinceRecordsBegan = pd.read_csv(data_dir + 'PercDelaysBy_' + grouping_col + '_SinceRecordsBegan.csv')
    #
    CancellationCountBy_Group_OneWeek = pd.read_csv(data_dir + 'CancellationCountBy_' + grouping_col + '_OneWeek.csv')
    CancellationCountBy_Group_TwoWeeks = pd.read_csv(data_dir + 'CancellationCountBy_' + grouping_col + '_TwoWeeks.csv')
    CancellationCountBy_Group_FourWeeks = pd.read_csv(data_dir + 'CancellationCountBy_' + grouping_col + '_FourWeeks.csv')
    CancellationCountBy_Group_TwelveWeeks = pd.read_csv(data_dir + 'CancellationCountBy_' + grouping_col + '_TwelveWeeks.csv')
    CancellationCountBy_Group_SinceRecordsBegan = pd.read_csv(data_dir + 'CancellationCountBy_' + grouping_col + '_SinceRecordsBegan.csv')

    Mean_OneWeek = (MeanBy_Group_OneWeek[[grouping_col, 'mean', 'count']]
                    .rename(columns={'mean': 'Mean_OneWeek', 'count': 'Count_OneWeek_NoCancellations'}))
    Mean_TwoWeeks = (MeanBy_Group_TwoWeeks[[grouping_col, 'mean', 'count']]
                     .rename(columns={'mean': 'Mean_TwoWeeks', 'count': 'Count_TwoWeeks_NoCancellations'}))
    Mean_FourWeeks = (MeanBy_Group_FourWeeks[[grouping_col, 'mean', 'count']]
                      .rename(columns={'mean': 'Mean_FourWeeks', 'count': 'Count_FourWeeks_NoCancellations'}))
    Mean_TwelveWeeks = (MeanBy_Group_TwelveWeeks[[grouping_col, 'mean', 'count']]
                      .rename(columns={'mean': 'Mean_TwelveWeeks', 'count': 'Count_TwelveWeeks_NoCancellations'}))
    Mean_SinceRecordsBegan = (MeanBy_Group_SinceRecordsBegan[[grouping_col, 'mean', 'count']]
                              .rename(columns={'mean': 'Mean_SinceRecordsBegan', 'count': 'Count_SinceRecordsBegan_NoCancellations'}))

    PercDelays_OneWeek = (PercDelaysBy_Group_OneWeek[[grouping_col, 'delay_lte5Mins_perc']]
                          .rename(columns={'delay_lte5Mins_perc': 'Perc_lte5MinDelay_OneWeek'}))
    PercDelays_TwoWeeks = (PercDelaysBy_Group_TwoWeeks[[grouping_col, 'delay_lte5Mins_perc']]
                           .rename(columns={'delay_lte5Mins_perc': 'Perc_lte5MinDelay_TwoWeeks'}))
    PercDelays_FourWeeks = (PercDelaysBy_Group_FourWeeks[[grouping_col, 'delay_lte5Mins_perc']]
                            .rename(columns={'delay_lte5Mins_perc': 'Perc_lte5MinDelay_FourWeeks'}))
    PercDelays_TwelveWeeks = (PercDelaysBy_Group_TwelveWeeks[[grouping_col, 'delay_lte5Mins_perc']]
                            .rename(columns={'delay_lte5Mins_perc': 'Perc_lte5MinDelay_TwelveWeeks'}))
    PercDelays_SinceRecordsBegan = (PercDelaysBy_Group_SinceRecordsBegan[[grouping_col, 'delay_lte5Mins_perc']]
                                    .rename(columns={'delay_lte5Mins_perc': 'Perc_lte5MinDelay_SinceRecordsBegan'}))

    Cancellations_OneWeek = (CancellationCountBy_Group_OneWeek[[grouping_col, 'count_True', 'cancellation_percentage']]
                             .rename(columns={'count_True': 'cancellation_count_OneWeek',
                                              'cancellation_percentage': 'cancellation_percentage_OneWeek'}))
    Cancellations_TwoWeeks = (CancellationCountBy_Group_TwoWeeks[[grouping_col, 'count_True', 'cancellation_percentage']]
                              .rename(columns={'count_True': 'cancellation_count_TwoWeeks',
                                               'cancellation_percentage': 'cancellation_percentage_TwoWeeks'}))
    Cancellations_FourWeeks = (CancellationCountBy_Group_FourWeeks[[grouping_col, 'count_True', 'cancellation_percentage']]
                               .rename(columns={'count_True': 'cancellation_count_FourWeeks',
                                                'cancellation_percentage': 'cancellation_percentage_FourWeeks'}))
    Cancellations_TwelveWeeks = (CancellationCountBy_Group_TwelveWeeks[[grouping_col, 'count_True', 'cancellation_percentage']]
                               .rename(columns={'count_True': 'cancellation_count_TwelveWeeks',
                                                'cancellation_percentage': 'cancellation_percentage_TwelveWeeks'}))
    Cancellations_SinceRecordsBegan = (CancellationCountBy_Group_SinceRecordsBegan[[grouping_col, 'count_True', 'cancellation_percentage']]
                                       .rename(columns={'count_True': 'cancellation_count_SinceRecordsBegan',
                                                        'cancellation_percentage': 'cancellation_percentage_SinceRecordsBegan'}))

    summary_table = Mean_OneWeek
    for df in [Mean_TwoWeeks, Mean_FourWeeks, Mean_TwelveWeeks, Mean_SinceRecordsBegan,
               PercDelays_OneWeek, PercDelays_TwoWeeks, PercDelays_FourWeeks, PercDelays_TwelveWeeks, PercDelays_SinceRecordsBegan,
               Cancellations_OneWeek, Cancellations_TwoWeeks, Cancellations_FourWeeks, Cancellations_TwelveWeeks, Cancellations_SinceRecordsBegan]:
        summary_table = pd.merge(summary_table, df, on=grouping_col, how='outer')
    if line_filter:
        summary_table = summary_table[summary_table.Service.isin(services)].copy()
    # print(summary_table.head(10))

    # There'll be NAs for lines where there were no cancellations in the given time period - fill with 0s
    for col in ['cancellation_count_OneWeek', 'cancellation_percentage_OneWeek', 'Perc_lte5MinDelay_OneWeek',
                'cancellation_count_TwoWeeks', 'cancellation_percentage_TwoWeeks', 'Perc_lte5MinDelay_TwoWeeks',
                'cancellation_count_FourWeeks', 'cancellation_percentage_FourWeeks', 'Perc_lte5MinDelay_FourWeeks',
                'cancellation_count_TwelveWeeks', 'cancellation_percentage_TwelveWeeks', 'Perc_lte5MinDelay_TwelveWeeks',
                'cancellation_count_SinceRecordsBegan', 'cancellation_percentage_SinceRecordsBegan', 'Perc_lte5MinDelay_SinceRecordsBegan']:
        summary_table[col] = summary_table[col].fillna(0)

    summary_table['Count_OneWeek'] = summary_table['Count_OneWeek_NoCancellations'] + summary_table['cancellation_count_OneWeek']
    summary_table['Count_TwoWeeks'] = summary_table['Count_TwoWeeks_NoCancellations'] + summary_table['cancellation_count_TwoWeeks']
    summary_table['Count_FourWeeks'] = summary_table['Count_FourWeeks_NoCancellations'] + summary_table['cancellation_count_FourWeeks']
    summary_table['Count_TwelveWeeks'] = summary_table['Count_TwelveWeeks_NoCancellations'] + summary_table['cancellation_count_TwelveWeeks']
    summary_table['Count_SinceRecordsBegan'] = summary_table['Count_SinceRecordsBegan_NoCancellations'] + summary_table['cancellation_count_SinceRecordsBegan']

    if not line_filter:
        # Descriptive names and colours for line groups
        lineGroup_descriptiveNames = {'1':  ['Antrim Rd', '#f7941e'],
                                      '2':  ['Shore Rd', '#ed1e24'],
                                      '3':  ['Holywood Rd', '#00a99d'],
                                      '4':  ["Upper N'Ards Rd", '#a72c31'],
                                      '5':  ['Castlereagh Rd', '#53b7e8'],
                                      '6':  ['Cregagh Rd', '#005826'],
                                      '7':  ['Ormeau Rd', '#a6ce39'],
                                      '8':  ['Malone Rd', '#6f2c91'],
                                      '9':  ['Lisburn Rd', '#ec008c'],
                                      '10': ['Falls Rd', '#b0acd5'],
                                      '11': ['Shankill Rd', '#845339'],
                                      '12': ['Oldpark Rd', '#0072bc'],
                                      'G':  ['East-West / Titanic', '#000000']}
        lineGroup_descriptiveNames_df = pd.DataFrame.from_dict(lineGroup_descriptiveNames,
            orient='index', columns=['descriptive_name', 'colour'])
        summary_table = pd.merge(summary_table, lineGroup_descriptiveNames_df, left_on=grouping_col, right_index=True)
    else:
        summary_table['descriptive_name'] = ''
        summary_table['colour'] = ''

    ## Round off the mean delay and % delay values
    for col in ['Mean_OneWeek', 'Mean_TwoWeeks', 'Mean_FourWeeks', 'Mean_TwelveWeeks', 'Mean_SinceRecordsBegan']:
        summary_table[col] = round(summary_table[col], 1)

    # Round each % of departures to nearest percentage
    for col in ['Perc_lte5MinDelay_OneWeek', 'Perc_lte5MinDelay_TwoWeeks', 'Perc_lte5MinDelay_FourWeeks',
                'Perc_lte5MinDelay_TwelveWeeks', 'Perc_lte5MinDelay_SinceRecordsBegan']:
        summary_table[col] = round(summary_table[col], 0).astype(int)

    # Round each cancellation % to nearest percentage
    for col in ['cancellation_percentage_OneWeek', 'cancellation_percentage_TwoWeeks', 'cancellation_percentage_FourWeeks',
                'cancellation_percentage_TwelveWeeks']:
        # # There'll be NAs for lines where there were no cancellations in the given time period
        # summary_table[col] = summary_table[col].fillna(0)
        summary_table[col] = round(summary_table[col], 0).astype(int)

    # Make sure departure counts are integers
    for col in ['Count_OneWeek', 'Count_TwoWeeks', 'Count_FourWeeks', 'Count_TwelveWeeks', 'Count_SinceRecordsBegan']:
        summary_table[col] = summary_table[col].astype(int)

    summary_table = summary_table[[grouping_col, 'descriptive_name', 'colour',
                                   'Mean_OneWeek', 'Mean_TwoWeeks', 'Mean_FourWeeks', 'Mean_TwelveWeeks', 'Mean_SinceRecordsBegan',
                                   'Count_OneWeek', 'Count_TwoWeeks', 'Count_FourWeeks', 'Count_TwelveWeeks', 'Count_SinceRecordsBegan',
                                   'Perc_lte5MinDelay_OneWeek', 'Perc_lte5MinDelay_TwoWeeks', 'Perc_lte5MinDelay_FourWeeks',
                                   'Perc_lte5MinDelay_TwelveWeeks', 'Perc_lte5MinDelay_SinceRecordsBegan',
                                   'cancellation_percentage_OneWeek', 'cancellation_percentage_TwoWeeks', 'cancellation_percentage_FourWeeks',
                                   'cancellation_percentage_TwelveWeeks']]
    # print(summary_table.head(10))

    return(summary_table)


summary_table = make_summary_table()
summary_table_lines = {}
for line in lines_list:
    summary_table_lines[line] = make_summary_table(line_filter=line)

@app.route('/')
def homepage():
    return(render_template('homepage.html', title='Home',
                           summary_table=summary_table,
                           HighLevelSummary=HighLevelSummary[HighLevelSummary.Line=='All']))

@app.route('/lines/<line>')
def line_summary(line):
    if line not in lines_list:
        ### TODO: Handle this
        return()
    if line == 'G':
        line_description = 'Glider lines'
    else:
        line_description = line + ' Metro line'
    return(render_template('line_summary.html', title=f'Line {line} Summary', line=line,
                           # line_descriptive_name is like "1 (Antrim Rd)"
                           line_descriptive_name=summary_table[summary_table.Line==line]['descriptive_name'].values[0],
                           # line_description is like "1 Metro line"
                           line_description=line_description,
                           line_colour=summary_table[summary_table.Line==line]['colour'].values[0],
                           summary_table=summary_table_lines[line],
                           HighLevelSummary=HighLevelSummary[HighLevelSummary.Line==line]))

##################
# Altair Functions
##################

#####################################
# "Average Delay by Time of Day" card
#####################################
def make_MeanByTimeOfDay_plot(date_range, line_filter=None):
    if line_filter:
        if date_range == 'OneWeek':
            plot_df = pd.read_csv(data_dir + 'MeanBy_Line_TimeOfDay30MinBuckets_WeekdayOrWeekend_OneWeek.csv')
        elif date_range == 'TwoWeeks':
            plot_df = pd.read_csv(data_dir + 'MeanBy_Line_TimeOfDay30MinBuckets_WeekdayOrWeekend_TwoWeeks.csv')
        elif date_range == 'FourWeeks':
            plot_df = pd.read_csv(data_dir + 'MeanBy_Line_TimeOfDay30MinBuckets_WeekdayOrWeekend_FourWeeks.csv')
        elif date_range == 'TwelveWeeks':
            plot_df = pd.read_csv(data_dir + 'MeanBy_Line_TimeOfDay30MinBuckets_WeekdayOrWeekend_TwelveWeeks.csv')
        else:
            plot_df = pd.read_csv(data_dir + 'MeanBy_Line_TimeOfDay30MinBuckets_WeekdayOrWeekend_SinceRecordsBegan.csv')
        plot_df = plot_df[plot_df.Line == line_filter]
        # print(f'{date_range}, {line_filter}, {plot_df.shape}')
    else:
        if date_range == 'OneWeek':
            plot_df = pd.read_csv(data_dir + 'MeanBy_TimeOfDay30MinBuckets_WeekdayOrWeekend_OneWeek.csv')
        elif date_range == 'TwoWeeks':
            plot_df = pd.read_csv(data_dir + 'MeanBy_TimeOfDay30MinBuckets_WeekdayOrWeekend_TwoWeeks.csv')
        elif date_range == 'FourWeeks':
            plot_df = pd.read_csv(data_dir + 'MeanBy_TimeOfDay30MinBuckets_WeekdayOrWeekend_FourWeeks.csv')
        elif date_range == 'TwelveWeeks':
            plot_df = pd.read_csv(data_dir + 'MeanBy_TimeOfDay30MinBuckets_WeekdayOrWeekend_TwelveWeeks.csv')
        else:
            plot_df = pd.read_csv(data_dir + 'MeanBy_TimeOfDay30MinBuckets_WeekdayOrWeekend_SinceRecordsBegan.csv')
        # print(f'{date_range}, {line_filter}, {plot_df.shape}')

    plot_df['Time'] = pd.to_datetime(plot_df['PlannedDepartureTime30MinBuckets'], format='%H:%M:%S')
    plot_df = plot_df[(plot_df.Time.dt.time >= time(7,0)) & (plot_df.Time.dt.time <= time(23,0))].copy()
    plot_df['Day Type'] = plot_df['WeekdayOrWeekend']
    plot_df['Average Delay (mins)'] = round(plot_df['mean'], 2)

    base = (
        alt.Chart(plot_df)
        .mark_point(tooltip=True)
        .encode(x=alt.X('Time:T',
                        axis=alt.Axis(title=['Planned Departure Time','(30 Minute Buckets)'], format='%H:%M')),
        y=alt.Y('Average Delay (mins)', axis=alt.Axis(title='Average Delay (minutes)')),
        color=alt.Color('Day Type')
    )).properties(width='container', height=350)

    lines = base.mark_line(tooltip=True).encode(
        size=alt.value(3),
        color=alt.Color('Day Type', legend=alt.Legend(title="", orient="top", labelFontSize=15, symbolSize=1000, columns=1))#,
    ).properties(
        width='container',
        height=350
    )

    chart = lines
    chart = chart.configure_axis(labelFontSize=15, titleFontSize=15)

    return chart.to_json()

# Create jsons once on app load
# All routes
MeanByTimeOfDay_plot_OneWeek_json = make_MeanByTimeOfDay_plot('OneWeek')
MeanByTimeOfDay_plot_TwoWeeks_json = make_MeanByTimeOfDay_plot('TwoWeeks')
MeanByTimeOfDay_plot_FourWeeks_json = make_MeanByTimeOfDay_plot('FourWeeks')
MeanByTimeOfDay_plot_TwelveWeeks_json = make_MeanByTimeOfDay_plot('TwelveWeeks')
MeanByTimeOfDay_plot_SinceRecordsBegan_json = make_MeanByTimeOfDay_plot('SinceRecordsBegan')
# Line by line
MeanByTimeOfDay_Line_plot_jsons = {}
for line in lines_list:
    MeanByTimeOfDay_Line_plot_jsons[line] = {}
    MeanByTimeOfDay_Line_plot_jsons[line]['OneWeek'] = make_MeanByTimeOfDay_plot('OneWeek', line)
    MeanByTimeOfDay_Line_plot_jsons[line]['TwoWeeks'] = make_MeanByTimeOfDay_plot('TwoWeeks', line)
    MeanByTimeOfDay_Line_plot_jsons[line]['FourWeeks'] = make_MeanByTimeOfDay_plot('FourWeeks', line)
    MeanByTimeOfDay_Line_plot_jsons[line]['TwelveWeeks'] = make_MeanByTimeOfDay_plot('TwelveWeeks', line)
    MeanByTimeOfDay_Line_plot_jsons[line]['SinceRecordsBegan'] = make_MeanByTimeOfDay_plot('SinceRecordsBegan', line)


# @app.route('/plots/plot_MeanByTimeOfDay_OneWeek')
# def plot_MeanByTimeOfDay_OneWeek():
#     return(MeanByTimeOfDay_plot_OneWeek_json)

# @app.route('/plots/plot_MeanByTimeOfDay_TwoWeeks')
# def plot_MeanByTimeOfDay_TwoWeeks():
#     return(MeanByTimeOfDay_plot_TwoWeeks_json)

# @app.route('/plots/plot_MeanByTimeOfDay_FourWeeks')
# def plot_MeanByTimeOfDay_FourWeeks():
#     return(MeanByTimeOfDay_plot_FourWeeks_json)

# @app.route('/plots/plot_MeanByTimeOfDay_TwelveWeeks')
# def plot_MeanByTimeOfDay_TwelveWeeks():
#     return(MeanByTimeOfDay_plot_TwelveWeeks_json)

# @app.route('/plots/plot_MeanByTimeOfDay_SinceRecordsBegan')
# def plot_MeanByTimeOfDay_SinceRecordsBegan():
#     return(MeanByTimeOfDay_plot_SinceRecordsBegan_json)

@app.route('/plots/plot_MeanByTimeOfDay_SinceRecordsBegan/<line>')
def plot_MeanByTimeOfDay_SinceRecordsBegan(line):
    if line=='All':
        return(MeanByTimeOfDay_plot_SinceRecordsBegan_json)
    else:
        return(MeanByTimeOfDay_Line_plot_jsons[line]['SinceRecordsBegan'])

@app.route('/plots/plot_MeanByTimeOfDay_TwelveWeeks/<line>')
def plot_MeanByTimeOfDay_TwelveWeeks(line):
    if line=='All':
        return(MeanByTimeOfDay_plot_TwelveWeeks_json)
    else:
        return(MeanByTimeOfDay_Line_plot_jsons[line]['TwelveWeeks'])

@app.route('/plots/plot_MeanByTimeOfDay_FourWeeks/<line>')
def plot_MeanByTimeOfDay_FourWeeks(line):
    if line=='All':
        return(MeanByTimeOfDay_plot_FourWeeks_json)
    else:
        return(MeanByTimeOfDay_Line_plot_jsons[line]['FourWeeks'])

@app.route('/plots/plot_MeanByTimeOfDay_TwoWeeks/<line>')
def plot_MeanByTimeOfDay_TwoWeeks(line):
    if line=='All':
        return(MeanByTimeOfDay_plot_TwoWeeks_json)
    else:
        return(MeanByTimeOfDay_Line_plot_jsons[line]['TwoWeeks'])

@app.route('/plots/plot_MeanByTimeOfDay_OneWeek/<line>')
def plot_MeanByTimeOfDay_OneWeek(line):
    if line=='All':
        return(MeanByTimeOfDay_plot_OneWeek_json)
    else:
        return(MeanByTimeOfDay_Line_plot_jsons[line]['OneWeek'])


##############################
# "Average Delay by Date" card
##############################
def make_MeanByDate_plot(date_range, line_filter=None):
    if line_filter:
        plot_df = pd.read_csv(data_dir + 'MeanBy_Line_Date_SinceRecordsBegan.csv')
        plot_df = plot_df[plot_df.Line == line_filter]
    else:
        plot_df = pd.read_csv(data_dir + 'MeanBy_Date_SinceRecordsBegan.csv')
        # plot_df = MeanBy_Date_SinceRecordsBegan.copy()

    plot_df['PlannedDepartureDate'] = pd.to_datetime(plot_df['PlannedDepartureDate'], format='%Y/%m/%d')

    if date_range == 'OneWeek':
        plot_df = plot_df[(datetime.now().date() - plot_df['PlannedDepartureDate'].dt.date) <= timedelta(weeks=1)]
    elif date_range == 'TwoWeeks':
        plot_df = plot_df[(datetime.now().date() - plot_df['PlannedDepartureDate'].dt.date) <= timedelta(weeks=2)]
    elif date_range == 'FourWeeks':
        plot_df = plot_df[(datetime.now().date() - plot_df['PlannedDepartureDate'].dt.date) <= timedelta(weeks=4)]
    elif date_range == 'TwelveWeeks':
        plot_df = plot_df[(datetime.now().date() - plot_df['PlannedDepartureDate'].dt.date) <= timedelta(weeks=12)]

    plot_df['Date'] = pd.to_datetime(plot_df['PlannedDepartureDate'], format='%Y/%m/%d')

    plot_df['Average Delay (mins)'] = round(plot_df['mean'], 2)
    plot_df['7-Day Average (mins)'] = round(plot_df['rolling_avg_7day'], 2)
    base = (
        alt.Chart(plot_df)
        .mark_point(tooltip=True)
        .encode(
            x=alt.X('Date:T',
                    axis=alt.Axis(title='Date', format='%e %b %y')),
            y=alt.Y('Average Delay (mins)', axis=alt.Axis(title='Average Departure Delay (minutes)'))
            )
        ).properties(width='container', height=350)

    fit = base.mark_line(color='red', tooltip=True
        ).encode(#x='PlannedDepartureDateFormatted', y='rolling_avg_7day')
                 x=alt.X('Date:T',
                         axis=alt.Axis(title='Date', format='%e %b %y')),
                 y=alt.Y('7-Day Average (mins)')#=, axis=alt.Axis(title='7-Day Average Delay (mins)'))
        ).properties(width='container',
                     height=350
        )

    chart = base + fit
    chart = chart.configure_axis(labelFontSize=15, titleFontSize=15)

    return chart.to_json()    

# Create jsons once on app load
MeanByDate_plot_OneWeek_json = make_MeanByDate_plot('OneWeek')
MeanByDate_plot_TwoWeeks_json = make_MeanByDate_plot('TwoWeeks')
MeanByDate_plot_FourWeeks_json = make_MeanByDate_plot('FourWeeks')
MeanByDate_plot_TwelveWeeks_json = make_MeanByDate_plot('TwelveWeeks')
MeanByDate_plot_SinceRecordsBegan_json = make_MeanByDate_plot('SinceRecordsBegan')

# Line by line
MeanByDate_Line_plot_jsons = {}
for line in lines_list:
    MeanByDate_Line_plot_jsons[line] = {}
    MeanByDate_Line_plot_jsons[line]['OneWeek'] = make_MeanByDate_plot('OneWeek', line)
    MeanByDate_Line_plot_jsons[line]['TwoWeeks'] = make_MeanByDate_plot('TwoWeeks', line)
    MeanByDate_Line_plot_jsons[line]['FourWeeks'] = make_MeanByDate_plot('FourWeeks', line)
    MeanByDate_Line_plot_jsons[line]['TwelveWeeks'] = make_MeanByDate_plot('TwelveWeeks', line)
    MeanByDate_Line_plot_jsons[line]['SinceRecordsBegan'] = make_MeanByDate_plot('SinceRecordsBegan', line)


# @app.route('/plots/plot_MeanByDate_OneWeek')
# def plot_MeanByDate_OneWeek():
#     return(MeanByDate_plot_OneWeek_json)

# @app.route('/plots/plot_MeanByDate_TwoWeeks')
# def plot_MeanByDate_TwoWeeks():
#     return(MeanByDate_plot_TwoWeeks_json)

# @app.route('/plots/plot_MeanByDate_FourWeeks')
# def plot_MeanByDate_FourWeeks():
#     return(MeanByDate_plot_FourWeeks_json)

# @app.route('/plots/plot_MeanByDate_TwelveWeeks')
# def plot_MeanByDate_TwelveWeeks():
#     return(MeanByDate_plot_TwelveWeeks_json)

# @app.route('/plots/plot_MeanByDate_SinceRecordsBegan')
# def plot_MeanByDate_SinceRecordsBegan():
#     return(MeanByDate_plot_SinceRecordsBegan_json)


@app.route('/plots/plot_MeanByDate_SinceRecordsBegan/<line>')
def plot_MeanByDate_SinceRecordsBegan(line):
    if line=='All':
        return(MeanByDate_plot_SinceRecordsBegan_json)
    else:
        return(MeanByDate_Line_plot_jsons[line]['SinceRecordsBegan'])

@app.route('/plots/plot_MeanByDate_TwelveWeeks/<line>')
def plot_MeanByDate_TwelveWeeks(line):
    if line=='All':
        return(MeanByDate_plot_TwelveWeeks_json)
    else:
        return(MeanByDate_Line_plot_jsons[line]['TwelveWeeks'])

@app.route('/plots/plot_MeanByDate_FourWeeks/<line>')
def plot_MeanByDate_FourWeeks(line):
    if line=='All':
        return(MeanByDate_plot_FourWeeks_json)
    else:
        return(MeanByDate_Line_plot_jsons[line]['FourWeeks'])

@app.route('/plots/plot_MeanByDate_TwoWeeks/<line>')
def plot_MeanByDate_TwoWeeks(line):
    if line=='All':
        return(MeanByDate_plot_TwoWeeks_json)
    else:
        return(MeanByDate_Line_plot_jsons[line]['TwoWeeks'])

@app.route('/plots/plot_MeanByDate_OneWeek/<line>')
def plot_MeanByDate_OneWeek(line):
    if line=='All':
        return(MeanByDate_plot_OneWeek_json)
    else:
        return(MeanByDate_Line_plot_jsons[line]['OneWeek'])

###########################################
# "Percentage of "On-Time" Departures" card
###########################################
def make_PercDelayByDate_plot(date_range, line_filter=None, multirow_legend=False, show_all_points=True):
    if line_filter:
        PercDelaysBy_Date_SinceRecordsBegan = pd.read_csv(data_dir + 'PercDelaysBy_Line_Date_SinceRecordsBegan.csv')
        PercDelaysBy_Date_SinceRecordsBegan = PercDelaysBy_Date_SinceRecordsBegan[PercDelaysBy_Date_SinceRecordsBegan.Line == line_filter].copy()
    else:
        PercDelaysBy_Date_SinceRecordsBegan = pd.read_csv(data_dir + 'PercDelaysBy_Date_SinceRecordsBegan.csv')

    y_min = min(PercDelaysBy_Date_SinceRecordsBegan.delay_lte3Mins_perc.min(),
                PercDelaysBy_Date_SinceRecordsBegan.delay_lte7Mins_perc.min(),
                PercDelaysBy_Date_SinceRecordsBegan.delay_lte15Mins_perc.min())

    full_df = PercDelaysBy_Date_SinceRecordsBegan.copy()

    plot_df = (full_df[['PlannedDepartureDate', 'delay_lte2Mins_perc','rolling_perc_lte2Mins']]
               .rename(columns={'delay_lte2Mins_perc': 'delay_lteXMins_perc','rolling_perc_lte2Mins': 'rolling_perc_lteXMins'}))
    plot_df['Delay'] = '2 mins'

    temp = (full_df[['PlannedDepartureDate', 'delay_lte3Mins_perc','rolling_perc_lte3Mins']]
            .rename(columns={'delay_lte3Mins_perc': 'delay_lteXMins_perc','rolling_perc_lte3Mins': 'rolling_perc_lteXMins'}))
    temp['Delay'] = '3 mins'
    plot_df = pd.concat([plot_df, temp])

    temp = (full_df[['PlannedDepartureDate', 'delay_lte5Mins_perc','rolling_perc_lte5Mins']]
            .rename(columns={'delay_lte5Mins_perc': 'delay_lteXMins_perc','rolling_perc_lte5Mins': 'rolling_perc_lteXMins'}))
    temp['Delay'] = '5 mins'
    plot_df = pd.concat([plot_df, temp])

    temp = (full_df[['PlannedDepartureDate', 'delay_lte7Mins_perc','rolling_perc_lte7Mins']]
            .rename(columns={'delay_lte7Mins_perc': 'delay_lteXMins_perc','rolling_perc_lte7Mins': 'rolling_perc_lteXMins'}))
    temp['Delay'] = '7 mins'
    plot_df = pd.concat([plot_df, temp])

    temp = (full_df[['PlannedDepartureDate', 'delay_lte10Mins_perc','rolling_perc_lte10Mins']]
            .rename(columns={'delay_lte10Mins_perc': 'delay_lteXMins_perc','rolling_perc_lte10Mins': 'rolling_perc_lteXMins'}))
    temp['Delay'] = '10 mins'
    plot_df = pd.concat([plot_df, temp])

    temp = (full_df[['PlannedDepartureDate', 'delay_lte15Mins_perc','rolling_perc_lte15Mins']]
            .rename(columns={'delay_lte15Mins_perc': 'delay_lteXMins_perc','rolling_perc_lte15Mins': 'rolling_perc_lteXMins'}))
    temp['Delay'] = '15 mins'
    plot_df = pd.concat([plot_df, temp])

    plot_df['rolling_perc_lteXMins'] = plot_df['rolling_perc_lteXMins'] * 100

    plot_df['Date'] = pd.to_datetime(plot_df['PlannedDepartureDate'], format='%Y/%m/%d')

    if date_range == 'OneWeek':
        plot_df = plot_df[(datetime.now().date() - plot_df['Date'].dt.date) <= timedelta(weeks=1)]
    elif date_range == 'TwoWeeks':
        plot_df = plot_df[(datetime.now().date() - plot_df['Date'].dt.date) <= timedelta(weeks=2)]
    elif date_range == 'FourWeeks':
        plot_df = plot_df[(datetime.now().date() - plot_df['Date'].dt.date) <= timedelta(weeks=4)]
    elif date_range == 'TwelveWeeks':
        plot_df = plot_df[(datetime.now().date() - plot_df['Date'].dt.date) <= timedelta(weeks=12)]

    if show_all_points:
        plot_df['delay_lteXMins_perc'] = np.where(plot_df['Delay'].isin(['3 mins', '7 mins', '15 mins']), plot_df['delay_lteXMins_perc'], np.nan)
    else:
        plot_df['delay_lteXMins_perc'] = np.where(plot_df['Delay'] != '7 mins', np.nan, plot_df['delay_lteXMins_perc'])
    plot_df['delay_lteXMins_perc'] = round(plot_df['delay_lteXMins_perc'],1)
    plot_df = plot_df[(plot_df.Delay.isin(['3 mins', '7 mins', '15 mins']))].copy()
    y_min = (min(y_min, plot_df.rolling_perc_lteXMins.min())//10)*10

    plot_df = plot_df.rename(columns={'delay_lteXMins_perc': 'Departures with Delay ≤ 7 Minutes (%)'})

    plot_df['Percentage over 7 Days'] = round(plot_df['rolling_perc_lteXMins'], 1)

    domain = ['3 mins', '7 mins', '15 mins']
    range_ = ['red', 'green', 'blue']

    base = alt.Chart(plot_df).properties(width='container', height=350)
    if show_all_points:
        base = (
            base.mark_point(tooltip=True).encode(
                x=alt.X('Date:T', axis=alt.Axis(title='Date', format='%e %b %y')),
                y=alt.Y('Departures with Delay ≤ 7 Minutes (%)',
                        axis=alt.Axis(title='Departures within X Minutes of Schedule (%)'),
                        scale=alt.Scale(domain=[y_min,100])),
                color=alt.Color('Delay', legend=alt.Legend(symbolSize=250)))
            )
    else:
        base = (
            base.mark_point(tooltip=True, color='green').encode(
                x=alt.X('Date:T', axis=alt.Axis(title='Date', format='%e %b %y')),
                y=alt.Y('Departures with Delay ≤ 7 Minutes (%)',
                        axis=alt.Axis(title='Departures within X Minutes of Schedule (%)'),
                        scale=alt.Scale(domain=[y_min,100])))
            )   

    fit = base.mark_line(tooltip=True).properties(width='container', height=350)
    if multirow_legend:
        fit = (
            fit.encode(x=alt.X('Date:T'),
                       y=alt.Y('Percentage over 7 Days'),
                       color=alt.Color('Delay', scale=alt.Scale(domain=domain, range=range_),
                                       legend=alt.Legend(title="Departure Delay ≤", orient="top", titleFontSize=15,
                                                         labelFontSize=15, titleLimit=0, columns=1, symbolSize=1000)))
            )
    else:
        fit = (
            fit.encode(x=alt.X('Date:T'),
                       y=alt.Y('Percentage over 7 Days'),
                       color=alt.Color('Delay', scale=alt.Scale(domain=domain, range=range_),
                                       legend=alt.Legend(title="Departure Delay ≤", orient="top", titleFontSize=15,
                                                         labelFontSize=15, titleLimit=0, symbolSize=1000)))
            )

    chart = base + fit
    chart = chart.configure_axis(labelFontSize=15, titleFontSize=15)

    return chart.to_json()

# Create jsons once on app load
PercDelayByDate_plot_OneWeek_json = make_PercDelayByDate_plot('OneWeek')
PercDelayByDate_plot_TwoWeeks_json = make_PercDelayByDate_plot('TwoWeeks')
PercDelayByDate_plot_FourWeeks_json = make_PercDelayByDate_plot('FourWeeks')
PercDelayByDate_plot_TwelveWeeks_json = make_PercDelayByDate_plot('TwelveWeeks')
PercDelayByDate_plot_SinceRecordsBegan_json = make_PercDelayByDate_plot('SinceRecordsBegan', show_all_points=False)
# Separate jsons for small screens, where the legend is split into multiple rows (one column)
PercDelayByDate_plot_OneWeek_json_smallScreen = make_PercDelayByDate_plot('OneWeek', multirow_legend=True)
PercDelayByDate_plot_TwoWeeks_json_smallScreen = make_PercDelayByDate_plot('TwoWeeks', multirow_legend=True)
PercDelayByDate_plot_FourWeeks_json_smallScreen = make_PercDelayByDate_plot('FourWeeks', multirow_legend=True)
PercDelayByDate_plot_TwelveWeeks_json_smallScreen = make_PercDelayByDate_plot('TwelveWeeks', multirow_legend=True)
PercDelayByDate_plot_SinceRecordsBegan_json_smallScreen = make_PercDelayByDate_plot('SinceRecordsBegan', multirow_legend=True, show_all_points=False)

# Line by line
PercDelaysByDate_Line_plot_jsons = {}
PercDelaysByDate_Line_plot_jsons_smallScreen = {}
for line in lines_list:
    PercDelaysByDate_Line_plot_jsons[line] = {}
    PercDelaysByDate_Line_plot_jsons_smallScreen[line] = {}

    PercDelaysByDate_Line_plot_jsons[line]['OneWeek'] = make_PercDelayByDate_plot('OneWeek', line)
    PercDelaysByDate_Line_plot_jsons[line]['TwoWeeks'] = make_PercDelayByDate_plot('TwoWeeks', line)
    PercDelaysByDate_Line_plot_jsons[line]['FourWeeks'] = make_PercDelayByDate_plot('FourWeeks', line)
    PercDelaysByDate_Line_plot_jsons[line]['TwelveWeeks'] = make_PercDelayByDate_plot('TwelveWeeks', line)
    PercDelaysByDate_Line_plot_jsons[line]['SinceRecordsBegan'] = make_PercDelayByDate_plot('SinceRecordsBegan',line, show_all_points=False)
    # Separate jsons for small screens, where the legend is split into multiple rows (one column)
    PercDelaysByDate_Line_plot_jsons_smallScreen[line]['OneWeek'] = make_PercDelayByDate_plot('OneWeek', line)
    PercDelaysByDate_Line_plot_jsons_smallScreen[line]['TwoWeeks'] = make_PercDelayByDate_plot('TwoWeeks', line)
    PercDelaysByDate_Line_plot_jsons_smallScreen[line]['FourWeeks'] = make_PercDelayByDate_plot('FourWeeks', line)
    PercDelaysByDate_Line_plot_jsons_smallScreen[line]['TwelveWeeks'] = make_PercDelayByDate_plot('TwelveWeeks', line)
    PercDelaysByDate_Line_plot_jsons_smallScreen[line]['SinceRecordsBegan'] = make_PercDelayByDate_plot('SinceRecordsBegan',line, multirow_legend=True, show_all_points=False)


# @app.route('/plots/plot_PercDelayByDate_OneWeek')
# def plot_PercDelayByDate_OneWeek():
#     return(PercDelayByDate_plot_OneWeek_json)

# @app.route('/plots/plot_PercDelayByDate_TwoWeeks')
# def plot_PercDelayByDate_TwoWeeks():
#     return(PercDelayByDate_plot_TwoWeeks_json)

# @app.route('/plots/plot_PercDelayByDate_FourWeeks')
# def plot_PercDelayByDate_FourWeeks():
#     return(PercDelayByDate_plot_FourWeeks_json)

# @app.route('/plots/plot_PercDelayByDate_TwelveWeeks')
# def plot_PercDelayByDate_TwelveWeeks():
#     return(PercDelayByDate_plot_TwelveWeeks_json)

# @app.route('/plots/plot_PercDelayByDate_SinceRecordsBegan')
# def plot_PercDelayByDate_SinceRecordsBegan():
#     return(PercDelayByDate_plot_SinceRecordsBegan_json)

# @app.route('/plots/plot_PercDelayByDate_OneWeek_smallScreen')
# def plot_PercDelayByDate_OneWeek_smallScreen():
#     return(PercDelayByDate_plot_OneWeek_json_smallScreen)

# @app.route('/plots/plot_PercDelayByDate_TwoWeeks_smallScreen')
# def plot_PercDelayByDate_TwoWeeks_smallScreen():
#     return(PercDelayByDate_plot_TwoWeeks_json_smallScreen)

# @app.route('/plots/plot_PercDelayByDate_FourWeeks_smallScreen')
# def plot_PercDelayByDate_FourWeeks_smallScreen():
#     return(PercDelayByDate_plot_FourWeeks_json_smallScreen)

# @app.route('/plots/plot_PercDelayByDate_TwelveWeeks_smallScreen')
# def plot_PercDelayByDate_TwelveWeeks_smallScreen():
#     return(PercDelayByDate_plot_TwelveWeeks_json_smallScreen)

# @app.route('/plots/plot_PercDelayByDate_SinceRecordsBegan_smallScreen')
# def plot_PercDelayByDate_SinceRecordsBegan_smallScreen():
#     return(PercDelayByDate_plot_SinceRecordsBegan_json_smallScreen)



@app.route('/plots/plot_PercDelayByDate_SinceRecordsBegan/<line>')
def plot_PercDelayByDate_SinceRecordsBegan(line):
    if line=='All':
        return(PercDelayByDate_plot_SinceRecordsBegan_json)
    else:
        return(PercDelaysByDate_Line_plot_jsons[line]['SinceRecordsBegan'])

@app.route('/plots/plot_PercDelayByDate_TwelveWeeks/<line>')
def plot_PercDelayByDate_TwelveWeeks(line):
    if line=='All':
        return(PercDelayByDate_plot_TwelveWeeks_json)
    else:
        return(PercDelaysByDate_Line_plot_jsons[line]['TwelveWeeks'])

@app.route('/plots/plot_PercDelayByDate_FourWeeks/<line>')
def plot_PercDelayByDate_FourWeeks(line):
    if line=='All':
        return(PercDelayByDate_plot_FourWeeks_json)
    else:
        return(PercDelaysByDate_Line_plot_jsons[line]['FourWeeks'])

@app.route('/plots/plot_PercDelayByDate_TwoWeeks/<line>')
def plot_PercDelayByDate_TwoWeeks(line):
    if line=='All':
        return(PercDelayByDate_plot_TwoWeeks_json)
    else:
        return(PercDelaysByDate_Line_plot_jsons[line]['TwoWeeks'])

@app.route('/plots/plot_PercDelayByDate_OneWeek/<line>')
def plot_PercDelayByDate_OneWeek(line):
    if line=='All':
        return(PercDelayByDate_plot_OneWeek_json)
    else:
        return(PercDelaysByDate_Line_plot_jsons[line]['OneWeek'])


@app.route('/plots/plot_PercDelayByDate_SinceRecordsBegan_smallScreen/<line>')
def plot_PercDelayByDate_SinceRecordsBegan_smallScreen(line):
    if line=='All':
        return(PercDelayByDate_plot_SinceRecordsBegan_json_smallScreen)
    else:
        return(PercDelaysByDate_Line_plot_jsons_smallScreen[line]['SinceRecordsBegan'])

@app.route('/plots/plot_PercDelayByDate_TwelveWeeks_smallScreen/<line>')
def plot_PercDelayByDate_TwelveWeeks_smallScreen(line):
    if line=='All':
        return(PercDelayByDate_plot_TwelveWeeks_json_smallScreen)
    else:
        return(PercDelaysByDate_Line_plot_jsons_smallScreen[line]['TwelveWeeks'])

@app.route('/plots/plot_PercDelayByDate_FourWeeks_smallScreen/<line>')
def plot_PercDelayByDate_FourWeeks_smallScreen(line):
    if line=='All':
        return(PercDelayByDate_plot_FourWeeks_json_smallScreen)
    else:
        return(PercDelaysByDate_Line_plot_jsons_smallScreen[line]['FourWeeks'])

@app.route('/plots/plot_PercDelayByDate_TwoWeeks_smallScreen/<line>')
def plot_PercDelayByDate_TwoWeeks_smallScreen(line):
    if line=='All':
        return(PercDelayByDate_plot_TwoWeeks_json_smallScreen)
    else:
        return(PercDelaysByDate_Line_plot_jsons_smallScreen[line]['TwoWeeks'])

@app.route('/plots/plot_PercDelayByDate_OneWeek_smallScreen/<line>')
def plot_PercDelayByDate_OneWeek_smallScreen(line):
    if line=='All':
        return(PercDelayByDate_plot_OneWeek_json_smallScreen)
    else:
        return(PercDelaysByDate_Line_plot_jsons_smallScreen[line]['OneWeek'])


##################
# Folium Functions
##################
# Created outside of app code (see folium_prep.py)
# Save each folium plot out as a html to be loaded when needed
# def plot_Folium_prep():
#     DataForFolium_AllLines_OneWeek = pd.read_csv(data_dir + 'DataForFolium_AllLines_OneWeek.csv')
#     DataForFolium_AllLines_TwoWeeks = pd.read_csv(data_dir + 'DataForFolium_AllLines_TwoWeeks.csv')
#     DataForFolium_AllLines_FourWeeks = pd.read_csv(data_dir + 'DataForFolium_AllLines_FourWeeks.csv')
#     DataForFolium_AllLines_TwelveWeeks = pd.read_csv(data_dir + 'DataForFolium_AllLines_TwelveWeeks.csv')
#     DataForFolium_AllLines_SinceRecordsBegan = pd.read_csv(data_dir + 'DataForFolium_AllLines_SinceRecordsBegan.csv')

#     _ = make_folium_plots(DataForFolium_AllLines_OneWeek,
#                           filename='foliumMap_AllLines_OneWeek.html')
#     _ = make_folium_plots(DataForFolium_AllLines_OneWeek, altColour=True,
#                           filename='foliumMap_AllLines_OneWeek_altColour.html')
#     _ = make_folium_plots(DataForFolium_AllLines_OneWeek, watercolour=True,
#                           filename='foliumMap_AllLines_OneWeek_watercolour.html')

#     _ = make_folium_plots(DataForFolium_AllLines_TwoWeeks,
#                           filename='foliumMap_AllLines_TwoWeeks.html')
#     _ = make_folium_plots(DataForFolium_AllLines_TwoWeeks, altColour=True,
#                           filename='foliumMap_AllLines_TwoWeeks_altColour.html')
#     _ = make_folium_plots(DataForFolium_AllLines_TwoWeeks, watercolour=True,
#                           filename='foliumMap_AllLines_TwoWeeks_watercolour.html')

#     _ = make_folium_plots(DataForFolium_AllLines_FourWeeks,
#                           filename='foliumMap_AllLines_FourWeeks.html')
#     _ = make_folium_plots(DataForFolium_AllLines_FourWeeks, altColour=True,
#                           filename='foliumMap_AllLines_FourWeeks_altColour.html')
#     _ = make_folium_plots(DataForFolium_AllLines_FourWeeks, watercolour=True,
#                           filename='foliumMap_AllLines_FourWeeks_watercolour.html')

#     _ = make_folium_plots(DataForFolium_AllLines_TwelveWeeks,
#                           filename='foliumMap_AllLines_TwelveWeeks.html')
#     _ = make_folium_plots(DataForFolium_AllLines_TwelveWeeks, altColour=True,
#                           filename='foliumMap_AllLines_TwelveWeeks_altColour.html')
#     _ = make_folium_plots(DataForFolium_AllLines_TwelveWeeks, watercolour=True,
#                           filename='foliumMap_AllLines_TwelveWeeks_watercolour.html')

#     _ = make_folium_plots(DataForFolium_AllLines_SinceRecordsBegan,
#                           filename='foliumMap_AllLines_SinceRecordsBegan.html')
#     _ = make_folium_plots(DataForFolium_AllLines_SinceRecordsBegan, altColour=True,
#                           filename='foliumMap_AllLines_SinceRecordsBegan_altColour.html')
#     _ = make_folium_plots(DataForFolium_AllLines_SinceRecordsBegan, watercolour=True,
#                           filename='foliumMap_AllLines_SinceRecordsBegan_watercolour.html')

#     return()

# def make_folium_plots(data_for_folium, filename, watercolour=False, altColour=False):
#     map_df = data_for_folium[~data_for_folium.Longitude_mean.isnull()]

#     fig = folium.elements.Figure(width=500, height=1000)

#     if watercolour:
#         folium_map = folium.Map(location = [54.62, -5.94], zoom_start = 11, tiles="Stamen Watercolor")
#     else:
#         folium_map = folium.Map(location = [54.62, -5.94], zoom_start = 11, tiles="Stamen Toner")

#     for idx, row in map_df.iterrows():
#         if altColour:
#             _ = folium.CircleMarker(location=[row.Latitude_mean, row.Longitude_mean], radius = 7, weight=1,
#                                     color='black', fill_color=row['MarkerColourAlt'], fill_opacity = 1,
#                                     fill=True).add_child(folium.Tooltip(row['TooltipText'])).add_to(folium_map)
#         else:
#             _ = folium.CircleMarker(location=[row.Latitude_mean, row.Longitude_mean], radius = 7, weight=1,
#                                     color='black', fill_color=row['MarkerColour'], fill_opacity = 1,
#                                     fill=True).add_child(folium.Tooltip(row['TooltipText'])).add_to(folium_map)

#     folium_map.save(static_dir + filename)

#     return()

# _ = plot_Folium_prep()

