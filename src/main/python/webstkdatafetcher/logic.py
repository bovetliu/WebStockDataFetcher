from typing import List, Callable
from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from datetime import date, datetime

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from webstkdatafetcher import constants
from webstkdatafetcher import utility
from webstkdatafetcher.data_connection import mysql_related

__internal_header_mapping = {
    "Company": "company",
    "Sym": "symbol",
    "%Val": "vol_percent",
    "+Date": "date",
    "$Add": "price",
    "$Last": "last_price",
    "%Chg": "change_percent",
    "Type": "type"   # only Counterstrike,  TAZR and shortlist have Type column
}


def __table_header_name_remap(header: str):
    if header in __internal_header_mapping:
        return __internal_header_mapping[header]
    else:
        return header.lower()


def __process_rows_of_table(
        driver, operation, trs, port_name: str, header_vs_col_idx,
        callback_on_record_line: Callable[[List], None] = None, *args, **kwarg):
    if not isinstance(driver, WebDriver):
        raise TypeError("driver can only be instance of WebDriver")
    if operation not in ["additions", "deletions", "scan"]:
        raise ValueError("accepted operation can only be \"additions\" or \"deletions\"")
    for tr in trs:
        if not isinstance(tr, WebElement):
            raise TypeError("trs can only be a list of WebElement")
    print("operation: {}, TODO".format(operation))
    symbol_temp = ''

    # click all "Details>>" of addition, deletion and Open Portfolio tables to load js
    for tr in trs:
        # td in one line
        for td in tr.find_elements_by_tag_name("td"):
            if "Detail" in td.text:
                td.click()
    for tr in trs:
        # td in one line
        tds = tr.find_elements_by_tag_name("td")
        if "No Current Signal" in tds[0].text:
            continue
        if tds[1].text:
            symbol_temp = tds[1].text
        if "Detail" in tds[3].text:
            continue
        # "portfolio name", "symbol", "vol_percent", "date", "type", "price"

        trade_type = __determine_trade_type(tds, header_vs_col_idx)
        if operation == 'deletions':
            trade_type = trade_type + '_close'  # close long or short position
        elif operation == 'additions':
            trade_type = trade_type + '_init'   # long_init short_init,  initialize long or short postion

        record_format = "{}\t{}\t{}\t{}\t{}\t{}\t{}"
        arguments = [port_name, symbol_temp,
                     round(float(tds[header_vs_col_idx['vol_percent']].text.strip('%')) / 100.0, 4)
                     if 'vol_percent' in header_vs_col_idx else 'NULL',
                     datetime.strptime(tds[header_vs_col_idx['date']].text, '%m/%d/%y').date(),
                     trade_type,
                     round(float(tds[header_vs_col_idx['price']].text), 2),
                     date.today()]
        one_record_line = record_format.format(*arguments)
        # TODO(Bowei): handle deletions and additions table
        print(one_record_line)
        if callback_on_record_line:
            callback_on_record_line(arguments, *args, **kwarg)


