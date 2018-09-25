import unittest
from datetime import date
from webstkdatafetcher import logic
from selenium import webdriver


class TestLogicModule(unittest.TestCase):

    def test_is_same_trade(self):
        prev_record = ("test_port", "XYZ", 0.034, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 14), 'fakeunique')
        curr_record = ["test_port", "XYZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeunique']
        self.assertTrue(logic.is_same_trade(curr_record, prev_record))
        curr_record = ["test_port", "XZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeunique']
        self.assertFalse(logic.is_same_trade(curr_record, prev_record))
        curr_record = ["tt_port2", "XZZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeunique']
        self.assertFalse(logic.is_same_trade(curr_record, prev_record))
        curr_record = [
            "test_port", "XYZ", 0.038, date(2018, 9, 7), 'short_init', 34.78, date(2018, 9, 18), 'fakeunique']
        self.assertFalse(logic.is_same_trade(curr_record, prev_record))
        curr_record = [
            "test_port", "XYZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeuniqueasd']
        self.assertTrue(logic.is_same_trade(curr_record, prev_record))
        curr_record = ["test_port", "XYZ", 0.038, date(2018, 9, 7), 'long_init', 34.79, date(2018, 9, 18), 'fakeunique']
        self.assertFalse(logic.is_same_trade(curr_record, prev_record))

    def test_get_latest_price(self):
        chrome_option = webdriver.ChromeOptions()
        # invokes headless setter
        chrome_option.headless = True
        chrome_option.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=chrome_option)
        driver.maximize_window()
        symbols = ["LMT", "AMAT", "NVDA", "BABA"]
        try:

            for symbol in symbols:
                price = logic.get_stock_price(driver, symbol)
                print("Latest quote {} : {}".format(symbol, price))
            for symbol in symbols:
                price = logic.get_stock_price(driver, symbol)
                print("Latest quote {} : {}".format(symbol, price))
            for symbol in symbols:
                price = logic.get_stock_price(driver, symbol)
                print("Latest quote {} : {}".format(symbol, price))
        finally:
            driver.close()
