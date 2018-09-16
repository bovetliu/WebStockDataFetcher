import os
from os.path import dirname

chrome_log_path = "/home/boweiliu/workrepo/WebStockDataFetcher/src/test/resources/chrome.log"
project_root = dirname(dirname(dirname(dirname(dirname(os.path.realpath(__file__))))))
credentials_path = os.path.join(project_root, "credentials")
