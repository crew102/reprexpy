docs:
	. .venv/bin/activate; cd docs; sphinx-build source build; deactivate

# Reminder: To run tests locally against several OS/Python combos, run `act`
test:
	.venv/bin/python setup.py test

# Run act tests for all Python versions (runs in parallel)
test-act: test-act-3.8 test-act-3.9 test-act-3.10
	@echo "All tests completed"

# Individual test targets for each Python version
test-act-3.8:
	@echo "Testing Python 3.8..."
	-act -j build --matrix '{"os":"ubuntu-latest","python-version":"3.8"}' -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest || echo "Python 3.8 test failed"

test-act-3.9:
	@echo "Testing Python 3.9..."
	-act -j build --matrix '{"os":"ubuntu-latest","python-version":"3.9"}' -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest || echo "Python 3.9 test failed"

test-act-3.10:
	@echo "Testing Python 3.10..."
	-act -j build --matrix '{"os":"ubuntu-latest","python-version":"3.10"}' -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest || echo "Python 3.10 test failed"

clean:
	- rm -rf docs/build
	- rm -rf dist

dist:
	- rm dist/*
	python setup.py sdist bdist_wheel

upload-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	twine upload dist/*

.PHONY: docs test test-act test-act-3.8 test-act-3.9 test-act-3.10 clean dist upload-test upload
