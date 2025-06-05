import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_draggable as dg
import plotly.io as pio


pio.templates.default = "plotly_dark"

def _controls_body() -> html.Div:
    return html.Div(
        [
            html.H5("Панель графиков"),
            html.Hr(),
            dcc.Upload(
                id="upload-data",
                children=dbc.Button("📂 Upload", color="secondary"),
                multiple=False,
                className="mb-3",
            ),
            dbc.Label("Тип графика"),
            dcc.Dropdown(
                id="chart-type",
                options=[
                    {"label": "Line", "value": "line"},
                    {"label": "Bar", "value": "bar"},
                    {"label": "Scatter", "value": "scatter"},
                    {"label": "Histogram", "value": "histogram"},
                    {"label": "Box", "value": "box"},
                    {"label": "Heatmap", "value": "heatmap"},
                ],
                value="line",
                className="mb-2",
            ),
            dbc.Label("Ось X"),
            dcc.Dropdown(id="x-column", className="mb-2"),
            dbc.Label("Ось Y"),
            dcc.Dropdown(id="y-column", className="mb-3"),
            dbc.Button("➕ Add", id="add-chart", n_clicks=0, color="success"),
            html.Hr(),
            html.Div(id="output-data-upload"),
        ],
        className="p-3",
    )

def make_layout() -> html.Div:
    board = dg.GridLayout(
        id="board",
        children=[],
        ncols=70,
        height=50,
        width=3000,
        layout=[],
        compactType=None,
        isDraggable=True,
        isResizable=True,
        preventCollision=False,
        isBounded=False,
        verticalCompact=False,
        style={
            "transform": "scale(1)",
            "minHeight": "700px",
            "minWidth": "700px",
        },
    )

    return html.Div(
        [
            dbc.NavbarSimple("Dashboard", dark=True, color="primary", fixed="top"),
            
            dbc.Button(
                "☰", id="controls-toggle", size="lg",
                style={
                    "position": "fixed", "top": "12px", "left": "12px",
                    "zIndex": 1050
                },
                color="secondary",
            ),

            dbc.Offcanvas(
                _controls_body(),
                id="controls-offcanvas",
                placement="start",
                is_open=False,
                backdrop=False,
                scrollable=True,
                style={"width": "500px"},
            ),

            html.Div(
                html.Div(
                    board,
                    id="board-container",
                    style={
                        "width": "3000px",
                        "height": "3000px",
                        "position": "relative",
                    },
                ),
                id="board-wrapper",
                style={
                    "height": "100vh",
                    "overflow": "scroll",
                    "cursor": "grab",
                    "padding": "60px 20px 20px 20px",
                },
            ),

            dcc.Store(id="stored-data"),
            dcc.Store(id="stored-layout", data=[]),
        ]
    )