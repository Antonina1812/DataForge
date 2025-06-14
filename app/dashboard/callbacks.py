import uuid
import pandas as pd
from dash import dcc, html, Input, Output, State, ctx, ALL, no_update
import dash_bootstrap_components as dbc
from app import app
from .data_manager import DataManager
from .chart_factory import ChartFactory


dm = DataManager(app.config.get('UPLOAD_FOLDER'))

def register_callbacks(app):
    @app.callback(
        Output("file-selector", "options"),
        [Input("refresh-files", "n_clicks")],
        prevent_initial_call=False
    )
    def update_file_list(n_clicks):
        return dm.get_available_files()
    
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
        Input("file-selector", "value"),
        prevent_initial_call=True,
    )
    def load_selected_file(filename):
        if not filename:
            return no_update, no_update
        
        try:
            data, preview = dm.load_from_directory(filename)
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
        Output("board", "layouts"),
        Output("board", "children"),
        Input("add-chart", "n_clicks"),
        Input({"role": "close", "id": ALL}, "n_clicks"),
        State("chart-type", "value"),
        State("x-column", "value"),
        State("y-column", "value"),
        State("stored-data", "data"),
        State("board", "layouts"),
        State("board", "children"),
        prevent_initial_call=True,
    )
    def manage_cards(_, __, kind, x, y, records, current_layouts, children):
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
                        style={
                            "position": "absolute", 
                            "top": 5, 
                            "right": 4, 
                            "zIndex": 1000
                        },
                    ),
                    dcc.Graph(
                        figure=fig,
                        config={
                            "displaylogo": False,
                            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                            "responsive": True,
                        },
                        style={"height": "100%", "width": "100%"},
                        responsive=True,
                    ),
                ],
                id=cid,
                style={
                    "height": "100%",
                    "width": "100%",
                    "padding": "8px",
                    "boxSizing": "border-box",
                    "backgroundColor": "#111",
                    "border": "1px solid #444",
                    "borderRadius": "10px",
                    "overflow": "hidden",
                },
            )
            
            new_layout = {
                "lg": {"i": cid, "x": 0, "y": 0, "w": 6, "h": 4, "minW": 3, "minH": 2},
                "md": {"i": cid, "x": 0, "y": 0, "w": 8, "h": 4, "minW": 4, "minH": 2},
                "sm": {"i": cid, "x": 0, "y": 0, "w": 12, "h": 4, "minW": 6, "minH": 2},
                "xs": {"i": cid, "x": 0, "y": 0, "w": 12, "h": 4, "minW": 12, "minH": 2},
            }
            
            updated_layouts = current_layouts or {"lg": [], "md": [], "sm": [], "xs": []}
            for breakpoint in ["lg", "md", "sm", "xs"]:
                if breakpoint not in updated_layouts:
                    updated_layouts[breakpoint] = []
                updated_layouts[breakpoint].append(new_layout[breakpoint])
            
            updated_children = (children or []) + [card]
            return updated_layouts, updated_children

        if isinstance(t_id, dict) and t_id.get("role") == "close":
            cid = t_id["id"]
            
            new_children = [c for c in children if c["props"]["id"] != cid]
            
            updated_layouts = current_layouts or {"lg": [], "md": [], "sm": [], "xs": []}
            for breakpoint in updated_layouts:
                updated_layouts[breakpoint] = [
                    item for item in updated_layouts[breakpoint] 
                    if item.get("i") != cid
                ]
            
            return updated_layouts, new_children

        return no_update, no_update

    @app.callback(
        Output("download-file", "data"),
        Input("download-btn", "n_clicks"),
        State("file-selector", "value"),
        prevent_initial_call=True
    )
    def trigger_download(n_clicks, filename):
        if not filename:
            raise no_update
        
        try:
            file_path = dm.get_file_path(filename)
            return dcc.send_file(file_path)
        except Exception as e:
            print(f"Download error: {str(e)}")
            return no_update

    @app.callback(
        Output("download-status", "children"),
        Input("download-btn", "n_clicks"),
        State("file-selector", "value"),
        prevent_initial_call=True
    )
    def show_download_status(n_clicks, filename):
        if not filename:
            return dbc.Alert("Please select a file first", color="danger", duration=3000)
        return no_update