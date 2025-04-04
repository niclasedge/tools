import sqlite3
import json

def convert_db_to_json():
    # Connect to SQLite database
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()

    # Get database schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Available tables:", tables)

    # Get schema for each table
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"\nSchema for table {table[0]}:")
        for col in columns:
            print(col)

    # Get all URLs from the appropriate table (we'll update this after seeing the schema)
    try:
        cursor.execute("SELECT * FROM sqlite_master")
        print("\nFull database structure:")
        print(cursor.fetchall())
    except Exception as e:
        print(f"Error querying database: {e}")

    # Get all URLs from the database
    cursor.execute("SELECT image_url FROM image_history")
    rows = cursor.fetchall()

    # Convert to list of dictionaries
    images = [{"url": row[0]} for row in rows]

    # Write to JSON file
    with open('images.json', 'w') as f:
        json.dump({"images": images}, f, indent=2)

    conn.close()
    print("Successfully converted database to images.json")

if __name__ == "__main__":
    convert_db_to_json()
