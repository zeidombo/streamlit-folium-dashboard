import folium
import pandas as pd
from millify import millify
import streamlit as st
from streamlit_folium import st_folium

APP_TITLE = 'Fraud and Identity Theft Report'
APP_SUB_TITLE = 'Source: US Federal Trade Commission'


def display_fraud_facts(df, year, quarter, state_name,
                        report_type, field_name, metric_title, is_median=False, nf=''):

    df = df[(df['Year'] == year) & (df['Quarter'] == quarter)
            & (df['Report Type'] == report_type)]
    if state_name:
        df = df[df['State Name'] == state_name]
    df.drop_duplicates(inplace=True)

    if is_median:
        total = df[field_name].sum() / len(df[field_name]
                                           ) if len(df[field_name]) else 0
    else:
        total = df[field_name].sum()
    st.metric(metric_title, nf + millify(
        total, precision=2))


def display_map(df, year, quarter):
    df = df[(df['Year'] == year) & (df['Quarter'] == quarter)]

    map = folium.Map(location=[38, -96.5],
                     zoom_start=4,
                     # zoom_control=False,
                     scrollWheelZoom=False,
                     tiles='CartoDB positron')
    choropleth = folium.Choropleth(
        geo_data='data/us-state-boundaries.geojson',
        data=df,
        columns=('State Name', 'State Total Reports Quarter'),
        key_on='feature.properties.name',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(map)

    df = df.set_index('State Name')
    # state_name = 'North Carolina'
    # st.write(df.loc[state_name, 'State Pop'][0])

    for feature in choropleth.geojson.data['features']:
        state_name = feature['properties']['name']
        feature['properties']['population'] = 'Population: ' + \
            str(millify(df.loc[state_name, 'State Pop'][0], precision=2)
                if state_name in list(df.index) else 'Not Available')
        feature['properties']['per_100k'] = 'Report/100k Population: ' + \
            str(millify(df.loc[state_name, 'Reports per 100K-F&O together'][0], precision=2)
                if state_name in list(df.index) else 'Not Available')

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            ['name', 'population', 'per_100k'], labels=False)
    )

    st_map = st_folium(map, width=700, height=450)
    state_name = ''
    if st_map['last_active_drawing']:
        state_name = st_map['last_active_drawing']['properties']['name']

    return state_name


def display_time_filters(df):
    year_list = list(df['Year'].unique())
    year_list.sort()
    # len(year) -1 to sort the sidebar from most recent year
    year = st.sidebar.selectbox('Year', year_list, len(year_list) - 1)
    quarter = st.sidebar.radio('Quarter', [1, 2, 3, 4], )
    st.header(f'{year} Q{quarter}')

    return year, quarter


def display_state_filters(df, state_name):
    state_list = [''] + list(df['State Name'].unique())
    state_list.sort()
    # display the state in the sidebar when selected on the map
    state_index = state_list.index(
        state_name) if state_name and state_name in state_list else 0

    return st.sidebar.selectbox('State', state_list, state_index)


def display_report_filters():
    report_types = ['Fraud', 'Other']

    return st.sidebar.radio('Report Type', report_types)


def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    # LOAD DATA
    df_continental = pd.read_csv('data/AxS-Continental_Full Data_data.csv')
    df_fraud = pd.read_csv('data/AxS-Fraud Box_Full Data_data.csv')
    df_median = pd.read_csv('data/AxS-Median Box_Full Data_data.csv')
    df_loss = pd.read_csv('data/AxS-Losses Box_Full Data_data.csv')

    # DISPLAY FILTER AND MAP
    year, quarter = display_time_filters(df_continental)
    state_name = display_map(df_continental, year, quarter)
    state_name = display_state_filters(df_continental, state_name)
    report_type = display_report_filters()

    # DISPLAY METRICS
    st.subheader(f'{state_name} {report_type} Facts')
    col1, col2, col3 = st.columns(3)

    with col1:
        display_fraud_facts(df_fraud, year, quarter, state_name,
                            report_type, 'State Fraud/Other Count', f"Nb of {report_type} Reports")
    with col2:
        display_fraud_facts(df_median, year, quarter, state_name,
                            report_type, 'Overall Median Losses Qtr', 'Median Loss', is_median=True, nf='$')
    with col3:
        display_fraud_facts(df_loss, year, quarter, state_name,
                            report_type, 'Total Losses', 'Total $ Loss', nf='$')


if __name__ == '__main__':
    main()
