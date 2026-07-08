PYTHON ?= python3
SOURCE := resume.md
PDF := output/pdf/denis-glotov-resume.pdf

.PHONY: build check clean

build:
	$(PYTHON) scripts/build_resume.py $(SOURCE) $(PDF)

check: build
	$(PYTHON) scripts/check_pdf_text.py $(PDF)

clean:
	rm -f $(PDF)
