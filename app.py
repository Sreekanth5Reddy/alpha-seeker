import streamlit as st
import pandas as pd
import plotly.express as px
import sqlalchemy
from analytics import calculate_var, calculate_beta

# Configuration
DATABASE_URL = "sqlite:///market.db"
st.set_page_config(page_title="Alpha-Seeker Dashboard", layout="wide")


@st.cache_data
def get_tickers():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    query = "SELECT ticker FROM dim_stock WHERE ticker != 'SPY' ORDER BY ticker"
    df = pd.read_sql(query, engine)
    return df['ticker'].tolist()


@st.cache_data
def get_stock_history(ticker):
    engine = sqlalchemy.create_engine(DATABASE_URL)
    query = f"""
        SELECT date, close_price
        FROM fact_price_daily
        WHERE ticker = '{ticker}'
        ORDER BY date ASC
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data
def get_market_data_for_scatter(ticker):
    """Fetch joined data of Stock Returns vs 10Y Treasury Yield."""
    engine = sqlalchemy.create_engine(DATABASE_URL)

    # Get Stock Data
    stock_query = f"""
        SELECT date, close_price
        FROM fact_price_daily
        WHERE ticker = '{ticker}'
        ORDER BY date ASC
    """
    df_stock = pd.read_sql(stock_query, engine)
    df_stock['date'] = pd.to_datetime(df_stock['date'])
    df_stock['return'] = df_stock['close_price'].pct_change()

    # Get Economic Data
    eco_query = "SELECT date, interest_rate_10y FROM fact_economic ORDER BY date ASC"
    df_eco = pd.read_sql(eco_query, engine)
    df_eco['date'] = pd.to_datetime(df_eco['date'])

    # Merge
    df_merged = pd.merge(df_stock, df_eco, on='date', how='inner').dropna()
    return df_merged


# Sidebar
st.sidebar.title("Alpha-Seeker")
tickers = get_tickers()
selected_ticker = st.sidebar.selectbox("Select Ticker", tickers)

if selected_ticker:
    st.title(f"{selected_ticker} Market Dashboard")

    # Metrics Row
    col1, col2 = st.columns(2)

    with col1:
        beta = calculate_beta(selected_ticker)
        st.metric("Beta (vs SPY)", f"{beta:.2f}" if beta else "N/A")

    with col2:
        var_95 = calculate_var(selected_ticker)
        st.metric("95% Historical VaR", f"{var_95:.2%}" if var_95 else "N/A")

    # Charts
    st.subheader("Price History")
    df_history = get_stock_history(selected_ticker)
    if not df_history.empty:
        fig_price = px.line(
            df_history,
            x='date',
            y='close_price',
            title=f"{selected_ticker} Daily Close Price")
        st.plotly_chart(fig_price, use_container_width=True)
    else:
        st.write("No price data available.")

    st.subheader("Daily Returns vs 10Y Treasury Yield")
    df_scatter = get_market_data_for_scatter(selected_ticker)
    if not df_scatter.empty:
        fig_scatter = px.scatter(
            df_scatter,
            x='interest_rate_10y',
            y='return',
            title=f"Daily Returns vs 10Y Yield",
            labels={
                'interest_rate_10y': '10Y Treasury Yield (%)',
                'return': 'Daily Return'})
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.write("No data for scatter plot.")
