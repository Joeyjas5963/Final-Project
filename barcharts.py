"""
Jack Krolik
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



def main():
    # run dashboard server
    app.run_server(debug=True)


main()
