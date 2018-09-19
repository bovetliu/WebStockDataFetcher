import hashlib
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
            if not line:
                continue
            line_splits = line.split("=")
            if len(line_splits) != 2:
                raise ValueError(line + " could not split into key and value")
            tbr[line_splits[0]] = line_splits[1]
    return tbr


def compute_uniqueness_str(*args):
    str_list = []
    for ar in args:
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