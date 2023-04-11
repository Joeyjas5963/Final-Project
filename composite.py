"""
Everyone
DS 3500
Homework 2
02/10/2023
"""
# import necessary libraries
from dash import Dash, dcc, html, Input, Output
from cities import city_state_list
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import json
from datetime import date, datetime, timedelta
import dash_bootstrap_components as dbc

# DATA PREP

API_KEY = '41888fdfc7cb4fb9bfd194727230404'

IMAGE_KEY = 'AIzaSyBa7_tGiDTn4v4PQAYwWc5umPhg0vaIN3E'

def str_to_date(date_str):
    '''
    converts a string in the form 'YYYY-MM-DD' to a date object
    :param date_str: (string) string to convert into a date object
    :return: date, a date object representing the date in date_str
    '''

    # converts string to date object
    date = datetime.strptime(date_str, '%Y-%m-%d').date()

    return date


def get_location_data(city):
    '''
    obtains data on the location of the input city
    :param city: (string) a city to gather location data of
    :return:
        city: (string) the name of the city
        state: (string) the state in which the city is located
        lat: (float) the latitude of the city
        long (float) the longitude of the city
    '''
    # request for retrieving data
    request = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&aqi=no'

    # converting data to json and then pandas dataframe
    city_data = pd.DataFrame(requests.get(request).json())

    # isolating necessary information
    loc_info = city_data['location']
    city, state, _, lat, long = loc_info[: 'lon']

    return city, state, lat, long


def get_weather_data(city, start_date, end_date=None):
    '''
    obtains weather data of a city between two dates
    :param city: (string) the city for which to obtain data
    :param start_date: (date object or string) the starting date for collecting weather data
    :param end_date: (date object or string) the ending date for collecting weather data, defaults to none, allowing
        easy access to weather for a specific date
    :return: forecast_data: (dataframe) a dataframe containing all obtainable weather data from the city between
        start_date and end_date
    '''

    # if no end date specified, assume gathering data for one day
    if end_date is None:
        end_date = start_date

    # convert start_date and end_date from strings to date objects if necessary
    if isinstance(start_date, str):
        start_date = str_to_date(start_date)

    if isinstance(end_date, str):
        end_date = str_to_date(end_date)

    # counting number of days between start_date and end_date
    days = (end_date - date.today()).days + 1

    # request for obtaining weather data
    request = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&aqi=no' \
              f'&days={days}&alerts=no'

    # converting data to dataframe and isolating necessary data
    weather_data = pd.DataFrame(requests.get(request).json())
    forecast_data = pd.DataFrame(weather_data['forecast']['forecastday'])

    # converting date strings to date objects
    for row_idx in range(len(forecast_data)):
        forecast_data.loc[row_idx, 'strptime'] = str_to_date(forecast_data.loc[row_idx, 'date'])

    # filtering data to necessary range
    forecast_data = forecast_data[forecast_data['strptime'] >= start_date]

    return forecast_data


def generate_hour_data(city, date, hour, units):
    '''
    generates weather data from a city in an hour with given units
    :param city: (string) the city for which to obtain data
    :param date: (date object or string) the date for collecting weather data
    :param hour: (int) the hour for collecting weather data (assumes 24 hour time)
    :param units: (string) either Fahrenheit or Celsius - specifies unit of temperature
    :return: new_hour_data (dataframe): dataframe containing weather data for specific city and hour
    '''

    # obtain and filter data
    weather_data = get_weather_data(city, date).reset_index()
    hour_data = pd.DataFrame(weather_data['hour'][0]).loc[hour, :]

    # create new dataframe to isolate data
    new_hour_data = pd.Series(dtype='float64')

    # adding necessary data to new dataframe
    new_hour_data['Time'] = hour_data['time'].split(sep=' ')[1][:5]

    # isolating condition and image information
    cond, image, _ = hour_data['condition'].values()
    new_hour_data['Image'], new_hour_data['Condition'] = html.Img(src=image), cond

    # adding temperature data
    if units == 'Fahrenheit':
        new_hour_data['Temperature'] = str(hour_data['temp_f']) + '°F'
        new_hour_data['Feels Like'] = str(hour_data['feelslike_f']) + '°F'

    elif units == 'Celsius':
        new_hour_data['Temperature'] = str(hour_data['temp_c']) + '°C'
        new_hour_data['Feels Like'] = str(hour_data['feelslike_c']) + '°C'

    # finding chance of precipitation by adding chance of rain and chance of snow
    new_hour_data['Chance of Precipitation'] = str(hour_data['chance_of_rain'] + hour_data['chance_of_snow']) + '%'

    return new_hour_data


