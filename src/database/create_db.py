import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from pathlib import Path
import yaml
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_db_config():
    config_path = Path("config/database_config.yaml")
    default_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'bitunix_data',
        'user': 'postgres',
        'password': 'your_password_here'
    }
    
    try:
        if not config_path.exists():
            logger.warning(f"Config file not found at {config_path}. Using default configuration.")
            return default_config
            
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            
        if not config:
            logger.warning("Empty config file. Using default configuration.")
            return default_config
            
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {e}. Using default configuration.")
        return default_config

def create_database():
    config = load_db_config()
    
    # Create connection params without database name
    connection_params = {
        "host": config['host'],
        "port": config['port'],
        "user": config['user'],
        "password": config['password']
    }
    
    try:
        # Connect to PostgreSQL server
        logger.info("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(**connection_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check if database exists
        database_name = config['database']
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (database_name,))
        exists = cur.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{database_name}'...")
            cur.execute(f'CREATE DATABASE {database_name}')
            logger.info("Database created successfully!")
        else:
            logger.info(f"Database '{database_name}' already exists!")
            
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    try:
        create_database()
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        sys.exit(1) 