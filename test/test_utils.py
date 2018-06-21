import po_dictum as p
import unittest
from libs.dictionary import dictionary

class TestIdentifyType(unittest.TestCase):

    def test_identify_case(self):
        self.assertEqual(p.identify_case('foo'), 'lower')
        self.assertEqual(p.identify_case('FOO'), 'upper')
        self.assertEqual(p.identify_case('Foo'), 'sentence')
        self.assertEqual(p.identify_case('FoO'), 'weird')
        # Should survive silly input
        self.assertEqual(p.identify_case(''), 'weird')
        self.assertEqual(p.identify_case('123'), 'weird')
        with self.assertRaises(AttributeError):
            p.identify_case(2)

class TestRestoreCase(unittest.TestCase):

    def test_restore_case(self):
        self.assertEqual(p.restore_case('foo','lower'), 'foo')
        self.assertEqual(p.restore_case('foo','upper'), 'FOO')
        self.assertEqual(p.restore_case('foo','sentence'), 'Foo')
        self.assertEqual(p.restore_case('FoO','weird'), 'FoO')
        # Should survive silly input
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

    def test_place_in_middle(self):
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
        l = [p.fragment("_neaiztiec","literal")]
        frag_list, acc_char = p.remove_accelerator(l, "_")
        self.assertEqual(frag_list[0].text,"_neaiztiec")
        self.assertEqual(frag_list[0].found_accelerator,False)
        self.assertEqual(acc_char,None)

class TestMarkDuplicateFragmentsAsDuplicates(unittest.TestCase):

    def test_empty_fragments(self):
        source = [p.fragment("Sveiki","word")]
        target = []
        p.mark_duplicates(source, target)
        self.assertEqual(source[0].flag,"word")
        self.assertEqual(target,[])

    def test_duplicates(self):
        source = [p.fragment("sveiki","word"),p.fragment("āraiši","word")]
        target = [p.fragment("āraiši","word"),p.fragment("uzvar","word")]
        p.mark_duplicates(source, target)
        self.assertEqual(target[0].flag,"exist")

class TestWordReplacement(unittest.TestCase):

    # def __init__(self, *args, **kwargs):
        # self.table = {
        #     "datne":[{transl:"fails",is_problematic:True},],
        #     "logs":[{transl:"lūgs",is_problematic:Flase}],
        #     "ieiet":[
        #         {transl:"eeeet",is_problematic:False,prevalence:1},
        #         {transl:"ieīt",is_problematic:False,prevalence:10},
        #     ]
        # }
    def setUp(self):
        #self.table = {"datne":"fails", "logs":"lūgs", "ieiet":"ieīt"}
        self.table = dictionary('test/dictionary_sample.csv')

    def test_replace_fragments_success(self):
        f = [p.fragment("Logs","word"), p.fragment(" "), p.fragment("ieiet","word")]
        fuzzy = p.replace_words(f, self.table)
        self.assertEqual(f[0].text,"Lūgs")
        self.assertEqual(fuzzy,False)

    def test_replace_fragments_fails(self):
        f = [p.fragment("Kalks","word"), p.fragment(" "), p.fragment("ieiet","word")]
        fuzzy = p.replace_words(f, self.table)
        self.assertEqual(f[0].text,"Kalks")
        self.assertEqual(fuzzy,True)

class TestRestoreAccelerator(unittest.TestCase):

    def test_accel_to_target(self):
        t = [p.fragment("Sveiks","word")]
        p.restore_accelerator(t, "H", "v", "_")
        self.assertEqual(t[0].text,"S_veiks")

    def test_accel_to_source(self):
        t = [p.fragment("Sveiks","exist")]
        p.restore_accelerator(t, "E", "M", "_")
        self.assertEqual(t[0].text,"Sv_eiks")

    def test_accel_to_beginning(self):
        t = [p.fragment("Sveiks","pending")]
        p.restore_accelerator(t, "X", "M", "_")
        self.assertEqual(t[0].text,"_Sveiks")

class TestConvertFragmentsToString(unittest.TestCase):

    def test_empty_fragments_to_empty_string(self):
        self.assertEqual(p.fragments_to_string([]),"")

    def test_trivial_fragment_to_string(self):
        self.assertEqual(p.fragments_to_string([p.fragment("Saule")]),"Saule")

    def test_multiple_fragments_to_string(self):
        self.assertEqual(p.fragments_to_string([p.fragment("Saule"),p.fragment("!!")]),"Saule!!")

class TestExcludeRegExStrings(unittest.TestCase):

    def NO_test_exclude_from_simple_string(self):
        print("")
        print(p.exclude("Wērd1","\w+",          "word"))
        print(p.exclude("Wērd1","[^\W_0-9]+"   ,"word"))
        #p.exclude(original, exclude, flag)
        #print (p.exclude("a,b,c", ",", "scrap") )
        #print (p.excl("a,b,c", ",", "scrap") )

class TestExcludeAllTheThings(unittest.TestCase):

    def NO_test_null(self):
        f = p.exclude(" %1$ lls ", "%(\d\$)?['\-+ #0]?(ll|l)?[sS]", "literal")
        #print (f)

    def test_exclude_simple_c_variable(self):
        msg = "Simple %s string"
        f = p.exclude(msg, p.get_escapeables(flags="c-format"), "literal")
        self.assertEqual(len(f),3)
        self.assertEqual(f[1].text,"%s")

    def test_exclude_flagged_c_variable(self):
        msg = "Complex % 'llu string"
        f = p.exclude(msg, p.get_escapeables(flags="c-format"), "literal")
        self.assertEqual(len(f),3)
        self.assertEqual(f[1].text,"% 'llu")

if __name__ == '__main__':
    unittest.main()
