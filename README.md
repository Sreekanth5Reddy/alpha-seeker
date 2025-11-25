# 📈 Alpha-Seeker Market Dashboard

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.51-FF4B4B)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57)
![License](https://img.shields.io/badge/License-MIT-green)

**Alpha-Seeker** is a local financial dashboard designed to provide insights into stock market performance and risk metrics. It ingests daily stock data and economic indicators to visualize price history, calculate risk metrics like Beta and VaR, and analyze market correlations.

---

## 🚀 Features

- **📊 Interactive Dashboard**: Built with Streamlit and Plotly for dynamic visualizations.
- **🔄 Automated ETL Pipeline**: Fetches 5 years of daily data for major tickers (`AAPL`, `MSFT`, `GOOGL`, `JPM`, `SPY`).
- **📉 Risk Analytics**:
  - **Beta**: Measures stock volatility relative to the S&P 500 (SPY).
  - **VaR (Value at Risk)**: Calculates 95% Historical VaR to estimate potential losses.
- **🏦 Economic Insights**: Correlates daily stock returns with 10-Year Treasury Rates (fetched from FRED).
- **💾 Local Storage**: Efficiently stores cleaned and normalized data in a local SQLite database.

## 🛠️ Tech Stack

- **Language**: Python
- **Frontend**: Streamlit, Plotly
- **Database**: SQLite, SQLAlchemy
- **Data Sources**: `yfinance` (Yahoo Finance), `pandas_datareader` (FRED)

## 📂 Project Structure

```text
alpha-seeker/
├── app.py              # 📱 Main Streamlit Dashboard application
├── etl_pipeline.py     # 🔄 ETL Script (Extract, Transform, Load)
├── analytics.py        # 🧮 Core logic for financial calculations (VaR, Beta)
├── schema.sql          # 🗄️ Database Schema definitions
├── init_db.py          # 🛠️ Database initialization utility
├── verify_etl.py       # ✅ Script to verify data integrity
├── requirements.txt    # 📦 Python dependencies
└── README.md           # 📄 Project Documentation
```

## ⚡ Getting Started

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/alpha-seeker.git
    cd alpha-seeker
    ```

2.  **Create a Virtual Environment**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

### Usage

1.  **Initialize the Database**
    Set up the SQLite database and tables.

    ```bash
    python init_db.py
    ```

2.  **Run the ETL Pipeline**
    Fetch the latest stock and economic data.

    ```bash
    python etl_pipeline.py
    ```

    _Note: The pipeline includes retry logic and forward-fills missing data._

3.  **Launch the Dashboard**
    Start the Streamlit app.
    ```bash
    streamlit run app.py
    ```
    Open your browser to `http://localhost:8501`.

## 📸 Screenshots

_(Add screenshots of your dashboard here)_

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
