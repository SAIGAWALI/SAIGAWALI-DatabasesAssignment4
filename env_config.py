"""
Environment Configuration Loader
Loads environment variables from .env file
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the Module_B directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Main Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'dms_db')

# Shard Database Configuration
SHARD_DB_USER = os.getenv('SHARD_DB_USER', 'root')
SHARD_DB_PASSWORD = os.getenv('SHARD_DB_PASSWORD', '')
SHARD_DB_NAME = os.getenv('SHARD_DB_NAME', 'dms_db')

# Shard Server Configuration
SHARD_HOST = os.getenv('SHARD_HOST', '10.0.116.184')
SHARD_PORT_0 = int(os.getenv('SHARD_PORT_0', 3307))
SHARD_PORT_1 = int(os.getenv('SHARD_PORT_1', 3308))
SHARD_PORT_2 = int(os.getenv('SHARD_PORT_2', 3309))

SHARD_PORTS = [SHARD_PORT_0, SHARD_PORT_1, SHARD_PORT_2]

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


def get_db_config():
    """Return main database configuration dictionary"""
    return {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'database': DB_NAME
    }


def get_shard_config():
    """Return shard database configuration dictionary"""
    return {
        'host': SHARD_HOST,
        'user': SHARD_DB_USER,
        'password': SHARD_DB_PASSWORD,
        'database': SHARD_DB_NAME,
        'ports': SHARD_PORTS
    }


if __name__ == '__main__':
    # Test if configuration loaded correctly
    print("✓ Main DB Config:")
    config = get_db_config()
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  User: {config['user']}")
    print(f"  Database: {config['database']}")
    
    print("\n✓ Shard DB Config:")
    shard_config = get_shard_config()
    print(f"  Host: {shard_config['host']}")
    print(f"  Ports: {shard_config['ports']}")
    print(f"  User: {shard_config['user']}")
    print(f"  Database: {shard_config['database']}")
