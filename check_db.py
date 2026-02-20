import sqlite3
import os

db_path = 'data/upi_fraud.db'
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Connected! Tables:", tables)
        conn.close()
    except Exception as e:
        print("Connection failed:", e)
else:
    print("DB file not found at", db_path)
