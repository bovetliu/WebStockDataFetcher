import hashlib
import math
from collections import OrderedDict
from datetime import date, datetime


def get_content_of_file(path: str):
    with open(path, 'r') as file:
        lines = file.readlines()
        return ''.join(lines)


def get_propdict_file(path: str):
    tbr = {}
    with open(path, 'r') as credential_file:
        for line in credential_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line_splits = line.split("=")
            if len(line_splits) != 2:
                raise ValueError(line + " could not split into key and value")
            tbr[line_splits[0]] = line_splits[1]
    return tbr


def compute_uniqueness_str(*args):
    str_list = []
    for ar in args:
        if isinstance(ar, list) or isinstance(ar, set):
            raise TypeError("probably did not add \"*\" when supplying list as argument")
        if isinstance(ar, str):
            str_list.append(ar)
        elif isinstance(ar, float):
            str_list.append("{0:.5f}".format(ar))
        elif isinstance(ar, date):
            str_list.append(ar.strftime("%y-%m-%d"))
        elif ar is None:
            str_list.append("None")
        else:
            raise ValueError("{} is not supported type {}", ar, type(ar))

    to_be_hashed = '\n'.join(str_list)
    hash_object = hashlib.md5(to_be_hashed.encode())
    return hash_object.hexdigest()


def null_safe_number_compare(num1, num2, threshold: float = 0.001):
    if num1 is None and num2 is None:
        return 0
    if num1 is None:
        return -1
    elif num2 is None:
        return 1
    if math.isclose(num1, num2, abs_tol=threshold):
        return 0
    return (num1 > num2) - (num1 < num2)


def remove_operation_suffix(record: dict):
    if not isinstance(record, OrderedDict):
        raise TypeError("record is not OrderedDict type")
    tbr = OrderedDict(record)
    type_val = tbr['type']
    type_val = type_val.replace('_init', '')
    type_val = type_val.replace('_close', '')
    tbr['type'] = type_val
    return tbr
