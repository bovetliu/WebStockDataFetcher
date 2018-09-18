import unittest
from webstkdatafetcher.data_connection import mysql_related

from datetime import date, datetime

from webstkdatafetcher import utility

import mysql.connector
from mysql.connector import errorcode


class TestMysqlRelatedModule(unittest.TestCase):

    def test_mysql_helper(self):

        target_portfolio = "portfolio_scan"
        mysql_helper = mysql_related.MySqlHelper(reuse_connection=True)
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
                        result_collect.append(row)
                        row = cursor.fetchone()
                    print("there is/are {} results returned.".format(len(result_collect)))

            mysql_helper.select(target_portfolio, callback_on_cursor=temp, result_collect=results)
            initial_num = len(results)
            mysql_helper.insert_one_record(target_portfolio, col_val_dict=col_val_dict)

            mysql_helper.select(target_portfolio,
                                col_val_dict=col_val_dict,
                                callback_on_cursor=temp,
                                result_collect=results)
            print(results)
            self.assertEqual(1, len(results))

            try:
                mysql_helper.insert_one_record(target_portfolio, col_val_dict=col_val_dict)
            except mysql.connector.Error as err:
                if err.errno != errorcode.ER_DUP_ENTRY:
                    raise err
                else:
                    print("Caught excepted error : {}".format(err.msg))
            mysql_helper.insert_one_record(target_portfolio, col_val_dict=col_val_dict, suppress_duplicate=True)
            mysql_helper.delete_table(target_portfolio, col_val_dict=col_val_dict)
            mysql_helper.select(target_portfolio, callback_on_cursor=temp, result_collect=results)
            self.assertEqual(initial_num, len(results))
        finally:
            mysql_helper.set_reuse_connection(False)
            mysql_helper.execute_update(
                "DELETE FROM {} WHERE symbol = '{}'".format(target_portfolio, values[1])
            )
