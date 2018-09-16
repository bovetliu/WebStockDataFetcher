import mechanicalsoup
from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from webstkdatafetcher import constants


__internal_header_mapping = {
    "Company": "company",
    "Sym": "symbol",
    "%Val": "vol_percent",
    "+Date": "date",
    "$Add": "price",
    "$Last": "last_price",
    "%Chg": "change_percent",
    "Type": "type"
}


def seach_in_duckduckgo():
    # Connect to duckduckgo
    browser = mechanicalsoup.StatefulBrowser()
    browser.open("https://duckduckgo.com/")

    # Fill-in the search form
    browser.select_form('#search_form_homepage')
    browser["q"] = "MechanicalSoup"
    browser.submit_selected()

    # Display the results
    for link in browser.get_current_page().select('a.result__a'):
        print(link.text, '->', link.attrs['href'])


def get_propdict_file(path: str):
    tbr = {}
    with open(path) as credential_file:
        for line in credential_file:
            line = line.rstrip()
            line_splits = line.split("=")
            if len(line_splits) != 2:
                raise ValueError(line + " could not split into key and value")
            tbr[line_splits[0]] = line_splits[1]
    return tbr


def __table_header_name_remap(header: str):
    if header in __internal_header_mapping:
        return __internal_header_mapping[header]
    else:
        return header.lower()


def selenium_chrome(output: str = None, clear_previous_content: bool = False):
    """

    :param output: output path
    :param clear_previous_content clear content if one file already exist at path specified in output
    """
    chrome_option = webdriver.ChromeOptions()
    # invokes headless setter
    chrome_option.headless = True
    chrome_option.add_argument("--window-size=1920x1080")
    driver = None
    output_file = None
    try:
        if output:
            output_file = open(output, 'w+')
        if clear_previous_content and output_file is not None:
            output_file.seek(0)
            output_file.truncate()

        driver = webdriver.Chrome(options=chrome_option, service_log_path=constants.chrome_log_path)
        driver.get("https://www.zacks.com/ultimate/")
        credentials = get_propdict_file(constants.credentials_path)
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

        # interested_portfolios = ["Home Run Investor", "Income Investor", "Stocks Under $10",
        #                          "Value Investor", "Technology", "Large-Cap Trader",
        #                          "TAZR", "Momentum Trader", "Counterstrike", "Insider Trader",
        #                          "Black Box Trader"]
        interested_portfolios = [
            "Home Run Investor", "Income Investor",
            # "Stocks Under $10","Value Investor", "Technology",
            # "Large-Cap Trader", "TAZR", "Momentum Trader", "Counterstrike", "Insider Trader", "Black Box Trader"
        ]
        for int_port in interested_portfolios:
            assert int_port.lower() in service_name_vs_url, "\"" + int_port.lower() + "\" could not be found."

        header = "{}\t{}\t{}\t{}\t{}\t{}".format(
            "portfolio", "symbol", "vol_percent", "date", "type", "price")
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
            symbol_temp = ''
            for tr in trs:
                # td in one line
                tds = tr.find_elements_by_tag_name("td")

                if tds[1].text:
                    symbol_temp = tds[1].text
                if "Detail" in tds[3].text:
                    continue
                # "symbol", "vol_percent", "date", "type", "price"
                one_record_line = "{}\t{}\t{}\t{}\t{}\t{}".format(
                    int_port,
                    symbol_temp,
                    tds[header_vs_col_idx['vol_percent']].text if 'vol_percent' in header_vs_col_idx else 'NULL',
                    tds[header_vs_col_idx['date']].text,
                    tds[header_vs_col_idx['type']].text if 'type' in header_vs_col_idx else 'buy',
                    tds[header_vs_col_idx['price']].text)
                print(one_record_line)
                if output_file is not None:
                    output_file.write(one_record_line + '\n')
    finally:
        if driver is not None:
            driver.get("https://www.zacks.com/logout.php")
            driver.close()
        if output_file is not None:
            output_file.close()


if __name__ == "__main__":
    # execute only if run as a script
    selenium_chrome("../../../../data/record2.txt", clear_previous_content=True)
