import mechanicalsoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from webstkdatafetcher import constants


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


def open_zacks_ultimate():

    browser = mechanicalsoup.StatefulBrowser(
        soup_config={'features': 'lxml'},
        raise_on_404=True,
        user_agent=constants.user_agent,
    )

    ultimate_main_page = None
    try:

        browser.open("https://www.zacks.com/ultimate/")
        sleep(1)
        browser.select_form("#loginform")
        browser['username'] = ""
        browser['password'] = ""
        resp = browser.submit_selected()
        ultimate_main_page = browser.get_current_page()
        # currently at https://www.zacks.com/ultimate/
        '''
        <section id="zacks_services">
          <h1 class="arrow_down">Services</h1>
          <div style="display: block;">
            <h1 class="sub_nav_expand">Investor Services</h1>
            <ul class="is_list" style="display: block;">
              <li><a href="/investorcollection/">Investor Collection</a></li>
              <li><a href="/etfinvestor/">ETF Investor</a></li>
              <li><a href="/homerun/">Home Run Investor</a></li>
              <li><a href="/incomeinvestor/">Income Investor</a></li>
              <li><a href="/stocksunder10/">Stocks Under $10</a></li>
              <li><a href="/valueinvestor/">Value Investor</a></li>
              <li><a href="/top10/">Zacks Top 10</a></li>
            </ul>
            <h1 class="sub_nav_expand">Innovators</h1>
            <ul style="display: block;">
              <li><a href="/blockchaininnovators/">Blockchain</a></li>
              <li><a href="/healthcareinnovators/">Healthcare</a></li>
              <li><a href="/technologyinnovators/">Technology</a></li>
            </ul>
            <h1 class="sub_nav_expand">Other Services</h1>
            <ul style="display: block;">
              <li><a href="/confidential/">Zacks Confidential</a></li>
              <li><a href="/premium/">Zacks Premium</a></li>
            </ul>
          </div>
          <div style="display: block;">
            <h1 class="sub_nav_expand">Trading Services</h1>
            <ul style="display: block;">
              <li><a href="/blackboxtrader/">Black Box Trader</a></li>
              <li><a href="/counterstrike/">Counterstrike</a></li>
              <li><a href="/insidertrader/">Insider Trader</a></li>
              <li><a href="/largecaptrader/">Large-Cap Trader</a></li>
              <li><a href="/momentumtrader/">Momentum Trader</a></li>
              <li><a href="/optionstrader/">Options Trader</a></li>
              <li><a href="/shortlist/">Short List</a></li>
              <li><a href="/surprisetrader/">Surprise Trader</a></li>
              <li><a href="/tazr/">TAZR</a></li>
            </ul>
          </div>
        </section>
        '''
        zacks_services_section = ultimate_main_page.find("section", id="zacks_services")
        links = zacks_services_section.find_all("a")
        service_dict = {}
        for link in links:
            service_dict[link.string] = link
            print(link)
        browser.follow_link(service_dict["Counterstrike"])
        counterstrike_page = browser.get_current_page()
        trs = counterstrike_page.find("table", id="port_sort").tbody.find_all("tr")
        print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            "sym", "%val", "date_added", "type", "price_added", "last_price", "change_percent"))
        for tr in trs:
            tds = tr.contents

            print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                tds[1].string, tds[2].string, tds[3].string, tds[4].string, tds[5].string,
                tds[6].string, tds[7].string))
            if "Details" in tds[3].string:
                print("the symbol has multiple")

        sleep(3.0)
    finally:
        if ultimate_main_page is not None:
            browser.follow_link(ultimate_main_page.find("a", id="logout"))
            assert browser.select_form("form[name=loginform]") is not None
        browser.close()


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


def selenium_chrome():
    chrome_option = webdriver.ChromeOptions()
    # invokes headless setter
    chrome_option.headless = False
    driver = None
    try:
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
        service_dict = {}
        for link in service_links:
            if not link.get_attribute("textContent"):
                raise ValueError("link.text should not be evaluated as false")
            service_dict[link.get_attribute("textContent")] = link.get_attribute("href")
            # print("link.get_attribute(\"textContent\"): {}, link href: {}".format(
            #     link.get_attribute("textContent"), link.get_attribute("href")))
        assert "Counterstrike" in service_dict
        driver.get(service_dict["Counterstrike"])
        trs = driver.find_elements_by_css_selector("table#port_sort tbody tr")
        print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
            "sym", "%val", "date_added", "type", "price_added", "last_price", "change_percent"))
        # click all Details of table to load js
        for tr in trs:
            # td in one line
            tds = tr.find_elements_by_tag_name("td")
            for td in tds:
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
            print("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                symbol_temp, tds[2].text, tds[3].text, tds[4].text, tds[5].text,
                tds[6].text, tds[7].text))

    finally:
        if driver is not None:
            driver.get("https://www.zacks.com/logout.php")
            driver.close()


if __name__ == "__main__":
    # execute only if run as a script
    selenium_chrome()
