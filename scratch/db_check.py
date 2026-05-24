import sqlite3
conn = sqlite3.connect('C:/Users/Asus/Desktop/Okul/websunucum/app.db')
print("Tables:", conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())
try:
    conn.execute("DROP TABLE IF EXISTS comment")
    conn.execute("DROP TABLE IF EXISTS _alembic_tmp_post")
    conn.commit()
    print("Tables dropped.")
except Exception as e:
    print(e)
