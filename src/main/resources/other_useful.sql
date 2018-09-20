INSERT INTO portfolio_operations (portfolio, symbol, vol_percent, date_added, type,price, record_date, uniqueness)
  VALUES ('Momentum Trader', 'CSBR', 0.1275, '2018-09-19', 'long_init', NULL, '2018-09-19', 'asdfasf');

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