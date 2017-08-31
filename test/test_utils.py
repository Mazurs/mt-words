import po_dictum as p
import unittest

class TestIdentifyType(unittest.TestCase):

    def test_identify_case(self):
        self.assertEqual(p.identify_case('foo'), 'lower')
        self.assertEqual(p.identify_case('FOO'), 'upper')
        self.assertEqual(p.identify_case('Foo'), 'sentence')
        self.assertEqual(p.identify_case('FoO'), 'weird')
        self.assertEqual(p.identify_case(''), 'weird')
        self.assertEqual(p.identify_case('123'), 'weird')
        with self.assertRaises(AttributeError):
            p.identify_case(2)

class TestRestoreCase(unittest.TestCase):

    def test_restore_case(self):
        self.assertEqual(p.restore_case('foo','lower'), 'foo')
        self.assertEqual(p.restore_case('foo','upper'), 'FOO')
        self.assertEqual(p.restore_case('foo','sentence'), 'Foo')
        self.assertEqual(p.restore_case('foo','weird'), 'foo')
        self.assertEqual(p.restore_case('','weird'), '')
        self.assertEqual(p.restore_case('','upper'), '')
        self.assertEqual(p.restore_case('123','upper'), '123')


class TestRemoveAcceleratorFromFragment(unittest.TestCase):

    def test_remove(self):
        self.assertEqual(p.remove_accel('_Sveiks', '_'),('S','Sveiks'))
        self.assertEqual(p.remove_accel('Sveiks', '_'),None)
        self.assertEqual(p.remove_accel('&Sveiks', '&'),('S','Sveiks'))

class TestPlaceAcceleratorIntoFragment(unittest.TestCase):

    def test_place_at_beginning(self):
        self.assertEqual(p.place_accel('Sveiks', 'S', '_'),('_Sveiks'))
        self.assertEqual(p.place_accel('Sveiks', 's', '_'),('_Sveiks'))

    def test_place2(self):
        self.assertEqual(p.place_accel('Sveiks', 'v', '_'),('S_veiks'))

class TestRemoveAcceleratorFromListOfFragments(unittest.TestCase):

    def test_remove_from_a_single_fragment(self):
        l = [p.fragment("_Sveiks")]
        frag_list, acc_char = p.remove_accelerator(l, "_")
        self.assertEqual(frag_list[0].text,"Sveiks")
        self.assertEqual(frag_list[0].found_accelerator,True)
        self.assertEqual(acc_char,"S")

    def test_fail_to_remove_from_a_single_fragment(self):
        l = [p.fragment("Sveiks")]
        frag_list, acc_char = p.remove_accelerator(l, "_")
        self.assertEqual(frag_list[0].text,"Sveiks")
        self.assertEqual(frag_list[0].found_accelerator,False)
        self.assertEqual(acc_char,None)

    def test_remove_from_several_fragments(self):
        l = [p.fragment("Sveiks"),p.fragment("d_raugs")]
        frag_list, acc_char = p.remove_accelerator(l, "_")
        self.assertEqual(frag_list[0].text,"Sveiks")
        self.assertEqual(frag_list[0].found_accelerator,False)
        self.assertEqual(frag_list[1].text,"draugs")
        self.assertEqual(frag_list[1].found_accelerator,True)
        self.assertEqual(acc_char,"r")

    def test_fail_to_remove_from_a_specal_fragment(self):
        l = [p.fragment("_neaiztiec","var")]
        frag_list, acc_char = p.remove_accelerator(l, "_")
        self.assertEqual(frag_list[0].text,"_neaiztiec")
        self.assertEqual(frag_list[0].found_accelerator,False)
        self.assertEqual(acc_char,None)

class TestConvertFragmentsToString(unittest.TestCase):
    def test_empty_fragments_to_empty_string(self):
        self.assertEqual(p.fragments_to_string([]),"")

    def test_trivial_fragment_to_string(self):
        self.assertEqual(p.fragments_to_string([p.fragment("Saule")]),"Saule")

    def test_multiple_fragments_to_string(self):
        self.assertEqual(p.fragments_to_string([p.fragment("Saule"),p.fragment("!!")]),"Saule!!")

class TestExcludeRegExStrings(unittest.TestCase):

    def test_exclude_from_simple_string(self):
        #p.exclude(original, exclude, flag)
        #print (p.exclude("a,b,c", ",", "scrap") )
        print (p.excl("a,b,c", ",", "scrap") )

if __name__ == '__main__':
    unittest.main()
