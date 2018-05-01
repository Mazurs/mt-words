import po_dictum as p
import unittest
from translate.storage.pypo import pounit

class TestSubstitutionWorker(unittest.TestCase):

    def setUp(self):
        table = {"datne":"fails", "logs":"lūgs", "ieiet":"ieīt"}
        self.c = p.word_substitute(table)
        print (self.c.table)
        self.unit = pounit()

    def test_empty(self):
        u=pounit()
        self.c.substitute(u)
        self.assertEqual(u.target,"")

    def test_untranslated(self):
        u=pounit()
        u.setsource("Some string")
        u.settarget("") # untranslated
        self.c.substitute(u)
        self.assertEqual(u.target,"")

    def test_garbage(self):
        u=pounit()
        u.setsource("... ?")
        u.settarget("... ?")
        self.c.substitute(u)
        self.assertEqual(u.target,"... ?")

    def test_abbreviation(self):
        u=pounit()
        u.setsource("VHS")
        u.settarget("VHS")
        self.c.substitute(u)
        self.assertEqual(u.target,"VHS")
        self.assertEqual(u.isfuzzy(),False)

    def test_found_in_dictionary(self):
        u=pounit()
        u.setsource("file")
        u.settarget("datne")
        self.c.substitute(u)
        self.assertEqual(u.target,"fails")
        self.assertEqual(u.isfuzzy(),False)

    def test_missing_in_dictionary(self):
        u=pounit()
        u.setsource("Absinthe")
        u.settarget("Absints")
        self.c.substitute(u)
        self.assertEqual(u.target,"Absints")
        self.assertEqual(u.isfuzzy(),True)

if __name__ == '__main__':
    unittest.main()
