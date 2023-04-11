from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import copy

app = Dash(__name__)

# Example Data
d = {'Cost': [1, 3, 2], 'Carbon Emission': [7, 5, 6], 'Time': [20, 50, 30],
     'Type': ['Car', 'Bike', 'Bus']}
df_trav = pd.DataFrame(data=d)
df = copy.deepcopy(df_trav.iloc[:, :-1])
df_n = (df - df.mean()) / df.std()
df_n['Type'] = df_trav['Type'].copy()

app.layout = html.Div([
    html.H4('Pareto Optimal Curve Example'),
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
        value=4
    ),

])


@app.callback(
    Output("graph", "figure"),
    Input("time_slider", "value"),
    Input("carbon_slider", "value"),
    Input("time_slider", "value")
)
def update_bar_chart(cost_w, carbon_w, time_w):
    df_g = df_n.copy()
    df_g['Cost'] = df_n['Cost'] * cost_w
    df_g['Carbon Emission'] = df_n['Carbon Emission'] * carbon_w
    df_g['Time'] = df_n['Time'] * time_w

    fig = px.scatter_3d(df_g,
                        x='Cost', y='Carbon Emission', z='Time',
                        color="Type",
                        hover_data=['Type', 'Time', 'Cost', 'Carbon Emission'])
    return fig


app.run_server(debug=True)
