CREATE DATABASE IF NOT EXISTS zacks;
USE zacks;
-- DROP TABLE IF EXISTS portfolio_scan;

CREATE TABLE IF NOT EXISTS portfolio_scan (
    id BIGINT NOT NULL AUTO_INCREMENT,
    portfolio VARCHAR(50) NOT NULL,       # Value Investor
    symbol VARCHAR(10) NOT NULL,          # NVDA
    vol_percent FLOAT NULL,               # NULL or 0.1123
    date_added DATE NOT NULL,             # 2018-04-23
    type VARCHAR(10) NOT NULL,            # long, short, long_close, short_close
    price FLOAT NOT NULL,                 # 35.76
    record_date DATE NOT NULL,            # 2018-08-24
    uniqueness VARCHAR(128) NOT NULL UNIQUE,  # generate by hashing function
    PRIMARY KEY ( id )
)
ENGINE=InnoDB,
CHARACTER SET utf8;


-- DROP TABLE IF EXISTS portfolio_operations;
-- only store operations made to portfolios, additions and deletions
CREATE TABLE IF NOT EXISTS portfolio_operations (
    id BIGINT NOT NULL AUTO_INCREMENT,
    portfolio VARCHAR(50) NOT NULL,       # Value Investor
    symbol VARCHAR(10) NOT NULL,          # NVDA
    vol_percent FLOAT NULL,               # NULL or 0.1123
    date_added DATE NOT NULL,             # 2018-04-23
    type VARCHAR(10) NOT NULL,            # long_init, short_init, long_close, short_close
    price FLOAT NULL,                     # 35.76 or NULL
    record_date DATE NOT NULL,            # 2018-08-24
    uniqueness VARCHAR(128) NOT NULL UNIQUE,  # generate by hashing function
    PRIMARY KEY ( id )
)
ENGINE=InnoDB,
CHARACTER SET utf8;


--INSERT INTO portfolio_operations (portfolio, symbol, vol_percent, date_added, type,price, record_date, uniqueness)
--  VALUES ('Momentum Trader', 'CSBR', 0.1275, '2018-09-19', 'long_init', NULL, '2018-09-19', 'asdfasf');

-- look for duplications
SELECT t1.id, t1.portfolio, t1.symbol, t1.vol_percent, t1.date_added, t1.type, t1.price, t1.record_date FROM portfolio_operations t1
  INNER JOIN portfolio_operations t2
WHERE t1.id < t2.id
  AND t1.portfolio = t2.portfolio
  AND t1.symbol = t2.symbol
  AND t1.date_added = t2.date_added
  AND t1.type = t2.type
  AND t1.record_date = t2.record_date;


SELECT t1.id, t1.portfolio, t1.symbol, t1.vol_percent, t1.date_added, t1.type, t1.price, t1.record_date FROM portfolio_scan t1
  INNER JOIN portfolio_scan t2
WHERE t1.id < t2.id
  AND t1.portfolio = t2.portfolio
  AND t1.symbol = t2.symbol
  AND t1.date_added = t2.date_added
  AND t1.type = t2.type
  AND t1.record_date = t2.record_date;

-- deduplication sql
DELETE t1  FROM portfolio_operations t1
  INNER JOIN portfolio_operations t2
WHERE t1.id < t2.id
  AND t1.portfolio = t2.portfolio
  AND t1.symbol = t2.symbol
  AND t1.date_added = t2.date_added
  AND t1.type = t2.type
  AND t1.record_date = t2.record_date;


DELETE t1 FROM portfolio_scan t1
  INNER JOIN portfolio_scan t2
WHERE t1.id < t2.id
  AND t1.portfolio = t2.portfolio
  AND t1.symbol = t2.symbol
  AND t1.date_added = t2.date_added
  AND t1.type = t2.type
  AND t1.record_date = t2.record_date;

DELETE t1 FROM portfolio_operations t1
INNER JOIN portfolio_operations t2
    WHERE t1.portfolio = t2.portfolio
      AND t1.symbol = t2.symbol
      AND t1.date_added = t2.date_added
      AND t1.type != t2.type
      AND t1.record_date = t2.record_date;

-- ALTER TABLE portfolio_operations MODIFY price FLOAT NULL;