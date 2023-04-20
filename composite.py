"""
TIDES Dashboard
DS 3500
Final Project
Yash Bhora, Brady Duncan, Benjamin Ecsedy, Jack Krolik, Emily Liu, Joey Scolponeti
"""
from dash import Dash, dcc, html, Input, Output
from cities import city_state_list
import plotly.express as px
import pandas as pd
import requests
import json
from datetime import date, datetime, timedelta
import dash_bootstrap_components as dbc
import googlemaps
import re
import copy

# defining keys for APIS, and establishing data structure

API_KEY = '41888fdfc7cb4fb9bfd194727230404'

IMAGE_KEY = 'AIzaSyBa7_tGiDTn4v4PQAYwWc5umPhg0vaIN3E'

HEAD = 'https://maps.googleapis.com/maps/api/staticmap?'

d = {'Cost': [1, 2, 3], 'Carbon Emission': [1, 2, 3], 'Time': [1, 2, 3],
     'Type': ['Car', 'Bike', 'Transit']}


# Below are functions that will be called by the app callback functions later on
def combine(dct):
    """ combines coordinates for Google Maps Static Image API

    Args:
        dct (dict): dictionary of a longitude and latitude coordinate

    Returns:
        Coordinates combined as a string for the URL
    """
    return '|' + str(dct['lat']) + ',' + str(dct['lng'])


def str_to_date(date_str):
    """ converts a string in the form 'YYYY-MM-DD' to a date object

    Args:
        date_str (str): string to convert into a date object

    Returns:
        date_obj (date object): date represented by date_str
    """

    # converts string to date object
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    return date_obj


def get_location_data(city_str):
    """ obtains data on the location of the input city

    Args:
        city_str (str): a city to gather location data

    Returns:
        city_iso (str): the name of the city
        state_iso (str): the state in which the city is located
        lat_iso (float): the latitude of the city
        long_iso (float): the longitude of the city
    """
    # request for retrieving data
    request = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city_str}&aqi=no'

    # converting data to json and then pandas dataframe
    city_data = pd.DataFrame(requests.get(request).json())

    # isolating necessary information
    loc_info = city_data['location']
    city_iso, state_iso, _, lat_iso, long_iso = loc_info[: 'lon']

    return city_iso, state_iso, lat_iso, long_iso


def get_weather_data(city_str, start_date, end_date=None):
    """ obtains weather data of a city between two dates

    Args:
        city_str (str): the city for which to obtain data
        start_date (str or date obj): the starting date for collecting weather data
        end_date (str or date obj):   the ending date for collecting weather data

    Returns:
        forecast_data: (dataframe): a dataframe containing all obtainable weather data in the data range
    """

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
    request = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city_str}&aqi=no' \
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


def generate_hour_data(city_str, date_str, hour, units):
    """ generates weather data from a city in an hour with given units

    Args:
        city_str (str): the city for which to obtain data
        date_str (str or date obj): the date for collecting weather data
        hour (int): the hour for collecting weather data (assumes 24 hour time)
        units (str): either Fahrenheit or Celsius - specifies unit of temperature

    Returns:
        new_hour_data (dataframe): dataframe containing weather data for specific city and hour
    """

    # obtain and filter data
    weather_data = get_weather_data(city_str, date_str).reset_index()
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


def create_hourly_df(city_str, date_str, units):
    """ creates dataframe containing weather data for a date in increments of 4 hours

    Args:
        city_str (str): the city for which to obtain data
        date_str (str or date obj): the date for collecting weather data
        units (str): either Fahrenheit or Celsius - specifies unit of temperature

    Returns:
        hourly_df (dataframe): dataframe containing weather data for specific city and hour
    """
    # storing row names
    row_names = pd.Series(['Time', 'Weather', 'Condition', 'Temperature', 'Feels Like', 'Chance of Precipitation'])

    # concatenating dataframes for weather data at 0:00, 4:00, 8:00, 12:00, 16:00, and 20:00
    hourly_df = pd.concat([generate_hour_data(city_str, date_str, hour, units) for hour in range(0, 24, 4)],
                          axis=1, ignore_index=True).reset_index()

    # adding row names to dataframe
    hourly_df = pd.concat([row_names, hourly_df], axis=1).rename(columns=hourly_df.iloc[0]).iloc[1:, 1:]

    return hourly_df


