import plotly.express as px
import pandas as pd


class ChartFactory:
    @staticmethod
    def create(kind: str, df: pd.DataFrame, x: str, y: str = None):
        if kind == 'line':
            fig = px.line(df, x=x, y=y, title=f'{y} vs {x}')
        if kind == 'bar':
            fig = px.bar(df, x=x, y=y, title=f'{y} by {x}')
        if kind == 'scatter':
            fig = px.scatter(df, x=x, y=y, title=f'{y} vs {x}')
        if kind == 'histogram':
            fig = px.histogram(df, x=x, title=f'Distribution of {x}')
        if kind == 'box':
            fig = px.box(df, x=x, y=y, title=f'{y} by {x}')
        if kind == 'heatmap':
            num = df.select_dtypes('number')
            if num.empty:
                raise ValueError("No numeric columns for heatmap")
            fig = px.imshow(num.corr(), title='Correlation Heatmap')

        return fig