from typing import List, Dict

import logging
from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support import expected_conditions
from time import sleep
import pytz
from datetime import date, datetime
from collections import OrderedDict
import operator

from selenium.webdriver.remote.webdriver import WebDriver
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


def compare_trade(this_record: dict, that_record: dict, compare_price: bool = False, compare_vol_percent: bool = False):
    this_record = utility.remove_operation_suffix(this_record)
    that_record = utility.remove_operation_suffix(that_record)

    attrs = ["portfolio", "symbol", "date_added", "type"]
    for attr in attrs:
        result = (this_record[attr] > that_record[attr]) - (this_record[attr] < that_record[attr])
        if result != 0:
            return result
    if not compare_price and not compare_vol_percent:
        return 0
    if compare_price:
        price_result = utility.null_safe_number_compare(this_record["price"], that_record["price"], 0.005)
        if price_result != 0:
            return price_result
    if compare_vol_percent:
        vol_percent_result = utility.null_safe_number_compare(
            this_record["vol_percent"], that_record["vol_percent"], 0.00001)
        if vol_percent_result != 0:
            return vol_percent_result
    return 0


def __extract_price(price_text, num_of_decimal):
    price_text = price_text.strip()
    try:
        if price_text:
            price = round(float(price_text), num_of_decimal)
        else:
            price = 0.0
    except ValueError:
        price = round(float(price_text.replace(',', '')), num_of_decimal)
    return price


def tbody_html_to_records(tbody_content: str, header_vs_col_idx, operation: str, port_name: str,
                          today_date: datetime.date) -> List[Dict]:

    symbol_temp = ''
    records = []
    soup = BeautifulSoup(tbody_content, 'html.parser')
    trs = soup.find_all('tr')
    for tr in trs:
        # td in one line
        tds = tr.find_all('td')
        if "No Current Signal" in str(tds[0]):
            continue
        if tds[1].a and tds[1].a.span.string:
            symbol_temp = tds[1].a.span.string.strip()
        if "Detail" in str(tds[3]):
            continue
        # "portfolio name", "symbol", "vol_percent", "date", "type", "price"

        trade_type = __determine_trade_type_bs4(tds, header_vs_col_idx)
        if operation == 'deletions':
            trade_type = trade_type + '_close'  # close long or short position
        elif operation == 'additions':
            trade_type = trade_type + '_init'   # long_init short_init,  initialize long or short postion

        one_record = OrderedDict([
            ('portfolio', port_name),
            ('symbol', symbol_temp),
            ('vol_percent', round(float(tds[header_vs_col_idx['vol_percent']].string.strip().strip('%')) / 100.0, 4)
                if 'vol_percent' in header_vs_col_idx else None),
            ('date_added', datetime.strptime(tds[header_vs_col_idx['date']].string.strip(), '%m/%d/%y').date()),
            ('type', trade_type),
            ('price', __extract_price(tds[header_vs_col_idx['price']].string.strip(), 2)),
            ('record_date', today_date),
            ('last_price', __extract_price(tds[header_vs_col_idx['last_price']].string.strip(), 2)),
        ])

        record_format = "{}\t{}\t{}\t{}\t{}\t{}\t{}"
        one_record_values = list(one_record.values())
        one_record_line = record_format.format(*one_record_values)
        logging.info("%s %s", operation, one_record_line)
        one_record['uniqueness'] = utility.compute_uniqueness_str(*one_record_values)
        records.append(one_record)
    if operation == 'scan' and len(records) <= 2 and port_name != 'Surprise Trader':
        logging.warning("scan {} only yields {} records".format(port_name, len(records)))
        logging.warning("tbody_content html:\n{}".format(soup.prettify()))
    return records


def get_prev_records(mysql_helper: mysql_related.MySqlHelper, port_name, table: str = 'portfolio_scan'):
    if not isinstance(port_name, str) or len(port_name.strip()) == 0:
        raise ValueError("port_name must be valid portfolio name")

    previous_records = []
    selected_cols = ['id', 'portfolio', 'symbol', 'vol_percent', 'date_added', 'type', 'price', 'record_date',
                     'uniqueness']
    col_val_dict = {
        'record_date': '(SELECT MAX(record_date) FROM {} '.format(table) +
                       '    WHERE portfolio = \'{}\')'.format(port_name),
        'portfolio': port_name
    }
    if table == 'portfolio_operations':
        record_date_condition_for_portfolio_operation = [
            '>=',
            '(SELECT IFNULL(DATE_SUB(MAX(record_date), INTERVAL 1 DAY), '
            + 'STR_TO_DATE(\'1970-01-01\', \'%Y-%m-%d\') ) FROM {} '.format(table)
            + '    WHERE portfolio = \'{}\')'.format(port_name)
        ]
        col_val_dict['record_date'] = record_date_condition_for_portfolio_operation
    mysql_helper.select_from(table, None, selected_cols,
                             col_val_dict=col_val_dict,
                             callback_on_cursor=mysql_related.MySqlHelper.default_select_collector,
                             result_holder=previous_records)
    for idx, one_prev_record in enumerate(previous_records):
        previous_records[idx] = OrderedDict(
            [(selected_cols[col_idx], val) for col_idx, val in enumerate(one_prev_record)])
    return previous_records


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


