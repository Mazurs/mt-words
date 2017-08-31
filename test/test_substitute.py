import po_dictum as p
import unittest
from translate.storage.pypo import pounit

class TestWholeSubstitution(unittest.TestCase):

    def setUp(self):
        self.c = p.word_substitute("dummy")
        self.unit = pounit()

    def test_minimal_run(self):
        print(type(self.unit))
        self.unit.setsource("Uuu")
        self.c.substitute(self.unit)

if __name__ == '__main__':
    unittest.main()
