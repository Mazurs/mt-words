# mt-words
Machine translation script for closely related languages

For this software to work, Tranlate Toolkit project must be installed:
```
Fedora: dnf install translate-toolkit
Ubuntu: apt-get install translate-toolkit
```

# Contents of the repo
* po-dict.py - the translation script
* dictionary - the dictionary for the Latgalina (LTG) language

# Usage
For Mozilla products
```
python po-dict.py -i lv-po/ -o ltg-po --dictionary dictionary --project MOZILLA
```
* -i - the input translation files in po format
* -o - the output folder 
* --dictionary - the dictionary file to use
* --project MOZILLA - a flag to use Mozilla specific rules