# mt-words
Machine translation script for closely related languages

For this software to work, Tranlate Toolkit project must be installed:
```
Fedora: dnf install translate-toolkit
Ubuntu: apt-get install translate-toolkit
```

# Contents of the repo
* po_dictum.py - the translation script
* dictionary_ltg.csv - the dictionary for the Latgalina (LTG) language

# Usage
For Mozilla products
```
python po_dictum.py -i lv-po/ -o ltg-po --dictionary dictionary_ltg.csv --project MOZILLA
```
* -i - the input translation files in po format
* -o - the output folder 
* --dictionary - the dictionary file to use
* --project MOZILLA - a flag to use Mozilla specific rules
* --new_words - output file with new words not found in the dictionary
* --all_words - output file with dictionary, which contains both old and new words  