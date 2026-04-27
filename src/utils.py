import os
import sys

import pandas as pd
import numpy as np
import dill
import pickle
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV

from src.exception import CustomException

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

def evaluate_model(x_train, x_test, y_train, y_test, models):
    try:
        report = {}
        
        for i in range(len(list(models))):
            model = list(models.values())[i]

            model.fit(x_train, y_train) # Train the model
            y_train_pred = model.predict(x_train)
            y_test_pred = model.predict(x_test)

            train_model_score = r2_score(y_train, y_train_pred)
            test_model_score = r2_score(y_test, y_test_pred)

            report[list(models.keys())[i]] = test_model_score

        return report
    
    except Exception as e:
        raise CustomException(e, sys)
     
def save_object(file_path, obj):
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, 'wb') as file_obj:
            dill.dump(obj, file_obj)
    except Exception as e:
        raise CustomException(e, sys)