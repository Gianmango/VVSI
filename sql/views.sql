-- v_geom_mean_10
CREATE OR REPLACE VIEW v_geom_mean_10 AS
SELECT
    symbol,
    date,
    open_price,
    high,
    low,
    close_price,
    adj_close,
    volume,
    EXP(AVG(LN(close_price)) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 9 PRECEDING AND CURRENT ROW)) AS geom_mean_10
FROM prices;

-- v_geom_mean_50
CREATE OR REPLACE VIEW v_geom_mean_50 AS
SELECT
    symbol,
    date,
    open_price,
    high,
    low,
    close_price,
    adj_close,
    volume,
    EXP(AVG(LN(close_price)) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)) AS geom_mean_50
FROM prices;

-- v_geom_mean_100
CREATE OR REPLACE VIEW v_geom_mean_100 AS
SELECT
    symbol,
    date,
    open_price,
    high,
    low,
    close_price,
    adj_close,
    volume,
    EXP(AVG(LN(close_price)) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 99 PRECEDING AND CURRENT ROW)) AS geom_mean_100
FROM prices;

-- v_geom_mean_200
CREATE OR REPLACE VIEW v_geom_mean_200 AS
SELECT
    symbol,
    date,
    open_price,
    high,
    low,
    close_price,
    adj_close,
    volume,
    EXP(AVG(LN(close_price)) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW)) AS geom_mean_200
FROM prices;
