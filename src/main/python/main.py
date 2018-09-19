from webstkdatafetcher import logic
from webstkdatafetcher import constants
from webstkdatafetcher import utility
from os.path import join
import sys

if __name__ == "__main__":
    # execute only if run as a script
    if len(sys.argv) != 2:
        print("usage: python3 src/main/python/main.py example01")
        exit(1)
    usecase = sys.argv[1]
    if  usecase == 'example01':
        # data/record_momenturm.txt
        output_file_path = join(constants.project_root, "data", "record_momentum.txt")
        logic.selenium_chrome(output_file_path, clear_previous_content=True)
    elif usecase == 'email_content01':
        email01_path = join(constants.test_resources, 'sample_email01.html')
        logic.handle_zacks_email(utility.get_content_of_file(email01_path))
    else:
        print("usage: python3 src/main/python/main.py <usage>")
        print("acceptable usage: example01, email_content01")
