import unittest
import os.path
from collections import OrderedDict

from webstkdatafetcher.data_connection import mysql_related

from datetime import date

from webstkdatafetcher import utility, constants

import mysql.connector
from mysql.connector import errorcode


class TestMysqlRelatedModule(unittest.TestCase):

    @staticmethod
    def update_record(record, key, value):
        if key not in record:
            raise KeyError("key: " + key + ", is not in record")
        record[key] = value
        record["uniqueness"] = utility.compute_uniqueness_str(
            *[record[key] for key in ['portfolio', 'symbol', 'vol_percent', 'date_added', 'type',
                                      'price', 'record_date']])
        return record

    @unittest.skip("only use this method to quickly operate db")
    def test_add(self):
        target_table = "portfolio_scan"
        db_prop_path = os.path.join(constants.main_resources, "database.properties")
        utility.get_propdict_file(db_prop_path)
        mysql_helper = mysql_related.MySqlHelper(db_config_dict=utility.get_propdict_file(db_prop_path),
                                                 reuse_connection=False)
        col_val_dict = {
            "id": 2228,
            "portfolio": "Counterstrike",
            "symbol": "WTW",
            "vol_percent": 0.0559,
            "date_added": date(2018, 8, 13),
            "type": 'long',
            "price": 75.55,
            "record_date": date(2018, 9, 28)
        }
        TestMysqlRelatedModule.update_record(col_val_dict, "symbol", "WTW")
        mysql_helper.insert_one_record(target_table, None, col_val_dict)
        col_val_dict = {
            "id": 2229,
            "portfolio": "Counterstrike",
            "symbol": "WTW",
            "vol_percent": 0.0559,
            "date_added": date(2018, 8, 20),
            "type": 'long',
            "price": 72.1,
            "record_date": date(2018, 9, 28)
        }
        TestMysqlRelatedModule.update_record(col_val_dict, "symbol", "WTW")
        mysql_helper.insert_one_record(target_table, None, col_val_dict)


    def test_mysql_helper(self):

        target_portfolio = "portfolio_scan"
        db_prop_path = os.path.join(constants.main_resources, "database.properties")
        utility.get_propdict_file(db_prop_path)
        mysql_helper = mysql_related.MySqlHelper(db_config_dict=utility.get_propdict_file(db_prop_path),
                                                 reuse_connection=True)
        values = ["test_portfolio",
                  "TEST",
                  0.034,
                  date(2018, 8, 6),
                  "long",
                  34.43,
                  date.today()]
        col_val_dict = {
            "portfolio": values[0],
            "symbol": values[1],
            "vol_percent": values[2],
            "date_added": values[3],
            "type": values[4],
            "price": values[5],
            "record_date": values[6],
            "uniqueness": utility.compute_uniqueness_str(*values)
        }
        try:
            results = []

            def temp(cursor, *args, **kwarg):
                row = cursor.fetchone()
                if 'result_collect' in kwarg:
                    result_collect = kwarg['result_collect']
                    result_collect.clear()
                    while row is not None:
                        row_as_dcit = OrderedDict([(col_name, row[col_idx])
                                                   for col_idx, col_name in enumerate(cursor.column_names)])
                        result_collect.append(row_as_dcit)
                        row = cursor.fetchone()
                    print("there is/are {} results returned.".format(len(result_collect)))

            mysql_helper.select_from(target_portfolio, callback_on_cursor=temp, result_collect=results)
            initial_num = len(results)
            mysql_helper.insert_one_record(target_portfolio, col_val_dict=col_val_dict)

            mysql_helper.select_from(target_portfolio,
                                     col_val_dict=col_val_dict,
                                     callback_on_cursor=temp,
                                     result_collect=results)
            print(results)
            self.assertEqual(1, len(results))
            tgt_record = results[0]
            prev_id = tgt_record["id"]
            self.assertEqual(results[0]["portfolio"], 'test_portfolio')
            self.assertEqual(results[0]["symbol"], 'TEST')
            self.assertEqual(results[0]["vol_percent"], 0.034)
            self.assertEqual(results[0]["date_added"], date(2018, 8, 6))
            try:
                mysql_helper.insert_one_record(target_portfolio, col_val_dict=col_val_dict)
            except mysql.connector.Error as err:
                if err.errno != errorcode.ER_DUP_ENTRY:
                    raise err
                else:
                    print("Caught excepted error : {}".format(err.msg))

            # now test update
            tgt_record['vol_percent'] = 0.03
            mysql_helper.update_one_record(target_portfolio, col_val_dict=tgt_record)
            mysql_helper.select_from(target_portfolio,
                                     col_val_dict={"id": prev_id},
                                     callback_on_cursor=temp,
                                     result_collect=results)
            self.assertEqual(1, len(results))
            self.assertEqual(results[0]["id"], prev_id)
            self.assertEqual(results[0]["portfolio"], 'test_portfolio')
            self.assertEqual(results[0]["symbol"], 'TEST')
            self.assertEqual(results[0]["vol_percent"], 0.03)
            self.assertEqual(results[0]["date_added"], date(2018, 8, 6))

            mysql_helper.insert_one_record(target_portfolio, col_val_dict=col_val_dict, suppress_duplicate=True)
            col_val_dict['uniqueness'] = {col_val_dict['uniqueness'], 'abc', 'asdfsaw', 'vxcvzxqqwe'}

            del col_val_dict["vol_percent"]
            mysql_helper.delete_from_table(target_portfolio, col_val_dict=col_val_dict)
            mysql_helper.select_from(target_portfolio, callback_on_cursor=temp, result_collect=results)
            self.assertEqual(initial_num, len(results))
        finally:
            mysql_helper.set_reuse_connection(False)
            mysql_helper.execute_update(
                "DELETE FROM {} WHERE symbol = '{}'".format(target_portfolio, values[1])
            )

    def test_select_from_recent(self):
        target_portfolio = "portfolio_scan"
        results = []

        def temp(cursor, *args, **kwarg):
            row = cursor.fetchone()
            if 'result_collect' in kwarg:
                result_collect = kwarg['result_collect']
                result_collect.clear()
                while row is not None:
                    result_collect.append(row)
                    row = cursor.fetchone()
                print("there is/are {} results returned.".format(len(result_collect)))
        mysql_helper = mysql_related.MySqlHelper(reuse_connection=False)
        col_val_dict = {
            "record_date": "(SELECT MAX(record_date) FROM {})".format(target_portfolio),
            "portfolio": "Large-Cap Trader"
        }
        mysql_helper.select_from(target_portfolio,col_val_dict=col_val_dict,
                                 callback_on_cursor=temp, result_collect=results)
        self.assertTrue(len(results) > 0)
        for result in results:
            self.assertEqual('Large-Cap Trader', result[1])
