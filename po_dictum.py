#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import string
import csv
from translate.storage import factory, po
from translate.convert import convert
from translate.misc.multistring import multistring  # why you hate me?
from xml.etree import ElementTree
from xml.dom.minidom import parseString

the_dictionary = None
the_new_words = None
the_all_words = None

# Banners sponsored by http://patorjk.com/software/taag/#p=display&f=Banner3

# ######## ########     ###     ######   ##     ## ######## ##    ## ########
# ##       ##     ##   ## ##   ##    ##  ###   ### ##       ###   ##    ##
# ##       ##     ##  ##   ##  ##        #### #### ##       ####  ##    ##
# ######   ########  ##     ## ##   #### ## ### ## ######   ## ## ##    ##
# ##       ##   ##   ######### ##    ##  ##     ## ##       ##  ####    ##
# ##       ##    ##  ##     ## ##    ##  ##     ## ##       ##   ###    ##
# ##       ##     ## ##     ##  ######   ##     ## ######## ##    ##    ##


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

#  ######   #######  ##    ## ##     ## ######## ########  ########
# ##    ## ##     ## ###   ## ##     ## ##       ##     ##    ##
# ##       ##     ## ####  ## ##     ## ##       ##     ##    ##
# ##       ##     ## ## ## ## ##     ## ######   ########     ##
# ##       ##     ## ##  ####  ##   ##  ##       ##   ##      ##
# ##    ## ##     ## ##   ###   ## ##   ##       ##    ##     ##
#  ######   #######  ##    ##    ###    ######## ##     ##    ##


class word_substitute:
    """Worker that does dictionary replacement"""

    def __init__(self, dictionary_file, all_words=None, new_words=None,
                 project=None, accelerator=None):
        global the_dictionary
        global the_new_words
        global the_all_words
        if not the_dictionary:
            the_dictionary = dictionary(dictionary_file)
        if not the_new_words:
            the_new_words = new_words
        if not the_all_words:
            the_all_words = all_words
        self.project = project
        self.escapeables = escapeables(project)
        self.accel = get_accelerator(project)
        if accelerator:
            self.accel = accelerator

    def substitute(self, unit):
        """Piplne that converts translation @unit to the new language"""
        flags = unit.allcomments[3]
        source = unit.getsource()
        target = unit.gettarget()

        # Cut out immutable substrings
        source = mark(source, escapeables(self.project, flags), "literal")
        target = mark(target, escapeables(self.project, flags), "literal")

        source, source_accl = remove_accelerator(source, self.accel)
        target, target_accl = remove_accelerator(target, self.accel)

        # Mark dem words

        source = mark(source, '[^\W_0-9]+', "word")  # The magic 7
        target = mark(target, '[^\W_0-9]+', "word")

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
        """The same as substitue(), but for multistring"""
        sources = list()
        for source in unit.source.strings:
            sources.append(str(source))
        targets = list()
        for target in unit.target.strings:
            targets.append(str(target))

        for idx, source in enumerate(sources):
            sources[idx] = mark(source, escapeables(self.project, flags),
                                "literal")
        for idx, target in enumerate(targets):
            targets[idx] = mark(target, escapeables(self.project, flags),
                                "literal")

        # If accel char chages between plural forms, someone is being difficult
        for idx, source in enumerate(sources):
            sources[idx], source_accl = remove_accelerator(source, self.accel)
        for idx, target in enumerate(targets):
            targets[idx], target_accl = remove_accelerator(target, self.accel)

        for idx, source in enumerate(sources):
            sources[idx] = mark(source, '[^\W_0-9]+', "word")
        for idx, target in enumerate(targets):
            targets[idx] = mark(target, '[^\W_0-9]+', "word")

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
        """Translates whole po file (@fromstore) to the new language"""
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

#      ########  ####  ######  ########
#      ##     ##  ##  ##    ##    ##
#      ##     ##  ##  ##          ##
#      ##     ##  ##  ##          ##
#      ##     ##  ##  ##          ##
#      ##     ##  ##  ##    ##    ##
#      ########  ####  ######     ##


