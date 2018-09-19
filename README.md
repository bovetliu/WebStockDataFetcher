# Web Stock Data Fetcher

Scraping stock data

### Prerequisites

1. Ubuntu 16.04 (not necessarily exactly Ubuntu 16.04, but I used this for development)
2. Chrome Browser installed, at time of writing, its version is Version 69.0.3497.92 (Official Build) (64-bit)
3. Make chrome driver available in PATH, url to download https://sites.google.com/a/chromium.org/chromedriver/downloads
    ```bash
    $ which chromedriver
    /home/boweiliu/.local/bin/chromedriver
    ```
4. Python 3.5 and above available, **IMPORTANT** venv module should be installed
5. Subscription to Zacks Ultimate 

### Installing

1. Git clone this project to favorable path
2. Change directory to project
3. Store zacks ultimate file `credentials` at project root, change following username and password to yours.
    ```properties
    username=your@email.com
    password=your_password
    ```
4. Add file `remotedb.properties` to `src/main/resources`. This file holds information about remote mysql
  database, like username, password, host and database (schema name). Its format would be similar with 
  `src/main/resources/database.properties`   
  This is needed to run `scrapezacks_to_remote`.

## Running

Make sure following commands executed at project root directory

* IF you want to scrape data and store to local (using database.properties)
    ```bash
    ./one_step_run.sh scrapezacks
    ```
* IF you want to srape data and store to remote mysql (using remotedb.properties)
    ```bash
    ./one_step_run.sh scrapezacks_to_remote
    ```

After a successful run, you should be able to see data like following in `portfolio_scan` and `portfolio_operations` 
table  

```SQL
SELECT portfolio, symbol, vol_percent, date_added, type, price, record_date FROM portfolio_scan;
```

```text
+-------------------+--------+-------------+------------+------+--------+-------------+
| portfolio         | symbol | vol_percent | date_added | type | price  | record_date |
+-------------------+--------+-------------+------------+------+--------+-------------+
| Home Run Investor | SQ     |        NULL | 2017-07-11 | long |  25.37 | 2018-09-19  |
| Home Run Investor | EPAY   |        NULL | 2018-02-02 | long |  37.75 | 2018-09-19  |
....

| Technology        | BE     |        NULL | 2018-08-23 | long |  28.37 | 2018-09-19  |
| Technology        | SATS   |        NULL | 2018-08-07 | long |  47.52 | 2018-09-19  |
| Technology        | VEEV   |        NULL | 2018-09-13 | long | 105.53 | 2018-09-19  |
| Technology        | DIOD   |        NULL | 2018-07-12 | long |  35.45 | 2018-09-19  |
| Technology        | DOCU   |        NULL | 2018-09-10 | long |  55.15 | 2018-09-19  |
| Large-Cap Trader  | CC     |      0.0168 | 2017-05-05 | long |  40.42 | 2018-09-19  |
| Large-Cap Trader  | CC     |      0.0174 | 2017-04-20 | long |  36.58 | 2018-09-19  |
| Large-Cap Trader  | CC     |      0.0363 | 2016-11-01 | long |  16.66 | 2018-09-19  |
| Large-Cap Trader  | MU     |      0.0321 | 2017-09-19 | long |   35.8 | 2018-09-19  |
| Large-Cap Trader  | MU     |      0.0579 | 2017-08-17 | long |  30.07 | 2018-09-19  |
....
| Black Box Trader  | DHI    |        NULL | 2018-09-17 | long |   42.8 | 2018-09-19  |
| Black Box Trader  | TSCO   |        NULL | 2018-09-04 | long |  90.46 | 2018-09-19  |
| Black Box Trader  | TJX    |        NULL | 2018-09-04 | long | 110.86 | 2018-09-19  |
+-------------------+--------+-------------+------------+------+--------+-------------+


+-------------------+--------+-------------+------------+------------+-------+-------------+
| portfolio         | symbol | vol_percent | date_added | type       | price | record_date |
+-------------------+--------+-------------+------------+------------+-------+-------------+
| Home Run Investor | ACXM   |        NULL | 2018-09-19 | long_init  |  NULL | 2018-09-19  |
| Momentum Trader   | CSBR   |      0.1344 | 2018-09-19 | long_init  |  NULL | 2018-09-19  |
| Insider Trader    | SGMS   |      0.0687 | 2018-08-15 | long_close | 29.68 | 2018-09-19  |
| Insider Trader    | SSP    |      0.0002 | 2018-09-19 | long_init  |  NULL | 2018-09-19  |
+-------------------+--------+-------------+------------+------------+-------+-------------+

```

### And coding style tests

PEP8

## Deployment

TODO

## Contributing

TODO

## Authors

* Bowei Liu

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
