develop:
	pip install -q "file://`pwd`#egg=spreedly[tests]"
	pip install -q -e .

install-test-requirements:
	pip install "file://`pwd`#egg=spreedly[tests]"

test: install-test-requirements test-python

test-python:
	@echo "Running Python tests"
	python setup.py test || exit 1
	@echo ""

clean:
	find . -name '*.pyc' | xargs rm -f