import plotly.express as px
import pandas as pd


class ChartFactory:
    @staticmethod
    def create(kind: str, df: pd.DataFrame, x: str, y: str = None):
        if kind == 'line':
            return px.line(df, x=x, y=y, title=f'{y} vs {x}')
        if kind == 'bar':
            return px.bar(df, x=x, y=y, title=f'{y} by {x}')
        if kind == 'scatter':
            return px.scatter(df, x=x, y=y, title=f'{y} vs {x}')
        if kind == 'histogram':
            return px.histogram(df, x=x, title=f'Distribution of {x}')
        if kind == 'box':
            return px.box(df, x=x, y=y, title=f'{y} by {x}')
        if kind == 'heatmap':
            num = df.select_dtypes('number')
            if num.empty:
                raise ValueError("Нет числовых столбцов для heatmap")
            return px.imshow(num.corr(), title='Correlation Heatmap')
        raise ValueError(f"Unknown kind: {kind}")