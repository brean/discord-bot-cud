install:
	pipenv install

run:
	pipenv run python3 main.py

python-test:
	pipenv run python3 -m pytest
	pipenv run python3 -m flake8
