from typing import List, Dict

import logging
from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support import expected_conditions
from time import sleep
from datetime import date, datetime

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup


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

__latest_symbol_prices = {}

__portfolio_idx = 0
__symbol_idx = 1
__vol_percent_idx = 2
__date_added_idx = 3
__type_idx = 4
__price_idx = 5
__record_date_idx = 6


def __table_header_name_remap(header: str):
    if header in __internal_header_mapping:
        return __internal_header_mapping[header]
    else:
        return header.lower()


def is_in(one_record, records):
    for that_record in records:
        if is_same_trade(one_record, that_record):
            return True
    return False


def is_same_trade(this_record, that_record):
    """
    check whether portfolio, symbol, date_added, type and price are the same

    :param this_record: one record
    :param that_record: previous records
    :return: true if portfolio, symbol, date_added, type and price of two trade records are the same, otherwise false.
    """
    if this_record is that_record:
        return True
    return (this_record[__portfolio_idx] == that_record[__portfolio_idx]) and \
           (this_record[__symbol_idx] == that_record[__symbol_idx]) and \
           (this_record[__date_added_idx] == that_record[__date_added_idx]) and \
           (this_record[__type_idx] == that_record[__type_idx]) and \
           (this_record[__price_idx] == that_record[__price_idx])


def __process_rows_of_table(driver, mysql_helper: mysql_related.MySqlHelper,
                            operation: str,
                            trs: List[WebElement],
                            port_name: str,
                            port_url: str,
                            header_vs_col_idx):
    if not isinstance(driver, WebDriver):
        raise TypeError("driver can only be instance of WebDriver")
    if operation not in ["additions", "deletions", "scan"]:
        raise ValueError("accepted operation can only be \"additions\" or \"deletions\"")
    for tr in trs:
        if not isinstance(tr, WebElement):
            raise TypeError("trs can only be a list of WebElement")
    symbol_temp = ''

    previous_scanned_records = []
    uniqs_of_last_scan = []
    today_date = date.today()
    selected_cols = ['portfolio', 'symbol', 'vol_percent', 'date_added', 'type', 'price', 'record_date', 'uniqueness']
    if operation == 'scan':
        mysql_helper.select_from("portfolio_scan", None, selected_cols,
                                 col_val_dict={
                                     'record_date': '(SELECT MAX(record_date) FROM zacks.portfolio_scan ' +
                                                    '    WHERE portfolio = \'{}\')'.format(port_name),
                                     'portfolio': port_name
                                 },
                                 callback_on_cursor=mysql_related.MySqlHelper.default_select_collector,
                                 result_holder=previous_scanned_records)
        uniqs_of_last_scan = set([record[-1] for record in previous_scanned_records])

    records = []
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

        price_text = tds[header_vs_col_idx['price']].text.strip()
        record_format = "{}\t{}\t{}\t{}\t{}\t{}\t{}"
        try:
            if price_text:
                price = round(float(price_text), 2)
            else:
                price = None
        except ValueError:
                price = round(float(price_text.replace(',', '')), 2)
        one_record = [port_name,
                      symbol_temp,
                      round(float(tds[header_vs_col_idx['vol_percent']].text.strip('%')) / 100.0, 4)
                      if 'vol_percent' in header_vs_col_idx else None,
                      datetime.strptime(tds[header_vs_col_idx['date']].text, '%m/%d/%y').date(),
                      trade_type,
                      price,
                      today_date]
        one_record_line = record_format.format(*one_record)
        logging.info("%s %s", operation, one_record_line)
        temp_record_for_uniq_calc = one_record[:]
        temp_record_for_uniq_calc[2] = None  # vol_percent should not be included into uniqueness calculation
        one_record.append(utility.compute_uniqueness_str(*temp_record_for_uniq_calc))
        records.append(one_record)

    target_mysql_table = 'portfolio_scan' if operation == 'scan' else 'portfolio_operations'
    col_names = ["portfolio", "symbol", "vol_percent", "date_added", "type", "price", "record_date", "uniqueness"]

    if operation == 'scan' and len(previous_scanned_records) > 0:
        cnt = 0
        for one_record in records:
            if one_record[-1] in uniqs_of_last_scan:
                uniqs_of_last_scan.remove(one_record[-1])
            else:
                mysql_helper.insert_one_record(target_mysql_table,
                                               col_names=col_names, values=one_record, suppress_duplicate=True)
            # if current record is not among previous scan of this portfolio, and its record date is today
            # then it is a newly added record in open_portfolio
            if not is_in(one_record, previous_scanned_records) and one_record[__date_added_idx] == today_date:
                record_derived = one_record[:-1]
                # lone becomes lone_init, short becomes short_init
                record_derived[__type_idx] = record_derived[__type_idx] + "_init"
                temp_record_for_uniq_calc = record_derived[:]
                # vol_percent should'nt be included into uniqueness calculation
                temp_record_for_uniq_calc[__vol_percent_idx] = None
                record_derived.append(utility.compute_uniqueness_str(*temp_record_for_uniq_calc))
                mysql_helper.insert_one_record('portfolio_operations',
                                               col_names=col_names, values=record_derived, suppress_duplicate=True)
                cnt = cnt + 1
        logging.info("Portfolio \"%s\"(%s) has %s records added compared against last last scan.",
                     port_name, today_date.strftime('%y-%m-%d'), cnt)

        # at this time, elements inside uniqs_of_last_scan belong to those trades which no longer appear in
        # current portfolio (likely have been deleted)
        if len(uniqs_of_last_scan) > 0:
            mysql_helper.delete_from_table(target_mysql_table,
                                           col_val_dict={
                                               'portfolio': port_name,
                                               'record_date': today_date,
                                               'uniqueness': uniqs_of_last_scan,
                                           })
            cnt = 0
            for prev_record in previous_scanned_records:
                if is_in(prev_record, records):
                    continue
                record_derived = list(prev_record)[:-1]
                # lone becomes lone_close, short becomes short_close
                record_derived[__type_idx] = record_derived[__type_idx] + "_close"
                record_derived[__record_date_idx] = today_date
                temp_record_for_uniq_calc = record_derived[:]
                # vol_percent should not be included into uniqueness calculation
                temp_record_for_uniq_calc[__vol_percent_idx] = None
                record_derived.append(utility.compute_uniqueness_str(*temp_record_for_uniq_calc))
                copied_col_names = col_names[:]
                try:
                    record_derived.append(get_stock_price(driver, record_derived[__symbol_idx]))
                    copied_col_names.append('price_at_close')
                except ValueError as ve:
                    logging.error(str(ve))
                finally:
                    driver.get(port_url)
                mysql_helper.insert_one_record('portfolio_operations',
                                               col_names=copied_col_names,
                                               values=record_derived,
                                               suppress_duplicate=True)
                cnt = cnt + 1
            logging.info("Portfolio \"{}\"({}) has {} records removed from last last scan.".format(
                port_name, today_date.strftime('%y-%m-%d'), cnt))
        else:
            logging.info("Portfolio \"{}\"({}) has {} records removed from last last scan.".format(
                port_name, today_date.strftime('%y-%m-%d'), 0))
    else:
        if operation == 'scan':
            logging.warning("operation: {}, len(previous_scanned_records): {}".format(
                operation, len(previous_scanned_records)))
        for one_record in records:
            copied_col_names = col_names[:]
            if one_record[__type_idx].endswith("_close"):
                try:
                    one_record.append(get_stock_price(driver, one_record[__symbol_idx]))
                    copied_col_names.append('price_at_close')
                except ValueError as ve:
                    logging.error(str(ve))
                finally:
                    driver.get(port_url)
            mysql_helper.insert_one_record(target_mysql_table, col_names=copied_col_names, values=one_record,
                                           suppress_duplicate=True)