def get_slickcharts_stock_constituents(driver: WebDriver, index_name: str) -> List[List]:
    if not isinstance(index_name, str) or index_name == "":
        raise ValueError("index_name must be str, and cannot be empty")
    index_name = index_name.lower()
    valid_index_name = {"sp500", "nasdaq100", "dowjones"}
    if index_name not in valid_index_name:
        raise ValueError("index_name must be one of \"sp500\", \"nasdaq100\", \"dowjones\"")

    slick_charts = "https://www.slickcharts.com/"
    url = slick_charts + index_name
    get_stocks = False
    stocks = [["#", "Company", "Symbol", "Weight", "Price", "Change"]]
    for i in range(3):
        if get_stocks:
            break
        try:
            stocks = stocks[0:1]
            driver.get(url)
            table_element = driver.find_element_by_css_selector("div.row table")
            soup = BeautifulSoup(table_element.get_attribute("outerHTML"), 'html.parser')
            trs = soup.select("tbody tr")
            for tr in trs:
                tds = tr.find_all("td")
                row = [
                    int(tds[0].string.strip()),
                    tds[1].string.strip(),
                    tds[2].string.strip(),
                    float(tds[3].get_text().strip()),
                    float(tds[4].get_text().replace(",", "").strip()),
                ]
                temp_str = tds[5].get_text().strip()
                row.append(float(temp_str.split("  ")[0].strip()))
                # logging.info(tds[2].string)
                stocks.append(row)
            get_stocks = True
        finally:
            # make three attemps at most
            pass
    if not get_stocks:
        raise Exception("could not stocks of {}".format(index_name))
    return stocks


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


def process(records_by_operation: Dict[str, List[Dict]],
            prev_portfolio: List[OrderedDict],
            prev_operations: List[OrderedDict],
            cur_scan_record_date: date,
            web_driver: WebDriver = None):

    tbr = {
        "portfolio_scan": {
            "update": [],
            "insert": [],
            "delete": []  # records or only ids
        },
        "portfolio_operations": {
            "delete": [],
            "insert": [],
            "update": []
        }}
    current_portfolio = records_by_operation["additions"][:]
    current_portfolio.extend(records_by_operation["scan"])
    current_portfolio = sorted(current_portfolio, key=operator.itemgetter("symbol", "date_added"))
    prev_portfolio = sorted(prev_portfolio, key=operator.itemgetter("symbol", "date_added"))

    prev_scan_record_date = prev_portfolio[0]["record_date"] if len(prev_portfolio) else None

    cur_idx = 0
    cur_len = len(current_portfolio)
    pre_idx = 0
    pre_len = len(prev_portfolio)
    while cur_idx < cur_len and pre_idx < pre_len:
        if compare_trade(prev_portfolio[pre_idx], current_portfolio[cur_idx], False, False) < 0:
            # now deleted
            tbr["portfolio_scan"]["delete"].append(prev_portfolio[pre_idx])
            tbr["portfolio_operations"]["delete"].append(OrderedDict(prev_portfolio[pre_idx]))
            pre_idx += 1
        elif compare_trade(current_portfolio[cur_idx], prev_portfolio[pre_idx], False, False) < 0:
            # new trade
            tbr["portfolio_scan"]["insert"].append(current_portfolio[cur_idx])
            tbr["portfolio_operations"]["insert"].append(OrderedDict(current_portfolio[cur_idx]))
            cur_idx += 1
        else:
            # both list have this trade, do nothing
            # if compare_trade(current_portfolio[cur_idx], prev_portfolio[pre_idx])
            if compare_trade(current_portfolio[cur_idx], prev_portfolio[pre_idx], True, True) != 0:
                prev_portfolio[pre_idx].update(current_portfolio[cur_idx])
                tbr["portfolio_scan"]["update"].append(prev_portfolio[pre_idx])
                for prev_operation in prev_operations:
                    if compare_trade(prev_operation, current_portfolio[cur_idx], False, False) == 0:
                        utility.update_record(prev_operation, "price", current_portfolio[cur_idx]["price"])
                        utility.update_record(prev_operation, "vol_percent", current_portfolio[cur_idx]["vol_percent"])
                        tbr["portfolio_operations"]["update"].append(prev_operation)
            pre_idx += 1
            cur_idx += 1
    while pre_idx < pre_len:
        tbr["portfolio_scan"]["delete"].append(prev_portfolio[pre_idx])
        tbr["portfolio_operations"]["delete"].append(OrderedDict(prev_portfolio[pre_idx]))
        pre_idx += 1
    while cur_idx < cur_len:
        tbr["portfolio_scan"]["insert"].append(current_portfolio[cur_idx])
        tbr["portfolio_operations"]["insert"].append(OrderedDict(current_portfolio[cur_idx]))
        cur_idx += 1

    # if prev scanned records are from previous day, or previous there are no records (means today is first day
    # started recording data), put all currently scanned data to "insert"
    if prev_scan_record_date is None or prev_scan_record_date < cur_scan_record_date:
        tbr["portfolio_scan"]["insert"].clear()
        tbr["portfolio_scan"]["insert"].extend(current_portfolio)
        tbr["portfolio_scan"]["delete"].clear()
        tbr["portfolio_scan"]["update"].clear()

    for record in tbr["portfolio_operations"]["insert"]:
        if "last_price" in record:
            del record["last_price"]
        if not record["type"].endswith("_init"):
            record["type"] = record["type"] + "_init"
    for record in tbr["portfolio_operations"]["delete"]:
        if "last_price" in record:
            del record["last_price"]
        if not record["type"].endswith("_close"):
            record["type"] = record["type"] + "_close"
        record["price_at_close"] = get_stock_price(web_driver, record["symbol"]) if (web_driver is not None) else -1.0
        record["uniqueness"] = utility.compute_uniqueness_str(
            *[record[key] for key in ['portfolio', 'symbol', 'vol_percent', 'date_added', 'type', 'price',
                                      'record_date', 'price_at_close']])
        del record["id"]
    for operation, records in tbr["portfolio_scan"].items():
        for record in records:
            if "last_price" in record:
                del record["last_price"]
    return tbr


