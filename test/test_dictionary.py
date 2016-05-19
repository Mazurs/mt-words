from libs.dictionary import dictionary
import unittest
import os

class dict_test(unittest.TestCase):

    def setUp(self):
        self.empty_dict = "empty_dictionary.xml"
        self.dic = dictionary("dict.xml")

    def tearDown(self):
        if os.access(self.empty_dict, os.F_OK):
            os.remove(self.empty_dict)

    def test_read(self):
        print len (self.dic.dictionary)

if __name__ == '__main__':
    unittest.main()
