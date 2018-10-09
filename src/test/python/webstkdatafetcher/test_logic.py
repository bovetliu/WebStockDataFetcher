import logging
import operator
import os.path
import sys
import unittest
from collections import OrderedDict
import datetime
from datetime import date
from typing import List

from bs4 import BeautifulSoup

from webstkdatafetcher import logic, constants, utility
from selenium import webdriver

from webstkdatafetcher.data_connection import mysql_related


class TestLogicModule(unittest.TestCase):

    def __init__(self, arg):
        super().__init__(arg)
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    def test_is_same_trade(self):
        col_names = ['portfolio', 'symbol', 'vol_percent', 'date_added', 'type', 'price', 'record_date',
                     'uniqueness']
        prev_record = ("test_port", "XYZ", 0.034, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 14), 'fakeunique')
        prev_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(prev_record)])

        curr_record = ["test_port", "XYZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeunique']
        curr_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(curr_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, True, True))
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, False, True))

        curr_record_scan_record = ["test_port", "XYZ", 0.038, date(2018, 9, 7), 'long', 34.78, date(2018, 9, 18),
                                   'fakeunique']
        curr_record_scan_record = OrderedDict([(col_names[col_idx], col_val)
                                               for col_idx, col_val in enumerate(curr_record_scan_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record_scan_record, prev_record, True, True))
        self.assertNotEqual(0, logic.compare_trade(curr_record_scan_record, prev_record, False, True))

        # symbol changed
        curr_record = ["test_port", "XZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeunique']
        curr_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(curr_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, False, False))

        # portfolio changed
        curr_record = ["tt_port2", "XZZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeunique']
        curr_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(curr_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, False, False))

        # type changed
        curr_record = [
            "test_port", "XYZ", 0.038, date(2018, 9, 7), 'short_init', 34.78, date(2018, 9, 18), 'fakeunique']
        curr_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(curr_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, False, False))

        # uniqueness changed
        curr_record = [
            "test_port", "XYZ", 0.038, date(2018, 9, 7), 'long_init', 34.78, date(2018, 9, 18), 'fakeuniqueasd']
        curr_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(curr_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, True, True))
        self.assertEqual(0, logic.compare_trade(curr_record, prev_record, True, False))

        # price change a little, +0.01
        curr_record = ["test_port", "XYZ", 0.038, date(2018, 9, 7), 'long_init', 34.79, date(2018, 9, 18), 'fakeunique']
        curr_record = OrderedDict([(col_names[col_idx], col_val) for col_idx, col_val in enumerate(curr_record)])
        self.assertNotEqual(0, logic.compare_trade(curr_record, prev_record, True, False))

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

    def test_deuplicate(self):
        db_config_path = os.path.join(constants.main_resources, "database.properties")
        mysql_helper = mysql_related.MySqlHelper(reuse_connection=False,
                                                 db_config_dict=utility.get_propdict_file(db_config_path))
        logic.deduplicate(mysql_helper)

    def test_tbody_html_to_records(self):
        deletion_table_html = os.path.join(constants.test_resources, "deletions_table.html")
        html_content = utility.get_content_of_file(deletion_table_html)
        operation = "scan"
        header_vs_col_idx = {
            "company": 0,
            "symbol": 1,
            "vol_percent": 2,
            "date": 3,
            "type": 4,
            "price": 5,
            "last_price": 6,
        }
        int_port = "Counterstrike"
        today_date = date(2018, 9, 28)
        trs_by_operation = {}
        soup = BeautifulSoup(html_content, 'html.parser')

        trs_by_operation[operation] = logic.tbody_html_to_records(
            soup.select_one("section.ts-table-wrap tbody").prettify(),
            header_vs_col_idx,
            operation,
            int_port,
            today_date
        )
        self.assertEqual(0.0376, trs_by_operation[operation][0]['vol_percent'])
        self.assertEqual('long', trs_by_operation[operation][1]['type'])
        self.assertEqual(162.49, trs_by_operation[operation][2]['last_price'])
        self.assertEqual('KEYS', trs_by_operation[operation][3]['symbol'])
        self.assertEqual(0.0559, trs_by_operation[operation][6]['vol_percent'])
        self.assertEqual("5944e127b26ad45c2db7b59e2be5196d", trs_by_operation[operation][0]['uniqueness'])

    def test_get_prev_records(self):
        mysql_helper = self.get_mysql_helper()
        port_name = "Black Box Trader"
        results = logic.get_prev_records(mysql_helper, port_name)
        self.assertTrue(len(results) > 0)
        for one_prev_record in results:
            self.assertEqual(one_prev_record['portfolio'], port_name)

        port_name = 'Momentum Trader'
        results = logic.get_prev_records(mysql_helper, port_name, 'portfolio_operations')
        self.assertTrue(len(results) > 0)
        for one_prev_record in results:
            print(one_prev_record)
            self.assertEqual(one_prev_record['portfolio'], port_name)

    def test_process(self):
        chrome_option = webdriver.ChromeOptions()
        # invokes headless setter
        chrome_option.headless = True
        chrome_option.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=chrome_option)
        driver.maximize_window()
        # mysql_helper = self.get_mysql_helper()
        # port_name = "Black Box Trader"

        # new scan happened at the same day, no modification found
        fake_prev_portfolio = TestLogicModule.get_fake_prev_scanned_results()
        fake_prev_record_date = fake_prev_portfolio[0]["record_date"]
        fake_new_scanned_records = self.generate_new_records_based_old(fake_prev_portfolio)
        fake_records_by_operation = {
            "scan": fake_new_scanned_records,
            "additions": [],
            "deletions": []
        }
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_prev_record_date,
                                 web_driver=driver)
        self.assertEqual([], returned["portfolio_operations"]["insert"])
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])

        # new scan happened at the same day, but a new record appeared in fake_new_scanned_records
        one_new_long_position = OrderedDict([('portfolio', 'Black Box Trader'), ('symbol', 'NVDA'),
                                             ('vol_percent', None), ('date_added', fake_prev_record_date),
                                             ('type', 'long'), ('price', 277.35),
                                             ('record_date', fake_prev_record_date)])
        utility.update_record(one_new_long_position, "symbol", "NVDA")
        fake_new_scanned_records.append(one_new_long_position)
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_prev_record_date,
                                 web_driver=driver)
        self.assertEqual(1, len(returned["portfolio_operations"]["insert"]))
        self.assertEqual("long_init", returned["portfolio_operations"]["insert"][0]["type"])
        self.assertEqual("NVDA", returned["portfolio_operations"]["insert"][0]["symbol"])
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual([one_new_long_position], returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])
        self.assertNotEqual(len(fake_new_scanned_records), len(fake_prev_portfolio))
        fake_new_scanned_records.pop()

        # new scan happened at the same day, but a record is deleted in fake_new_scanned_records
        index_of_popped = 2
        popped = fake_new_scanned_records.pop(index_of_popped)
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_prev_record_date,
                                 web_driver=None)
        self.assertEqual([], returned["portfolio_operations"]["insert"])
        # self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual(1, len(returned["portfolio_operations"]["delete"]))
        self.assertEqual("long_close", returned["portfolio_operations"]["delete"][0]["type"])
        self.assertEqual("DNOW", returned["portfolio_operations"]["delete"][0]["symbol"])
        self.assertEqual(-1, returned["portfolio_operations"]["delete"][0]["price_at_close"])
        self.assertEqual([], returned["portfolio_scan"]["insert"])
        self.assertEqual([fake_prev_portfolio[index_of_popped]], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])
        fake_new_scanned_records.insert(index_of_popped, popped)

        # new scan happened at the same day, but a record changed a from None to 16.21, simulating price updating after
        # market close
        index_of_changed = 2
        old_val = fake_new_scanned_records[index_of_changed]["price"]
        fake_new_scanned_records[index_of_changed]["price"] = 16.21
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_prev_record_date,
                                 web_driver=driver)
        self.assertEqual([], returned["portfolio_operations"]["insert"])
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])

        self.assertEqual(16.21, returned["portfolio_scan"]["update"][0]["price"])
        self.assertEqual(fake_prev_portfolio[index_of_changed]["id"], returned["portfolio_scan"]["update"][0]["id"])
        fake_new_scanned_records[index_of_changed]["price"] = old_val

        # new scan happened at the same day, but a record changed a from None to 16.21, simulating price updating after
        # market close, and this record is one of operation
        index_of_changed = 2
        fake_prev_portfolio = TestLogicModule.get_fake_prev_scanned_results()
        fake_new_scanned_records = self.generate_new_records_based_old(fake_prev_portfolio)
        old_val = fake_new_scanned_records[index_of_changed]["price"]
        fake_new_scanned_records[index_of_changed]["price"] = 16.21
        fake_prev_insertion_operation = OrderedDict(fake_prev_portfolio[index_of_changed])
        fake_prev_insertion_operation["type"] = fake_prev_insertion_operation["type"] + "_init"

        fake_records_by_operation = {
            "scan": fake_new_scanned_records,
            "additions": [],
            "deletions": []
        }
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio,
                                 [fake_prev_insertion_operation],
                                 fake_prev_record_date,
                                 web_driver=driver)
        self.assertEqual([], returned["portfolio_operations"]["insert"])
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual(1, len(returned["portfolio_operations"]["update"]))
        self.assertEqual(16.21, returned["portfolio_operations"]["update"][0]["price"])
        self.assertEqual("long_init", returned["portfolio_operations"]["update"][0]["type"])
        self.assertEqual([], returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual(16.21, returned["portfolio_scan"]["update"][0]["price"])
        self.assertEqual(fake_prev_portfolio[index_of_changed]["id"], returned["portfolio_scan"]["update"][0]["id"])
        fake_new_scanned_records[index_of_changed]["price"] = old_val

        # test scenario: new scan happened at a new day, no new change
        self.assertEqual(len(fake_new_scanned_records), len(fake_prev_portfolio))
        fake_prev_record_date = fake_prev_portfolio[0]["record_date"]
        fake_cur_record_date = fake_prev_record_date + datetime.timedelta(days=1)
        for fake_new_scan_record in fake_new_scanned_records:
            utility.update_record(fake_new_scan_record, "record_date", fake_cur_record_date)
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_cur_record_date,
                                 web_driver=driver)
        # print(returned["portfolio_operations"]["insert"])
        self.assertEqual([], returned["portfolio_operations"]["insert"])
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual(sorted(fake_new_scanned_records, key=operator.itemgetter("symbol", "date_added")),
                         returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])

        # test scenario: new scan happened at a new day, one new record in new day, in additions table #
        # test scenario: new scan happened at a new day, one new record in new day, in additions table #
        fake_prev_portfolio = TestLogicModule.get_fake_prev_scanned_results()
        fake_prev_record_date = fake_prev_portfolio[0]["record_date"]

        # add record date by by one
        fake_new_scanned_records = self.generate_new_records_based_old(fake_prev_portfolio)
        fake_cur_record_date = fake_prev_record_date + datetime.timedelta(days=1)
        for fake_new_scan_record in fake_new_scanned_records:
            utility.update_record(fake_new_scan_record, "record_date", fake_cur_record_date)

        # creat this new record, it would be "additions" table
        one_new_long_position = OrderedDict([('portfolio', 'Black Box Trader'), ('symbol', 'NVDA'),
                                             ('vol_percent', None), ('date_added', fake_cur_record_date),
                                             ('type', 'long'), ('price', 277.35),
                                             ('record_date', fake_cur_record_date)])
        fake_records_by_operation = {
            "scan": fake_new_scanned_records,
            "additions": [one_new_long_position],
            "deletions": []
        }
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_cur_record_date,
                                 web_driver=driver)
        self.assertEqual(1, len(returned["portfolio_operations"]["insert"]),
                         "portfolio_operation.insert should have only one new record.")
        self.assertEqual(0, logic.compare_trade(one_new_long_position, returned["portfolio_operations"]["insert"][0]))
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        cur_portfolio = fake_new_scanned_records[:]
        cur_portfolio.append(one_new_long_position)
        self.assertEqual(sorted(cur_portfolio, key=operator.itemgetter("symbol", "date_added")),
                         returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])

        # test scenario: new scan happened at a new day, one new record in new day, in open portfolio table #
        # test scenario: new scan happened at a new day, one new record in new day, in open portfolio table #
        fake_prev_portfolio = TestLogicModule.get_fake_prev_scanned_results()
        fake_prev_record_date = fake_prev_portfolio[0]["record_date"]

        # add record date by by one
        fake_new_scanned_records = self.generate_new_records_based_old(fake_prev_portfolio)
        fake_cur_record_date = fake_prev_record_date + datetime.timedelta(days=1)
        for fake_new_scan_record in fake_new_scanned_records:
            utility.update_record(fake_new_scan_record, "record_date", fake_cur_record_date)

        # creat this new record, it would be "open portfolio" table
        one_new_long_position = OrderedDict([('portfolio', 'Black Box Trader'), ('symbol', 'NVDA'),
                                             ('vol_percent', None), ('date_added', fake_cur_record_date),
                                             ('type', 'long'), ('price', 277.35),
                                             ('record_date', fake_cur_record_date)])
        fake_new_scanned_records.append(one_new_long_position)
        fake_records_by_operation = {
            "scan": fake_new_scanned_records,
            "additions": [],
            "deletions": []
        }
        print("len(fake_new_scanned_records): {}, len(fake_prev_portfolio): {}".format(
            len(fake_new_scanned_records),
            len(fake_prev_portfolio)
        ))

        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_cur_record_date,
                                 web_driver=driver)
        self.assertEqual(1, len(returned["portfolio_operations"]["insert"]),
                         "portfolio_operation.insert should have only one new record.")
        self.assertEqual(0, logic.compare_trade(one_new_long_position, returned["portfolio_operations"]["insert"][0]))
        self.assertEqual([], returned["portfolio_operations"]["delete"])
        cur_portfolio = fake_new_scanned_records[:]
        self.assertEqual(len(cur_portfolio), len(returned["portfolio_scan"]["insert"]))
        self.assertEqual(sorted(cur_portfolio, key=operator.itemgetter("symbol", "date_added")),
                         returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])

        # test scenario: new scan happened at a new day, one new record in new day, in open portfolio table #
        # and one record in deletions table #
        fake_prev_portfolio = TestLogicModule.get_fake_prev_scanned_results()
        fake_prev_record_date = fake_prev_portfolio[0]["record_date"]

        fake_new_scanned_records = self.generate_new_records_based_old(fake_prev_portfolio)
        fake_cur_record_date = fake_prev_record_date + datetime.timedelta(days=1)
        for fake_new_scan_record in fake_new_scanned_records:
            utility.update_record(fake_new_scan_record, "record_date", fake_cur_record_date)

        # creat this new record, it would be "open portfolio" table
        one_new_long_position = OrderedDict([('portfolio', 'Black Box Trader'), ('symbol', 'NVDA'),
                                             ('vol_percent', None), ('date_added', fake_cur_record_date),
                                             ('type', 'long'), ('price', 277.35),
                                             ('record_date', fake_cur_record_date)])
        fake_new_scanned_records.append(one_new_long_position)
        popped = fake_new_scanned_records.pop(4)
        fake_records_by_operation = {
            "scan": fake_new_scanned_records,
            "additions": [],
            "deletions": [popped]
        }
        print("len(fake_new_scanned_records): {}, len(fake_prev_portfolio): {}".format(
            len(fake_new_scanned_records),
            len(fake_prev_portfolio)
        ))
        returned = logic.process(fake_records_by_operation, fake_prev_portfolio, [], fake_cur_record_date,
                                 web_driver=driver)
        self.assertEqual(1, len(returned["portfolio_operations"]["insert"]),
                         "portfolio_operation.insert should have only one new record.")
        self.assertEqual(0, logic.compare_trade(one_new_long_position, returned["portfolio_operations"]["insert"][0]))
        the_old_one_equal_to_popped = None
        for old_record in fake_prev_portfolio:
            if logic.compare_trade(old_record, popped, True, False) == 0:
                the_old_one_equal_to_popped = old_record
                break
        del the_old_one_equal_to_popped["id"]
        utility.update_record(the_old_one_equal_to_popped, 'type', the_old_one_equal_to_popped["type"] + "_close")
        self.assertEqual(0, logic.compare_trade(
            the_old_one_equal_to_popped, returned["portfolio_operations"]["delete"][0]))
        cur_portfolio = fake_new_scanned_records[:]
        self.assertEqual(len(cur_portfolio), len(returned["portfolio_scan"]["insert"]))
        self.assertEqual(sorted(cur_portfolio, key=operator.itemgetter("symbol", "date_added")),
                         returned["portfolio_scan"]["insert"])
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])

    def test_process02(self):
        """
        after realize that 10/08/2018, TAZR made huge mistake when genrate operations, I decied to write one test
        here.

        For example, I see long_close of SDOW, TZA, SGH,R ,PHM, NVDA, MU, EDU, DIN, BABA in 10/08/2018. But actually
        TAZR only have long_init of SDOW.
        """
        # mysql_helper = self.get_mysql_helper("remotedb.properties")
        # result_holder_temp = []
        #
        # mysql_helper.select_from("portfolio_operations", "zacks_from_ec2",
        #                          col_val_dict={
        #                              "record_date": date(2018, 10, 5),
        #                          },
        #                          callback_on_cursor=TestLogicModule.temp_collector,
        #                          result_holder=result_holder_temp)
        # print(result_holder_temp)

        chrome_option = webdriver.ChromeOptions()
        # invokes headless setter
        chrome_option.headless = True
        chrome_option.add_argument("--window-size=1920x1080")
        driver = webdriver.Chrome(options=chrome_option)
        driver.maximize_window()

        fake_records_by_operation = {
            "scan": self.generate_new_records_based_old(
                TestLogicModule.get_fake_prev_scanned_results02("2018-10-08", "portfolio_scan")),
            "additions": [],
            "deletions": []
        }

        fake_prev_portfolio = TestLogicModule.get_fake_prev_scanned_results02("2018-10-05", "portfolio_scan")
        fake_prev_operations = TestLogicModule.get_fake_prev_scanned_results02("2018-10-05", "portfolio_operations")
        fake_current_scan_date = date(2018, 10, 8)
        returned = logic.process(fake_records_by_operation,
                                 fake_prev_portfolio,
                                 fake_prev_operations,
                                 fake_current_scan_date,
                                 web_driver=driver)
        # self.assertEqual([], returned["portfolio_operations"]["insert"])
        # self.assertEqual([], returned["portfolio_operations"]["delete"])
        self.assertEqual(1, len(returned["portfolio_operations"]["insert"]))
        the_operation_insert = returned["portfolio_operations"]["insert"][0]
        self.assertEqual(0, logic.compare_trade(fake_records_by_operation["scan"][-3], the_operation_insert))
        self.assertEqual(0, len(returned["portfolio_operations"]["delete"]))

        # self.assertEqual([], returned["portfolio_scan"]["insert"])
        for i in range(len(returned["portfolio_scan"]["insert"])):
            self.assertEqual(0, logic.compare_trade(
                fake_records_by_operation["scan"][i],
                returned["portfolio_scan"]["insert"][i]))
        self.assertEqual([], returned["portfolio_scan"]["delete"])
        self.assertEqual([], returned["portfolio_scan"]["update"])

        # simulate current date change
        temp_scanned_records = self.generate_new_records_based_old(
                TestLogicModule.get_fake_prev_scanned_results02("2018-10-08", "portfolio_scan"))
        temp_additions = [temp_scanned_records.pop(10)]
        fake_records_by_operation = {
            "scan": temp_scanned_records,
            "additions": temp_additions,
            "deletions": []
        }
        fake_prev_portfolio = temp_scanned_records
        fake_prev_operations = TestLogicModule.get_fake_prev_scanned_results02("2018-10-05", "portfolio_operations")
        returned = logic.process(fake_records_by_operation,
                                 fake_prev_portfolio,
                                 fake_prev_operations,
                                 fake_current_scan_date,
                                 web_driver=driver)
        self.assertEqual(1, len(returned["portfolio_operations"]["insert"]))
        the_operation_insert = returned["portfolio_operations"]["insert"][0]
        self.assertEqual(0, logic.compare_trade(fake_records_by_operation["additions"][0], the_operation_insert))
        self.assertEqual(0, len(returned["portfolio_operations"]["delete"]))
        self.assertEqual(1, len(returned["portfolio_scan"]["insert"]))

    # noinspection PyMethodMayBeStatic
    def generate_new_records_based_old(self, fake_prev_portfolio: List[dict]):
        fake_new_scanned_records = []
        for prev_record in fake_prev_portfolio:
            fake_new_scan_record = OrderedDict(prev_record)
            del fake_new_scan_record["id"]
            fake_new_scan_record["uniqueness"] = utility.compute_uniqueness_str(
                *[prev_record[key] for key in ['portfolio', 'symbol', 'vol_percent', 'date_added', 'type', 'price',
                                               'record_date']])
            fake_new_scanned_records.append(fake_new_scan_record)
        return fake_new_scanned_records

    # noinspection PyMethodMayBeStatic
    def get_mysql_helper(self, db_prop: str = "database.properties"):
        db_prop_path = os.path.join(constants.main_resources, db_prop)
        utility.get_propdict_file(db_prop_path)
        mysql_helper = mysql_related.MySqlHelper(db_config_dict=utility.get_propdict_file(db_prop_path),
                                                 reuse_connection=False)
        return mysql_helper

    @staticmethod
    def get_fake_prev_scanned_results02(fake_date: str = "2018-10-05", table: str = "portfolio_scan"):
        """
        created for test_process02
        :return:
        """
        if fake_date == '2018-10-05' and table == "portfolio_scan":
            return [
                OrderedDict([('id', 4719), ('portfolio', 'TAZR'), ('symbol', 'BABA'), ('vol_percent', 0.0286),
                             ('date_added', datetime.date(2018, 2, 6)), ('type', 'long'), ('price', 179.0),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', 'bae7475678bd3b7e5790392a05e062cb')]), OrderedDict(
                    [('id', 4720), ('portfolio', 'TAZR'), ('symbol', 'BABA'), ('vol_percent', 0.0686),
                     ('date_added', datetime.date(2018, 9, 18)), ('type', 'long'), ('price', 156.0),
                     ('record_date', datetime.date(2018, 10, 5)), ('uniqueness', '5b359766aa303039a2b1d7f0cad929dc')]),
                OrderedDict([('id', 4721), ('portfolio', 'TAZR'), ('symbol', 'DIN'), ('vol_percent', 0.0943),
                             ('date_added', datetime.date(2018, 9, 13)), ('type', 'long'), ('price', 79.0),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', '1beadf151770b83c19078de7e7c2691f')]), OrderedDict(
                    [('id', 4722), ('portfolio', 'TAZR'), ('symbol', 'EDIT'), ('vol_percent', 0.0528),
                     ('date_added', datetime.date(2018, 8, 7)), ('type', 'long'), ('price', 28.5),
                     ('record_date', datetime.date(2018, 10, 5)), ('uniqueness', '208feafdfc5462c7f3eaa298ba6e8b3b')]),
                OrderedDict([('id', 4723), ('portfolio', 'TAZR'), ('symbol', 'EDIT'), ('vol_percent', 0.0422),
                             ('date_added', datetime.date(2018, 9, 25)), ('type', 'long'), ('price', 32.0),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', 'fdb525dc0b3e4331eb4989e0f3b511e8')]), OrderedDict(
                    [('id', 4724), ('portfolio', 'TAZR'), ('symbol', 'MU'), ('vol_percent', 0.0596),
                     ('date_added', datetime.date(2018, 9, 12)), ('type', 'long'), ('price', 41.74),
                     ('record_date', datetime.date(2018, 10, 5)), ('uniqueness', '2c1e9a077343932bb955e62ca6aff6c7')]),
                OrderedDict([('id', 4725), ('portfolio', 'TAZR'), ('symbol', 'NVDA'), ('vol_percent', 0.0798),
                             ('date_added', datetime.date(2018, 4, 16)), ('type', 'long'), ('price', 231.49),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', 'f401dca15cbbebe8e1d8f5be74411113')]), OrderedDict(
                    [('id', 4726), ('portfolio', 'TAZR'), ('symbol', 'NVDA'), ('vol_percent', 0.0539),
                     ('date_added', datetime.date(2018, 6, 26)), ('type', 'long'), ('price', 242.5),
                     ('record_date', datetime.date(2018, 10, 5)), ('uniqueness', '1ef55181789eb1fa5eaae54b28595a92')]),
                OrderedDict([('id', 4727), ('portfolio', 'TAZR'), ('symbol', 'PHM'), ('vol_percent', 0.0617),
                             ('date_added', datetime.date(2018, 9, 21)), ('type', 'long'), ('price', 26.25),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', '74a6314f33df0499c8d26237dafc83b1')]), OrderedDict(
                    [('id', 4728), ('portfolio', 'TAZR'), ('symbol', 'R'), ('vol_percent', 0.0656),
                     ('date_added', datetime.date(2018, 9, 21)), ('type', 'long'), ('price', 74.5),
                     ('record_date', datetime.date(2018, 10, 5)), ('uniqueness', 'b89af002a267b92c103a97a25d7237fc')]),
                OrderedDict([('id', 4729), ('portfolio', 'TAZR'), ('symbol', 'SGH'), ('vol_percent', 0.0757),
                             ('date_added', datetime.date(2018, 8, 15)), ('type', 'long'), ('price', 29.0),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', '2b8d99cb088cc60a48bf23428e6cea32')]), OrderedDict(
                    [('id', 4730), ('portfolio', 'TAZR'), ('symbol', 'TZA'), ('vol_percent', 0.0558),
                     ('date_added', datetime.date(2018, 9, 6)), ('type', 'long'), ('price', 8.2),
                     ('record_date', datetime.date(2018, 10, 5)), ('uniqueness', 'd50ddff0c9240f1c6ea34cbc55721c37')])]
        elif fake_date == '2018-10-08' and table == "portfolio_scan":
            return [OrderedDict([('id', 4943), ('portfolio', 'TAZR'), ('symbol', 'BABA'), ('vol_percent', 0.0299),
                                 ('date_added', datetime.date(2018, 2, 6)), ('type', 'long'), ('price', 179.0),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', 'cee6db044eadde4d5a0edb08d0a8a1c7')]),
                    OrderedDict(
                        [('id', 4944), ('portfolio', 'TAZR'), ('symbol', 'BABA'), ('vol_percent', 0.0718),
                         ('date_added', datetime.date(2018, 9, 18)), ('type', 'long'), ('price', 156.0),
                         ('record_date', datetime.date(2018, 10, 8)),
                         ('uniqueness', '05870ee141aa5d20bcb7bdd9dd752bdc')]),
                    OrderedDict([('id', 4945), ('portfolio', 'TAZR'), ('symbol', 'DIN'), ('vol_percent', 0.1029),
                                 ('date_added', datetime.date(2018, 9, 13)), ('type', 'long'), ('price', 79.0),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', 'd3378f21f4b77558849588c7dd631fde')]),
                    OrderedDict(
                        [('id', 4946), ('portfolio', 'TAZR'), ('symbol', 'EDIT'), ('vol_percent', 0.0552),
                         ('date_added', datetime.date(2018, 8, 7)), ('type', 'long'), ('price', 28.5),
                         ('record_date', datetime.date(2018, 10, 8)),
                         ('uniqueness', 'dce7e39c5287b75e8ea4b775b72b2728')]),
                    OrderedDict([('id', 4947), ('portfolio', 'TAZR'), ('symbol', 'EDIT'), ('vol_percent', 0.0441),
                                 ('date_added', datetime.date(2018, 9, 25)), ('type', 'long'), ('price', 32.0),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', 'e8459af90754d0c3cfc37c634d1c14ed')]),
                    OrderedDict(
                        [('id', 4948), ('portfolio', 'TAZR'), ('symbol', 'MU'), ('vol_percent', 0.0631),
                         ('date_added', datetime.date(2018, 9, 12)), ('type', 'long'), ('price', 41.74),
                         ('record_date', datetime.date(2018, 10, 8)),
                         ('uniqueness', 'b1d1bb7f99f00a3cd7c84fb944105260')]),
                    OrderedDict([('id', 4949), ('portfolio', 'TAZR'), ('symbol', 'NVDA'), ('vol_percent', 0.0842),
                                 ('date_added', datetime.date(2018, 4, 16)), ('type', 'long'), ('price', 231.49),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', 'cdd74c2b277a8bdaa899351d36c0aa4f')]),
                    OrderedDict(
                        [('id', 4950), ('portfolio', 'TAZR'), ('symbol', 'NVDA'), ('vol_percent', 0.0568),
                         ('date_added', datetime.date(2018, 6, 26)), ('type', 'long'), ('price', 242.5),
                         ('record_date', datetime.date(2018, 10, 8)),
                         ('uniqueness', 'a126916a0cbd099420057f56da293405')]),
                    OrderedDict([('id', 4951), ('portfolio', 'TAZR'), ('symbol', 'PHM'), ('vol_percent', 0.0671),
                                 ('date_added', datetime.date(2018, 9, 21)), ('type', 'long'), ('price', 26.25),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', '3af785094c1ffacb91b28974cd29e7d6')]),
                    OrderedDict(
                        [('id', 4952), ('portfolio', 'TAZR'), ('symbol', 'R'), ('vol_percent', 0.0699),
                         ('date_added', datetime.date(2018, 9, 21)), ('type', 'long'), ('price', 74.5),
                         ('record_date', datetime.date(2018, 10, 8)),
                         ('uniqueness', '79a5cf2d6bc9650cf17dfd11864408b0')]),
                    OrderedDict([('id', 4953), ('portfolio', 'TAZR'), ('symbol', 'SDOW'), ('vol_percent', 0.1016),
                                 ('date_added', datetime.date(2018, 10, 8)), ('type', 'long'), ('price', 14.25),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', '297fc20956adaa3317787a13e1451866')]),
                    OrderedDict(
                        [('id', 4954), ('portfolio', 'TAZR'), ('symbol', 'SGH'), ('vol_percent', 0.073),
                         ('date_added', datetime.date(2018, 8, 15)), ('type', 'long'), ('price', 29.0),
                         ('record_date', datetime.date(2018, 10, 8)),
                         ('uniqueness', '74f744f9b60531577256b899a311e59d')]),
                    OrderedDict([('id', 4955), ('portfolio', 'TAZR'), ('symbol', 'TZA'), ('vol_percent', 0.06),
                                 ('date_added', datetime.date(2018, 9, 6)), ('type', 'long'), ('price', 8.2),
                                 ('record_date', datetime.date(2018, 10, 8)),
                                 ('uniqueness', '6b45fd19d09b8711f39fe4ed67df32e0')])]
        elif table == "portfolio_operations" and fake_date == "2018-10-05":
            return [
                OrderedDict([('id', 653), ('portfolio', 'Momentum Trader'), ('symbol', 'IMXI'), ('vol_percent', 0.1161),
                             ('date_added', datetime.date(2018, 10, 5)), ('type', 'long_init'), ('price', 12.47),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', '93b18624e77ebe8d15d7985aee257255'),
                             ('price_at_close', None)]),
                OrderedDict(
                    [('id', 659), ('portfolio', 'Insider Trader'), ('symbol', 'HPR'), ('vol_percent', 0.0731),
                     ('date_added', datetime.date(2018, 8, 30)), ('type', 'long_close'), ('price', 5.37),
                     ('record_date', datetime.date(2018, 10, 5)),
                     ('uniqueness', '4c178c145ee5963a89938a9f47e8989c'),
                     ('price_at_close', 4.28)]),
                OrderedDict([('id', 660), ('portfolio', 'Insider Trader'), ('symbol', 'LLEX'), ('vol_percent', 0.0782),
                             ('date_added', datetime.date(2018, 8, 30)), ('type', 'long_close'), ('price', 5.34),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', 'cf5e2340f042223e79f4a308fd792af8'),
                             ('price_at_close', 4.54)]),
                OrderedDict(
                    [('id', 662), ('portfolio', 'Value Investor'), ('symbol', 'M'), ('vol_percent', None),
                     ('date_added', datetime.date(2018, 1, 11)), ('type', 'long_close'), ('price', 26.28),
                     ('record_date', datetime.date(2018, 10, 5)),
                     ('uniqueness', 'ab845fd145d7597b0926e5c911dc398f'),
                     ('price_at_close', 32.52)]),
                OrderedDict([('id', 663), ('portfolio', 'Value Investor'), ('symbol', 'TRTN'), ('vol_percent', None),
                             ('date_added', datetime.date(2017, 6, 2)), ('type', 'long_close'), ('price', 29.25),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', '830ec086c9dc491477e5d4d7b0304d75'),
                             ('price_at_close', 32.3)]),
                OrderedDict(
                    [('id', 664), ('portfolio', 'Value Investor'), ('symbol', 'VAC'), ('vol_percent', None),
                     ('date_added', datetime.date(2016, 2, 29)), ('type', 'long_close'), ('price', 60.82),
                     ('record_date', datetime.date(2018, 10, 5)),
                     ('uniqueness', '2c27d2522eaa296f82be3a0c89d20882'),
                     ('price_at_close', 102.02)]),
                OrderedDict([('id', 665), ('portfolio', 'Value Investor'), ('symbol', 'WSM'), ('vol_percent', None),
                             ('date_added', datetime.date(2017, 8, 10)), ('type', 'long_close'), ('price', 45.33),
                             ('record_date', datetime.date(2018, 10, 5)),
                             ('uniqueness', '1ec84b446ee706169af207261b3fb21b'),
                             ('price_at_close', 61.79)])]
        else:
            raise ValueError("illegal fake_date")

    @staticmethod
    def get_fake_prev_scanned_results():
        prev_results = [
            OrderedDict(
                [('id', 2218), ('portfolio', 'Black Box Trader'), ('symbol', 'CI'), ('vol_percent', None),
                 ('date_added', datetime.date(2018, 9, 10)), ('type', 'long'), ('price', 187.63),
                 ('record_date', datetime.date(2018, 9, 28)), ('uniqueness', '854f289819b13558780e18fcfbfcda76')]),
            OrderedDict([('id', 2219), ('portfolio', 'Black Box Trader'), ('symbol', 'AOBC'),
                         ('vol_percent', None), ('date_added', datetime.date(2018, 9, 10)),
                         ('type', 'long'), ('price', 14.84),
                         ('record_date', datetime.date(2018, 9, 28)),
                         ('uniqueness', '09f257f91ad807ab38e1406f4641f544')]),
            OrderedDict(
                [('id', 2220), ('portfolio', 'Black Box Trader'), ('symbol', 'DNOW'), ('vol_percent', None),
                 ('date_added', datetime.date(2018, 9, 17)), ('type', 'long'), ('price', None),
                 ('record_date', datetime.date(2018, 9, 28)), ('uniqueness', 'dabdda9d34b78138354a111750dcc223')]),
            OrderedDict([('id', 2221), ('portfolio', 'Black Box Trader'), ('symbol', 'TLYS'),
                         ('vol_percent', None), ('date_added', datetime.date(2018, 9, 24)),
                         ('type', 'long'), ('price', 18.79),
                         ('record_date', datetime.date(2018, 9, 28)),
                         ('uniqueness', '7739232f045baa8ddeebcaa45130304c')]),
            OrderedDict(
                [('id', 2222), ('portfolio', 'Black Box Trader'), ('symbol', 'ATI'), ('vol_percent', None),
                 ('date_added', datetime.date(2018, 9, 24)), ('type', 'long'), ('price', 29.35),
                 ('record_date', datetime.date(2018, 9, 28)), ('uniqueness', '62c856b037a39be6f5e3d831b4a4a294')]),
            OrderedDict([('id', 2223), ('portfolio', 'Black Box Trader'), ('symbol', 'TJX'),
                         ('vol_percent', None), ('date_added', datetime.date(2018, 9, 4)),
                         ('type', 'long'), ('price', 110.86),
                         ('record_date', datetime.date(2018, 9, 28)),
                         ('uniqueness', '81362410b2d32aaa96759a4a4ccb9591')]),
            OrderedDict(
                [('id', 2224), ('portfolio', 'Black Box Trader'), ('symbol', 'TSCO'), ('vol_percent', None),
                 ('date_added', datetime.date(2018, 9, 4)), ('type', 'long'), ('price', 90.46),
                 ('record_date', datetime.date(2018, 9, 28)), ('uniqueness', '94a07ca28100981c8d58209b5b42c1c5')]),
            OrderedDict([('id', 2225), ('portfolio', 'Black Box Trader'), ('symbol', 'URI'),
                         ('vol_percent', None), ('date_added', datetime.date(2018, 9, 24)),
                         ('type', 'long'), ('price', 168.05),
                         ('record_date', datetime.date(2018, 9, 28)),
                         ('uniqueness', '77b5a0a35d029d401b6888dd178c10a1')]),
            OrderedDict(
                [('id', 2226), ('portfolio', 'Black Box Trader'), ('symbol', 'AFL'), ('vol_percent', None),
                 ('date_added', datetime.date(2018, 9, 24)), ('type', 'long'), ('price', 47.78),
                 ('record_date', datetime.date(2018, 9, 28)), ('uniqueness', '12599cd14b62e56263e356bcc84feda9')]),
            OrderedDict([('id', 2227), ('portfolio', 'Black Box Trader'), ('symbol', 'MOH'),
                         ('vol_percent', None), ('date_added', datetime.date(2018, 9, 24)),
                         ('type', 'long'), ('price', 152.56),
                         ('record_date', datetime.date(2018, 9, 28)),
                         ('uniqueness', '11c98fe31c209c0f7610a00e39615dcb')])]
        return prev_results

    @staticmethod
    def temp_collector(cursor, result_holder: List = None, *args, **kwargs):
        if result_holder is None:
            if len(args) > 0:
                result_holder = args[0]
            else:
                result_holder = kwargs["result_holder"]
        row = cursor.fetchone()
        while row is not None:
            temp_row = row[0] if len(row) == 1 else row
            result_holder.append(OrderedDict([
                ('id', temp_row[0]),
                ('portfolio', temp_row[1]),
                ('symbol', temp_row[2]),
                ('vol_percent', temp_row[3]),
                ('date_added', temp_row[4]),
                ('type', temp_row[5]),
                ('price', temp_row[6]),
                ('record_date', temp_row[7]),
                ('uniqueness', temp_row[8]),
            ]))
            row = cursor.fetchone()
