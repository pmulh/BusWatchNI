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

def plot_Folium_prep():
    DataForFolium_AllLines_OneWeek = pd.read_csv(data_dir + 'DataForFolium_AllLines_OneWeek.csv')
    DataForFolium_AllLines_TwoWeeks = pd.read_csv(data_dir + 'DataForFolium_AllLines_TwoWeeks.csv')
    DataForFolium_AllLines_FourWeeks = pd.read_csv(data_dir + 'DataForFolium_AllLines_FourWeeks.csv')
    DataForFolium_AllLines_TwelveWeeks = pd.read_csv(data_dir + 'DataForFolium_AllLines_TwelveWeeks.csv')
    DataForFolium_AllLines_SinceRecordsBegan = pd.read_csv(data_dir + 'DataForFolium_AllLines_SinceRecordsBegan.csv')

    _ = make_folium_plots(DataForFolium_AllLines_OneWeek,
                          filename='foliumMap_AllLines_OneWeek.html')
    _ = make_folium_plots(DataForFolium_AllLines_OneWeek, altColour=True,
                          filename='foliumMap_AllLines_OneWeek_altColour.html')
    _ = make_folium_plots(DataForFolium_AllLines_OneWeek, watercolour=True,
                          filename='foliumMap_AllLines_OneWeek_watercolour.html')

    _ = make_folium_plots(DataForFolium_AllLines_TwoWeeks,
                          filename='foliumMap_AllLines_TwoWeeks.html')
    _ = make_folium_plots(DataForFolium_AllLines_TwoWeeks, altColour=True,
                          filename='foliumMap_AllLines_TwoWeeks_altColour.html')
    _ = make_folium_plots(DataForFolium_AllLines_TwoWeeks, watercolour=True,
                          filename='foliumMap_AllLines_TwoWeeks_watercolour.html')

    _ = make_folium_plots(DataForFolium_AllLines_FourWeeks,
                          filename='foliumMap_AllLines_FourWeeks.html')
    _ = make_folium_plots(DataForFolium_AllLines_FourWeeks, altColour=True,
                          filename='foliumMap_AllLines_FourWeeks_altColour.html')
    _ = make_folium_plots(DataForFolium_AllLines_FourWeeks, watercolour=True,
                          filename='foliumMap_AllLines_FourWeeks_watercolour.html')

    _ = make_folium_plots(DataForFolium_AllLines_TwelveWeeks,
                          filename='foliumMap_AllLines_TwelveWeeks.html')
    _ = make_folium_plots(DataForFolium_AllLines_TwelveWeeks, altColour=True,
                          filename='foliumMap_AllLines_TwelveWeeks_altColour.html')
    _ = make_folium_plots(DataForFolium_AllLines_TwelveWeeks, watercolour=True,
                          filename='foliumMap_AllLines_TwelveWeeks_watercolour.html')

    _ = make_folium_plots(DataForFolium_AllLines_SinceRecordsBegan,
                          filename='foliumMap_AllLines_SinceRecordsBegan.html')
    _ = make_folium_plots(DataForFolium_AllLines_SinceRecordsBegan, altColour=True,
                          filename='foliumMap_AllLines_SinceRecordsBegan_altColour.html')
    _ = make_folium_plots(DataForFolium_AllLines_SinceRecordsBegan, watercolour=True,
                          filename='foliumMap_AllLines_SinceRecordsBegan_watercolour.html')

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

_ = plot_Folium_prep()