'''
Benjamin Ecsedy
DS 3500
Final Project
weather.py
Creates weather forecasting dashboard by accessing weatherapi.com data
'''

# import libraries
from dash import Dash, dcc, html, Input, Output, dash_table
import requests
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
import dash_bootstrap_components as dbc
from image import *

# key for accessing weather api
API_KEY = '41888fdfc7cb4fb9bfd194727230404'

# creating app
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])


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

app.layout = html.Div([
    # titles and universal components
    html.Div([
        # titles
        html.H1('Weather Forecast Dashboard :)', className='text-center'),
        html.H2(f'Viewing Weather for: {city}, {state}', className='text-center'),
        html.H2(f'Coordinates: {lat}, {long}', className='text-center'),

        # temperature unit selection
        html.H4('Units:', className='text-center'),
        dcc.RadioItems(['Fahrenheit', 'Celsius'], id='units', value='Fahrenheit', className='text-center'),
        html.Br(),
    ], style={'width': '100%', 'display': 'inline-block', 'float': 'center',},),

    # hourly forecasts
    html.Div([
        html.H4('View Weather Throughout Date:'),
        dcc.DatePickerSingle(
            id='weather_day',
            min_date_allowed=date.today(),
            max_date_allowed=date.today()+timedelta(days=14),
            date=date.today(),
        ),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(id='hourly_forecast', style={'width': '90%', 'display': 'inline-block', 'float': 'left'}),
    ], style={'width': '50%', 'display': 'inline-block', 'float': 'left'}),

    # temperature plot
    html.Div([
        html.H4('Days to Forecast:'),
        dcc.DatePickerRange(
            id='forecast_days',
            min_date_allowed=date.today(),
            max_date_allowed=date.today()+timedelta(days=14),
            start_date=date.today(),
            end_date=date.today(),
        ),
        html.Br(),
        dcc.Graph(id='temp_graph', figure={}),
    ], style={'width': '50%', 'display': 'inline-block', 'float': 'right'})
])


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
"""
# running app
if __name__ == '__main__':
    app.run_server(debug=True)
"""