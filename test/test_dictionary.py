from libs.dictionary import dictionary
import unittest
import os

class dict_test(unittest.TestCase):

    def setUp(self):
        self.empty_dict = "test/new_words_sample.xml"
        self.dic = dictionary("test/dictionary_sample.xml")

    def tearDown(self):
        if os.access(self.empty_dict, os.F_OK):
            os.remove(self.empty_dict)

    def test_read(self):
        self.assertGreater(len(self.dic.dictionary), 0)
        print(self.dic.dictionary)
        
    def test_find(self):
        self.assertEqual(self.dic.find('abhāzu'), ('abhazu', False))
        self.assertEqual(self.dic.find('abos'), ('obejūs', False))
        self.assertEqual(self.dic.find('zebra'), None)
             
    def test_find_all(self):
        self.assertEqual(self.dic.find_all('abos'), ['obūs', 'obejūs'])		
        
    def test_add(self):
        self.dic.add('maize')
        self.assertEqual(self.dic.new, {'maize'})
        
    def test_dump(self):
        self.dic.add('maize')
        self.dic.dump_untranslated(self.empty_dict)
        self.new_from_file = dictionary(self.empty_dict)
        self.assertEqual(self.new_from_file.dictionary, {'maize': [{'review': False, 'target': ''}]})
    

if __name__ == '__main__':
    unittest.main()
