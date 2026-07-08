# Resume Markdown Source

This project builds `resume.md` into a text-first PDF resume.

```bash
python3 -m pip install -r requirements.txt
make build
make check
```

The output is written to `output/pdf/denis-glotov-resume.pdf`.

The PDF generator uses standard PDF text objects rather than screenshot or image text. The included `make check` target verifies that required resume text is extractable and that no images are embedded.
