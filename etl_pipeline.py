import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
import sqlalchemy
from sqlalchemy import text
import datetime
import time

# Configuration
DATABASE_URL = "sqlite:///market.db"
# Added SPY for Beta calculation
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'JPM', 'SPY']
START_DATE = (
    datetime.date.today() -
    datetime.timedelta(
        days=5 *
        365)).strftime('%Y-%m-%d')
END_DATE = datetime.date.today().strftime('%Y-%m-%d')


def get_db_engine():
    return sqlalchemy.create_engine(DATABASE_URL)


def fetch_stock_data(ticker, retries=3):
    """Fetch stock data from yfinance with retry logic."""
    for i in range(retries):
        try:
            print(f"Fetching data for {ticker}...")
            df = yf.download(
                ticker,
                start=START_DATE,
                end=END_DATE,
                progress=False)
            if df.empty:
                print(f"Warning: No data found for {ticker}")
                return None

            # Reset index to make Date a column
            df = df.reset_index()

            # Normalize columns (yfinance can return MultiIndex)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(
                    1)  # Drop Ticker level if present

            # Rename columns to match schema
            df = df.rename(columns={
                'Date': 'date',
                'Close': 'close_price',
                'Volume': 'volume'
            })

            # Keep only necessary columns
            df = df[['date', 'close_price', 'volume']]
            df['ticker'] = ticker

            # Normalize date
            df['date'] = pd.to_datetime(df['date']).dt.date

            return df
        except Exception as e:
            print(f"Attempt {i + 1} failed for {ticker}: {e}")
            time.sleep(1)
    print(f"Failed to fetch data for {ticker} after {retries} retries.")
    return None


def fetch_economic_data():
    """Fetch 10-Year Treasury Rate from FRED."""
    try:
        print("Fetching 10-Year Treasury Rate (DGS10)...")
        # DGS10: 10-Year Treasury Constant Maturity Rate
        # CPIAUCSL: Consumer Price Index for All Urban Consumers: All Items in
        # U.S. City Average

        # Fetching DGS10
        df_rate = web.DataReader('DGS10', 'fred', START_DATE, END_DATE)
        df_rate = df_rate.reset_index().rename(
            columns={'DATE': 'date', 'DGS10': 'interest_rate_10y'})

        # Fetching CPI (Monthly, so we might need to forward fill or just store as is)
        # For simplicity in this daily dashboard, let's just stick to DGS10 as requested in Phase 2 logic
        # But schema has inflation_cpi. Let's try to fetch it.
        try:
            df_cpi = web.DataReader('CPIAUCSL', 'fred', START_DATE, END_DATE)
            df_cpi = df_cpi.reset_index().rename(
                columns={'DATE': 'date', 'CPIAUCSL': 'inflation_cpi'})
        except Exception as e:
            print(f"Could not fetch CPI data: {e}")
            df_cpi = pd.DataFrame(columns=['date', 'inflation_cpi'])

        # Merge economic data
        # Since CPI is monthly and Rates are daily, we merge on Date.
        # We will need a master date range to merge properly or just merge on available dates.
        # Let's start with Rates as the base.
        df_eco = df_rate

        # Normalize date
        df_eco['date'] = pd.to_datetime(df_eco['date']).dt.date

        return df_eco
    except Exception as e:
        print(f"Error fetching economic data: {e}")
        return None


def load_data(engine):
    """Main ETL process."""

    # 1. Load Dimension Table (Stocks)
    with engine.connect() as conn:
        # Clear existing data to avoid duplicates (simple approach for this
        # task)
        conn.execute(text("DELETE FROM fact_price_daily"))
        conn.execute(text("DELETE FROM dim_stock"))
        conn.execute(text("DELETE FROM fact_economic"))
        conn.commit()

        stocks = [
            {'ticker': 'AAPL', 'company_name': 'Apple Inc.', 'sector': 'Technology'},
            {'ticker': 'MSFT', 'company_name': 'Microsoft Corp.', 'sector': 'Technology'},
            {'ticker': 'GOOGL', 'company_name': 'Alphabet Inc.', 'sector': 'Technology'},
            {'ticker': 'JPM', 'company_name': 'JPMorgan Chase & Co.', 'sector': 'Financials'},
            {'ticker': 'SPY', 'company_name': 'SPDR S&P 500 ETF Trust', 'sector': 'ETF'}
        ]

        print("Loading dim_stock...")
        df_stocks = pd.DataFrame(stocks)
        df_stocks.to_sql('dim_stock', engine, if_exists='append', index=False)

    # 2. Load Fact Table (Prices)
    all_prices = []
    for ticker in TICKERS:
        df = fetch_stock_data(ticker)
        if df is not None:
            # Forward fill missing values
            df = df.ffill()
            all_prices.append(df)

    if all_prices:
        print("Loading fact_price_daily...")
        df_final_prices = pd.concat(all_prices)
        df_final_prices.to_sql(
            'fact_price_daily',
            engine,
            if_exists='append',
            index=False)

    # 3. Load Fact Table (Economic)
    df_eco = fetch_economic_data()
    if df_eco is not None:
        print("Loading fact_economic...")
        # Forward fill missing values
        df_eco = df_eco.ffill()
        df_eco.to_sql('fact_economic', engine, if_exists='append', index=False)

    print("ETL Pipeline completed successfully.")


if __name__ == "__main__":
    engine = get_db_engine()
    load_data(engine)
