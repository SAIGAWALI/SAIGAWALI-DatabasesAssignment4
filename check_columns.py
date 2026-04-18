import mysql.connector
from mysql.connector import Error

credentials = {
    'host': '10.0.116.184',
    'user': 'The_Boys',
    'password': 'password@123',
    'database': 'The_Boys'
}

# Check column names in shard_1_member table
try:
    conn = mysql.connector.connect(
        host=credentials['host'],
        port=3308,  # Shard 1
        user=credentials['user'],
        password=credentials['password'],
        database=credentials['database']
    )
    cursor = conn.cursor()
    
    print("Checking shard_1_member table structure...")
    cursor.execute("DESCRIBE shard_1_member")
    columns = cursor.fetchall()
    
    print("\n✓ shard_1_member columns:")
    for col in columns:
        print(f"  • {col[0]} ({col[1]})")
    
    # Also check a sample query
    print("\n✓ Sample data from shard_1_member:")
    cursor.execute("SELECT * FROM shard_1_member LIMIT 2")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")
    
    conn.close()
except Error as e:
    print(f"Error: {e}")
