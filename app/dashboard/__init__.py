# app/dashboard/__init__.py
import dash
import dash_bootstrap_components as dbc
from flask import Blueprint
import os


def create_dash_app(flask_app):
    dash_bp = Blueprint(
        'dash_bp',
        __name__,
        static_folder='assets',
        static_url_path='/dash/assets'
    )
    
    flask_app.register_blueprint(dash_bp)

    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        external_stylesheets=[dbc.themes.VAPOR],
        suppress_callback_exceptions=True,
        url_base_pathname='/dash/',
        assets_folder=os.path.join(os.path.dirname(__file__), 'assets'),
    )
    
    from .layout import serve_layout
    from .callbacks import register_callbacks
    
    dash_app.layout = serve_layout
    register_callbacks(dash_app)
    
    return dash_app