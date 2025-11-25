-- Drop tables if they exist
DROP TABLE IF EXISTS fact_economic;
DROP TABLE IF EXISTS fact_price_daily;
DROP TABLE IF EXISTS dim_stock;

-- Create Dimension Table: Stock
CREATE TABLE dim_stock (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255),
    sector VARCHAR(100)
);

-- Create Fact Table: Daily Price
CREATE TABLE fact_price_daily (
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    close_price DECIMAL(15, 4),
    volume BIGINT,
    PRIMARY KEY (date, ticker),
    FOREIGN KEY (ticker) REFERENCES dim_stock(ticker)
);

-- Create Fact Table: Economic Indicators
CREATE TABLE fact_economic (
    date DATE PRIMARY KEY,
    interest_rate_10y DECIMAL(10, 4),
    inflation_cpi DECIMAL(10, 4)
);
