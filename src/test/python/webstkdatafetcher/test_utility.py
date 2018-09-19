import unittest
from webstkdatafetcher import utility
from webstkdatafetcher import constants
from os.path import join


class TestUtility(unittest.TestCase):

    def test_get_content_of_file(self):
        sample_email_01_path = join(constants.test_resources, "sample_email01.html")
        file_content = utility.get_content_of_file(sample_email_01_path)
        self.assertTrue(file_content.startswith('<div data-test-id="message-body-container">'))
        self.assertTrue(file_content.endswith('</div>'))
