lint:	format
	python -m flake8 SciFiPaint/

format:
	python -m black SciFiPaint/

.PHONY:	lint