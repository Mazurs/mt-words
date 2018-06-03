#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import string
import codecs
from translate.storage import factory
from translate.lang import factory as lang_factory


class dict_translate:

# status of substrings:
# w - translatable word
# p - potential for translating
# t - untranslatable tag
# v - untranslatable variable
# e - untranslatable, because exists
# - - untranslatable non-letters

#    def __init__(self, sourcelang,
#                targetlang, 
#                stripspaces=True, 
#                onlyaligned=False):
    def __init__(self,dict_file,project="GNOME"):
        #self.sourcelang = sourcelang
        #self.targetlang = targetlang
        #self.stripspaces = stripspaces
        #self.onlyaligned = onlyaligned
        self.dictionary = dict()
        self.new_words = set()
        #self.accel_char_source = u""
        #self.accel_char_target = u""

        if project == "GNOME":
            self.accel = "_"
        elif project == "MOZILLA":
            self.accel = "&"
        else:
            self.accel = "_"

        # Initiate dictionaty
        f = codecs.open(dict_file, encoding = 'utf-8', mode='r')
        for line in f:
            regex = re.compile(r'[%s\s]+' % re.escape(string.punctuation))
            array = regex.split(line, 1)
            if len(array) < 2 or array[1].strip() == u"": #keys without value
                continue
            self.dictionary[array[0].strip()] = array[1].strip()
        f.close

    def replace_words (self, chops, new_chops, stat, acc_source, acc_target):
        new = u""
        acc_pos = -1
        fuzzy = False               #are any words missing from dictionary
        for i in range(len(chops)): #getting counter for both lists
            if stat[i] != 'w' or stat[i] == 'e':
                new_chops.append(chops[i])
                continue
            capitalization = self.identify_type(chops[i])
            normal = chops[i].lower()
            if self.dictionary.has_key(normal):
                new = self.denormalize(self.dictionary[normal], capitalization)
                new_chops.append(new)
            else:
                new_chops.append(chops[i])
                fuzzy = True
                self.new_words.add(normal)
        #find where to put back accelerator
        if acc_source == "" or acc_target == "":
            return fuzzy
        for i in range(len(new_chops)): #first search for target lang accel
            if stat[i] == 'w' or stat[i] == 'e' or stat[i] == '-':
                acc_pos = new_chops[i].find(acc_target)
                if acc_pos != -1: #found replacement
                    new_chops[i] = new_chops[i][:acc_pos] + self.accel + new_chops[i][acc_pos:]
                    return fuzzy
                    #break #when found, search no more
        for i in range(len(new_chops)): # if not found in target lang, search in source lang
            if stat[i] == 'w' or stat[i] == 'e' or stat[i] == '-':
                acc_pos = new_chops[i].find(acc_source)
                if acc_pos != -1: #found replacement
                    new_chops[i] = new_chops[i][:acc_pos] + self.accel + new_chops[i][acc_pos:]
                    return fuzzy
                    #break #when found, search no more
        for i in range(len(new_chops)): # if all else fails, put accel at first letter in first word
            if stat[i] == 'w' or stat[i] == 'e':
                new_chops[i] = self.accel + new_chops[i]
                return fuzzy
        return fuzzy

    def split_string (self, fragments, frag_stat, target):
        is_current_text = None    
        current = u""
        accel = u""
        original = [[target, 'p']] # p for potential
        variables = []
        imposter = list(original)
        print(original)
        # Escape HTML tags
        tag = re.compile('<.*?>')
        tags = tag.findall(original[0][0])
        for t in tags:
            for index, texts in enumerate(original):
                if texts[1] != 'p':
                    continue
                pos = unicode(texts[0]).find(t)
                if pos != -1:
                    #tag found, shread it!
                    imposter = original[:index]
                    if texts[0][:pos] != "":
                        imposter.append([texts[0][:pos], 'p'])
                    imposter.append([texts[0][pos:pos+len(t)], 'h'])
                    if texts[0][pos+len(t):] != "":
                        imposter.append([texts[0][pos+len(t):], 'p'])
                    imposter.extend(original[index+1:])
                    break
            original = list(imposter)
        print("Tags:" + str(original))
        # Escape C variables
        c_simple = re.compile('%[diuoxXfFeEgGaAcspn]')
        c_named = re.compile('%\([word]*\)[diuoxXfFeEgGaAcspn]')
        c_moved = re.compile('%[0-9]\$[diuoxXfFeEgGaAcspn]')
        # Escape Mozilla variables
        m_standart = re.compile('&[\w|\.]+;')
        # Escape URLs
        url = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        # Escape some other weirdness
        naked_ampersand = re.compile('\s&\s')
        for item in original:
            if item [1] != 'p':
                continue
            variables.extend(url.findall(item[0]))
            variables.extend(c_simple.findall(item[0]))
            variables.extend(c_named.findall(item[0]))
            variables.extend(c_moved.findall(item[0]))
            variables.extend(m_standart.findall(item[0]))
            variables.extend(naked_ampersand.findall(item[0]))
        for var in variables:
            for index, texts in enumerate(original):
                if texts[1] != 'p':
                    continue
                pos = unicode(texts[0]).find(var)
                if pos != -1:
                    #variable found, shread it!
                    imposter = original[:index]
                    if texts[0][:pos] != "":
                        imposter.append([texts[0][:pos], 'p'])
                    imposter.append([texts[0][pos:pos+len(var)], 'v'])
                    if texts[0][pos+len(var):] != "":
                        imposter.append([texts[0][pos+len(var):], 'p'])
                    imposter.extend(original[index+1:])
                    break
            original = list(imposter)
        print("Vars: " + str(original))
        #Find and remove accelerator
        for texts in original:
            if texts[1] == 'p':
                pos = texts[0].find(self.accel) #dissapears later
                if pos != -1:
                    accel = texts[0][pos+1] #storing accelerator char
                    texts[0] = texts[0][:pos] + texts[0][pos+1:]
        print("Accell: " + str(original))
        #Split by words
        for texts in original:
            current = u""
            if texts[1] != 'p':
                fragments.append(texts[0])
                frag_stat.append(texts[1])
            else:
                if texts[0][0].isalpha(): #first char of translatable
                    is_current_text = True
                else:
                    is_current_text = False
                for ch in texts[0]:
                    if is_current_text == ch.isalpha():
                        current = current + ch
                    else:
                        fragments.append(current)
                        current = u"" + ch
                        if is_current_text:
                            frag_stat.append('w')
                            is_current_text = False
                        else:
                            frag_stat.append('-')
                            is_current_text = True
                #At the end, store the tail
                fragments.append(current)
                if is_current_text:
                    frag_stat.append('w')
                else:
                    frag_stat.append('-')
        print("Words: " + str(fragments))
        return accel

    def identify_type(self, string):
        if string.islower():
            return "lower"
        if string.isupper():
            return "upper"
        if string.istitle():
            return "sentence"
        return "wierd"

    def denormalize (self, string, s_type):
        # string should be in lowercase
        if s_type == "lower":
            return string
        if s_type == "upper":
            return string.upper()
        if s_type == "sentence":
            return string[0:1].upper() + string[1:]
        # Case with "weird" capitalization is omitted
        return string

    def translate_target (self, unit):
        fragments = []
        new_fragments = []
        frag_stat = []
        source_fragments = []
        source_frag_stat = []
        new_lines = u""
        # unit.msgstr can be unicode string 
        # or dict of unicode with [0-2] index
        accel_char_target = self.split_string (fragments, 
                                               frag_stat, 
                                               unicode(unit.gettarget()))
        accel_char_source = self.split_string (source_fragments,
                                               source_frag_stat, 
                                               unicode(unit.getsource()))
        # mark words, that are identical in source
        # and target as untranslatable
        for i, target in enumerate(fragments):
            if frag_stat[i] == 'w':
                for j, source in enumerate(source_fragments):
                    if source_frag_stat[j] == 'w' and source == target:
                        frag_stat[i] = 'e'
        fuzzy = self.replace_words(fragments, new_fragments, frag_stat, accel_char_source, accel_char_target)
        if fuzzy == True:
            unit.markfuzzy()
        for chunk in new_fragments:
            new_lines = new_lines + chunk
        unit.settarget(new_lines)
        return unit
