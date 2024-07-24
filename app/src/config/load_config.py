"""
Module for loading configuration from a YAML file.

This module provides a function `load_config` to load configuration settings
from a specified YAML file into a dictionary. If the file does not exist, 
it returns an empty dictionary.

Imports:
    os: Provides a way of using operating system dependent functionality like 
    reading or writing to the file system.
    yaml: Provides YAML parsing and emitting capabilities.

Function:
    load_config: Loads the configuration from a YAML file into a dictionary.
"""

import os  # Module pour interagir avec le système d'exploitation
import yaml  # Module pour manipuler les fichiers YAML


def load_config(config_path="config.yaml"):
    """
    Load the YAML configuration from the specified path.
    
    Parameters:
    config_path (str): The path to the configuration file. Default is "config.yaml".
    
    Returns:
    dict: The loaded configuration as a dictionary. Returns an
    empty dictionary if the file does not exist.
    
    This function checks if the configuration file exists at the specified path.
    If it does, it opens the file, reads the YAML content, and loads it into a dictionary.
    If the file does not exist, it returns an empty dictionary.
    """
    config = {}  # Initialise un dictionnaire vide pour stocker la configuration
    if os.path.exists(config_path):  # Vérifie si le fichier de configuration existe
        with open(config_path, "r", encoding="utf-8") as file:  # Ouvre le fichier en lecture
# avec encodage UTF-8
            config = yaml.safe_load(file)  # Charge le contenu YAML dans un dictionnaire
    return config  # Retourne le dictionnaire de configuration
