docs:
	. venv/bin/activate; cd docs; sphinx-build source build; deactivate

# Reminder: To run tests locally against several OS/Python combos, run `act`
test:
	venv/bin/python setup.py test

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

.PHONY: docs test clean dist upload-test upload
