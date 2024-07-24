"""
Module for loading data.

This module provides a function `load_csv_data` to load data
from a specified CSV file path into a DataFrame.

Example usage:
--------------
data = load_csv_data("path/to/file.csv")
print(data)

Functions:
----------
- load_csv_data(filepath): Loads the data from the specified CSV file path.
"""

import pandas as pd  # Importation de la bibliothèque pandas pour manipuler les données


def load_csv_data(filepath):
    """
    Load data from the specified CSV file path.
    
    Parameters:
    filepath (str): The path to the CSV file.
    
    Returns:
    pd.DataFrame: The loaded data as a DataFrame.
    
    This function reads the CSV file from the specified path and loads it
    into a pandas DataFrame.
    """
    return pd.read_csv(filepath)  # Lecture du fichier CSV et chargement dans un DataFrame
