import dash
from dash import dcc, html, Input, Output, State, ALL, ctx, no_update, MATCH
import plotly.graph_objects as go
import data_utils
import pandas as pd
import subprocess
from functools import reduce

app = dash.Dash(__name__, suppress_callback_exceptions=True)

COLORS = [
    '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
    '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
]


def make_folder_row(index, value=''):
    return html.Div([
        html.Label(f"Folder Path {index + 1}:"),
        html.Div([
            dcc.Input(
                id={'type': 'folder-path', 'index': index},
                type='text',
                value=value or '',
                placeholder=f'Enter path to folder {index + 1}',
                style={'flex': '1', 'minWidth': '0'},
            ),
            html.Button(
                'Browse',
                id={'type': 'browse-btn', 'index': index},
                n_clicks=0,
                style={'marginLeft': '8px', 'flexShrink': '0'},
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginTop': '4px'}),
    ], style={
        'width': '48%',
        'minWidth': '320px',
        'display': 'inline-block',
        'padding': '10px',
        'verticalAlign': 'top',
    })


app.layout = html.Div([
    html.H1("Metric Comparison Dashboard by Harish Chodu"),

    dcc.Store(id='folder-count', data=2),

    html.Div(
        id='folder-inputs-container',
        children=[make_folder_row(0), make_folder_row(1)],
    ),

    html.Div([
        html.Button(
            '+ Add Data',
            id='add-folder-btn',
            n_clicks=0,
            style={
                'margin': '10px 20px',
                'padding': '8px 18px',
                'backgroundColor': '#00CC96',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'cursor': 'pointer',
                'fontWeight': 'bold',
            },
        ),
    ]),

    html.Button('Compare Metrics', id='compare-btn', n_clicks=0, style={'margin': '20px'}),

    html.Div(id='error-message', style={'color': 'red', 'padding': '10px'}),

    dcc.Graph(id='comparison-graph'),

    html.Div([
        html.H3("Logs"),
        html.Div(id='logs-content', style={
            'whiteSpace': 'pre-wrap',
            'fontFamily': 'monospace',
            'fontSize': '13px',
            'backgroundColor': '#1e1e1e',
            'color': '#d4d4d4',
            'padding': '12px',
            'borderRadius': '6px',
            'maxHeight': '220px',
            'overflowY': 'auto',
        }),
    ], style={'padding': '10px 20px', 'marginTop': '10px'}),
])


@app.callback(
    Output('folder-inputs-container', 'children'),
    Output('folder-count', 'data'),
    Input('add-folder-btn', 'n_clicks'),
    State('folder-count', 'data'),
    State({'type': 'folder-path', 'index': ALL}, 'value'),
    prevent_initial_call=True,
)
def add_folder_row(n_clicks, current_count, existing_values):
    new_count = current_count + 1
    rows = []
    for i in range(new_count):
        val = existing_values[i] if i < len(existing_values) else ''
        rows.append(make_folder_row(i, value=val))
    return rows, new_count


@app.callback(
    Output({'type': 'folder-path', 'index': MATCH}, 'value'),
    Input({'type': 'browse-btn', 'index': MATCH}, 'n_clicks'),
    State({'type': 'folder-path', 'index': MATCH}, 'value'),
    prevent_initial_call=True,
)
def browse_for_folder(_n_clicks, current_value):
    result = subprocess.run(
        ["osascript", "-e",
         'POSIX path of (choose folder with prompt "Select a folder")'],
        capture_output=True, text=True, timeout=120,
    )
    selected_path = result.stdout.strip().rstrip("/")
    if not selected_path:
        return current_value or no_update
    return selected_path


@app.callback(
    [Output('comparison-graph', 'figure'),
     Output('error-message', 'children'),
     Output('logs-content', 'children')],
    Input('compare-btn', 'n_clicks'),
    State({'type': 'folder-path', 'index': ALL}, 'value'),
    prevent_initial_call=True,
)
def update_graph(n_clicks, all_paths):
    if not n_clicks:
        return go.Figure(), "", ""

    paths = [p.strip() for p in all_paths if p and p.strip()]

    if len(paths) < 2:
        return go.Figure(), "Please provide at least two folder paths.", ""

    logs = []
    dataframes = []
    labels = []

    for i, path in enumerate(paths):
        tag = f"Path {i + 1}"
        sub = data_utils.get_highest_solo_inference_path(path)
        logs.append(f"[{tag}] Root folder : {path}")
        logs.append(f"[{tag}] Sub-folder  : {sub or 'NOT FOUND'}")
        logs.append("")

        df = data_utils.load_overall_results(path)
        if df is None:
            logs.append(f"✗ No overall_results.csv found under {tag}")
            return (
                go.Figure(),
                f"Could not find valid data in {tag}: {path}",
                "\n".join(logs),
            )

        label = data_utils.get_folder_label(path)
        if label in labels:
            label = f"{label} ({i + 1})"
        labels.append(label)

        logs.append(f"✓ Loaded {len(df)} metrics from {tag} ({label})")
        dataframes.append(df.rename(columns={'Value': f'Value_{label}'}))

    merged = reduce(
        lambda left, right: pd.merge(left, right, on='Metric', how='inner'),
        dataframes,
    )

    if merged.empty:
        logs.append("\n✗ No common metrics across the folders")
        return go.Figure(), "No common metrics found across the folders.", "\n".join(logs)

    logs.append(f"\n✓ {len(merged)} common metrics matched for comparison")

    fig = go.Figure(data=[
        go.Bar(
            name=label,
            x=merged['Metric'],
            y=merged[f'Value_{label}'],
            marker_color=COLORS[i % len(COLORS)],
        )
        for i, label in enumerate(labels)
    ])

    fig.update_layout(
        barmode='group',
        title='Metric Comparison',
        xaxis_title='Metric',
        yaxis_title='Value',
        legend_title='Folders',
    )

    return fig, "", "\n".join(logs)


if __name__ == '__main__':
    app.run(debug=True, port=5121)
