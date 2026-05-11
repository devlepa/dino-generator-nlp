#!/usr/bin/env python3
import json
import re
from pathlib import Path

from pypdf import PdfReader


INPUT_PDF = Path("Generador de caracteres - Dino.pdf")
OUTPUT_JSON = Path("Generador de caracteres - Dino.json")


def pdf_date_to_iso(value):
    if not value or not isinstance(value, str):
        return value
    match = re.match(
        r"^D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})([+-])(\d{2})'(\d{2})'",
        value,
    )
    if not match:
        return value
    year, month, day, hour, minute, second, sign, offset_hour, offset_minute = match.groups()
    return (
        f"{year}-{month}-{day}T{hour}:{minute}:{second}"
        f"{sign}{offset_hour}:{offset_minute}"
    )


def clean_metadata(metadata):
    if not metadata:
        return {}
    cleaned = {}
    for key, value in metadata.items():
        plain_key = str(key).lstrip("/")
        plain_value = str(value)
        if plain_key in {"CreationDate", "ModDate"}:
            cleaned[plain_key] = {
                "raw": plain_value,
                "iso": pdf_date_to_iso(plain_value),
            }
        else:
            cleaned[plain_key] = plain_value
    return cleaned


def page_size(page):
    box = page.mediabox
    return {
        "width": float(box.width),
        "height": float(box.height),
        "unit": "points",
    }


def extract_annotations(page):
    annotations = []
    if "/Annots" not in page:
        return annotations
    for annot_ref in page["/Annots"]:
        annot = annot_ref.get_object()
        item = {
            "subtype": str(annot.get("/Subtype", "")).lstrip("/"),
            "contents": str(annot.get("/Contents", "")) if annot.get("/Contents") else None,
        }
        action = annot.get("/A")
        if action and action.get("/URI"):
            item["uri"] = str(action.get("/URI"))
        annotations.append(item)
    return annotations


def main():
    reader = PdfReader(INPUT_PDF)
    pages = []
    full_text_parts = []

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        lines = [line.rstrip() for line in text.splitlines()]
        full_text_parts.append(text.strip())
        pages.append(
            {
                "page_number": index,
                "size": page_size(page),
                "text": text,
                "lines": lines,
                "annotations": extract_annotations(page),
            }
        )

    result = {
        "source_file": str(INPUT_PDF),
        "page_count": len(reader.pages),
        "metadata": clean_metadata(reader.metadata),
        "pages": pages,
        "full_text": "\n\n".join(part for part in full_text_parts if part),
    }

    OUTPUT_JSON.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JSON} with {len(reader.pages)} pages")


if __name__ == "__main__":
    main()
