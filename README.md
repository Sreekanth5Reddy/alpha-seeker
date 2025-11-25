# Alpha-Seeker Market Dashboard

**Role:** Senior Full-Stack Engineer and Data Architect Project

A local financial dashboard built with Python, SQLite, and Streamlit. It ingests daily stock data and economic indicators to visualize price history and calculate risk metrics like Beta and VaR.

## Features

- **Data Pipeline:** Fetches 5 years of daily data for AAPL, MSFT, GOOGL, JPM, and SPY using `yfinance`.
- **Economic Data:** Fetches 10-Year Treasury Rates from FRED (via `pandas_datareader`).
- **Storage:** Stores cleaned and normalized data in a local SQLite database (`market.db`).
- **Dashboard:** Interactive Streamlit app with:
  - Stock Price Charts (Plotly)
  - Risk Metrics: Beta (vs SPY) and 95% Historical VaR
  - Scatter Plot: Daily Returns vs 10Y Treasury Yields

## Setup & Installation

1.  **Prerequisites:** Python 3.8+
2.  **Clone/Navigate** to the project directory.
3.  **Initialize Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

## Database Setup

Initialize the SQLite database and schema:

```bash
python init_db.py
```

## Running the ETL Pipeline

Fetch and load the latest data:

```bash
python etl_pipeline.py
```

_Note: The pipeline includes retry logic for API calls._

## Launching the Dashboard

Start the Streamlit app:

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`.

## Project Structure

- `etl_pipeline.py`: Main script for data extraction, transformation, and loading.
- `analytics.py`: Logic for calculating Beta and VaR.
- `app.py`: Streamlit frontend application.
- `schema.sql`: Database schema definitions.
- `init_db.py`: Utility to create the database tables.
- `requirements.txt`: Python dependencies.
