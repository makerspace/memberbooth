test:
	PYTHONPATH="$(shell pwd)" pytest

flake8:
	flake8 src *.py

.PHONY: init init-font test flake8