def persist_records(mysql_helper: mysql_related.MySqlHelper, tbr):
    """
        tbr = {
        "portfolio_scan": {
            "update": [],
            "insert": [],
            "delete": []  # records or only ids
        },
        "portfolio_operations": {
            "delete": [],
            "insert": []
        }}
    :param mysql_helper:
    :param tbr:
    :return:
    """

    for record in tbr["portfolio_scan"]["insert"]:
        mysql_helper.insert_one_record("portfolio_scan", None, col_val_dict=record)
    if len(tbr["portfolio_scan"]["delete"]):
        where_id_in_this_list = {"id": [record["id"] for record in tbr["portfolio_scan"]["delete"]]}
        mysql_helper.delete_from_table("portfolio_scan", None, where_id_in_this_list)
    for record in tbr["portfolio_scan"]["update"]:
        mysql_helper.update_one_record("portfolio_scan", None, record)
    for record in tbr["portfolio_operations"]["insert"]:
        mysql_helper.insert_one_record("portfolio_operations", None, record, suppress_duplicate=True)
    for record in tbr["portfolio_operations"]["delete"]:
        mysql_helper.insert_one_record("portfolio_operations", None, record, suppress_duplicate=True)
    for record in tbr["portfolio_operations"]["update"]:
        mysql_helper.update_one_record("portfolio_operations", None, record)


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
        if len(service_name_vs_url) == 0:
            logging.error("could not find service name and corresponding urls")
            # logging.error(driver.page_source)
            raise ValueError("could not find service name and corresponding urls")

        interested_portfolios = [
            "Home Run Investor",
            "Income Investor",
            "Stocks Under $10",
            "Value Investor",
            "Technology",
            "Large-Cap Trader",
            "TAZR",
            "Momentum Trader",
            "Counterstrike",
            "Insider Trader",
            "Black Box Trader",
            "Surprise Trader"
        ]
        if not interested_portfolios or not len(interested_portfolios):
            logging.error("no interested portfolio selected")
            return

        for int_port in interested_portfolios:
            assert int_port.lower() in service_name_vs_url, '{} could not be found in {}'.format(
                int_port.lower(), service_name_vs_url)

        # record_date means the date this record generated
        header = "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            "portfolio", "symbol", "vol_percent", "date_added", "type", "price", "record_date")
        logging.info(header)
        if output_file is not None:
            output_file.write(header + "\n")

        utc_now = pytz.utc.localize(datetime.utcnow())
        et_now = utc_now.astimezone(pytz.timezone('US/Eastern'))
        today_date = et_now.date()
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
                    trs_in_open_portfolio = driver.find_elements_by_css_selector(
                        "#ts_content section.portfolio.open tbody tr")
                    if len(trs_in_open_portfolio) <= 1 and int_port != 'Surprise Trader':
                        raise NoSuchElementException('could not find records in open portfolio of {}'.format(int_port))
                    # might not be able to find
                    head_tr = driver.find_element_by_css_selector("#ts_content section.portfolio.open table thead tr")
                except NoSuchElementException as nse:
                    logging.error("At i: %s, except NoSuchElementException, msg: %s", 1, nse.msg)
            if not head_tr:
                logging.error("After three attempts, could not extract content of portfolio {}".format(int_port))
                logging.error("Going to skip portfolio {}".format(int_port))
                continue
                # raise NoSuchElementException('could not extract head_tr')
            ths_of_header_row = head_tr.find_elements_by_tag_name("th")
            header_vs_col_idx = {}
            for idx, th in enumerate(ths_of_header_row):
                table_column_header_name = __table_header_name_remap(th.text)
                header_vs_col_idx[table_column_header_name] = idx

            # click all "Details>>" of addition, deletion and Open Portfolio tables to load js
            trs = driver.find_elements_by_css_selector("table.display tbody tr")
            for tr in trs:
                # td in one line
                tds = tr.find_elements_by_tag_name("td")
                for td in tds:
                    if "Details" in td.text:
                        # noinspection PyStatementEffect
                        td.location_once_scrolled_into_view
                        td.click()
            records_by_operation = {}
            for operation in ["additions", "deletions", "scan"]:
                if operation == 'additions':
                    css_selector = "#ts_content section.additions tbody"
                elif operation == 'deletions':
                    css_selector = "#ts_content section.deletions tbody"
                else:
                    css_selector = "#ts_content section.portfolio.open tbody"
                tbody_html = driver.find_element_by_css_selector(css_selector).get_attribute('outerHTML')
                records_by_operation[operation] = tbody_html_to_records(
                    tbody_html,
                    header_vs_col_idx,
                    operation,
                    int_port,
                    today_date
                )
            prev_scanned_records = get_prev_records(mysql_helper, int_port, 'portfolio_scan')
            prev_operat_records = get_prev_records(mysql_helper, int_port, 'portfolio_operations')
            tbr = process(records_by_operation, prev_scanned_records, prev_operat_records, today_date, driver)
            persist_records(mysql_helper, tbr)

        # end of for loop:  for int_port in interested_portfolios:
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

    # remove those records having opposite operation, added at the same date, which might be added in an error
    dedup1_stmt_format = """
    DELETE t1 FROM {0} t1
      INNER JOIN {0} t2
    WHERE t1.portfolio = t2.portfolio
      AND t1.symbol = t2.symbol
      AND t1.date_added = t2.date_added
      AND t1.type != t2.type
      AND (ISNULL(t1.price) OR (t1.price > -0.05 AND t1.price < 0.05)) 
      AND (ISNULL(t2.price) OR (t2.price > -0.05 AND t2.price < 0.05));
    """
    deduplicate1_operations = dedup1_stmt_format.format("portfolio_operations")
    mysql_helper.execute_update(deduplicate1_operations)

    # remove those operations (actually the same one, but its price might be modified later) which added earlier
    dedup2_stmt_format = """
    DELETE t1  FROM {0} t1
      INNER JOIN {0} t2
    WHERE t1.id < t2.id
      AND t1.portfolio = t2.portfolio
      AND t1.symbol = t2.symbol
      AND t1.date_added = t2.date_added
      AND t1.type = t2.type;
    """
    deduplicate2_operations = dedup2_stmt_format.format("portfolio_operations")
    mysql_helper.execute_update(deduplicate2_operations)

    # remove records like following:
    # | 276 | Momentum Trader   | CDXS   |      0.1127 | 2018-09-26 | long_init  |     19 |
    # 2018-09-27  | 2bd7e4f009b0a16c035d79a61cc02457 |           NULL |
    # | 278 | Momentum Trader   | CDXS   |      0.1255 | 2018-09-26 | long_close |      0 |
    # 2018-09-27  | d7b58fcc0712cc1e470e38f74fa635c0 |         17.375 |

    dedup2_stmt_format = """
    DELETE t1 FROM {0} t1
      INNER JOIN {0} t2
    WHERE t1.portfolio = t2.portfolio
      AND t1.symbol = t2.symbol
      AND t1.date_added = t2.date_added
      AND t1.type != t2.type
      AND (ISNULL(t1.price) OR (t1.price > -0.05 AND t1.price < 0.05))
      AND t2.price > 0.05;
    """
    deduplicate2_operations = dedup2_stmt_format.format("portfolio_operations")
    mysql_helper.execute_update(deduplicate2_operations)

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
    deduplicate2_scan = dedup2_stmt_format.format("portfolio_scan")
    mysql_helper.execute_update(deduplicate2_scan)
    logging.info("de-duplication executed correctly")


def __determine_trade_type_bs4(tds, header_vs_col_idx: Dict[str, int]):
    return tds[header_vs_col_idx['type']].string.lower().strip() if 'type' in header_vs_col_idx else 'long'
