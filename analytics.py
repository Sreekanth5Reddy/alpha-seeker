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


def calculate_rsi(series, period=14):
    """Calculate Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(series, window):
    """Calculate Simple Moving Average (SMA)."""
    return series.rolling(window=window).mean()


def calculate_portfolio_risk(tickers, weights):
    """
    Calculate Portfolio VaR and Beta.
    weights: list of floats summing to 1.0
    """
    if not tickers or not weights or len(tickers) != len(weights):
        return None

    # Fetch all data
    returns_list = []
    for ticker in tickers:
        df = get_data(ticker)
        if df.empty:
            continue
        returns_list.append(df['return'].rename(ticker))
    
    if not returns_list:
        return None

    # Combine into one DataFrame and align dates
    df_portfolio = pd.concat(returns_list, axis=1).dropna()
    
    if df_portfolio.empty:
        return None

    # Calculate Weighted Portfolio Return
    # We need to make sure we only use weights for tickers that had data
    valid_tickers = df_portfolio.columns.tolist()
    valid_weights = [weights[tickers.index(t)] for t in valid_tickers]
    
    # Normalize weights if some tickers were dropped
    total_weight = sum(valid_weights)
    if total_weight == 0:
        return None
    valid_weights = [w / total_weight for w in valid_weights]

    df_portfolio['portfolio_return'] = df_portfolio.dot(valid_weights)

    # Portfolio VaR (95%)
    var_95 = -df_portfolio['portfolio_return'].quantile(0.05)

    # Portfolio Beta vs SPY
    # We need to join with SPY again
    df_spy = get_data('SPY')
    # df_spy has 'return' column. We join it with df_portfolio which has 'portfolio_return'.
    # We use lsuffix and rsuffix to handle potential collisions if any, though here names are distinct.
    # However, join defaults to left join on index.
    joined = df_portfolio[['portfolio_return']].join(df_spy[['return']], rsuffix='_spy').dropna()
    
    # If 'return' in df_spy didn't collide with anything in df_portfolio[['portfolio_return']], 
    # it won't get the suffix. It will just be 'return'.
    # Let's explicitly rename before joining to be safe.
    df_spy = df_spy.rename(columns={'return': 'return_spy'})
    joined = df_portfolio[['portfolio_return']].join(df_spy[['return_spy']]).dropna()
    
    if joined.empty:
        beta = None
    else:
        cov = np.cov(joined['portfolio_return'], joined['return_spy'])[0][1]
        var_spy = np.var(joined['return_spy'])
        beta = cov / var_spy if var_spy != 0 else None

    return {
        'VaR_95': var_95,
        'Beta': beta,
        'Returns': df_portfolio['portfolio_return']
    }


if __name__ == "__main__":
    # Test
    print(f"VaR for AAPL: {calculate_var('AAPL')}")
    print(f"Beta for AAPL: {calculate_beta('AAPL')}")
    
    # Test Portfolio
    port_res = calculate_portfolio_risk(['AAPL', 'MSFT'], [0.5, 0.5])
    if port_res:
        print(f"Portfolio VaR: {port_res['VaR_95']}")
        print(f"Portfolio Beta: {port_res['Beta']}")

def forecast_price(ticker, days=30):
    """
    Forecast future prices using Prophet.
    Returns DataFrame with ds, yhat, yhat_lower, yhat_upper.
    """
    from prophet import Prophet
    
    df = get_data(ticker).reset_index()
    # Prophet requires columns 'ds' and 'y'
    df_prophet = df[['date', 'close_price']].rename(columns={'date': 'ds', 'close_price': 'y'})
    
    # Remove timezone if present
    if df_prophet['ds'].dt.tz is not None:
        df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)

    m = Prophet(daily_seasonality=True)
    m.fit(df_prophet)
    
    future = m.make_future_dataframe(periods=days)
    forecast = m.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

