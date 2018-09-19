CREATE DATABASE IF NOT EXISTS zacks;
USE zacks;
DROP TABLE IF EXISTS portfolio_scan;

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


DROP TABLE IF EXISTS portfolio_operations;
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


-- ALTER TABLE portfolio_operations MODIFY price FLOAT NULL;