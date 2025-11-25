import sqlalchemy
from sqlalchemy import text

DATABASE_URL = "sqlite:///market.db"

def verify_data():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Verifying data counts...")
        
        # Count dim_stock
        result = conn.execute(text("SELECT COUNT(*) FROM dim_stock"))
        count_stock = result.scalar()
        print(f"dim_stock count: {count_stock} (Expected: 5)")
        
        # Count fact_price_daily
        result = conn.execute(text("SELECT COUNT(*) FROM fact_price_daily"))
        count_price = result.scalar()
        print(f"fact_price_daily count: {count_price} (Expected: > 0)")
        
        # Count fact_economic
        result = conn.execute(text("SELECT COUNT(*) FROM fact_economic"))
        count_eco = result.scalar()
        print(f"fact_economic count: {count_eco} (Expected: > 0)")
        
        # Sample check
        print("\nSample Price Data:")
        result = conn.execute(text("SELECT * FROM fact_price_daily LIMIT 3"))
        for row in result:
            print(row)

if __name__ == "__main__":
    verify_data()
