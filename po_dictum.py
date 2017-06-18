import re
import string

#from libs.dictionary import dictionary
from libs import dictionary

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
# FIXME what is dis?"<*>"
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
        self.new_text = "" # FIXME is this real?
        self.found_accelerator = False

class word_substitute:
    """Worker that does dictionary replacement"""

    def __init__ (self, dictionary_file, project = "GNOME", missing=None):
        #self.table = dictionary (dictionary_file)
        self.table = {"tips":[{"tranlsation":"taps"}]}
        # TODO implement missing word list
        self.project = project # TODO later extract behaviour

    def substitute (self, unit):
        source = unit.getsource()
        target = unit.gettarget()

        # Cut out undesirables FIXME take project into consideration

        source_fragments = exclude (source, escapeables, "other")
        target_fragments = exclude (target, escapeables, "other")

        # Remove accelerator

        source_fragments, source_accl = remove_accelerator(source_fragments, "_") #FIXME hardcode
        target_fragments, target_accl = remove_accelerator(target_fragments, "_")

        # Strip out words

        source_fragments = exclude (source_fragments, '[\W]', "word")
        target_fragments = exclude (target_fragments, '[\W]', "word")

        # Mark duplicates

        for t in target_fragments:
            if t.flag == "word":
                for s in source_fragments:
                    if s.flag == "word" and s.text == t.text:
                        t.flag = "exist"

        # Replace words

        for t in target_fragments:
            if t.flag == "word":
                word_type = identify_case(t.text)
                translation = self.table.find(t.text.lower())
                if translation:
                    t.text = translation
                else:
                    unit.markfuzzy()

        # Put back accelerator FIXME is this really an improvement?

        found = False
        for t in target_fragments:
            if t.flag in ["word", "pending", "exist"]:
                replacement = place_accelerator(t.text, target_char, "_")
                if replacement:
                    t.text = replacement
                    found = True
                    break
        if not found:
            for t in target_fragments:
                if t.flag in ["word", "pending", "exist"]:
                    replacement = place_accelerator(t.text, source_char, "_")
                    if replacement:
                        t.text = replacement
                        found = True
                        break
        if not found:
            for t in target_fragments:
                if t.flag in ["word", "pending", "exist"]:
                    t.text = "_" + t.text
                    break

        # Collapse

        output = ""
        for t in target_fragments:
            output += t.text
        unit.settarget(output)

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
        #append new words in dictionary file
        # f = codecs.open('dictionary_new', encoding = 'utf-8', mode='w')
        # for key in sorted(self.dictionary.iterkeys()):
        #     f.write(key + " " + self.dictionary[key] + u"\n")
        # for item in self.new_words:
        #     f.write(item + " " + u"\n")
        # f.close()
        return tostore

def exclude (original, exclude, flag):
    if type(original) is str:
        given = [fragment(original)]
    elif type (original) is list:
        given = original
    else:
        given = [original]

    if type(exclude) is not list:
        exclude = [exclude]
    #print(source_fragment.text)

    # New compile
    for reg in escapeables:
        compiled = re.compile(reg)
        derivative = []

        for i in given: print (i.text)

        for index, fragment in enumerate(given):
            if fragment.flag != "pending":
                derivative.append(fragment)
                continue
            subfragments = []
            start = 0
            for pattern in compiled.finditer(fragment.text):
                pattern_end = pattern.start() + len(pattern.group())
                subfragments.append( fragment( fragment.text[start:pattern.start()], "pending" ) )
                subfragments.append( fragment( fragment.text[pattern.start():pattern_end], flag) )
                start = pattern_end
            subfragments.append(fragment( fragment.text[start:len(fragment.text)]))
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

def mtfile(inputfile, outputfile, templatefile, dictionary):
    from translate.storage import factory
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty(): #FIXME this check should not be necessary
        return 0
    convertor = word_substitute(dictionary)
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return 1


def main():
    from translate.convert import convert
    formats = {"po": ("po", mtfile), "xlf": ("xlf", mtfile), "tmx": ("tmx", mtfile)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.add_option("-d", "--dictionary", dest="dictionary",
                      help="Dictionary file. Record format: key<tab>translation<newline>")
    parser.passthrough.append("dictionary")
    parser.run()

if __name__ == '__main__':
    main()