def get_stock_price(driver, symbol):
    """
    parse html content, use symbol name to fetch lastest quote of one symbol

    :param driver: web driver
    :param symbol stock symbol, such as LMT, NVDA
    :return: symbol latest quote price
    """
    if symbol in __latest_symbol_prices:
        return __latest_symbol_prices[symbol]
    latest_price = 0
    for i in range(3):
        if latest_price:
            break
        try:
            driver.get("https://finance.yahoo.com/quote/" + symbol)
            element = driver.find_element_by_css_selector(
                "div#quote-header-info > div:nth-child(3) > div > div > span:first-child")
            latest_price = float(element.text)
        except NoSuchElementException:
            continue
    if not latest_price:
        raise ValueError("could not fetch quote price for " + symbol)
    __latest_symbol_prices[symbol] = latest_price
    return latest_price


def handle_zacks_email(email_content: str):
    """
    given part of html content of a zacks email wrapped by <div data-test-id="message-body-container">....</div>,
    process and output a list of list of records
    [
      [port_name, symbol, vol_percent, date_added, trade_type, price, record_date, uniqueness],
      [port_name, symbol, vol_percent, date_added, trade_type, price, record_date, uniqueness],
    ]
    :param email_content:
    :return: a list of records, each record is a list containing values of each column
    """
    soup = BeautifulSoup(email_content, 'html.parser')
    # print(type(soup.find('title')))
    # print(soup.find('title'))

    target_div = soup.find('div', class_="msg-body").div.div.div
    # print(target_div)
    interested_id = target_div['id']
    print("interested id {}nav".format(interested_id))
    nav_table = soup.find('table', class_=interested_id + 'nav')
    next_table = nav_table.find_next_sibling('table')
    while next_table is not None:
        the_th = next_table.find('th')
        if the_th.string:
            table_head = the_th.string.strip()
            print(table_head)
            trs = next_table.tbody.find_all("tr")
            for tr in trs:
                print(tr)
            next_table = next_table.find_next_sibling('table')
        else:
            break

    # tables = target_div.find_all('table')
    # print(len(tables))
    # for table in tables:
    #     print(table)


