docs:
	cd docs && sphinx-build source build

dist:
	- rm dist/*
	python setup.py sdist bdist_wheel

upload-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	twine upload dist/*

.PHONY: docs dist upload-test upload

