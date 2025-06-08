import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_draggable as dg
import plotly.io as pio


pio.templates.default = "plotly_dark"

def _controls_body() -> html.Div:
    return html.Div(
        [
            html.H5("GraphPanel"),
            html.Hr(),
            
            dbc.Label("Choose file"),
            dbc.InputGroup([
                dcc.Dropdown(
                    id="file-selector",
                    placeholder="Select...",
                    className="mb-2",
                ),
                dbc.Button(
                    "🔄", 
                    id="refresh-files", 
                    color="secondary", 
                    outline=True,
                    title="Refresh"
                ),
            ], className="mb-3"),
            
            dbc.Label("Graph Type"),
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
            dbc.Label("Axis X"),
            dcc.Dropdown(id="x-column", className="mb-2"),
            dbc.Label("Axis Y"),
            dcc.Dropdown(id="y-column", className="mb-3"),
            dbc.Button("➕ Add", id="add-chart", n_clicks=0, color="success"),
            html.Hr(),
            html.Div(id="output-data-upload"),
        ],
        className="p-3",
    )

def make_layout() -> html.Div:
    board = dg.ResponsiveGridLayout(
        id="board",
        children=[],
        layouts={"lg": [], "md": [], "sm": [], "xs": []},
        breakpoints={"lg": 1200, "md": 996, "sm": 768, "xs": 480},
        gridCols={"lg": 12, "md": 10, "sm": 6, "xs": 4},
        height=60,
        resizeHandles=['se', 's', 'e', 'sw', 'w', 'nw'],
        style={
            "minHeight": "calc(100vh - 120px)",
            "width": "100%",
        },
    )

    return html.Div(
        [
            dbc.NavbarSimple("Dashboard", dark=True, color="primary", fixed="top"),
            
            dbc.Button(
                "☰", id="controls-toggle", size="lg",
                style={
                    "position": "fixed", "top": "15px", "left": "12px",
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
                board,
                id="board-wrapper",
                style={
                    "paddingTop": "80px",
                    "paddingLeft": "20px",
                    "paddingRight": "20px",
                    "paddingBottom": "20px",
                    "minHeight": "100vh",
                    "width": "100%",
                },
            ),

            dcc.Store(id="stored-data"),
        ]
    )