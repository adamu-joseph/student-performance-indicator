import pandas as pd

class Variables:
    """ Stores the names of the columns in the dataset in their correct category [object, numerical, category]
    Supports only category, object and number datatypes """
    
    def __init__(self, df:pd.DataFrame):
        self.df = df
        self._extract_variables()

    def _extract_variables(self):
        """Automatically extract variable types from dataframe"""
        self.categorical_var = self.df.select_dtypes(include=['category']).columns.tolist()
        self.object_var = self.df.select_dtypes(include=['object']).columns.tolist()
        self.numerical_var = self.df.select_dtypes(include=['number']).columns.tolist()

    def refresh(self):
        """ Optimize and then refresh the lists """
        self._extract_variables()
        self.optimize()

    def optimize(self):
        """ Optimize the dataframe:
        - Convert low-cardinality object columns to category
        - Downcast integers and floats for memory efficiency
        - Refresh variable lists after changes 
        """
        for col in self.df.select_dtypes(include='object'):
            num_unique = self.df[col].nunique()
            num_total = len(self.df[col])
            
            if num_unique <= 10:
                self.df[col] = self.df[col].astype('category')

        # Integers
        for col in self.df.select_dtypes(include=['int']):
            self.df[col] = pd.to_numeric(self.df[col], downcast='integer')

        # Floats
        for col in self.df.select_dtypes(include=['float']):
            self.df[col] = pd.to_numeric(self.df[col], downcast='float')