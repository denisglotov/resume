# 👋 Denis Glotov resume

## I am a software engineer

<a href="https://commons.wikimedia.org/wiki/File:Moscow_State_University_crop.jpg">
  <img align="right" width="180" alt="Main building of Moscow State University" src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Moscow_State_University_crop.jpg/330px-Moscow_State_University_crop.jpg">
</a>
<!-- Photo: Dmitry A. Mottl, cropped by King of Hearts, CC BY-SA 3.0, via Wikimedia Commons: https://commons.wikimedia.org/wiki/File:Moscow_State_University_crop.jpg -->

I am a software engineer with a mathematical background and 25 years of experience in distributed systems, blockchain, and cryptography. I enjoy complex problems where correctness, performance, and clean abstractions all matter.

I am especially interested in zero-knowledge proofs, functional programming, system programming, kernel-level debugging, low-level optimization, data races, and distributed systems. I care about writing elegant code that is practical to run and maintain.

## Resume Markdown Source

This project builds `resume.md` into a text-first PDF resume.

```bash
python3 -m pip install -r requirements.txt
make build
make open
make check
```

The output is written to `output/pdf/denis-glotov-resume.pdf`.

The PDF generator uses standard PDF text objects rather than screenshot or image text. The included `make check` target verifies that required resume text is extractable and that no images are embedded.