class dictionary:

    def __init__(self, dict_file):
        """Open and read dictionary file"""
        self.dictionary = dict()
        self.new = set()
        self.old = list()
        self.dict_file = dict_file

        if not dict_file:
            pass
        elif dict_file[-3:] == "xml":
            tree = ElementTree.parse(dict_file)
            root = tree.getroot()
            for child in root:
                source = child.attrib['source']
                target = child.attrib['target']
                review = child.get('review')
                if not review or review.lower() == "no":
                    review = False
                else:
                    review = True

                self.add(source, target, review)

        elif dict_file[-3:] == "csv":
            with open(dict_file, newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                for record in csv_reader:
                    self.old.append(record)
                    source = record[0]
                    target = record[1]
                    review = record[2] if len(record) > 2 else None
                    if not review or review.lower() == "no":
                        review = False
                    else:
                        review = True

                    self.add(source, target, review)

    def find(self, word):
        """Return word in dictionary and if it needs review"""
        options = self.dictionary.get(word)
        if (options):
            return self.best_translation(options)
        else:
            self.add(word)
            # print ("WARNING: dictionary has no entry for " + word)
            return None

    def add(self, word, translation=None, review=False):
        """Add word and its translation (if it exists) to dictionary"""
        if translation is None:
            self.new.add(word)
        else:
            node = self.dictionary.get(word)
            if node is None:
                self.dictionary[word] = [
                    {"target": translation, "review": review}]
            else:
                for i in node:
                    if i["target"] == translation:
                        i["review"] = review
                        return
                node.append({"target": translation, "review": review})

    def find_all(self, word):
        """Returns list of all available translations"""
        options = self.dictionary.get(word)
        translations = []
        for o in options:
            translations.append(o['target'])
        return translations

    def best_translation(self, options):
        """Returns first translation, that needs no review (if exists),
            otherwise just first"""
        for value in options:
            if not value['review']:
                return value['target'], value['review']
        return options[0]['target'], options[0]['review']

    def untranslated_xml(self):
        """Return string unicode representation of untranslated words"""
        if len(self.new) == 0:
            return None
        dic = ElementTree.Element('dict')
        for word in sorted(self.new):
            child = ElementTree.SubElement(dic, 'term')
            child.set('source', word)
            child.set('target', '')
            child.set('review', 'no')

        return parseString(ElementTree.tostring(dic, encoding="UTF-8")
                           ).toprettyxml(indent=" ")

    def dump_untranslated(self, empty_dict_file):
        """Write untranslated words into empty dictionary file,
            if such words exist"""
        output = str()
        if empty_dict_file[-3:] == "xml":
            output = self.untranslated_xml()
        elif empty_dict_file[-3:] == "csv":
            new_words = list(self.new)
            new_words.sort()
            for word in new_words:
                output += word + ",,\n"  # FIXME brittle to future changes
        else:
            new_words = list(self.new)
            new_words.sort()
            for word in new_words:
                output += word + "\n"

        if output:
            with open(empty_dict_file, "w") as f:
                f.write(output)

    def dump_all(self, new_dict_file):
        """Write all words into empty dictionary file, sorted"""

        if new_dict_file[-3:] == "xml":
            print("ERROR: Not implemented yet")  # TODO implement
            return
        elif new_dict_file[-3:] == "csv":
            all_words = list()
            for word in self.new:
                all_words.append([word, None, None])
            all_words.extend(self.old)
            all_words.sort()
            with open(new_dict_file, "w") as f:
                csv_gen = csv.writer(f)
                for record in all_words:
                    csv_gen.writerow(record)
        else:
            print("ERROR: Invalid file extention. Must be csv or xml")


# ##     ## ######## #### ##       #### ######## #### ########  ######
# ##     ##    ##     ##  ##        ##     ##     ##  ##       ##    ##
# ##     ##    ##     ##  ##        ##     ##     ##  ##       ##
# ##     ##    ##     ##  ##        ##     ##     ##  ######    ######
# ##     ##    ##     ##  ##        ##     ##     ##  ##             ##
# ##     ##    ##     ##  ##        ##     ##     ##  ##       ##    ##
#  #######     ##    #### ######## ####    ##    #### ########  ######


def escapeables(project=None, flags=''):
    """Returns list of patterns of literals that should not be changed or
    have any impact on the translation processes.
    @flags - gettext flags ('#,')
    @project - name of the project, e.g. GNOME, MOZILLA"""
    if type(flags) == list:
        flags = ''.join(flags)
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
    """Checks if @text contains a gettext style (#,) flag @flag"""
    c = re.compile("^.*(\s|,|#|^)" + flag + "(\s|,|$).*$")
    if c.search(text):
        return True
    else:
        return False


def get_accelerator(project):
    """Returns the accelerator character the project uses"""
    if project == "GNOME":
        return '_'
    if project == "MOZILLA" or project == "KDE":
        return '&'
    else:
        return '_'


def translateable(unit):
    """Checks if the translation @unit should be translated"""
    if (not unit.istranslatable() or not unit.getsource() or unit.isfuzzy() or
            not unit.gettarget() or unit.getsource() == "translator-credits"):
        return False
    if ((unit.getsource() == "Your names" and
         unit.getcontext() == "NAME OF TRANSLATORS") or
        (unit.getsource() == "Your emails" and
         unit.getcontext() == "EMAIL OF TRANSLATORS")):
        return False
    return True


def mark(original, matching_regex, flag):
    """Mark fragments of @original text, which match the @matching_regex
    with the @flag. """
    # TODO add multistring support
    if type(original) is str:
        given = [fragment(original)]
    elif type(original) is list:
        given = original
    else:
        # <class 'translate.misc.multistring.multistring'>
        # print ("Sorry, no plural forms supported :/")
        print(type(original))
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

    # removing empty fragments
    ret = list()
    for e in derivative:
        if e.text != "":
            ret.append(e)
    return ret


def remove_accelerator(source_fragments, accelerator):
    """Looks for and removes the @accelerator character from the
    @source_fragments and saves info on where and if the character was found"""
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
    """Mark duplicate words in source and target strings"""
    # TODO multistring
    for t in target_fragments:
        if t.flag == "word":
            for s in source_fragments:
                if s.flag == "word" and s.text == t.text:
                    t.flag = "exist"


def replace_words(target_fragments, translations):
    """Replaces translateable (non-literal, non-duplicate) words according to
    the @translations dictionary"""
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
    """Puts back the previously removed accelerator character, hopefully where
    a human translator had put it."""
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
    """Helper function for the remove_accelerator(). Removes accelerator
    character from a string in a fragment."""
    pos = text.find(accelerator)
    if pos != -1 and (pos + 1 != len(text)):  # accel can't be the last char
        accel_char = text[pos + 1]  # storing accelerator char
        return accel_char, text[:pos] + text[pos + 1:]


def place_accel(text, accelerator, symbol):
    """Helper function for the restore_accelerator(). Puts back accelerator
    character to a string in a fragment."""
    acc_pos = text.lower().find(accelerator.lower())
    if acc_pos != -1:
        return text[:acc_pos] + symbol + text[acc_pos:]
    else:
        return None


def identify_case(word):
    """Returns what case the @word has"""
    if word.islower():
        return 'lower'
    if word.isupper():
        return 'upper'
    if word.istitle():
        return 'sentence'
    return 'weird'
    # TODO abbrevation plurals, e.g. URLs, JPEGs


def restore_case(word, type):
    """Restores the case of the @word according to what case @type it had"""
    # string should be in lowercase
    if type == 'lower':
        return word
    if type == 'upper':
        return word.upper()
    if type == 'sentence':
        return word[0:1].upper() + word[1:]
    # Case with 'weird' capitalization is omitted
    return word


def fragments_to_string(fragments):
    """Convert list of fragments back to the string format"""
    # TODO multistring
    output = str()
    for f in fragments:
        output += f.text
    return output

# ##     ##    ###    #### ##    ##
# ###   ###   ## ##    ##  ###   ##
# #### ####  ##   ##   ##  ####  ##
# ## ### ## ##     ##  ##  ## ## ##
# ##     ## #########  ##  ##  ####
# ##     ## ##     ##  ##  ##   ###
# ##     ## ##     ## #### ##    ##


def mtfile(inputfile, outputfile, templatefile, dictionary_file, new_words,
           all_words, project):
    """Gathers parameters supplied by the parser in the main(),
    sets up the store conversion"""
    if not dictionary_file and not all_words and not new_words:
        print("ERROR: must supply at least one flag: --dictionary, --new_words"
              "or --all_words")
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
