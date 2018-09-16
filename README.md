# Web Stock Data Fetcher

Scraping stock data

### Prerequisites

1. Ubuntu 16.04 (not necessarily exactly Ubuntu 16.04, but I used this for development)
2. Chrome Browser installed, at time of writing, its version is Version 69.0.3497.92 (Official Build) (64-bit)
3. make chrome driver available in PATH, url to download https://sites.google.com/a/chromium.org/chromedriver/downloads
    ```bash
    $ which chromedriver
    /home/boweiliu/.local/bin/chromedriver
    ```
4. python 3.5 and above available


### Installing

1. git clone this project to favorable path
2. change directory to project
3. python3 -m venv ./venv (create venv in project root directory)
4. source ./venv/bin/activate (activate python virtual environment)         
5. pip3 install -r ./requirements.txt (install dependencies according requirements.txt)
6. add file `credentials` at project root, change following username and password to yours.
    ```properties
    username=your@email.com
    password=your_password
    ```
7. add directory `data` at project root


## Running

```bash
# make sure following command is executed at project root directory
python3 src/main/python/main.py example01
```
you should be able see data/record2.txt, possible content would be like 

```text
portfolio	symbol	vol_percent	date	type	price
Home Run Investor	SQ	NULL	7/11/17	buy	25.37
Home Run Investor	EPAY	NULL	2/2/18	buy	37.75
Home Run Investor	ZEN	NULL	3/16/18	buy	47.00
Home Run Investor	I	NULL	5/30/18	buy	16.14
Home Run Investor	EVBG	NULL	5/16/18	buy	43.27
Home Run Investor	SEND	NULL	8/9/18	buy	31.11
Home Run Investor	IMAX	NULL	6/27/18	buy	22.40
Home Run Investor	ALTR	NULL	6/13/18	buy	36.43
Home Run Investor	HSC	NULL	9/5/18	buy	28.38
Home Run Investor	HABT	NULL	8/15/18	buy	16.25
Home Run Investor	TRN	NULL	7/25/18	buy	36.78
Home Run Investor	TITN	NULL	9/12/18	buy	17.94
Income Investor	WASH	NULL	10/8/12	buy	23.23
Income Investor	LMT	NULL	2/10/14	buy	144.57

```


### And coding style tests

PEP8

```
Give an example
```

## Deployment

TODO

## Contributing

TODO

## Authors

* Bowei Liu

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
