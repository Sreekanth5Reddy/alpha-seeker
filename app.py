import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlalchemy
from analytics import calculate_var, calculate_beta, calculate_rsi, calculate_sma, calculate_portfolio_risk, forecast_price
import datetime

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
    engine = sqlalchemy.create_engine(DATABASE_URL)
    stock_query = f"SELECT date, close_price FROM fact_price_daily WHERE ticker = '{ticker}' ORDER BY date ASC"
    df_stock = pd.read_sql(stock_query, engine)
    df_stock['date'] = pd.to_datetime(df_stock['date'])
    df_stock['return'] = df_stock['close_price'].pct_change()
    
    eco_query = "SELECT date, interest_rate_10y FROM fact_economic ORDER BY date ASC"
    df_eco = pd.read_sql(eco_query, engine)
    df_eco['date'] = pd.to_datetime(df_eco['date'])
    
    df_merged = pd.merge(df_stock, df_eco, on='date', how='inner').dropna()
    return df_merged

@st.cache_data
def get_sector_performance():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    query = """
        SELECT s.sector, p.date, p.close_price
        FROM fact_price_daily p
        JOIN dim_stock s ON p.ticker = s.ticker
        WHERE p.date >= date('now', '-30 days')
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate returns
    df['return'] = df.groupby('sector')['close_price'].pct_change()
    
    # Average daily return by sector
    sector_perf = df.groupby('sector')['return'].mean().reset_index()
    return sector_perf

# Sidebar
st.sidebar.title("Alpha-Seeker")
st.sidebar.markdown("---")
st.sidebar.info("Navigate using the tabs below.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Stock Analysis", "💼 Portfolio Builder", "🤖 AI Forecast", "💾 Data Management"])

# --- TAB 1: STOCK ANALYSIS ---
with tab1:
    tickers = get_tickers()
    selected_ticker = st.selectbox("Select Ticker", tickers)
    
    if selected_ticker:
        # Date Range Slider
        df_history = get_stock_history(selected_ticker)
        if not df_history.empty:
            min_date = df_history['date'].min().date()
            max_date = df_history['date'].max().date()
            
            col_date1, col_date2 = st.columns(2)
            start_date = col_date1.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
            end_date = col_date2.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
            
            # Filter data
            mask = (df_history['date'].dt.date >= start_date) & (df_history['date'].dt.date <= end_date)
            df_filtered = df_history.loc[mask]
            
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                beta = calculate_beta(selected_ticker)
                st.metric("Beta (vs SPY)", f"{beta:.2f}" if beta else "N/A")
            with col2:
                var_95 = calculate_var(selected_ticker)
                st.metric("95% Historical VaR", f"{var_95:.2%}" if var_95 else "N/A")
            
            # Chart with Tech Indicators
            st.subheader("Price History & Technicals")
            tech_cols = st.multiselect("Add Indicators", ["SMA 50", "SMA 200", "RSI"], default=[])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['close_price'], mode='lines', name='Close Price'))
            
            if "SMA 50" in tech_cols:
                sma50 = calculate_sma(df_filtered['close_price'], 50)
                fig.add_trace(go.Scatter(x=df_filtered['date'], y=sma50, mode='lines', name='SMA 50', line=dict(dash='dash')))
            
            if "SMA 200" in tech_cols:
                sma200 = calculate_sma(df_filtered['close_price'], 200)
                fig.add_trace(go.Scatter(x=df_filtered['date'], y=sma200, mode='lines', name='SMA 200', line=dict(dash='dot')))
                
            st.plotly_chart(fig, use_container_width=True)
            
            if "RSI" in tech_cols:
                rsi = calculate_rsi(df_filtered['close_price'])
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df_filtered['date'], y=rsi, mode='lines', name='RSI', line=dict(color='purple')))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                fig_rsi.update_layout(title="Relative Strength Index (RSI)", yaxis_range=[0, 100], height=300)
                st.plotly_chart(fig_rsi, use_container_width=True)

            # Scatter Plot
            st.subheader("Daily Returns vs 10Y Treasury Yield")
            df_scatter = get_market_data_for_scatter(selected_ticker)
            if not df_scatter.empty:
                fig_scatter = px.scatter(
                    df_scatter, 
                    x='interest_rate_10y', 
                    y='return', 
                    labels={'interest_rate_10y': '10Y Treasury Yield (%)', 'return': 'Daily Return'}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Download Button
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name=f'{selected_ticker}_data.csv',
                mime='text/csv',
            )

    # Sector Heatmap
    st.markdown("---")
    st.subheader("Sector Performance (Last 30 Days)")
    try:
        df_sector = get_sector_performance()
        if not df_sector.empty:
            fig_sector = px.bar(df_sector, x='sector', y='return', color='return', color_continuous_scale='RdYlGn', title="Avg Daily Return by Sector")
            st.plotly_chart(fig_sector, use_container_width=True)
    except Exception as e:
        st.write("Sector data unavailable.")

# --- TAB 2: PORTFOLIO BUILDER ---
with tab2:
    st.header("Portfolio Simulator")
    st.write("Construct a portfolio to see combined risk metrics.")
    
    all_tickers = get_tickers()
    selected_portfolio_tickers = st.multiselect("Select Assets", all_tickers, default=all_tickers[:2])
    
    if selected_portfolio_tickers:
        weights = []
        cols = st.columns(len(selected_portfolio_tickers))
        for i, ticker in enumerate(selected_portfolio_tickers):
            w = cols[i].number_input(f"Weight % for {ticker}", min_value=0.0, max_value=100.0, value=100.0/len(selected_portfolio_tickers))
            weights.append(w)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            norm_weights = [w/total_weight for w in weights]
            
            if st.button("Calculate Portfolio Risk"):
                with st.spinner("Calculating..."):
                    res = calculate_portfolio_risk(selected_portfolio_tickers, norm_weights)
                    if res:
                        p_col1, p_col2 = st.columns(2)
                        p_col1.metric("Portfolio Beta", f"{res['Beta']:.2f}" if res['Beta'] else "N/A")
                        p_col2.metric("Portfolio 95% VaR", f"{res['VaR_95']:.2%}" if res['VaR_95'] else "N/A")
                        
                        # Plot Cumulative Returns
                        cum_returns = (1 + res['Returns']).cumprod()
                        st.line_chart(cum_returns)
                        st.caption("Cumulative Portfolio Returns (Indexed)")
                    else:
                        st.error("Could not calculate portfolio metrics. Ensure data exists for all tickers.")
        else:
            st.warning("Total weight must be greater than 0.")

# --- TAB 3: AI FORECAST ---
with tab3:
    st.header("🤖 AI Price Prediction")
    st.write("Forecast future stock prices using **Facebook Prophet**.")
    
    ai_ticker = st.selectbox("Select Asset for Forecast", get_tickers(), key="ai_ticker")
    days = st.slider("Forecast Horizon (Days)", 7, 365, 30)
    
    if st.button("Generate Forecast"):
        with st.spinner(f"Training Prophet model for {ai_ticker}..."):
            try:
                forecast = forecast_price(ai_ticker, days)
                
                # Plot
                fig_ai = go.Figure()
                
                # Historical Data (Last 180 days for context)
                df_hist = get_stock_history(ai_ticker)
                df_hist_recent = df_hist[df_hist['date'] > (pd.Timestamp.now() - pd.Timedelta(days=180))]
                fig_ai.add_trace(go.Scatter(x=df_hist_recent['date'], y=df_hist_recent['close_price'], mode='lines', name='Historical'))
                
                # Forecast
                fig_ai.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast', line=dict(color='orange')))
                
                # Confidence Interval
                fig_ai.add_trace(go.Scatter(
                    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                    fill='toself',
                    fillcolor='rgba(255, 165, 0, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Confidence Interval'
                ))
                
                fig_ai.update_layout(title=f"{ai_ticker} Price Forecast ({days} Days)", xaxis_title="Date", yaxis_title="Price")
                st.plotly_chart(fig_ai, use_container_width=True)
                
                st.success("Forecast generated successfully!")
            except Exception as e:
                st.error(f"Error generating forecast: {e}")

# --- TAB 4: DATA MANAGEMENT ---
with tab4:
    st.header("Data Management")
    
    if st.button("🔄 Refresh Data (Run ETL)"):
        with st.spinner("Running ETL Pipeline... This may take a minute."):
            try:
                import subprocess
                result = subprocess.run(["python", "etl_pipeline.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("Data updated successfully!")
                    st.cache_data.clear() # Clear cache to show new data
                else:
                    st.error(f"ETL Failed:\n{result.stderr}")
            except Exception as e:
                st.error(f"Error running script: {e}")

    st.subheader("Raw Data Preview")
    engine = sqlalchemy.create_engine(DATABASE_URL)
    try:
        df_preview = pd.read_sql("SELECT * FROM fact_price_daily ORDER BY date DESC LIMIT 100", engine)
        st.dataframe(df_preview)
    except:
        st.write("No data found.")
