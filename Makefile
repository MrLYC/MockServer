ROOTPATH := .
PYSRCPATH := $(ROOTPATH)/mock_server
PYENV := env PYTHONPATH=$(ROOTPATH)
PEP8 := $(PYENV) pep8 --repeat --ignore=E202,E501
PYTEST := $(PYENV) py.test -v

.PHONY: dev-static-server
dev-static-server:
	python3 -m http.server

.PHONY: init
init:
	pip install -r requirements.txt

.PHONY: dev-init
dev-init: init
	echo '#!/bin/sh\nmake test' >> .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	pip install -r requirements-dev.txt

.PHONY: pytest
pytest:
	$(PEP8) $(PYSRCPATH)
	$(PYTEST) $(PYSRCPATH)/tests/

.PHONY: test
test: pytest
