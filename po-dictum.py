import re
import string

escapeables = 
[
	('<.*?>', 'tag'),
	('%[diuoxXfFeEgGaAcspn]','var'),
	('%\([word]*\)[diuoxXfFeEgGaAcspn]','var'),
	('%[0-9]\$[diuoxXfFeEgGaAcspn]','var'),
	('&\w*;','var'), # FIXME Mozilla vars can contain dots
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
    def __init__(self,string,flag="pending"):
        
        assert flag in ["word", "pending", "tag", "var", "exist", "scrap", "other"]

        self.string = string
        self.flag = flag
        self.new_string = "" # FIXME is this real?

        def __str__(self):
            return self.string

def split_string (source_fragment, target):
    original = [source_fragment]
    print(original)

    # New compile
    for reg, flag in escapeables:
        compiled = re.compile(reg)
        derivative = []
        for index, fragment in enumerate(original): #FIXME check for translateability
            subfragments = []
            start = 0
            for pattern in compiled.finditer(fragment.string):
	            pattern_end = pattern.start() + len(pattern.group())
	            subfragments.append( text_fragment( fragment[start:pattern.start()], "pending" ) )
	            subfragments.append( text_fragment( fragment[pattern.start():pattern_end], flag) )
	            start = pattern_end
            subfragments.append(text_fragment( fragment.string[start:len(fragment.string)]))

            derivative += subfragments
        original = derivative
            
