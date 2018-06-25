.PHONY: clean test

clean:
	rm *.pyc */*.pyc 2>/dev/null || true

test_utils:
	python3 -m test.test_utils

test_dictionary:
	python3 -m test.test_dictionary

test_substitute:
	python3 -m test.test_substitute

test: test_utils test_dictionary test_substitute

check_style:
	pycodestyle --statistics *.py */*.py

fix_style:
	autopep8 -i *.py */*.py