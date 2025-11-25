import sqlalchemy
from sqlalchemy import text

# SQLite connection string
DATABASE_URL = "sqlite:///market.db"

def init_db():
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL)
        with engine.connect() as conn:
            with open("schema.sql", "r") as f:
                sql_script = f.read()
            
            # SQLite driver might not support multiple statements in one call depending on the version/driver,
            # but SQLAlchemy usually handles it or we can split.
            # For SQLite, it's safer to execute statements one by one if they are separated by semicolons.
            statements = sql_script.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
            print("Schema executed successfully. Database 'market.db' created.")
    except Exception as e:
        print(f"Error executing schema: {e}")

if __name__ == "__main__":
    init_db()
