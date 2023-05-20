import pandas as pd

class DF(object):
    def __init__(self, df):
        if not isinstance(df, pd.DataFrame):
            raise TypeError
        self.df = df
        self._columns = set(df.columns)
    
    def __getattr__(self, name):
        if name in self._columns:
            return getattr(self,name)
        elif hasattr(self.df, name):
            return getattr(self.df, name)
        else:
            # Default behaviour
            return object.__getattribute__(self, name)
    
    @property
    def col_1(self):
        return self.df["col_1"]

    @property
    def col_2(self):
        return self.df["col_2"]

    