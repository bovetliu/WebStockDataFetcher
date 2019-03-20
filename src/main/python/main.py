from webstkdatafetcher import logic
from webstkdatafetcher import constants
from webstkdatafetcher import utility
from webstkdatafetcher import yahoo_fin_statistics
from webstkdatafetcher.data_connection import mysql_related
from os.path import join
import logging
import sys


if __name__ == "__main__":

    log_file_path = join(constants.main_resources, "web_stock_data_fetcher.log")
    logging.basicConfig(format='%(asctime)s %(levelname)-7s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%d-%m-%Y:%H:%M:%S',
                        level=logging.INFO,
                        stream=sys.stdout)

    # execute only if run as a script
    if len(sys.argv) > 3:
        print("usage: python3 src/main/python/main.py <usage> <optional_database_name: default zacks>")
        print("acceptable <usage>: scrapezacks, scrapezacks_to_remote, yahoo_statistics yahoo_statistics_to_remote")
        print("acceptable <database_name>: any valid MySQL database name")
        exit(1)
    non_default_db_name = None
    if len(sys.argv) == 3:
        non_default_db_name = sys.argv[2]
        logging.info("non_default_db_name: {}".format(non_default_db_name))
    usecase = sys.argv[1]
    logging.info("usecase: {}".format(usecase))

    if usecase.endswith("_remote"):
        db_config_path = join(constants.main_resources, "remotedb.properties")
    else:
        db_config_path = join(constants.main_resources, "database.properties")
    db_config_dict = utility.get_propdict_file(db_config_path)
    if non_default_db_name:
        db_config_dict["database"] = non_default_db_name

    # if use case is any of ["scrapezacks", "scrapezacks_to_remote", "deduplicate", "db_initialize"],
    # execute db_initialization.sql on target database.
    if usecase in ['scrapezacks',
                   'scrapezacks_to_remote',
                   'db_initialize',
                   'yahoo_statistics',
                   'yahoo_statistics_to_remote']:
        db_initialization_str = utility.get_content_of_file(join(constants.main_resources, "db_initialization.sql"))
        if non_default_db_name:
            db_initialization_str = db_initialization_str.replace("zacks", non_default_db_name)
        db_initialization_statements = db_initialization_str.split(";")
        mysql_helper = mysql_related.MySqlHelper(db_config_dict=db_config_dict)
        for stmt in db_initialization_statements:
            stmt = stmt.strip()
            if stmt:
                mysql_helper.execute_update(stmt, multi=True)

    # if use case is one of ["scrapezacks", "scrapezacks_to_remote"], use chrome driver to execute script.
    if usecase.startswith('scrapezacks'):
        logic.selenium_chrome(clear_previous_content=True,
                              headless=True,
                              db_config_dict=db_config_dict)
    elif usecase.startswith("deduplicate"):
        mysql_helper = mysql_related.MySqlHelper(db_config_dict=db_config_dict)
        logic.deduplicate(mysql_helper)
    elif usecase.startswith('yahoo_statistics'):
        yahoo_fin_statistics.start_scraping_yahoo_fin_statistics(None, True, db_config_dict, "sp500")
    elif usecase == 'db_initialize':
        pass
    else:
        print("usage: python3 src/main/python/main.py <usage> <optional_database_name: default zacks>")
        print("acceptable <usage>: scrapezacks, scrapezacks_to_remote, yahoo_statistics, yahoo_statistics_to_remote")
        print("acceptable <database_name>: any valid MySQL database name")
