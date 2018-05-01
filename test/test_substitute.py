import po_dictum as p
import unittest
from translate.storage.pypo import pounit

class TestSubstitutionWorker(unittest.TestCase):

    def setUp(self):
        table = {"datne":"fails", "logs":"lūgs", "ieiet":"ieīt", "atver":"atvar"}
        self.c = p.word_substitute(table)

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

    def test_multiple_found_in_dictionary(self):
        u=pounit()
        u.setsource("The window opens the file")
        u.settarget("Logs atver datne")
        self.c.substitute(u)
        self.assertEqual(u.target,"Lūgs atvar fails")
        self.assertEqual(u.isfuzzy(),False)

    def test_one_found_in_dictionary(self):
        u=pounit()
        u.setsource("The window opens the file")
        u.settarget("Logs atver datni")
        self.c.substitute(u)
        self.assertEqual(u.target,"Lūgs atvar datni")
        self.assertEqual(u.isfuzzy(),True)

    def test_accelerator_same_letter(self):
        u=pounit()
        u.setsource("Win_dow")
        u.settarget("Lo_gs")
        self.c.substitute(u)
        self.assertEqual(u.target,"Lū_gs")

    def test_accelerator_source_letter(self):
        u=pounit()
        u.setsource("Fi_le")
        u.settarget("_Datne")
        self.c.substitute(u)
        self.assertEqual(u.target,"Fai_ls")

    def test_accelerator_first_letter(self):
        u=pounit()
        u.setsource("%s Fil_e")
        u.settarget("%s Datn_e")
        self.c.substitute(u)
        self.assertEqual(u.target,"%s_ Fails")

if __name__ == '__main__':
    unittest.main()
