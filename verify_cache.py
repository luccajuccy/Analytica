import sqlite3
import os
import json
from datetime import datetime

DB_PATH = 'contatos_bms.db'

def verify():
    print(f"Checking DB at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("DB file not found!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='building_cache'")
        result = cursor.fetchone()
        
        if result:
            print("Table 'building_cache' exists.")
        else:
            print("Table 'building_cache' DOES NOT exist. (This is expected if server hasn't restarted/run init_cache_db yet)")
            # Try creating it manually to verify SQL syntax
            print("Trying to create table manually to verify syntax...")
            conn.execute('''
                CREATE TABLE IF NOT EXISTS building_cache (
                    building_name TEXT PRIMARY KEY,
                    data_json TEXT,
                    last_updated TEXT,
                    next_update TEXT
                )
            ''')
            print("Table creation syntax is valid.")
            
        # Test Insert
        test_data = {"test": "data"}
        conn.execute('''
            INSERT OR REPLACE INTO building_cache (building_name, data_json, last_updated, next_update)
            VALUES (?, ?, ?, ?)
        ''', ('TEST_BUILDING', json.dumps(test_data), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '2030-01-01 00:00:00'))
        conn.commit()
        print("Insert verification successful.")
        
        # Test Read
        row = conn.execute("SELECT * FROM building_cache WHERE building_name='TEST_BUILDING'").fetchone() 
        if row:
            print(f"Read verification successful: {row}")
        else:
            print("Read verification FAILED.")
            
        # Verify Summary Cache Existence (Likely won't exist yet unless job ran, but we can try)
        row_sum = conn.execute("SELECT * FROM building_cache WHERE building_name='BUILDINGS_SUMMARY'").fetchone()
        if row_sum:
             print(f"Summary Cache Found: {row_sum[0]} - {len(str(row_sum[1]))} bytes")
        else:
             print("Summary Cache NOT found (Job might not have matched tag yet or not run).")
            
        conn.close()
        
    except Exception as e:
        print(f"Verification Failed: {e}")

if __name__ == "__main__":
    verify()
