# mt-words
Machine translation script for closely related languages

The script is used for translating software, using an existing translation
to a related language as a source. It uses dictionary translation, i.e. replaces
words using a dictionary. Human editor should take a second look, since the
translation is not perfect, but it reduces the work from “translate the whole
software” to “create dictionary and fix minor mistakes”.

For this software to work, Tranlate Toolkit project must be installed:
```
Fedora: dnf install translate-toolkit
Ubuntu: apt-get install translate-toolkit
```

# Contents of the repo
* po_dictum.py - the translation script
* dictionary_ltg.csv - the dictionary for the Latgalina (LTG) language

# Usage

## Create new dictionary

To gather translateable words for a new dictionary, run
```
./po_dictum.py -i [path-to-po-file] --new_words dictionary.csv
```
Open the `dictionary.csv` in your favourite spreadsheet application and
write translations to the second column. If you believe that the translation
might cause problems down the line (ambiguity, not a real word, etc.), in the
third column write `yes`. This will inform script that the string should be
reviewed and will be marked `fuzzy`.

## Translate programs

To translate po files using the script, run
```
./po_dictum.py -i [source] -o [target] --dictionary dictionary.csv
```
* `-i` input po file or folder of input po files
* `-o` output po file or folder of output po files
* `--dictionary` dictionary file in a format described above

Some other parameters you might find useful:

* `--project [GNOME|MOZILLA]` if project is specified, it can do a better job
  at translating files.
* `--new_words` output file with new words not found in the dictionary
* `--all_words` output file with dictionary, which contains both old and new
  words; useful for updating the existing dictionary

## For Mozilla products
```
./po_dictum.py -i lv-po/ -o ltg-po --dictionary dictionary_ltg.csv --project MOZILLA
```

Use the `--project MOZILLA`, to properly handle mozilla style variables
and acceleratrors