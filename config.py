from pathlib import Path
import logging
import sys
from pprint import pformat
import yaml
import os, random, string
from datetime import timedelta
import pymongo
# Load config items from config.yaml.
# Use Path.resolve() to get the absolute path of the parent directory
yaml_dir = Path(__file__).resolve().parent
yaml_path = yaml_dir / "config.yaml"  # Use Path / operator to join paths

def load_yaml_config(path):
    """Load a yaml file and return a dictionary of its contents."""
    try:
        with open(path, "r") as stream:
            return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        logging.error(f"Failed to load {path}: {exc}")
        return None

# Load the config and update the global variables
yaml_config = load_yaml_config(yaml_path)
if yaml_config is not None:
    logging.info(f"Loaded config from {yaml_path}:")
    logging.info(pformat(yaml_config))
    globals().update(yaml_config)
else:
    logging.error(f"Could not load config from {yaml_path}.")
    sys.exit(1)  # Exit the program if the config is invalid

# Set a default value for SERVER_PORT if not specified in the config
SERVER_PORT = yaml_config.get("SERVER_PORT", None)

# Use Path.resolve() to get the absolute path of the current directory
SERVER_DIR = Path(__file__).resolve().parent

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

import os



class BaseConfig:
    
    SECRET_KEY = os.getenv('SECRET_KEY', None)
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', None)
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

    # GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', None)
    # GITHUB_CLIENT_SECRET = os.getenv('GITHUB_SECRET_KEY', None)

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    MONGO_URI ='mongodb+srv://kris:Baltimore10@test.ltopuuj.mongodb.net/?retryWrites=true&w=majority'

    if not MONGO_URI:
        raise ValueError('MONGO_URI environment variable is not set.')

    # pymongo connection options
    MONGO_OPTIONS = {
        'retryWrites': True,
        'w': 'majority'
    }

    # create a pymongo client instance
    MONGO_CLIENT = pymongo.MongoClient(MONGO_URI, **MONGO_OPTIONS)

    # extract database name from the uri
    DB_NAME = pymongo.uri_parser.parse_uri(MONGO_URI)['database']

    # set up the Flask app configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USE_SQLITE = False

    if not MONGO_URI.startswith('mongodb+srv://'):
        # parse the uri to extract the username, password, and other parameters
        parsed_uri = pymongo.uri_parser.parse_uri(MONGO_URI)
        username = parsed_uri['username']
        password = parsed_uri['password']
        auth_source = parsed_uri['options'].get('authSource', DB_NAME)

        # create a new uri with url-encoded username and password
        quoted_username = quote_plus(username)
        quoted_password = quote_plus(password)
        new_uri = f"mongodb://{quoted_username}:{quoted_password}@{parsed_uri['nodelist'][0][0]}:{parsed_uri['nodelist'][0][1]}/{DB_NAME}?authSource={auth_source}"

        # set the new uri as the connection uri
        MONGO_URI = new_uri

    # print the connection uri for debugging purposes
    print(f"Connecting to MongoDB at {MONGO_URI}")

    # set up the Flask app configuration
    MONGODB_SETTINGS = {
        'host': MONGO_URI,
    }
