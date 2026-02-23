import pandas as pd
from sqlalchemy import create_engine

# ---- LOAD RAW CSV ----
df = pd.read_csv("customer_shopping_behavior.csv")

# ---- CLEAN DATA ----
df.columns = df.columns.str.lower().str.replace(" ", "_")
df = df.drop_duplicates()

# ---- CONNECT TO POSTGRESQL ----
engine = create_engine(
    "postgresql+psycopg2://postgres:durvesh1107@localhost:5432/postgres"
)

# ---- WRITE DATA TO SQL ----
df.to_sql("shopping_behavior", engine, if_exists="replace", index=False)

print("Data loaded to PostgreSQL!")
