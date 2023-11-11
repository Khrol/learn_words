import sqlite3
from contextlib import closing

DB_NAME = "learn_words.db"
db_conn = sqlite3.connect(DB_NAME)

'''
progress:
0 - to learn
1 - repeat tomorrow
2 - repeat in 7 days
3 - repeat in 30 days
4 - learned
'''

def init_db():
    with closing(db_conn.cursor()) as cursor:
        cursor.execute("""
        SELECT count(*) 
        FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'""")
        table_count = cursor.fetchone()[0]
        if table_count == 0:
            cursor.execute("""
            CREATE TABLE words(
                word_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                progress INTEGER DEFAULT 0)
            """)
            cursor.execute("""
            CREATE TABLE results(
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER,
                result BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (word_id) REFERENCES customers (word_id)
                )
            """)
            db_conn.commit()


def select_one_value(sql, params=()):
    with closing(db_conn.cursor()) as cursor:
        result = cursor.execute(sql, params).fetchone()
        if result:
            return result[0]