def selenium_chrome(output: str = None, clear_previous_content: bool = False):
    """

    :param output: output path
    :param clear_previous_content clear content if one file already exist at path specified in output
    """
    chrome_option = webdriver.ChromeOptions()
    # invokes headless setter
    chrome_option.headless = False
    chrome_option.add_argument("--window-size=1920x1080")
    driver = None
    output_file = None
    mysql_helper = mysql_related.MySqlHelper(reuse_connection=True)

    try:
        if output:
            output_file = open(output, 'w+')
        if clear_previous_content and output_file is not None:
            output_file.seek(0)
            output_file.truncate()

        driver = webdriver.Chrome(options=chrome_option)
        driver.maximize_window()
        driver.get("https://www.zacks.com/ultimate/")
        credentials = utility.get_propdict_file(constants.credentials_path)
        input_username = driver.find_element_by_css_selector("input#username.txtFld.log_value")
        input_username.send_keys(credentials["username"])
        input_password = driver.find_element_by_css_selector("input#password.txtFld.log_value")

        input_password.send_keys(credentials["password"])
        input_password.submit()
        sleep(3)  # so page can be fully rendered
        service_links = driver.find_elements_by_css_selector("#ts_sidebar section#zacks_services a")
        service_name_vs_url = {}
        for link in service_links:
            if not link.get_attribute("textContent"):
                raise ValueError("link.text should not be evaluated as false")
            service_name_vs_url[link.get_attribute("textContent").lower()] = link.get_attribute("href")
            print("{}, link href: {}".format(link.get_attribute("textContent"), link.get_attribute("href")))

        interested_portfolios = [
            # "Home Run Investor",
            # "Income Investor",
            # "Stocks Under $10",
            # "Value Investor",
            # "Technology",
            # "Large-Cap Trader",
            # "TAZR",
            "Momentum Trader",
            # "Counterstrike",
            # "Insider Trader",
            # "Black Box Trader"
        ]
        if not interested_portfolios or not len(interested_portfolios):
            print("no interested portfolio selected")
            return

        for int_port in interested_portfolios:
            assert int_port.lower() in service_name_vs_url, "\"" + int_port.lower() + "\" could not be found."

        # record_date means the date this record generated
        header = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            "portfolio", "symbol", "vol_percent", "date_added", "type", "price", "record_date")
        print(header)
        if output_file is not None:
            output_file.write(header + "\n")

        for int_port in interested_portfolios:
            # visit specified portfolio
            print("now visiting url {}".format(service_name_vs_url[int_port.lower()]))
            driver.get(service_name_vs_url[int_port.lower()])
            sleep(2)
            head_tr = driver.find_element_by_css_selector("table#port_sort thead tr")
            ths_of_header_row = head_tr.find_elements_by_tag_name("th")
            header_vs_col_idx = {}
            for idx, th in enumerate(ths_of_header_row):
                table_column_header_name = __table_header_name_remap(th.text)
                header_vs_col_idx[table_column_header_name] = idx

            # click all "Details>>" of addition, deletion and Open Portfolio tables to load js
            for tr in driver.find_elements_by_css_selector("table.display tbody tr"):
                # td in one line
                for td in tr.find_elements_by_tag_name("td"):
                    if "Detail" in td.text:
                        td.click()

            trs = driver.find_elements_by_css_selector("table#port_sort tbody tr")
            __process_rows_of_table(driver, "scan", trs, int_port,
                                    header_vs_col_idx, insert_record, mysql_helper, 'portfolio_scan')
            trs = driver.find_elements_by_css_selector("#ts_content section.deletions tbody tr")
            __process_rows_of_table(driver, "deletions", trs, int_port,
                                    header_vs_col_idx, insert_record, mysql_helper, 'portfolio_operations')
            trs = driver.find_elements_by_css_selector("#ts_content section.additions tbody tr")
            __process_rows_of_table(driver, "additions", trs, int_port,
                                    header_vs_col_idx, insert_record, mysql_helper, 'portfolio_operations')
    finally:
        if driver is not None:
            driver.get("https://www.zacks.com/logout.php")
            driver.close()
        if output_file is not None:
            output_file.close()
        mysql_helper.set_reuse_connection(False)


def insert_record(records: List, *args, **kwargs):
    mysql_helper = args[0]
    tgt_table = args[1]
    col_names = ["portfolio", "symbol", "vol_percent", "date_added", "type", "price", "record_date", "uniqueness"]
    uniq = utility.compute_uniqueness_str(*records)
    records.append(uniq)
    mysql_helper.insert_one_record(tgt_table, col_names=col_names, values=records, suppress_duplicate=True)


def __determine_trade_type(tds, header_vs_col_idx):
    return tds[header_vs_col_idx['type']].text.lower() if 'type' in header_vs_col_idx else 'long'

