.PHONY: clean-pyc clean-build

SOURCE_PATH=./app
TEST_PATH=./tests

help:
	@echo "    clean-pyc"
	@echo "        Remove python artifacts."
	@echo "    clean-build"
	@echo "        Remove build artifacts."
	@echo "    lint"
	@echo "        Check style with flake8."
	@echo "    test"
	@echo "        Run py.test"

clean-pyc:
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '__pycache__' -delete

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

clean: clean-pyc clean-build

lint:
	flake8 --exclude=.tox --max-line-length 120 --ignore=E402 $(SOURCE_PATH)

test: clean-pyc
	(export PYTHONPATH=$(SOURCE_PATH); pytest --verbose --color=yes $(TEST_PATH))

git-push: test
	git push

update:
	pip install -Ur requirements.txt