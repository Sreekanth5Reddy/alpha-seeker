import pandas as pd
import numpy as np
import sqlalchemy

DATABASE_URL = "sqlite:///market.db"


def get_data(ticker):
    """Fetch daily price data for a specific ticker from the database."""
    engine = sqlalchemy.create_engine(DATABASE_URL)
    query = f"""
        SELECT date, close_price
        FROM fact_price_daily
        WHERE ticker = '{ticker}'
        ORDER BY date ASC
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['return'] = df['close_price'].pct_change()
    return df.dropna()


def calculate_var(ticker, confidence_level=0.95):
    """
    Calculate 95% Historical VaR.
    VaR is the negative of the (1 - confidence_level) percentile of returns.
    """
    df = get_data(ticker)
    if df.empty:
        return None

    # Historical VaR
    # If confidence is 0.95, we look for the 0.05 quantile
    var_percentile = 1 - confidence_level
    var_value = df['return'].quantile(var_percentile)

    # VaR is typically expressed as a positive number representing loss
    return -var_value


def calculate_beta(ticker, benchmark_ticker='SPY'):
    """
    Calculate Beta vs Benchmark (SPY).
    Beta = Cov(Stock, Benchmark) / Var(Benchmark)
    """
    df_stock = get_data(ticker)
    df_bench = get_data(benchmark_ticker)

    if df_stock.empty or df_bench.empty:
        return None

    # Align dates
    joined = df_stock[['return']].join(
        df_bench[['return']], lsuffix='_stock', rsuffix='_bench').dropna()

    if joined.empty:
        return None

    covariance = np.cov(joined['return_stock'], joined['return_bench'])[0][1]
    variance = np.var(joined['return_bench'])

    if variance == 0:
        return None

    beta = covariance / variance
    return beta


if __name__ == "__main__":
    # Test
    print(f"VaR for AAPL: {calculate_var('AAPL')}")
    print(f"Beta for AAPL: {calculate_beta('AAPL')}")
