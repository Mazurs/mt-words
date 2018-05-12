# -*- coding: utf-8 -*-
from xml.etree import ElementTree
from xml.dom.minidom import parseString
#from csv import reader
import csv

class dictionary:

    def __init__(self,dict_file):
        """Open and read dictionary file"""
        self.dictionary = dict()
        self.new = set()
        self.dict_file = dict_file

        if dict_file[-3:] == "xml":
            tree = ElementTree.parse(dict_file)
            root = tree.getroot()
            for child in root:
                source = child.attrib['source']
                target = child.attrib['target']
                review = child.get('review')
                if review == None or review.lower() == "no": review = False
                else: review = True

                self.add(source,target,review)

        elif dict_file[-3:] == "csv":
            with open(dict_file, newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                for record in csv_reader:
                    source = record[0]
                    target = record[1]
                    review = record[2] if len(record) > 2 else None
                    if review == None or review.lower() == "no": review = False
                    else: review = True

                    self.add(source,target,review)


    def find(self,word):
        """Return word in dictionary and if it needs review"""
        options = self.dictionary.get(word)
        if (options):
            return self.best_translation(options)
        else:
            self.add(word)
            # print ("WARNING: dictionary has no entry for " + word)
            return None

    def add(self,word,translation = None, review = False):
        """Add word and its translation (if it exists) to dictionary"""
        if translation == None:
            self.new.add(word) # TODO incorrect logic, first look up
        else:
            node = self.dictionary.get(word)
            if node == None:
                self.dictionary[word] = [{"target":translation,"review":review}]
            else:
                for i in node:
                    if  i["target"] == translation:
                        i["review"] = review
                        return
                node.append({"target":translation,"review":review})

    def find_all(self, word):
        """Returns list of all available translations"""
        options = self.dictionary.get(word)
        translations = []
        for o in options:
            translations.append(o['target'])
        return translations

    def best_translation(self,options):
        """Returns first translation, that needs no review (if exists), otherwise just first"""
        for value in options:
            if not value['review']:
                return value['target'] , value['review']
        return options[0]['target'] , options[0]['review']

    def untranslated_xml(self):
        """Return string unicode representation of untranslated words"""
        if len (self.new) == 0:
            return None
        dic = ElementTree.Element('dict')
        # TODO write xml comment that instructs user how to read/write/use dictionary
        for word in sorted(self.new):
            child = ElementTree.SubElement(dic, 'term')
            child.set('source',word)
            child.set('target','')
            child.set('review','no')

        return parseString(ElementTree.tostring(dic,encoding="UTF-8")).toprettyxml(indent=" ")

    def dump_untranslated(self,empty_dict_file, format="xml"):
        """Write untranslated words into empty dictionary file, if such words exist"""
        output = str()
        if format == "xml":
            output = self.untranslated_xml()
        elif format == "csv":
            l = list(self.new)
            l.sort()
            for item in l:
                output += item + "\n"

        if output:
            with open(empty_dict_file, "w") as f:
                f.write(output)
