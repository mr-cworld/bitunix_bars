import psycopg2
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
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def test_database_connection():
    config = load_db_config()
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=config['database'],
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port']
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Create a test table
        logger.info("Creating test table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                value FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert some test data
        logger.info("Inserting test data...")
        test_data = [
            ('BTC Test', 50000.0),
            ('ETH Test', 3000.0),
            ('SOL Test', 100.0)
        ]
        
        cur.executemany(
            "INSERT INTO test_table (name, value) VALUES (%s, %s)",
            test_data
        )
        
        # Commit the changes
        conn.commit()
        
        # Query and display the data
        logger.info("Querying test data...")
        cur.execute("SELECT * FROM test_table")
        rows = cur.fetchall()
        
        logger.info("Test table contents:")
        for row in rows:
            logger.info(f"Row: {row}")
            
        logger.info("Database test completed successfully!")
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    try:
        test_database_connection()
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        sys.exit(1) 