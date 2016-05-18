# -*- coding: utf-8 -*-
from xml.etree import ElementTree
from xml.dom.minidom import parseString

class dictionary:

    def __init__(self,dict_file):
        """Open and read dictionary file"""
        self.dictionary = dict()
        self.new = set()
        self.dict_file = dict_file

        tree = ElementTree.parse(dict_file)
        root = tree.getroot()
        for child in root:
            source = child.attrib['source']
            target = child.attrib['target']
            if (target != ""):
                self.dictionary[source] = target

    def find(self,word):
        """Return word in dictionary"""
        found = self.dictionary.get(word)
        if (found): return found
        else:
            self.add(word)
            print ("WARNING: dictionary has no entry for " + word)
            return None

    def add(self,word,translation = None):
        """Add word and its translation (if it exists) to dictionary"""
        if translation == None:
            self.new.add(word)
        else:
            self.dictionary[word] = translation

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

    def dump_untranslated(self,empty_dict_file):
        """Write untranslated words into empty dictionary file, if such words exist"""
        xml = self.untranslated_xml()
        if xml:
            with open(empty_dict_file, "w") as f: f.write(xml.encode('UTF-8'))
