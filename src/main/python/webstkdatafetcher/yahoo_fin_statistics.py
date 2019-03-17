import os
from typing import List, Dict

import logging
import datetime
from selenium import webdriver
from datetime import date, datetime
from collections import OrderedDict
import operator

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup


from webstkdatafetcher import utility, constants, logic
from webstkdatafetcher.data_connection import mysql_related


def start_scraping_yahoo_fin_statistics(output: str = None,
                                        clear_previous_content: bool = False,
                                        headless: bool = False,
                                        db_config_dict: dict = None,
                                        stock_collection: str = 'sp500'):
    """

    :param output: whether write content to an output
    :param clear_previous_content: whether clear previous content in file specified in output, if any
    :param headless:
    :param db_config_dict:
    :param stock_collection: sp500, or nasdaq100, or dowjones
    :return:
    """
    chrome_option = webdriver.ChromeOptions()
    # invokes headless setter
    chrome_option.headless = headless
    chrome_option.add_argument("--window-size=1920x1080")
    output_file = None
    mysql_helper = mysql_related.MySqlHelper(reuse_connection=True, db_config_dict=db_config_dict)
    should_commit = False
    mysql_table = "yahoo_fin_statistics"
    try:
        if output:
            output_file = open(output, 'w+')
        # clear content of opened file
        if clear_previous_content and output_file is not None:
            output_file.seek(0)
            output_file.truncate()

        driver = webdriver.Chrome(options=chrome_option)
        driver.maximize_window()

        stocks = logic.get_slickcharts_stock_constituents(driver, stock_collection)
        stocks = [stock[2] for stock in stocks[1:401]]
        # stocks = ["LIN"]
        print(stocks)
        for i in range(len(stocks)):
            stock = stocks[i]
            if "." in stock:
                stock = stock.replace(".", "-")
            url = "https://finance.yahoo.com/quote/{0}/key-statistics?p={0}".format(stock)
            logging.info("get statistics url {}".format(url))
            driver.get(url)
            statistics_html = driver.find_element_by_id("Col1-0-KeyStatistics-Proxy").get_attribute("outerHTML")
            extracted_data = extract_info_from_stat_html(statistics_html)

            quote_market_notice = \
                driver.find_element_by_id("quote-market-notice").find_element_by_tag_name("span").text.strip()
            effective_time_str = quote_market_notice.strip("At close: ").strip("EDT").strip()
            # sample effective_time: March 15 4:00PM EDT
            effective_date_time = datetime.strptime(effective_time_str, "%B %d %I:%M%p").replace(datetime.now().year)
            print("effective_date_time:{}".format(effective_date_time.strftime("%Y-%m-%dT%H:%M:%S")))

            db_ready_extracted_data = convert_to_db_ready(extracted_data, stock, effective_date_time.date())
            mysql_helper.delete_from_table(mysql_table, col_val_dict={
                "symbol": stock,
                "record_date": effective_date_time.date().strftime("%Y-%m-%d")
            })
            mysql_helper.insert_one_record(mysql_table, col_val_dict=db_ready_extracted_data)
        should_commit = True
    finally:
        if output_file is not None:
            output_file.close()
        mysql_helper.set_reuse_connection(False, should_commit)


def select_stock_symbol(collection_name: str='BA'):
    """
    return a list of stock symbols, something like [""]
    :param collection_name: single symbol, like BA, or can be index name like "sp500",
        "nasdaq100"
    :return:
    """
    if collection_name in ["sp500", "nasdaq100"]:
        raise Exception("currently does not support sp500, nasdaq100")

    selection = []
    try:
        with open(os.path.join(constants.main_resources, collection_name), 'r') as selection_file:
            for line in selection_file:
                selection.append(line.strip())
            return selection
    except FileNotFoundError:
        return [collection_name]


def extract_info_from_stat_html(statistics_html: str) -> OrderedDict:
    """
    parse and extract key-value information from statistics html.
    :param statistics_html: html string of yahoo finance company stock statistics
    :return: dictionary storing key-value information, like Market Cap (intraday): 214.12B, Trailing P/E: 21.23
    """
    if not isinstance(statistics_html, str) or len(statistics_html) == 0:
        raise ValueError("statistics_html must be non-empty string")

    tbr = OrderedDict([])
    soup = BeautifulSoup(statistics_html, 'html.parser')
    tbodys = soup.find_all("tbody")
    value_str_not_parsed = []
    for tbody in tbodys:
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            # logging.info(tds[0].span.string)
            # logging.info(tds[1].string)
            value_str = tds[1].string.strip()
            value = None
            field_name = tds[0].span.string.strip()
            try:
                if "N/A" in value_str:
                    value = None
                elif value_str.endswith("B"):
                    value = float(value_str.strip("B")) * 1000000000
                elif value_str.endswith("M"):
                    value = float(value_str.strip("M")) * 1000000
                elif value_str.endswith("k"):
                    value = float(value_str.strip("k")) * 1000
                elif utility.is_number_tryexcept(value_str):
                    value = float(value_str)
                elif value_str.endswith("%"):

                    try:
                        value = round(float(value_str.replace(",", "").strip("%")) * 0.01, 4)
                    except ValueError as ve:
                        logging.error("ValueError caught : %s", str(ve))
                        if "∞" in value_str:
                            value = None
                        else:
                            raise ve
                elif "," in value_str and "." not in value_str:
                    try:
                        value = datetime.strptime(value_str, "%b %d, %Y").date().strftime("%Y-%m-%d")
                    except ValueError as err:
                        logging.error(err)
                        pass
                elif "," in value_str and "." in value_str:
                    value = float(value_str.replace(",", ""))
                elif "Last Split Factor" in field_name and "/" in value_str:
                    value = value_str
                else:
                    value_str_not_parsed.append(value_str)
                if value_str in ["N/A"]:
                    tbr[field_name] = None
                else:
                    tbr[field_name] = value if value is not None else value_str
            except ValueError as ve:
                logging.error("field_name: {}, value_str: {}", field_name, value_str)
                logging.error(ve)
                raise ve

    logging.info("value_str_not_parsed: {}".format(value_str_not_parsed))
    return tbr


