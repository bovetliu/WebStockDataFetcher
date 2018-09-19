from webstkdatafetcher import logic
from webstkdatafetcher import constants
from webstkdatafetcher import utility
from os.path import join
import sys

if __name__ == "__main__":
    # execute only if run as a script
    if len(sys.argv) != 2:
        print("usage: python3 src/main/python/main.py <usage>")
        print("acceptable usage: scrapezacks, email_content01")
        exit(1)
    usecase = sys.argv[1]
    print("usecase: {}".format(usecase))
    if usecase == 'scrapezacks':
        db_config_path = join(constants.main_resources, "database.properties")
        logic.selenium_chrome(clear_previous_content=True,
                              headless=True,
                              db_config_dict=utility.get_propdict_file(db_config_path))
    elif usecase == 'scrapezacks_to_remote':
        db_config_path = join(constants.main_resources, "remotedb.properties")
        logic.selenium_chrome(clear_previous_content=True,
                              headless=True,
                              db_config_dict=utility.get_propdict_file(db_config_path))
    elif usecase == 'email_content01':
        email01_path = join(constants.test_resources, 'sample_email01.html')
        logic.handle_zacks_email(utility.get_content_of_file(email01_path))
    else:
        print("usage: python3 src/main/python/main.py <usage>")
        print("acceptable usage: scrapezacks, email_content01")
