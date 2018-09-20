import unittest
from datetime import date
from webstkdatafetcher import logic


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
