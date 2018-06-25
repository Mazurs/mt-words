import re
import string
from translate.storage import factory, po
from translate.convert import convert
from translate.misc.multistring import multistring  # why you hate me?
from libs.dictionary import dictionary

the_dictionary = None
the_new_words = None
the_all_words = None


def get_escapeables(project=None, flags=""):
    tag = '<.*?>'
    url = ('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|'
           '(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    # FIXME date formats? no-c-format

    moz_var = '&[\w|\.]*;'

    curly_var = '{[\w]*}'
    curly_var2 = '{{\w}}'

    amp_and = '\s&\s'

    common = [tag, url]

    variables = list()

    if (has_flag(flags, 'c-format') or has_flag(flags, 'javascript-format')):
        # http://pubs.opengroup.org/onlinepubs/007904975/functions/fprintf.html
        # https://github.com/alexei/sprintf.js
        # look into /usr/share/vim/vim81/syntax/po.vim
        # % (ordering) (flags) (? .\d ?) (length mods) (variable types)
        # TODO check correctness
        prefix = "%(\d\$)?['\-+ #0]*"
        c_var = prefix + "(h|hh|l|ll|j|z|t|L)?[diuoxXf]"
        c_var2 = prefix + "[FeEgGcCsSpn]"
        variables.extend(["%%", c_var, c_var2])
    elif (has_flag(flags, 'python-format')):
        # https://docs.python.org/3/library/stdtypes.html (4.7.2.)
        variables.append("%(\(\w\))[#0\-+ ]*[hlL]?[diouxXeEfFgGcrsa%]")
    elif (has_flag(flags, 'python-brace-format')):
        variables.append("\{.*?\}")
    elif (has_flag(flags, 'scheme-format')):
        # directive ::= ~{directive-parameter,}[:][@]directive-character
        # directive-parameter ::= [ [-|+]{0-9}+ | 'character | v | # ]
        param = "([\-+]?\d+|'.|v|#)"
        variables.append("~[%s]*[:]?[@]?." % param)

    if project == "GNOME":
        return common + [c_var, c_named_var, c_ordered_var, curly_var]
    if project == "MOZILLA":
        return common + [moz_var, curly_var2, amp_and]
    else:
        return common + variables


def has_flag(text, flag):
    c = re.compile("^.*(\s|,|#|^)" + flag + "(\s|,|$).*$")
    if c.search(text):
        return True
    else:
        return False


def get_accelerator(project):
    if project == "GNOME":
        return '_'
    if project == "MOZILLA" or project == "KDE":
        return '&'
    else:
        return '_'


class fragment:
    """Container for string fragments.
    Attributes:
        text: fragment of translation text
        flag: status of the text, possible values:
            word - translateable word
            pending - potentially translateable word
            literal - immutable strings
            exist - untranslatable, because exists
        found_accelerator: if accelerator character was found here
    """

    def __init__(self, text, flag="pending"):

        assert flag in ["word", "pending", "literal", "exist"]

        self.text = text
        self.flag = flag
        self.found_accelerator = False

    def __repr__(self):
        a = ""
        if self.found_accelerator:
            a = "!"
        return str("<" + a + self.text + ":" + self.flag + ">")


class word_substitute:
    """Worker that does dictionary replacement"""

    def __init__(self, dictionary_file, all_words, new_words,
                 project, accelerator=None):
        global the_dictionary
        global the_new_words
        global the_all_words
        if not the_dictionary:
            the_dictionary = dictionary(dictionary_file)
        if not the_new_words:
            the_new_words = new_words
        if not the_all_words:
            the_all_words = all_words
        self.escapeables = get_escapeables(project)
        self.accel = get_accelerator(project)
        if accelerator:
            self.accel = accelerator

    def substitute(self, unit):
        # Cut out immutable substrings

        source = exclude(unit.getsource(), self.escapeables, "literal")
        target = exclude(unit.gettarget(), self.escapeables, "literal")

        source, source_accl = remove_accelerator(source, self.accel)
        target, target_accl = remove_accelerator(target, self.accel)

        # Mark dem words

        source = exclude(source, '[^\W_0-9]+', "word")  # The magic 7
        target = exclude(target, '[^\W_0-9]+', "word")

        mark_duplicates(source, target)

        fuzzy = replace_words(target, the_dictionary)
        if fuzzy:
            unit.markfuzzy()

        restore_accelerator(target, source_accl, target_accl, self.accel)

        # Collapse
        unit.settarget(fragments_to_string(target))

        return unit

    # TODO this is ugly. Make it less horrible
    def mutli_substitute(self, unit):
        sources = list()
        for source in unit.source.strings:
            sources.append(str(source))
        targets = list()
        for target in unit.target.strings:
            targets.append(str(target))

        for idx, source in enumerate(sources):
            sources[idx] = exclude(source, self.escapeables, "literal")
        for idx, target in enumerate(targets):
            targets[idx] = exclude(target, self.escapeables, "literal")

        # If accel char chages between plural forms, someone is being difficult
        for idx, source in enumerate(sources):
            sources[idx], source_accl = remove_accelerator(source, self.accel)
        for idx, target in enumerate(targets):
            targets[idx], target_accl = remove_accelerator(target, self.accel)

        for idx, source in enumerate(sources):
            sources[idx] = exclude(source, '[^\W_0-9]+', "word")
        for idx, target in enumerate(targets):
            targets[idx] = exclude(target, '[^\W_0-9]+', "word")

        # TODO check if assumption holds
        mark_duplicates(sources[0], targets[0])
        for target in targets[1:]:
            mark_duplicates(sources[1], target)

        for idx, target in enumerate(targets):
            fuzzy = replace_words(target, the_dictionary)
            if fuzzy:
                unit.markfuzzy()
            targets[idx] = target

        for target in targets:
            restore_accelerator(target, source_accl, target_accl, self.accel)

        rets = list()
        for target in targets:
            rets.append(fragments_to_string(target))
        unit.target = multistring(rets)
        return unit

    def convertstore(self, fromstore):
        tostore = po.pofile()
        tostore.mergeheaders(fromstore)
        for unit in fromstore.units:
            if unit.isheader():
                pass
            elif translateable(unit):
                if unit.hasplural():
                    tostore.addunit(self.mutli_substitute(unit))
                else:
                    tostore.addunit(self.substitute(unit))
            else:
                tostore.addunit(unit)

        return tostore


def translateable(unit):
    if (not unit.istranslatable() or not unit.getsource() or unit.isfuzzy() or
            not unit.gettarget() or unit.getsource() == "translator-credits"):
        return False
    if ((unit.getsource() == "Your names" and
         unit.getcontext() == "NAME OF TRANSLATORS") or
        (unit.getsource() == "Your emails" and
         unit.getcontext() == "EMAIL OF TRANSLATORS")):
        return False
    return True


def exclude(original, matching_regex, flag):
    # TODO add multistring support
    if type(original) is str:
        given = [fragment(original)]
    elif type(original) is list:
        given = original
    else:
        # <class 'translate.misc.multistring.multistring'>
        # print ("Sorry, no plural forms supported :/")
        print (type(original))
        raise -1

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
                subfragments.append(
                    fragment(frag.text[start:pattern.start()], "pending"))
                subfragments.append(
                    fragment(frag.text[pattern.start():pattern_end], flag))
                start = pattern_end
            subfragments.append(fragment(frag.text[start:len(frag.text)]))
            derivative += subfragments
        given = derivative

    ret = list()  # removing empty fragments
    for e in derivative:
        if e.text != "":
            ret.append(e)
    return ret


def remove_accelerator(source_fragments, accelerator):
    source_char = None
    for f in source_fragments:
        if f.flag == "pending":
            response = remove_accel(f.text, accelerator)
            if (response is None):
                continue
            source_char, text = response
            f.text = text
            f.found_accelerator = True
            break
    return source_fragments, source_char


def mark_duplicates(source_fragments, target_fragments):
    # TODO multistring
    for t in target_fragments:
        if t.flag == "word":
            for s in source_fragments:
                if s.flag == "word" and s.text == t.text:
                    t.flag = "exist"


def replace_words(target_fragments, translations):
    # TODO multistring
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
            t.text = restore_case(translation, word_type)
            if needs_review:
                fuzzy = True
    return fuzzy


def restore_accelerator(target_fragments, target_accl, source_accl, accel):
    # TODO multistring
    if target_accl is None or source_accl is None:
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
    if pos != -1 and (pos + 1 != len(text)):  # accel can't be the last char
        accel_char = text[pos + 1]  # storing accelerator char
        return accel_char, text[:pos] + text[pos + 1:]


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


def fragments_to_string(fragments):
    # TODO multistring
    output = str()
    for f in fragments:
        output += f.text
    return output


def mtfile(inputfile, outputfile, templatefile, dictionary_file, new_words,
           all_words, project):
    if not dictionary_file:
        print ("ERROR: missing dictionary file")
        return 0
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty():
        return 0
    convertor = word_substitute(dictionary_file, all_words, new_words, project)
    outputstore = convertor.convertstore(inputstore)
    outputstore.serialize(outputfile)
    return 1


def main():
    formats = {"po": ("po", mtfile), "xlf": (
        "xlf", mtfile), "tmx": ("tmx", mtfile)}
    parser = convert.ConvertOptionParser(
        formats, usepots=True, description=__doc__)
    parser.add_option("-d", "--dictionary", dest="dictionary_file",
                      help="Dictionary file. Record format: "
                      "key<comma>translation<newline>")
    parser.passthrough.append("dictionary_file")
    parser.add_option("-n", "--new_words", dest="new_words",
                      help="File where to write words not found in dictionary")
    parser.passthrough.append("new_words")
    parser.add_option("-a", "--all_words", dest="all_words",
                      help="File where to write the dictionary with "
                      "new untranslated words")
    parser.passthrough.append("all_words")
    parser.add_option("-p", "--project", dest="project",
                      help="What project the translation belongs to."
                      "Currently supported provjects are GNOME and MOZILLA")
    parser.passthrough.append("project")
    parser.run()

    if the_all_words:
        the_dictionary.dump_all(the_all_words)
    if the_new_words:
        the_dictionary.dump_untranslated(the_new_words)


if __name__ == '__main__':
    main()
