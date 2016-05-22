import re
import string

from libs.dictionary import dictionary

escapeables = [
	'<.*?>',
	'%[diuoxXfFeEgGaAcspn]',
	'%\([word]*\)[diuoxXfFeEgGaAcspn]',
	'%[0-9]\$[diuoxXfFeEgGaAcspn]',
	'&[\w|\.]*;',
	'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    '\s&\s',
]
"<*>"
class text_fragment:
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

def flow (unit, dictionary_file, project = "GNOME"):
    table = dictionary (dictionary_file)
    source = unit.getsource()
    target = unit.gettarget()

    # Cut out undesirables

    source_fragments = exclude (source, escapeables, "other")
    target_fragments = exclude (target, escapeables, "other")

    # Remove accelerator

    source_char = None
    for f in source_fragments:
        if f.flag == "pending":
            source_char, text = remove_accelerator (f.text, "_") #FIXME hardcode
            f.text = text
            f.found_accelerator = True
            # FIXME what if several fragments have accelerator character?
            break

    target_char = None
    for f in target_fragments:
        if f.flag == "pending":
            target_char, text = remove_accelerator (f.text, "_") #FIXME hardcode
            f.text = text
            f.found_accelerator = True
            # FIXME what if several fragments have accelerator character?
            break

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
            word_type = identify_type(t.text)
            translation = table.find(t.text.lower())
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

def exclude (original, exclude, flag):
    if type(original) is str:
        given = [text_fragment(original)]
    elif type (original) is list:
        given = original
    else:
        given = [original]

    if type(exclude) is not list:
        exclude = [exclude]
    print(source_fragment.text)

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
                subfragments.append( text_fragment( fragment.text[start:pattern.start()], "pending" ) )
                subfragments.append( text_fragment( fragment.text[pattern.start():pattern_end], flag) )
                start = pattern_end
            subfragments.append(text_fragment( fragment.text[start:len(fragment.text)]))
            derivative += subfragments
        given = derivative
    return derivative

def remove_accelerator(text, accelerator):
    pos = text.find(accelerator)
    if pos != -1:
        accel_char = text[pos+1] #storing accelerator char
        return accel_char, text[:pos] + texts[pos+1:] #FIXME might fail if accel is last

def place_accelerator(text, accelerator, symbol):
    #find where to put back accelerator
    acc_pos = text.find(accelerator)
    if acc_pos != -1:
        return text[:acc_pos] + symbol + new_chops[acc_pos:]
    else:
        return None

def identify_type(string):
    if string.islower():
        return "lower"
    if string.isupper():
        return "upper"
    if string.istitle():
        return "sentence"
    return "wierd"

def denormalize (string, s_type):
    # string should be in lowercase
    if s_type == "lower":
        return string
    if s_type == "upper":
        return string.upper()
    if s_type == "sentence":
        return string[0:1].upper() + string[1:]
    # Case with "weird" capitalization is omitted
    return string