def selenium_chrome(output: str = None,
                    clear_previous_content: bool = False,
                    headless: bool = False,
                    db_config_dict: dict = None):
    """

    :param output: output path
    :param headless: whether to run browser in headless mode.
    :param clear_previous_content clear content if one file already exist at path specified in output
    :param db_config_dict db configuration dictionary, which includes fields host, username, password, database.
    """
    chrome_option = webdriver.ChromeOptions()
    # invokes headless setter
    chrome_option.headless = headless
    chrome_option.add_argument("--window-size=1920x1080")
    driver = None
    output_file = None
    mysql_helper = mysql_related.MySqlHelper(reuse_connection=True, db_config_dict=db_config_dict)
    should_commit = False
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
        logging.info("submitted ultimate login form")
        sleep(3)  # so page can be fully rendered
        try:
            driver.find_element_by_css_selector("#accept_cookie").click()
            logging.info("accepted cookie.")
        except NoSuchElementException:
            pass
        service_links = driver.find_elements_by_css_selector("#ts_sidebar section#zacks_services a")
        service_name_vs_url = {}
        for link in service_links:
            if not link.get_attribute("textContent"):
                raise ValueError("link.text should not be evaluated as false")
            service_name_vs_url[link.get_attribute("textContent").lower()] = link.get_attribute("href")

        interested_portfolios = [
            # "Home Run Investor",
            # "Income Investor",
            # "Stocks Under $10",
            # "Value Investor",
            # "Technology",
            # "Large-Cap Trader",
            "TAZR",
            # "Momentum Trader",
            # "Counterstrike",
            # "Insider Trader",
            # "Black Box Trader"
        ]
        if not interested_portfolios or not len(interested_portfolios):
            logging.error("no interested portfolio selected")
            return

        for int_port in interested_portfolios:
            assert int_port.lower() in service_name_vs_url, "\"" + int_port.lower() + "\" could not be found."

        # record_date means the date this record generated
        header = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            "portfolio", "symbol", "vol_percent", "date_added", "type", "price", "record_date")
        logging.info(header)
        if output_file is not None:
            output_file.write(header + "\n")

        for int_port in interested_portfolios:
            # visit specified portfolio
            logging.info("now visiting url {}".format(service_name_vs_url[int_port.lower()]))
            head_tr = None
            # try visiting this page for at most three times.
            for i in range(3):
                if head_tr:
                    # if head_tr is given valid value, no need to loop again
                    break
                try:
                    driver.get(service_name_vs_url[int_port.lower()])
                    sleep(3)
                    # might not be able to find
                    head_tr = driver.find_element_by_css_selector("table#port_sort thead tr")
                except NoSuchElementException as noSuchElmEx:
                    logging.error("At i : {}, could not find target portfolio table by CSS selector: {}",
                                  i, noSuchElmEx.msg)
            port_url = driver.current_url
            if not head_tr:
                raise NoSuchElementException()
            ths_of_header_row = head_tr.find_elements_by_tag_name("th")
            header_vs_col_idx = {}
            for idx, th in enumerate(ths_of_header_row):
                table_column_header_name = __table_header_name_remap(th.text)
                header_vs_col_idx[table_column_header_name] = idx

            # click all "Details>>" of addition, deletion and Open Portfolio tables to load js
            for operation in ["additions", "deletions", "scan"]:
                driver.get(port_url)
                trs = driver.find_elements_by_css_selector("table.display tbody tr")
                for tr in trs:
                    # td in one line
                    tds = tr.find_elements_by_tag_name("td")
                    for td in tds:
                        if "Details" in td.text:
                            # noinspection PyStatementEffect
                            td.location_once_scrolled_into_view
                            td.click()
                if operation == 'additions':
                    trs = driver.find_elements_by_css_selector("#ts_content section.additions tbody tr")
                elif operation == 'deletions':
                    trs = driver.find_elements_by_css_selector("#ts_content section.deletions tbody tr")
                elif operation == 'scan':
                    trs = driver.find_elements_by_css_selector("table#port_sort tbody tr")
                else:
                    raise ValueError("{} is not recognized operation".format(operation))
                __process_rows_of_table(driver, mysql_helper, operation, trs, int_port,
                                        port_url=port_url,
                                        header_vs_col_idx=header_vs_col_idx)

        should_commit = True
    finally:
        if driver is not None:
            driver.get("https://www.zacks.com/logout.php")
            driver.close()
        if output_file is not None:
            output_file.close()
        mysql_helper.set_reuse_connection(False, should_commit)
        deduplicate(mysql_helper)
    logging.info("selenium_chrome ends normally.")


