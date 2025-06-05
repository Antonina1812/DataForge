import uuid
import pandas as pd
from dash import dcc, html, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc

from .data_manager import DataManager
from .chart_factory import ChartFactory


dm = DataManager()

def register_callbacks(app):
    @app.callback(
        Output("controls-offcanvas", "is_open"),
        Input("controls-toggle", "n_clicks"),
        State("controls-offcanvas", "is_open"),
        prevent_initial_call=True
    )
    def toggle_sidebar(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(
        Output("stored-data", "data"),
        Output("output-data-upload", "children"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        prevent_initial_call=True,
    )
    def load_file(contents, filename):
        if not contents:
            return no_update, no_update
        try:
            data, preview = dm.load(contents, filename)
            return data, dcc.Markdown(preview, dangerously_allow_html=True)
        except Exception as e:
            return no_update, dbc.Alert(str(e), color="danger")

    @app.callback(
        Output("x-column", "options"),
        Output("y-column", "options"),
        Input("stored-data", "data"))
    def update_columns(records):
        if not records:
            return [], []
        cols = [{"label": c, "value": c} for c in pd.DataFrame(records).columns]
        return cols, cols

    @app.callback(
        Output("board", "children"),
        Output("board", "layout"),
        Input("add-chart", "n_clicks"),
        Input({"role": "close", "id": ALL}, "n_clicks"),
        State("chart-type", "value"),
        State("x-column", "value"),
        State("y-column", "value"),
        State("stored-data", "data"),
        State("board", "children"),
        State("board", "layout"),
        prevent_initial_call=True,
    )
    def manage_cards(_, __, kind, x, y, records, children, layout):
        t_id = ctx.triggered_id
        if t_id == "add-chart":
            if not (records and x and (y or kind == "histogram")):
                return no_update, no_update
            df = pd.DataFrame(records)
            fig = ChartFactory.create(kind, df, x, y)
            cid = str(uuid.uuid4())
            card = html.Div(
                [
                    dbc.Button(
                        "✕",
                        id={"role": "close", "id": cid},
                        color="link",
                        size="sm",
                        style={"position": "absolute", "top": 2, "right": 4},
                    ),
                    dcc.Graph(figure=fig, config={"displaylogo": False},
                              style={"height": "100%"}),
                ],
                id=cid,
                style={
                    "height": "100%", "width": "100%",
                    "background": "white",
                    "border": "1px solid #ddd",
                    "borderRadius": "4px",
                    "overflow": "hidden",
                },
            )
            default_item = {"i": cid, "x": 0, "y": 0, "w": 4, "h": 8}
            return (children or []) + [card], (layout or []) + [default_item]

        if isinstance(t_id, dict) and t_id.get("role") == "close":
            cid = t_id["id"]
            new_children = [c for c in children if c["props"]["id"] != cid]
            new_layout   = [l for l in layout   if l["i"] != cid]
            return new_children, new_layout

        return no_update, no_update