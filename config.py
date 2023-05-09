from pathlib import Path
import logging
import sys
from pprint import pformat
import yaml
import os, random, string
from datetime import timedelta
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
class BaseConfig():


    
    SECRET_KEY = os.getenv('SECRET_KEY', None)
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', None)
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

    GITHUB_CLIENT_ID     = os.getenv('GITHUB_CLIENT_ID' , None)
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_SECRET_KEY', None)
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_ENGINE   = os.getenv('DB_ENGINE'   , None)
    DB_USERNAME = os.getenv('DB_USERNAME' , None)
    DB_PASS     = os.getenv('DB_PASS'     , None)
    DB_HOST     = os.getenv('DB_HOST'     , None)
    DB_PORT     = os.getenv('DB_PORT'     , None)
    DB_NAME     = os.getenv('DB_NAME'     , None)

    USE_SQLITE  = True 

    # try to set up a Relational DBMS
    if DB_ENGINE and DB_NAME and DB_USERNAME:

        try:
            
            # Relational DBMS: PSQL, MySql
            SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
                DB_ENGINE,
                DB_USERNAME,
                DB_PASS,
                DB_HOST,
                DB_PORT,
                DB_NAME
            ) 

            USE_SQLITE  = False

        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )
            print('> Fallback to SQLite ')    

    if USE_SQLITE:

        # This will create a file in <app> FOLDER
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')