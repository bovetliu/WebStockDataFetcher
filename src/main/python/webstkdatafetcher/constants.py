import os
from os.path import dirname

chrome_log_path = "/home/boweiliu/workrepo/WebStockDataFetcher/src/test/resources/chrome.log"
project_root = dirname(dirname(dirname(dirname(dirname(os.path.realpath(__file__))))))
main_resources = os.path.join(project_root, "src", "main", "resources")
test_resources = os.path.join(project_root, "src", "test", "resources")
credentials_path = os.path.join(project_root, "credentials")
default_db_prop_path = os.path.join(main_resources, "database.properties")
