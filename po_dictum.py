import re
import string
from translate.storage import factory
from translate.convert import convert
from libs.dictionary import dictionary

# List of elements, that contains untranslatable strings
escapeables = [
    '<.*?>', # Tags
    '%[diuoxXfFeEgGaAcspn]', # C style variables, simple
    '%\([word]*\)[diuoxXfFeEgGaAcspn]', # C style variables, named
    '%[0-9]\$[diuoxXfFeEgGaAcspn]', # C style variables, positions indicated
    '&[\w|\.]*;', # Mozilla style variables
    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', # URLs
    '\s&\s', # Mozilla style "and" replacement. FIXME Dubious.
]

class fragment:
    """Container for string fragments.
    Attributes:
        text: fragment of translation text
        flag:   status of the text, possible values:
            word - translateable word
            pending - potentially translateable word
            tag - untranslatable tag name or attribute
            var - untranslatable variable
            exist - untranslatable, because exists
            scrap - untranslatable non-letter characters
            other
    """
    def __init__(self,text,flag="pending"):

        assert flag in ["word", "pending", "tag", "var", "exist", "scrap", "other"]

        self.text = text
        self.flag = flag
        self.found_accelerator = False

    def __repr__(self):
        return str("'"+self.text+"':"+self.flag)

class word_substitute:
    """Worker that does dictionary replacement"""

    def __init__ (self, dictionary_file, project = "GNOME", missing=None):
        self.dictionary_file = dictionary_file
        self.table = dictionary (dictionary_file)
        self.project = project # TODO later extract behaviour

    def substitute (self, unit):
        source = unit.getsource()
        target = unit.gettarget()

        # Cut out undesirables FIXME take project into consideration

        source_fragments = exclude (source, escapeables, "other")
        target_fragments = exclude (target, escapeables, "other")

        source_fragments, source_accl = remove_accelerator(source_fragments, "_") #FIXME hardcode
        target_fragments, target_accl = remove_accelerator(target_fragments, "_")

        # Strip out words

        source_fragments = exclude (source_fragments, '[^\W_0-9]+', "word")
        target_fragments = exclude (target_fragments, '[^\W_0-9]+', "word")

        mark_duplicates(source_fragments, target_fragments)

        fuzzy = replace_words(target_fragments, self.table)
        if fuzzy: unit.markfuzzy()

        restore_accelerator(target_fragments, source_accl, target_accl, "_")

        # Collapse
        unit.settarget( fragments_to_string(target_fragments) )

        return unit

    def convertstore(self, fromstore):
        tostore = type(fromstore)()
        for unit in fromstore.units:
            if not unit.istranslatable():
                continue
            # Skip translator credits TODO puti in fn
            if unit.getsource() == "translator-credits":
                continue
            if unit.getsource() == "Your names" and unit.getcontext() == "NAME OF TRANSLATORS":
                continue
            if unit.getsource() == "Your emails" and unit.getcontext() == "EMAIL OF TRANSLATORS":
                continue
            if unit.getsource() == "":
                continue
            newunit = unit # FIXME wuy?
            newunit = self.substitute(newunit)
            tostore.addunit(newunit)

        self.table.dump_all("new_dict.csv")

        return tostore

def exclude (original, matching_regex, flag):
    if type(original) is str:
        given = [fragment(original)]
    elif type (original) is list:
        given = original

    if type(matching_regex) is not list:
        matching_regex = [matching_regex]

    # New compile
    for reg in matching_regex:
        compiled = re.compile(reg)
        derivative = []

        for index, frag in enumerate(given):
            if frag.flag != "pending":
                derivative.append(frag)
                continue
            subfragments = []
            start = 0
            for pattern in compiled.finditer(frag.text):
                pattern_end = pattern.start() + len(pattern.group())
                subfragments.append( fragment( frag.text[start:pattern.start()], "pending" ) )
                subfragments.append( fragment( frag.text[pattern.start():pattern_end], flag) )
                start = pattern_end
            subfragments.append(fragment( frag.text[start:len(frag.text)]))
            derivative += subfragments
        given = derivative
    return derivative

def remove_accelerator(source_fragments, accelerator):
    source_char = None
    for f in source_fragments:
        if f.flag == "pending":
            response = remove_accel (f.text, accelerator)
            if (response == None): continue
            source_char, text = response
            f.text = text
            f.found_accelerator = True
            break
    return source_fragments, source_char

def mark_duplicates(source_fragments, target_fragments):
    for t in target_fragments:
        if t.flag == "word":
            for s in source_fragments:
                if s.flag == "word" and s.text == t.text:
                    t.flag = "exist"

def replace_words(target_fragments, translations):
    fuzzy = False
    for t in target_fragments:
        if t.flag == "word":
            word_type = identify_case(t.text)
            response = translations.find(t.text.lower())
            if not response:
                translations.add(t.text.lower())
                fuzzy = True
                continue
            translation, needs_review = response
            t.text = restore_case(translation,word_type)
            if needs_review:
                fuzzy = True
    return fuzzy

def restore_accelerator(target_fragments, target_accl, source_accl, accel):
    if target_accl == None or source_accl == None:
        return
    found = False
    for t in target_fragments:
        if t.flag in ["word", "pending", "exist"]:
            replacement = place_accel(t.text, target_accl, accel)
            if replacement:
                t.text = replacement
                found = True
                break
    if not found:
        for t in target_fragments:
            if t.flag in ["word", "pending", "exist"]:
                replacement = place_accel(t.text, source_accl, accel)
                if replacement:
                    t.text = replacement
                    found = True
                    break
    if not found:
        for t in target_fragments:
            if t.flag in ["word", "pending", "exist"] and t.text:
                t.text = accel + t.text
                break


def remove_accel(text, accelerator):
    pos = text.find(accelerator)
    if pos != -1:
        accel_char = text[pos+1] #storing accelerator char
        return accel_char, text[:pos] + text[pos+1:] #FIXME might fail if accel is last

def place_accel(text, accelerator, symbol):
    acc_pos = text.lower().find(accelerator.lower())
    if acc_pos != -1:
        return text[:acc_pos] + symbol + text[acc_pos:]
    else:
        return None

def identify_case(word):
    if word.islower():
        return 'lower'
    if word.isupper():
        return 'upper'
    if word.istitle():
        return 'sentence'
    return 'weird'

def restore_case(word, s_type):
    # string should be in lowercase
    if s_type == 'lower':
        return word
    if s_type == 'upper':
        return word.upper()
    if s_type == 'sentence':
        return word[0:1].upper() + word[1:]
    # Case with 'weird' capitalization is omitted
    return word

# FIXME this is a member function for framgment class
def fragments_to_string(fragments):
    output = str()
    for f in fragments:
        output += f.text
    return output

def mtfile(inputfile, outputfile, templatefile, dictionary_file):
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty():
        return 0
    convertor = word_substitute(dictionary_file)
    outputstore = convertor.convertstore(inputstore)
    outputstore.serialize(outputfile)
    return 1


def main():
    formats = {"po": ("po", mtfile), "xlf": ("xlf", mtfile), "tmx": ("tmx", mtfile)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.add_option("-d", "--dictionary", dest="dictionary_file",
                      help="Dictionary file. Record format: key<comma>translation<newline>")
    parser.passthrough.append("dictionary_file")
    parser.run()

if __name__ == '__main__':
    main()
