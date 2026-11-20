"""
MM9's script strings: MMIXSCRIPTTEXT.csv (mm9/extracted/SCRIPTS/SCRIPTS), the table JSL's `RollOverText <n>` shows
(row 0 is its welcome line). Every converter that shows an MM9 rollover, taunt or status line takes it from here
instead of its own words:

    from script_text import rollover_text
    rollover_text(8)        # "Ebora: Get them!" (its row in the CSV)
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

CSV = Path(__file__).resolve().parents[3] / "mm9/extracted/SCRIPTS/SCRIPTS/MMIXSCRIPTTEXT.csv"


@lru_cache(maxsize=None)
def rollover_table() -> dict[int, str]:
    """{row number: text} of MMIXSCRIPTTEXT.csv (a row is `<n>,<text>`; the text may hold commas)."""
    rows = {}
    with CSV.open(encoding="latin-1", newline="") as stream:
        for row in csv.reader(stream):
            if not row or not row[0].strip().isdigit():
                continue
            rows[int(row[0])] = ",".join(row[1:]).strip()
    return rows


def rollover_text(number: int) -> str:
    """The text of `RollOverText <number>`; a number the table lacks stops the build (no guessed line)."""
    table = rollover_table()
    if number not in table:
        raise SystemExit(f"RollOverText {number} is not in {CSV.name}")
    return table[number]


def speaker_line(number: int) -> tuple[str, str]:
    """(speaker, words) of a row written `Speaker: words` (Ebora's taunts); ('', text) when it names none."""
    text = rollover_text(number)
    head, sep, rest = text.partition(":")
    if sep and head and len(head) <= 40 and " " not in head.strip():
        return head.strip(), rest.strip()
    return "", text
