import dash
import dash_bootstrap_components as dbc
from app.dashboard.layout import make_layout
from app.dashboard.callbacks import register_callbacks


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.VAPOR], suppress_callback_exceptions=True)
app.layout = make_layout()
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True, port=6001)