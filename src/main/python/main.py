from webstkdatafetcher import logic
from webstkdatafetcher import constants
from os.path import join
import sys

if __name__ == "__main__":
    # execute only if run as a script
    if len(sys.argv) == 2 and sys.argv[1] == 'example01':
        logic.selenium_chrome(join(constants.project_root, "data", "record2.txt"), clear_previous_content=True)
    else:
        print("usage: python3 src/main/python/main.py example01")