def create_hourly_df(city, date, units):
    '''
    creates dataframe containing weather data for a date in increments of 4 hours
    :param city: (string) the city for which to obtain data
    :param date: (date object or string) the date for collecting weather data
    :param units: (string) either Fahrenheit or Celsius - specifies unit of temperature
    :return: hourly_df (dataframe): dataframe containing weather data for specific city and hour
    '''
    # storing row names
    row_names = pd.Series(['Time', 'Weather', 'Condition', 'Temperature', 'Feels Like', 'Chance of Precipitation'])

    # concatenating dataframes for weather data at 0:00, 4:00, 8:00, 12:00, 16:00, and 20:00
    hourly_df = pd.concat([generate_hour_data(city, date, hour, units) for hour in range(0, 24, 4)],
                          axis=1, ignore_index=True).reset_index()

    # adding row names to dataframe
    hourly_df = pd.concat([row_names, hourly_df], axis=1).rename(columns=hourly_df.iloc[0]).iloc[1:, 1:]

    return hourly_df

city, state, lat, long = get_location_data('Boston')

def create_app():

    # Data for emissions, time, cost, and distance for each transportation mode
    emissions = [0.0, 0.0, 0.3, 0.5, 53.3]
    time = [15, 10, 20, 40, 120]
    cost = [0, 0, 5, 10, 100]
    distance = [1, 2, 5, 10, 100]
    transport_type = ['Walking', 'Biking', 'Driving', 'Public Transit', 'Flying']

    # initialize the Dash Object
    app = Dash(__name__)

    # define the layout
    app.layout = html.Div(children=[
        # create main heading of dash: 'SunDash: Monitoring and Analyzing Solar Activity'
        html.H4('TravelDash: Analyzing Travel Data', style={'color':'#000080', 'fontSize': 30,
                                                            'fontFamily': 'Monaco, Monospace'}),

        # displays smoothed and non-smoothed graph with the number of sunspots over a user inputed year range
        html.P('Travel Modes vs Time, Cost and Emissions', style={'color':'#4682B4', 'fontSize': 20,
                                                                  'fontFamily': 'Monaco, Monospace'}),
        html.P("Select Origin City:", style={'color': 'black', 'fontSize': 20, 'fontFamily': 'Monaco, Monospace'}),
        dcc.Dropdown(city_state_list, 'Cambridge MA', id='origin_city_state'),

        html.P("Select Destination City:", style={'color': 'black', 'fontSize': 20, 'fontFamily': 'Monaco, Monospace'}),
        dcc.Dropdown(city_state_list, 'Boston MA', id='dest_city_state'),
        html.H1(children='Transportation Statistics'),
        html.Div(children='''
                        Bar charts for different transportation modes.
                    '''), html.Div(children=[
            dcc.Graph(
                id='emissions_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '50vh', 'height': '40vh'}
            ),
            dcc.Graph(
                id='time_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '50vh', 'height': '40vh'}
            ),
            dcc.Graph(
                id='cost_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '50vh', 'height': '40vh'}),
            dcc.Graph(
                id='distance_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '50vh', 'height': '40vh'}
            )


        ], style={'display': 'flex'})]

    )

    # JACK STATS

    @app.callback(
        Output('emissions_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_emissions_graph(origin_city_state, dest_city_state):
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'biking', 'driving', 'transit']
        # https://www.apta.com/wp-content/uploads/Standards_Documents/APTA-SUDS-CC-RP-001-09_Rev-1.pdf
        pm_emissions = [0, 0, .96, .45]
        emissions = [round(travel_data[mode]['distance'] * emission, 2) for emission, mode in zip(pm_emissions, modes)]

        fig = px.bar(x=modes, y=emissions, text=emissions,
                     title='Emissions by Transportation Mode', labels={'x': 'Transportation Mode', 'y': 'Emissions (lbs)'})

        return fig

    @app.callback(
        Output('time_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_time_graph(origin_city_state, dest_city_state):
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'biking', 'driving', 'transit']
        durations = [round(travel_data[mode]['duration'] * 60, 2) for mode in modes]

        fig = px.bar(x=modes, y=durations, text=durations,
                     title='Time by Transportation Mode', labels={'x': 'Transportation Mode', 'y': 'Time (minutes)'})

        return fig

    @app.callback(
        Output('cost_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_cost_graph(origin_city_state, dest_city_state):
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'biking', 'driving', 'transit']
        # https://calculator.academy/cost-per-mile-of-driving-calculator/
        # https://urbanreforminstitute.org/2019/09/transport-costs-and-subsidies-by-mode/#:~:text=In%202017%2C%20Americans%20paid%20%2415.8,28.8%20cents%20per%20passenger%20mile.
        pm_costs = [0, 0, .58, .28]
        costs = [round(travel_data[mode]['distance'] * pm_cost, 2) for pm_cost, mode in zip(pm_costs, modes)]

        fig = px.bar(x=modes, y=costs, text=costs,
                     title='Cost by Transportation Mode', labels={'x': 'Transportation Mode', 'y': 'Cost (Dollars)'})

        return fig

    @app.callback(
        Output('distance_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_distance_graph(origin_city_state, dest_city_state):
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'biking', 'driving', 'transit']
        distances = [round(travel_data[mode]['distance'], 2) for mode in modes]

        fig = px.bar(x=modes, y=distances, text=distances,
                     title='Distance by Transportation Mode', labels={'x': 'Transportation Mode', 'y': 'Distance (mi)'})

        return fig

    def get_transportation_data(origin_city_state, dest_city_state):
        origin_state = origin_city_state.split()[-1]
        origin_city = origin_city_state.rsplit(' ', 1)[0].replace(" ", "%20")
        origin = f'{origin_city}%2C%20{origin_state}'

        dest_state = dest_city_state.split()[-1]
        dest_city = dest_city_state.rsplit(' ', 1)[0].replace(" ", "%20")
        destination = f'{dest_city}%2C%20{dest_state}'
        KEY = 'AIzaSyDyONSXMFIoOzEqRiaxoGwmPwPbKaeLKew'
        payload = {}
        headers = {}

        transp_modes_list = ['driving', 'walking', 'biking', 'transit']
        transportation_dict = dict()

        for mode in transp_modes_list:
            url = f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}' \
                  + f'&units=imperial&mode={mode}&key={KEY}'
            response = requests.request("GET", url, headers=headers, data=payload)
            trans_data = json.loads(response.text)
            transportation_dict[mode] = dict()
            transportation_dict[mode]['destination'] = trans_data['destination_addresses'][0]
            transportation_dict[mode]['origin'] = trans_data['origin_addresses'][0]
            transportation_dict[mode]['distance_text'] = trans_data['rows'][0]['elements'][0]['distance']['text']
            transportation_dict[mode]['distance'] = trans_data['rows'][0]['elements'][0]['distance']['value'] / 1609
            transportation_dict[mode]['duration_text'] = trans_data['rows'][0]['elements'][0]['duration']['text']
            transportation_dict[mode]['duration'] = trans_data['rows'][0]['elements'][0]['duration']['value'] / 3600

        return transportation_dict

    # BEN STATS

    @app.callback(
        Output(component_id='temp_graph', component_property='figure'),
        Input(component_id='forecast_days', component_property='start_date'),
        Input(component_id='forecast_days', component_property='end_date'),
        Input(component_id='units', component_property='value'),
    )
    def plot_temps(start_date, end_date, units):
        '''
        plots temperature data for city between start_date and end_date
        :param start_date: (date object or string) the starting date for collecting weather data
        :param end_date: (date object or string) the ending date for collecting weather data
        :param units: (string) either Fahrenheit or Celsius - specifies unit of temperature
        :return: fig: (plotly figure) line plot of temperature over time
        '''
        forecast_data = get_weather_data('Boston', start_date, end_date)['hour']
        hourly_temps = {}

        for idx, day in enumerate(forecast_data):
            for jdx, hour in enumerate(day):
                day_x = datetime.fromtimestamp(hour['time_epoch'])
                if units == 'Fahrenheit':
                    hourly_temps[day_x] = hour['temp_f']
                elif units == 'Celsius':
                    hourly_temps[day_x] = hour['temp_c']

        fig = px.line(x=hourly_temps.keys(), y=hourly_temps.values(), title=f'Hourly Temperature for {city}',
                      labels={'x': 'Time', 'y': f'Temperature in {units}'})

        return fig

    @app.callback(
        Output(component_id='hourly_forecast', component_property='children'),
        Input(component_id='weather_day', component_property='date'),
        Input(component_id='units', component_property='value')
    )
    def update_table(day, units):
        '''
        updates the data in the hourly forecast table
        :param day: (string or date object) date for which to access and display weather data
        :param units: (string) either Fahrenheit or Celsius - specifies unit of temperature
        :return: table (dash table) table displaying data collected from accessing api
        '''
        # create dataframe by accessing create_hourly_dataframe function
        df = create_hourly_df(city, day, units)

        # convert dataframe to table
        table = dbc.Table.from_dataframe(df, bordered=True)

        return table



    return app


def main():

    app = create_app()
    # run dashboard server
    app.run_server(debug=True)


main()
