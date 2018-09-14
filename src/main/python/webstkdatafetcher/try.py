import mechanicalsoup
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


if __name__ == "__main__":
    # execute only if run as a script
    open_zacks_ultimate()
