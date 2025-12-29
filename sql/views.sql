-- v_symbols
CREATE OR REPLACE VIEW v_symbols AS
SELECT symbol, name, sector, industry, country
FROM symbols;

-- v_prices
CREATE OR REPLACE VIEW v_prices AS
SELECT symbol, date, open, high, low, adj_close AS price, volume
FROM prices
ORDER BY symbol, date;

-- v_geom_mean_30
CREATE OR REPLACE VIEW v_geom_mean_30 AS
SELECT
  symbol,
  date,
  EXP(
    AVG(LN(adj_close)) OVER (
      PARTITION BY symbol
      ORDER BY date
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    )
  ) AS geom_mean_30,
  adj_close AS price,
  volume
FROM prices;

-- v_buy_signal
CREATE OR REPLACE VIEW v_buy_signal AS
SELECT
  symbol,
  date,
  price,
  geom_mean_30,
  CASE
    WHEN price < geom_mean_30 * 0.98 THEN 1
    ELSE 0
  END AS buy_signal
FROM v_geom_mean_30;

-- v_sell_candidate
CREATE OR REPLACE VIEW v_sell_candidate AS
SELECT symbol, date, price, geom_mean_30
FROM v_geom_mean_30
WHERE price > geom_mean_30 * 1.05;