#######################
    def convertstore(self, fromstore):
        tostore = type(fromstore)()
        for unit in fromstore.units:
            if not unit.istranslatable():
                continue
            #Skip translator credits
            if unit.getsource() == "translator-credits":
                continue
            if unit.getsource() == "Your names" and unit.getcontext() == "NAME OF TRANSLATORS":
                continue
            if unit.getsource() == "Your emails" and unit.getcontext() == "EMAIL OF TRANSLATORS":
                continue
            if unit.getsource() == "":
                continue
            newunit = unit
            newunit = self.translate_target(newunit)
            tostore.addunit(newunit)
        #append new words in dictionary file
        f = codecs.open('dictionary_new', encoding = 'utf-8', mode='w')
        for key in sorted(self.dictionary.iterkeys()):
            f.write(key + " " + self.dictionary[key] + u"\n")
        for item in self.new_words:
            f.write(item + " " + u"\n")
        f.close()
        return tostore


def mtfile(inputfile,
           outputfile,
           templatefile,
           dictionary,
           #sourcelanguage="en",
           #targetlanguage=None,
           project="GNOME",
           trans_tag=False
           ):
    if (not dictionary):
        dictionary = "dictionary";
    """reads in inputfile, segments it then, writes to outputfile"""
    # note that templatefile is not used, but it is required by the converter...
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty():
        return 0
#    sourcelang = lang_factory.getlanguage(sourcelanguage)
#    targetlang = lang_factory.getlanguage(targetlanguage)
#    convertor = dict_translate(sourcelang,
#                               targetlang,
#                               stripspaces=stripspaces,
#                               onlyaligned=onlyaligned)
    convertor = dict_translate(dictionary,project)
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return 1


def main():
    from translate.convert import convert
    formats = {"po": ("po", mtfile), "xlf": ("xlf", mtfile), "tmx": ("tmx", mtfile)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
#    parser.add_option("-l", "--language", dest="targetlanguage", default=None,
#            help="the target language code", metavar="LANG")
#    parser.add_option("", "--source-language", dest="sourcelanguage", default=None,
#            help="the source language code (default 'en')", metavar="LANG")
#    parser.passthrough.append("sourcelanguage")
#    parser.passthrough.append("targetlanguage")
    parser.add_option("-d", "--dictionary", dest="dictionary",
                      help="Dictionary file. Record format: key<tab>translation<newline>")
    parser.passthrough.append("dictionary")
    parser.add_option("", "--project", dest="project", default="GNOME",
                      help="Project that the translation file belongs to. Supported options: GNOME, MOZILLA")
    parser.passthrough.append("project")
    parser.add_option("", "--translate_tags", dest="trans_tag", action="store_true",
            default=False, help="Translate words in <tags>")
    parser.passthrough.append("trans_tag")
    parser.run()

if __name__ == '__main__':
    main()
