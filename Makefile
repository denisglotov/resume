PYTHON ?= python3
SOURCE := resume.md
PDF := output/pdf/denis-glotov-resume.pdf

.PHONY: build check clean lint open

build: $(PDF)

$(PDF): $(SOURCE) scripts/build_resume.py
	$(PYTHON) scripts/build_resume.py $(SOURCE) $(PDF)

check: build
	$(PYTHON) scripts/check_pdf_text.py $(PDF)

lint:
	npx markdownlint-cli2 $(SOURCE)

open: $(PDF)
	@if command -v open >/dev/null 2>&1; then \
		open "$(PDF)"; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open "$(PDF)"; \
	else \
		printf '%s\n' "Built $(PDF); no PDF opener found."; \
	fi

clean:
	rm -f $(PDF)
