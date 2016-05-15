import re
import string

escapeables = [
	('<.*?>', 'tag'),
	('%[diuoxXfFeEgGaAcspn]','var'),
	('%\([word]*\)[diuoxXfFeEgGaAcspn]','var'),
	('%[0-9]\$[diuoxXfFeEgGaAcspn]','var'),
	('&[\w|\.]*;','var'), # FIXME Mozilla vars can contain dots
	('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+','other'),
    ('\s&\s','other'),
]

class text_fragment:
    """Container for string fragments.
    Attributes:
        string: fragment of translation text
        flag:   status of the string, possible values:
            word - translateable word
            pending - potentially translateable word
            tag - untranslatable tag name or attribute
            var - untranslatable variable
            exist - untranslatable, because exists
            scrap - untranslatable non-letter characters
            other
    """

#    def __str__(self):
#        return self.string
#    def __getitem__(self):
#        return self.string

    def __init__(self,string,flag="pending"):
        
        assert flag in ["word", "pending", "tag", "var", "exist", "scrap", "other"]

        self.string = string
        self.flag = flag
        self.new_string = "" # FIXME is this real?

def split_string (source_fragment):
    assert source_fragment.flag == "pending"
    original = [source_fragment]
    print(source_fragment.string)

    # New compile
    for reg, flag in escapeables:
        compiled = re.compile(reg)
        derivative = []

        for i in original: print (i.string)

        for index, fragment in enumerate(original):
            if fragment.flag != "pending":
                derivative.append(fragment)
                continue
            subfragments = []
            start = 0
            for pattern in compiled.finditer(fragment.string):
                pattern_end = pattern.start() + len(pattern.group())
                subfragments.append( text_fragment( fragment.string[start:pattern.start()], "pending" ) )
                subfragments.append( text_fragment( fragment.string[pattern.start():pattern_end], flag) )
                start = pattern_end
            subfragments.append(text_fragment( fragment.string[start:len(fragment.string)]))
            derivative += subfragments
        original = derivative
    return original
