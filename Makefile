docs:
	. venv/bin/activate; cd docs; sphinx-build source build; deactivate

test:
	venv/bin/python setup.py test

clean:
	- rm -rf docs/build

dist:
	- rm dist/*
	python setup.py sdist bdist_wheel

upload-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	twine upload dist/*

.PHONY: docs test clean dist upload-test upload