def deduplicate(mysql_helper: mysql_related.MySqlHelper):
    if not isinstance(mysql_helper, mysql_related.MySqlHelper):
        raise ValueError("mysql_helper must be instance of mysql_related.MySqlHelper")
    dedup1_stmt_format = """
    DELETE t1 FROM {0} t1
      INNER JOIN {0} t2
    WHERE t1.portfolio = t2.portfolio
      AND t1.symbol = t2.symbol
      AND t1.date_added = t2.date_added
      AND t1.type != t2.type
      AND t1.record_date = t2.record_date
      AND ROUND(t1.price, 2) = ROUND(t2.price, 2);
    """
    deduplicate1_operations = dedup1_stmt_format.format("portfolio_operations")
    mysql_helper.execute_update(deduplicate1_operations)

    dedup2_stmt_format = """
    DELETE t1  FROM {0} t1
      INNER JOIN {0} t2
    WHERE t1.id < t2.id
      AND t1.portfolio = t2.portfolio
      AND t1.symbol = t2.symbol
      AND t1.date_added = t2.date_added
      AND t1.type = t2.type
      AND t1.record_date = t2.record_date;
    """
    deduplicate2_operations = dedup2_stmt_format.format("portfolio_operations")
    deduplicate2_scan = dedup2_stmt_format.format("portfolio_scan")
    mysql_helper.execute_update(deduplicate2_operations)
    mysql_helper.execute_update(deduplicate2_scan)
    logging.info("de-duplication executed correctly")


def __determine_trade_type(tds: List[WebElement], header_vs_col_idx: Dict[str, int]):
    return tds[header_vs_col_idx['type']].text.lower() if 'type' in header_vs_col_idx else 'long'
