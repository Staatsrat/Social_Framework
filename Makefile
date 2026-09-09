# Social Framework Makefile

PYTHON = python3
SCRIPT = social_framework.py
PIP = $(PYTHON) -m pip

.PHONY: install run clean

install:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) $(SCRIPT)

clean:
	rm -rf __pycache__ captures visitor_data social_framework_log.txt
	@echo "Cleaned up generated files."
