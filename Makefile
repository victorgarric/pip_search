SHELL:=/bin/bash

.PHONY: help clean venv build install run

help:
	@echo "---------------HELP-----------------"
	@echo "To install the project type make install"
	@echo "To run the project type make run"
	@echo "To clean the project type make clean"
	@echo "To make a venv type make venv"
	@echo "To activate the venv type source venv/bin/activate"
	@echo "------------------------------------"

clean:
	@find ./ -name '__pycache__' | xargs rm -rf;
	@rm -rf build dist *.egg-info;

install: venv;
	python setup.py install;

venv:
	@python3 -m venv venv;
	@source venv/bin/activate;

run: venv;
	python -m pip_search bs4;
