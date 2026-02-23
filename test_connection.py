from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://postgres:durvesh1107@localhost:5432/postgres")

try:
    conn = engine.connect()
    print("Connection successful!")
    conn.close()
except Exception as e:
    print("Error:", e)
