import pandas as pd
import folium
import os

# For local testing
if os.environ['HOME'] == '/home/peter':
    data_dir = os.environ['HOME'] + '/Codes/python/BusWatchNI/data/'
    static_dir = os.environ['HOME'] + '/Codes/python/BusWatchNI/flaskApp/app/static/'
else:
    data_dir = os.environ['HOME'] + '/BusWatchNI/data/'
    static_dir = os.environ['HOME'] + '/BusWatchNI/flaskApp/app/static/'

def plot_Folium_prep(line_filter):
    DataForFolium_OneWeek = pd.read_csv(data_dir + 'DataForFolium_' + line_filter + '_OneWeek.csv')
    DataForFolium_TwoWeeks = pd.read_csv(data_dir + 'DataForFolium_' + line_filter + '_TwoWeeks.csv')
    DataForFolium_FourWeeks = pd.read_csv(data_dir + 'DataForFolium_' + line_filter + '_FourWeeks.csv')
    DataForFolium_TwelveWeeks = pd.read_csv(data_dir + 'DataForFolium_' + line_filter + '_TwelveWeeks.csv')
    DataForFolium_SinceRecordsBegan = pd.read_csv(data_dir + 'DataForFolium_' + line_filter + '_SinceRecordsBegan.csv')

    _ = make_folium_plots(DataForFolium_OneWeek,
                          filename='foliumMap_' + line_filter + '_OneWeek.html')
    _ = make_folium_plots(DataForFolium_OneWeek, altColour=True,
                          filename='foliumMap_' + line_filter + '_OneWeek_altColour.html')
    _ = make_folium_plots(DataForFolium_OneWeek, watercolour=True,
                          filename='foliumMap_' + line_filter + '_OneWeek_watercolour.html')

    _ = make_folium_plots(DataForFolium_TwoWeeks,
                          filename='foliumMap_' + line_filter + '_TwoWeeks.html')
    _ = make_folium_plots(DataForFolium_TwoWeeks, altColour=True,
                          filename='foliumMap_' + line_filter + '_TwoWeeks_altColour.html')
    _ = make_folium_plots(DataForFolium_TwoWeeks, watercolour=True,
                          filename='foliumMap_' + line_filter + '_TwoWeeks_watercolour.html')

    _ = make_folium_plots(DataForFolium_FourWeeks,
                          filename='foliumMap_' + line_filter + '_FourWeeks.html')
    _ = make_folium_plots(DataForFolium_FourWeeks, altColour=True,
                          filename='foliumMap_' + line_filter + '_FourWeeks_altColour.html')
    _ = make_folium_plots(DataForFolium_FourWeeks, watercolour=True,
                          filename='foliumMap_' + line_filter + '_FourWeeks_watercolour.html')

    _ = make_folium_plots(DataForFolium_TwelveWeeks,
                          filename='foliumMap_' + line_filter + '_TwelveWeeks.html')
    _ = make_folium_plots(DataForFolium_TwelveWeeks, altColour=True,
                          filename='foliumMap_' + line_filter + '_TwelveWeeks_altColour.html')
    _ = make_folium_plots(DataForFolium_TwelveWeeks, watercolour=True,
                          filename='foliumMap_' + line_filter + '_TwelveWeeks_watercolour.html')

    _ = make_folium_plots(DataForFolium_SinceRecordsBegan,
                          filename='foliumMap_' + line_filter + '_SinceRecordsBegan.html')
    _ = make_folium_plots(DataForFolium_SinceRecordsBegan, altColour=True,
                          filename='foliumMap_' + line_filter + '_SinceRecordsBegan_altColour.html')
    _ = make_folium_plots(DataForFolium_SinceRecordsBegan, watercolour=True,
                          filename='foliumMap_' + line_filter + '_SinceRecordsBegan_watercolour.html')

    return()

def make_folium_plots(data_for_folium, filename, watercolour=False, altColour=False):
    map_df = data_for_folium[~data_for_folium.Longitude_mean.isnull()]

    fig = folium.elements.Figure(width=500, height=1000)

    if watercolour:
        folium_map = folium.Map(location = [54.62, -5.94], zoom_start = 11, tiles="Stamen Watercolor")
    else:
        folium_map = folium.Map(location = [54.62, -5.94], zoom_start = 11, tiles="Stamen Toner")

    for idx, row in map_df.iterrows():
        if altColour:
            _ = folium.CircleMarker(location=[row.Latitude_mean, row.Longitude_mean], radius = 7, weight=1,
                                    color='black', fill_color=row['MarkerColourAlt'], fill_opacity = 1,
                                    fill=True).add_child(folium.Tooltip(row['TooltipText'])).add_to(folium_map)
        else:
            _ = folium.CircleMarker(location=[row.Latitude_mean, row.Longitude_mean], radius = 7, weight=1,
                                    color='black', fill_color=row['MarkerColour'], fill_opacity = 1,
                                    fill=True).add_child(folium.Tooltip(row['TooltipText'])).add_to(folium_map)

    folium_map.save(static_dir + filename)

    return()

for line in ['AllLines', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'G']:
  _ = plot_Folium_prep(line_filter=line)