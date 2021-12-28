run:
	python -m SciFiPaint

lint:	format
	python -m flake8 SciFiPaint/

format:
	python -m black SciFiPaint/

reqs:
	pip install -r requirements.txt

.PHONY:	run lint format reqs