def convert_to_db_ready(scraped_data: Dict, symbol: str, record_date):
    short_data = {}
    interested_fields = [
        "Shares Short",
        "Short Ratio",
        "Short % of Float",
        "Short % of Shares Outstanding"
    ]
    short_stat_record_date = None
    for field_name in scraped_data.keys():
        for interested_field in interested_fields:
            if interested_field in field_name and "prior" not in field_name:
                short_data[interested_field] = scraped_data[field_name]
                if short_stat_record_date is None:
                    short_stat_record_date = field_name.strip(interested_field).strip()
                    if "(" not in short_stat_record_date:
                        short_stat_record_date = None
                        short_data["Short Stat Record Date"] = None
                    else:
                        short_stat_record_date = datetime.strptime(short_stat_record_date, "(%b %d, %Y)")
                        short_data["Short Stat Record Date"] = short_stat_record_date.strftime("%Y-%m-%d")
                break
    result = {
        # Valuation Measures
        "market_cap": scraped_data["Market Cap (intraday)"],
        "enterprise_value": scraped_data["Market Cap (intraday)"],
        "trailing_p_e": scraped_data["Trailing P/E"],
        "forward_p_e": scraped_data["Forward P/E"],
        "peg_ratio": scraped_data["PEG Ratio (5 yr expected)"],
        "price_sales": scraped_data["Price/Sales"],
        "price_book": scraped_data["Price/Book"],
        "enterprise_value_div_revenue": scraped_data["Enterprise Value/Revenue"],
        "enterprise_value_div_ebitda": scraped_data["Enterprise Value/EBITDA"],

        # Financial Highlights
        "fiscal_year_ends": scraped_data["Fiscal Year Ends"],
        "most_recent_quarter": scraped_data["Most Recent Quarter"],

        # Profitability
        "profit_margin": scraped_data["Profit Margin"],
        "operating_margin": scraped_data["Operating Margin"],

        # Management Effectiveness
        "return_on_assets": scraped_data["Return on Assets"],
        "return_on_equity": scraped_data["Return on Equity"],

        # Income Statement
        "revenue": scraped_data["Revenue"],
        "revenue_per_share": scraped_data["Revenue Per Share"],
        "quarterly_revenue_growth_yoy": scraped_data["Quarterly Revenue Growth"],
        "quarterly_earnings_growth_yoy": scraped_data["Quarterly Earnings Growth"],
        "gross_profit": scraped_data["Gross Profit"],
        "ebitda": scraped_data["EBITDA"],

        # Balance Sheet
        "total_cash": scraped_data["Total Cash"],
        "total_cash_per_share": scraped_data["Total Cash Per Share"],
        "total_debt": scraped_data["Total Debt"],
        "total_debt_div_equity": scraped_data["Total Debt/Equity"],
        "current_ratio": scraped_data["Current Ratio"],
        "book_value_per_share": scraped_data["Book Value Per Share"],

        # Cash Flow Statement
        "operating_cash_flow": scraped_data["Operating Cash Flow"],
        "levered_free_cash_flow": scraped_data["Levered Free Cash Flow"],

        # Share Statistics
        "avg_vol_3_month": scraped_data["Avg Vol (3 month)"],
        "avg_vol_10_day": scraped_data["Avg Vol (10 day)"],
        "shares_outstanding": scraped_data["Shares Outstanding"],
        "float_shares": scraped_data["Float"],
        "percentage_held_by_insiders": scraped_data["% Held by Insiders"],
        "percentage_held_by_institutions": scraped_data["% Held by Institutions"],
        "short_stat_record_date": short_data["Short Stat Record Date"],
        "shares_short": short_data["Shares Short"],
        "short_ratio": short_data["Short Ratio"],
        "short_percentage_of_float": short_data["Short % of Float"],
        "short_percentage_of_shares_outstanding": short_data["Short % of Shares Outstanding"],

        # Record Date
        "record_date": record_date.strftime("%Y-%m-%d") if isinstance(record_date, date) else record_date,
        "symbol": symbol
    }
    return result


def get_valuation_measures(stats: Dict[str, str]):
    pass
