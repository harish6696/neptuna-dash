import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import data_utils
import pandas as pd

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Metric Comparison Dashboard"),
    
    html.Div([
        html.Div([
            html.Label("Folder Path 1:"),
            dcc.Input(id='path-1', type='text', placeholder='Enter path to folder 1', style={'width': '100%'}),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label("Folder Path 2:"),
            dcc.Input(id='path-2', type='text', placeholder='Enter path to folder 2', style={'width': '100%'}),
        ], style={'width': '45%', 'display': 'inline-block', 'padding': '10px'}),
    ]),
    
    html.Button('Compare Metrics', id='compare-btn', n_clicks=0, style={'margin': '20px'}),
    
    html.Div(id='error-message', style={'color': 'red', 'padding': '10px'}),
    
    dcc.Graph(id='comparison-graph')
])

@app.callback(
    [Output('comparison-graph', 'figure'),
     Output('error-message', 'children')],
    [Input('compare-btn', 'n_clicks')],
    [State('path-1', 'value'),
     State('path-2', 'value')]
)
def update_graph(n_clicks, path1, path2):
    if n_clicks == 0:
        return go.Figure(), ""
    
    if not path1 or not path2:
        return go.Figure(), "Please provide both folder paths."
    
    df1 = data_utils.load_overall_results(path1)
    df2 = data_utils.load_overall_results(path2)
    
    if df1 is None:
        return go.Figure(), f"Could not find valid data in Path 1: {path1}"
    if df2 is None:
        return go.Figure(), f"Could not find valid data in Path 2: {path2}"
    
    label1 = data_utils.get_folder_label(path1)
    label2 = data_utils.get_folder_label(path2)
    
    # Merge dataframes on Metric to ensure we compare the same things
    merged = pd.merge(df1, df2, on='Metric', suffixes=(f'_{label1}', f'_{label2}'))
    
    if merged.empty:
        return go.Figure(), "No common metrics found between the two folders."
    
    fig = go.Figure(data=[
        go.Bar(name=label1, x=merged['Metric'], y=merged[f'Value_{label1}']),
        go.Bar(name=label2, x=merged['Metric'], y=merged[f'Value_{label2}'])
    ])
    
    fig.update_layout(
        barmode='group',
        title='Metric Comparison',
        xaxis_title='Metric',
        yaxis_title='Value',
        legend_title='Folders'
    )
    
    return fig, ""

if __name__ == '__main__':
    app.run_server(debug=True, port=5121)
