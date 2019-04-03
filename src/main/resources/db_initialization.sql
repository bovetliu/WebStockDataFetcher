-- please not that database name can be programmatically replaced to any other name in main.py
CREATE DATABASE IF NOT EXISTS zacks;
USE zacks;
-- DROP TABLE IF EXISTS portfolio_scan;

CREATE TABLE IF NOT EXISTS portfolio_scan (
    id BIGINT NOT NULL AUTO_INCREMENT,
    portfolio VARCHAR(50) NOT NULL,           # Value Investor
    symbol VARCHAR(10) NOT NULL,              # NVDA
    vol_percent FLOAT NULL,                   # NULL or 0.1123
    date_added DATE NOT NULL,                 # 2018-04-23
    type VARCHAR(15) NOT NULL,                # long, short, long_close, short_close
    price FLOAT NOT NULL,                     # 35.76
    record_date DATE NOT NULL,                # 2018-08-24
    uniqueness VARCHAR(128) NOT NULL UNIQUE,  # generate by hashing function
    PRIMARY KEY ( id )
)
ENGINE=InnoDB,
CHARACTER SET utf8;


-- DROP TABLE IF EXISTS portfolio_operations;
-- only store operations made to portfolios, additions and deletions
CREATE TABLE IF NOT EXISTS portfolio_operations (
    id BIGINT NOT NULL AUTO_INCREMENT,
    portfolio VARCHAR(50) NOT NULL,           # Value Investor
    symbol VARCHAR(10) NOT NULL,              # NVDA
    vol_percent FLOAT NULL,                   # NULL or 0.1123
    date_added DATE NOT NULL,                 # 2018-04-23
    type VARCHAR(15) NOT NULL,                # long_init, short_init, long_close, short_close
    price FLOAT NULL,                         # 35.76 or NULL
    record_date DATE NOT NULL,                # 2018-08-24
    uniqueness VARCHAR(128) NOT NULL UNIQUE,  # generate by hashing function
    price_at_close FLOAT NULL,
    PRIMARY KEY ( id )
)
ENGINE=InnoDB,
CHARACTER SET utf8;


-- store data scraped from yahoo finance statistics
CREATE TABLE IF NOT EXISTS yahoo_fin_statistics (
  -- Valuation Measures
  id BIGINT NOT NULL AUTO_INCREMENT,
  market_cap DOUBLE NULL,
  enterprise_value DOUBLE NULL,
  trailing_p_e FLOAT NULL,
  forward_p_e FLOAT NULL,
  peg_ratio FLOAT NULL,
  price_sales FLOAT NULL,
  price_book FLOAT NULL,
  enterprise_value_div_revenue FLOAT NULL,
  enterprise_value_div_ebitda FLOAT NULL,

  -- Financial Highlights
  fiscal_year_ends DATE NULL,
  most_recent_quarter DATE NULL,

  -- Profitability
  profit_margin FLOAT NULL,
  operating_margin FLOAT NULL,

  -- Management Effectiveness
  return_on_assets FLOAT NULL,
  return_on_equity FLOAT NULL,

  -- Income Statement
  revenue DOUBLE NULL,
  revenue_per_share DOUBLE NULL,
  quarterly_revenue_growth_yoy FLOAT NULL,
  quarterly_earnings_growth_yoy FLOAT NULL,
  gross_profit DOUBLE NULL,
  ebitda DOUBLE NULL,

  -- Balance Sheet
  total_cash DOUBLE NULL,
  total_cash_per_share FLOAT NULL,
  total_debt DOUBLE NULL,
  total_debt_div_equity FLOAT NULL,
  current_ratio DOUBLE NULL,
  book_value_per_share DOUBLE NULL,

  -- Cash Flow Statement
  operating_cash_flow DOUBLE NULL,
  levered_free_cash_flow DOUBLE NULL,

  -- Share Statistics
  avg_vol_3_month DOUBLE NULL,
  avg_vol_10_day DOUBLE NULL,
  shares_outstanding DOUBLE NULL,
  float_shares DOUBLE NULL,
  percentage_held_by_insiders FLOAT NULL,
  percentage_held_by_institutions FLOAT NULL,
  short_stat_record_date DATE NULL,
  shares_short DOUBLE NULL,
  short_ratio FLOAT NULL,
  short_percentage_of_float FLOAT NULL,
  short_percentage_of_shares_outstanding FLOAT NULL,

  -- dividents & splits
  forward_annual_dividend_rate FLOAT NULL,
  forward_annual_dividend_yield FLOAT NULL,
  trailing_annual_dividend_rate FLOAT NULL,
  trailing_annual_dividend_yield FLOAT NULL,
  payout_ratio FLOAT NULL,
  divident_date DATE NULL,
  ex_dividend_date DATE NULL,

  -- Record Date and Symbol
  record_date DATE NOT NULL,
  symbol VARCHAR(10) NOT NULL,
  PRIMARY KEY ( id )
)
ENGINE=InnoDB,
CHARACTER SET utf8;
