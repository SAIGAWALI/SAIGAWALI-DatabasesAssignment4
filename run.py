#!/usr/bin/env python3
"""
Simple Flask app launcher
Run with: python run.py
"""

import sys
import os

# Add the Module_B directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
from app.main import app
from app.db import get_db_connection
from app.config import get_shard_settings
from app.sharding import get_shard_connection, NUM_SHARDS


def check_connections():
    """Check if both LOCAL DB and REMOTE SHARDS are accessible."""
    print("\n" + "=" * 60)
    print("Database Connection Status")
    print("=" * 60)
    
    # Check LOCAL DB
    print("\n[LOCAL DATABASE] localhost:3306")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM member")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"  ✅ Connected to dms_db")
        print(f"  ✅ Members table has {count} records")
    except Exception as e:
        print(f"  ❌ Connection Failed: {str(e)}")
        return False
    
    # Check REMOTE SHARDS
    print("\n[REMOTE SHARDS] 10.0.116.184")
    shard_config = get_shard_settings()
    shard_user = shard_config["user"]
    shard_password = shard_config["password"]
    shard_db = shard_config["database"]
    
    all_shards_ok = True
    for shard_id in range(NUM_SHARDS):
        port = 3307 + shard_id
        try:
            conn = get_shard_connection(shard_id, shard_user, shard_password, shard_db)
            cursor = conn.cursor()
            cursor.execute("SELECT @@hostname")
            hostname = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            print(f"  ✅ Shard {shard_id} (:{port}) - {hostname}")
        except Exception as e:
            print(f"  ❌ Shard {shard_id} (:{port}) - {str(e)}")
            all_shards_ok = False
    
    print("\n" + "=" * 60)
    if all_shards_ok:
        print("✅ All connections successful! App is ready.")
    else:
        print("⚠️  Some connections failed. Check errors above.")
    print("=" * 60 + "\n")
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Starting Doctor Management System")
    print("=" * 60)
    
    # Check database connections before starting server
    check_connections()
    
    print("Server running on: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='localhost', port=5000)
