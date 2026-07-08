#!/usr/bin/env python3
"""Check that the generated resume PDF exposes a useful text layer."""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader


REQUIRED_TEXT = [
    "Denis Glotov",
    "Senior Software Engineer",
    "Neon Labs",
    "Google Inc.",
    "RF Micro Devices",
    "US Patent application 20130035926",
]


def image_count(reader: PdfReader) -> int:
    count = 0
    for page in reader.pages:
        resources = page.get("/Resources") or {}
        xobjects = resources.get("/XObject") or {}
        for obj_ref in xobjects.values():
            obj = obj_ref.get_object()
            if obj.get("/Subtype") == "/Image":
                count += 1
    return count


def main(argv: list[str]) -> int:
    pdf_path = Path(argv[1]) if len(argv) > 1 else Path(
        "output/pdf/denis-glotov-resume.pdf")
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    missing = [needle for needle in REQUIRED_TEXT if needle not in text]
    images = image_count(reader)
    controls = sorted({ch for ch in text if ord(ch)
                      < 32 and ch not in "\n\r\t"})

    print(f"pages: {len(reader.pages)}")
    print(f"extractable characters: {len(text)}")
    print(f"embedded images: {images}")

    if missing:
        print("missing required text:")
        for needle in missing:
            print(f"- {needle}")
        return 1
    if images:
        print(
            "expected no embedded images so ATS can read the resume "
            "text directly"
        )
        return 1
    if controls:
        printable = ", ".join(f"0x{ord(ch):02x}" for ch in controls)
        print(f"unexpected control characters in extracted text: {printable}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