def get_transportation_data(origin_city_state, dest_city_state):
    """ obtains transportation data from API

    Args:
        origin_city_state (str): starting point
        dest_city_state (str): ending point

    Returns:
        transportation_dict (dict): dictionary containing all transportation statistics
    """

    # modifies origin string
    origin_state = origin_city_state.split()[-1]
    origin_city = origin_city_state.rsplit(' ', 1)[0].replace(" ", "%20")
    origin = f'{origin_city}%2C%20{origin_state}'

    # modifies destination split
    dest_state = dest_city_state.split()[-1]
    dest_city = dest_city_state.rsplit(' ', 1)[0].replace(" ", "%20")
    destination = f'{dest_city}%2C%20{dest_state}'

    # API Key
    KEY = 'AIzaSyDyONSXMFIoOzEqRiaxoGwmPwPbKaeLKew'

    # defining variables which will be filled in below for loop
    payload = {}
    headers = {}
    transp_modes_list = ['walking', 'bicycling', 'driving', 'transit']
    transportation_dict = dict()

    # obtains transport data from the distance matrix api
    for mode in transp_modes_list:
        url = f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}' \
              + f'&units=imperial&mode={mode}&key={KEY}'
        response = requests.request("GET", url, headers=headers, data=payload)
        trans_data = json.loads(response.text)
        transportation_dict[mode] = dict()
        transportation_dict[mode]['destination'] = trans_data['destination_addresses'][0]
        transportation_dict[mode]['origin'] = trans_data['origin_addresses'][0]

        # checks if data for this transport mode is available
        if trans_data['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
            transportation_dict[mode]['distance_text'] = 0
            transportation_dict[mode]['distance'] = 0
            transportation_dict[mode]['duration_text'] = 0
            transportation_dict[mode]['duration'] = 0

        else:

            # adds data for that mode to the transport dictionary
            transportation_dict[mode]['distance_text'] = trans_data['rows'][0]['elements'][0]['distance']['text']
            transportation_dict[mode]['distance'] = trans_data['rows'][0]['elements'][0]['distance']['value'] / 1609
            transportation_dict[mode]['duration_text'] = trans_data['rows'][0]['elements'][0]['duration']['text']
            transportation_dict[mode]['duration'] = trans_data['rows'][0]['elements'][0]['duration']['value'] / 3600

    return transportation_dict


def create_app():
    """ creates the dashboard """

    # initialize the Dash Object
    app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

    # define the layout
    app.layout = html.Div(children=[

        # header
        html.H1('TIDES: A Travel Dashboard',
                style={'text-align': 'center'}),

        html.P('(Travel Information Dashboard for Efficiency and Sustainability)',
               style={'text-align': 'center',
                      'font-size': 15}),


        html.H2('Comparing Distance, Time, Cost and Emissions',
                style={'text-align': 'center'}),

        # location selection
        html.Div(children=[

            html.H4("Select Origin City:",
                    style={'text-align': 'center'}),

            dcc.Dropdown(city_state_list, 'Canton MA', id='origin_city_state',
                         style={'width': '45%',
                                'margin': '0 auto'}),

            html.H4("Select Destination City:",
                    style={'text-align': 'center'}),

            dcc.Dropdown(city_state_list, 'Boston MA', id='dest_city_state',
                         style={'width': '45%',
                                'margin': '0 auto'}),

        ], style={'position': 'sticky',
                  'margin': '0 auto'}),

        html.Br(),

        # map and directions
        html.Div(children=[

            html.Img(id="html-img", src='',
                     style={'float': 'left',
                            'width': '45%',
                            'height': '50vh',
                            'padding-left': 30,
                            'display': 'block'}),

            html.Div(id='directions',
                     style={'float': 'right',
                            'width': '45%',
                            'height': '50vh',
                            'padding-right': 30,
                            'overflow-y': 'scroll',
                            'display': 'block'}),

            ], style={'display': 'inline'}),

        html.Br(),

        # weather header
        html.Div([

            html.H3('Weather Forecast', className='text-center'),

            html.H4('Units:', className='text-center'),

            dcc.RadioItems(['Fahrenheit', 'Celsius'], id='units', value='Fahrenheit', className='text-center'),

        ], style={'width': '100%',
                  'display': 'inline-block',
                  'float': 'center'}),

        # hourly forecast
        html.Div([
            html.H4('View Weather Throughout Date:'),
            dcc.DatePickerSingle(
                id='weather_day',
                min_date_allowed=date.today(),
                max_date_allowed=date.today() + timedelta(days=14),
                date=date.today(),
            ),
            html.Br(),
            html.Br(),
            html.Br(),
            html.Div(id='hourly_forecast',
                     style={'width': '30%',
                            'display': 'block',
                            'float': 'left'}),

        ], style={'width': '30%',
                  'display': 'block',
                  'float': 'left',
                  'padding-left': 30}),

        # temperature visualization
        html.Div([
            html.H4('Days to Forecast:'),
            dcc.DatePickerRange(
                id='forecast_days',
                min_date_allowed=date.today(),
                max_date_allowed=date.today() + timedelta(days=14),
                start_date=date.today(),
                end_date=date.today(),
            ),
            html.Br(),
            dcc.Graph(id='temp_graph', figure={}),

        ], style={'width': '40%',
                  'display': 'inline-block',
                  'float': 'right'}),

        # transportation header
        html.Div(children=[

            html.H3('Transportation Statistics', className='text-center',
                    style={'text-align': 'center'}),

            html.H4('See how each mode of transportation ranks on each factor', className='text-center',
                    style={'text-align': 'center'}),

            ], style={'width': '100%',
                      'display': 'inline-block',
                      'float': 'center'}),

        # factor graphs
        html.Div(className='box', children=[
            dcc.Graph(
                id='emissions_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '25%',
                       'height': '40vh',
                       'display': 'inline'}),

            dcc.Graph(
                id='time_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '25%',
                       'height': '40vh',
                       'display': 'inline'}),

            dcc.Graph(
                id='cost_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '25%',
                       'height': '40vh',
                       'display': 'inline'}),

            dcc.Graph(
                id='distance_graph',
                figure=px.bar(x=['walking', 'biking', 'driving', 'transit'], y=[0, 0, 0, 0]),
                style={'width': '25%',
                       'height': '40vh',
                       'display': 'inline'})

             ], style={'display': 'flex',
                       'width': '100%',
                       'padding-left': 30,
                       'padding-right': 30}),

        # 3D optimization graph and sliders
        html.Div([
            html.H3('3D Optimization Plot',
                    style={'text-align': 'center'}),

            html.P('Adjust weights below to adjust attribute preferences',
                   style={'text-align': 'center'}),
            html.P('Look for datapoints closest to the origin for best preference match',
                   style={'text-align': 'center'}),

            dcc.Graph(id="graph"),

            html.P("Cost Weight:"),
            dcc.Slider(
                id='cost_slider',
                min=0, max=5, step=0.1,
                value=1
            ),
            html.P("Carbon Emission Weight:"),
            dcc.Slider(
                id='carbon_slider',
                min=0, max=5, step=0.1,
                value=1
            ),
            html.P("Time:"),
            dcc.Slider(
                id='time_slider',
                min=0, max=5, step=0.1,
                value=1
            )

        ])

    ])

    # app callback functions

    @app.callback(
        Output('emissions_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_emissions_graph(origin_city_state, dest_city_state):
        """ updates the emissions bar chart

        Args:
            origin_city_state (str): starting point
            dest_city_state (str): ending point

        Returns:
            fig (figure): emissions bar chart
        """

        # collecting data
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'bicycling', 'driving', 'transit']

        # emission values sourced from below link
        # https://www.apta.com/wp-content/uploads/Standards_Documents/APTA-SUDS-CC-RP-001-09_Rev-1.pdf
        pm_emissions = [0, 0, .96, .45]

        # finding emissions from each mode of transport
        emission = [round(travel_data[mode]['distance'] * emission, 2) for emission, mode in zip(pm_emissions, modes)]

        # adding final values to the 3D plot's data dictionary
        d['Carbon Emission'] = emission[1:]

        # creating bar chart
        fig = px.bar(x=modes, y=emission, text=emission,
                     title='Emissions', labels={'x': 'Transportation Mode', 'y': 'Emissions (lbs)'})

        return fig

    @app.callback(
        Output('time_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_time_graph(origin_city_state, dest_city_state):
        """ update the time bar chart

        Args:
            origin_city_state (str): starting point
            dest_city_state (str): ending point

        Returns:
            fig (figure): time bar chart
        """

        # collecting data
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'bicycling', 'driving', 'transit']

        # finding time in minutes to get between locations
        durations = [round(travel_data[mode]['duration'] * 60, 2) for mode in modes]

        # adding data to the 3D plot's data dictionary
        d['Time'] = durations[1:]

        # creating the bar chart
        fig = px.bar(x=modes, y=durations, text=durations,
                     title='Time', labels={'x': 'Transportation Mode', 'y': 'Time (minutes)'})

        return fig

    @app.callback(
        Output('cost_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_cost_graph(origin_city_state, dest_city_state):
        """ creates the costs bar chart

        Args:
            origin_city_state (str): starting point
            dest_city_state (str): ending point

        Returns:
            fig (figure): costs bar chart
        """

        # collecting data
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'bicycling', 'driving', 'transit']

        # cost factors determined by these sources
        # https://calculator.academy/cost-per-mile-of-driving-calculator/
        # https://urbanreforminstitute.org/2019/09/transport-costs-and-subsidies-by-mode/#:~:text=In%202017%2C%20Americans%20paid%20%2415.8,28.8%20cents%20per%20passenger%20mile.
        pm_costs = [0, 0, .58, .28]

        # calculating the costs of taking each mode of transport
        costs = [round(travel_data[mode]['distance'] * pm_cost, 2) for pm_cost, mode in zip(pm_costs, modes)]

        # adding costs to the 3D plot's data dictionary
        d['Cost'] = costs[1:]

        # creating the bar chart
        fig = px.bar(x=modes, y=costs, text=costs,
                     title='Cost', labels={'x': 'Transportation Mode', 'y': 'Cost (Dollars)'})

        return fig

    @app.callback(
        Output('distance_graph', 'figure'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value'))
    def update_distance_graph(origin_city_state, dest_city_state):
        """ creates the distance bar chart

        Args:
            origin_city_state (str): starting point
            dest_city_state (str): ending point

        Returns:
            fig (figure): distance bar chart
        """

        # collecting data
        travel_data = get_transportation_data(origin_city_state, dest_city_state)
        modes = ['walking', 'bicycling', 'driving', 'transit']

        # finding the distances from each mode of tran
        distances = [round(travel_data[mode]['distance'], 2) for mode in modes]

        # creating the distances bar chart
        fig = px.bar(x=modes, y=distances, text=distances,
                     title='Distance', labels={'x': 'Transportation Mode', 'y': 'Distance (mi)'})

        return fig

    @app.callback(
        Output("graph", "figure"),
        Input("cost_slider", "value"),
        Input("carbon_slider", "value"),
        Input("time_slider", "value"),
    )
    def update_3d_chart(cost_w, carbon_w, time_w):
        """ updates the 3D chart

        Args:
            cost_w (float): weight of cost based on slider
            carbon_w (float): weight of carbon based on slider
            time_w (float): weight of time based on slider

        Returns:
            fig (figure): 3D plot
        """

        # gathers data from the bar chart functions
        df_trav = pd.DataFrame(data=d)
        df = copy.deepcopy(df_trav.iloc[:, :-1])
        df_n = (df - df.mean()) / df.std()
        df_n['Type'] = df_trav['Type'].copy()

        # applies weights to data
        df_g = df_n.copy()
        df_g['Cost'] = df_n['Cost'] * cost_w
        df_g['Carbon Emission'] = df_n['Carbon Emission'] * carbon_w
        df_g['Time'] = df_n['Time'] * time_w

        # creates 3D scatter plot
        fig = px.scatter_3d(df_g,
                            x='Cost', y='Carbon Emission', z='Time',
                            color="Type",
                            hover_data=['Type', 'Time', 'Cost', 'Carbon Emission'])
        return fig

    @app.callback(
        Output(component_id='temp_graph', component_property='figure'),
        Input(component_id='forecast_days', component_property='start_date'),
        Input(component_id='forecast_days', component_property='end_date'),
        Input(component_id='units', component_property='value'),
        Input('dest_city_state', 'value')
    )
    def plot_temps(start_date, end_date, units, city_str):
        """ plots temperature data for city between start_date and end_date

        Args:
            start_date (str or date obj): the starting date
            end_date (str or date obj): the ending date
            units (str): either Fahrenheit or Celsius
            city_str (str): city where temperature will be measured

        Returns:
            fig (figure): line plot of temperature over time
        """

        # gathers forecast data
        forecast_data = get_weather_data(city_str, start_date, end_date)['hour']
        hourly_temps = {}

        # find the hourly temps at location
        for idx, day in enumerate(forecast_data):
            for jdx, hour in enumerate(day):
                day_x = datetime.fromtimestamp(hour['time_epoch'])
                if units == 'Fahrenheit':
                    hourly_temps[day_x] = hour['temp_f']
                elif units == 'Celsius':
                    hourly_temps[day_x] = hour['temp_c']

        # plots a line plot of temps
        fig = px.line(x=hourly_temps.keys(), y=hourly_temps.values(), title=f'Hourly Temperature for {city_str}',
                      labels={'x': 'Time', 'y': f'Temperature in {units}'})

        return fig

    @app.callback(
        Output(component_id='hourly_forecast', component_property='children'),
        Input('dest_city_state', 'value'),
        Input(component_id='weather_day', component_property='date'),
        Input(component_id='units', component_property='value')
    )
    def update_table(dest_city_state, day, units):
        """ updates the data in the hourly forecast table

        Args:
            dest_city_state (str): destination from destination selection
            day (str or date obj): date for which to access and display weather data
            units (str): either Fahrenheit or Celsius

        Returns:
            table (Dash table): table displaying data collected from accessing api
        """

        # create dataframe by accessing create_hourly_dataframe function
        df = create_hourly_df(dest_city_state, day, units)

        # convert dataframe to table
        table = dbc.Table.from_dataframe(df, bordered=True)

        return table

    @app.callback(
        Output(component_id="html-img", component_property='src'),
        Output(component_id="directions", component_property='children'),
        Input('origin_city_state', 'value'),
        Input('dest_city_state', 'value')
    )
    def map_image(dest, origin):
        """ obtains the map and directions from google maps

        Args:
            dest (str): destination
            origin (str): origin

        Returns:
            link (str): source to the map image
            table (Dash table): data table of directions
        """

        # creates a google maps object, and geocodes the towns
        gmaps = googlemaps.Client(key=IMAGE_KEY)
        dest = gmaps.geocode(dest)
        origin = gmaps.geocode(origin)

        # gets the addresses from the geocodes
        dest_add = dest[0]['formatted_address']
        origin_add = origin[0]['formatted_address']

        # gets directions from origin to destination
        directions = gmaps.directions(dest_add, origin_add)[0]

        # gets coordinates of all turns and combines them
        path = combine(directions['legs'][0]['start_location'])
        steps = directions['legs'][0]['steps']
        for step in steps:
            path += combine(step['end_location'])

        # creates the link for the image
        link = HEAD + 'size=400x400&scale=2&path=color:0x0000ff|weight:5' + path + '&key=' + IMAGE_KEY

        # creating dataframe of direction steps
        df_steps = pd.DataFrame(steps)

        # getting text directions for the table
        texts = []
        for s in df_steps['distance']:
            texts.append(s['text'])

        # cleaning text directions to get rid of html tags
        df_steps['text'] = texts
        df_steps = df_steps.loc[:, ('html_instructions', 'text')]
        clean = re.compile('<.*?>')

        for i in range(len(df_steps['html_instructions'])):
            df_steps.loc[i, 'html_instructions'] = re.sub(clean, '', df_steps.loc[i, 'html_instructions'])

        # renaming columns for dataframe, and creating table
        df_steps.columns = ['Directions', 'Distance']
        table = dbc.Table.from_dataframe(df_steps, bordered=True)

        return link, table

    return app


def main():

    # creates app and runs server
    app = create_app()
    app.run_server(debug=True)


main()
