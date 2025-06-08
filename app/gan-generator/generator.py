from ydata.synthesizers.regular.model import RegularSynthesizer
from ydata.synthesizers.timeseries.model import TimeSeriesSynthesizer
from ydata.metadata import Metadata
from ydata.dataset import Dataset, DatasetType
import pandas as pd


class TabularGANGenerator:
    def __init__(self, data_type=DatasetType.TABULAR):
        self.data_type = data_type

    def generate_samples(
            self,
            example_data_path: str,
            n_samples: int = 50,
            contition_on: str = None) -> pd.DataFrame:
        df = pd.read_csv(example_data_path)
        dataset = Dataset(df)
        metadata = Metadata(dataset=dataset, dataset_type=self.data_type)
        
        if self.data_type is DatasetType.TABULAR:
            model = RegularSynthesizer()
        elif self.data_type is DatasetType.TIMESERIES:
            model = TimeSeriesSynthesizer()
        
        model.fit(X=dataset, metadata=metadata)
        
        synth_data = model.sample(n_samples=n_samples, balancing=True, contition_on=contition_on)
        
        return synth_data
