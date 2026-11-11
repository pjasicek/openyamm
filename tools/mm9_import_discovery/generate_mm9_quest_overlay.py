#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path


MM9_QBIT_BASE = 90000
REQUIRED_KEY_COLUMNS = (6, 8, 10, 12, 14)
FORBIDDEN_KEY_COLUMNS = (20, 21, 22, 23, 24)


def mapped_qbit(raw_key: str, source_row: int) -> int | None:
    try:
        value = int(raw_key)
    except ValueError as exception:
        raise ValueError(f"NPC997.rude row {source_row}: invalid quest key {raw_key!r}") from exception

    if value == 0:
        return None
    if value < 1 or value > 9999:
        raise ValueError(f"NPC997.rude row {source_row}: quest key {value} is outside 1-9999")
    return MM9_QBIT_BASE + value


def qbit_group(row: list[str], columns: tuple[int, ...], source_row: int) -> list[int]:
    result: list[int] = []
    for column in columns:
        qbit = mapped_qbit(row[column], source_row)
        if qbit is not None and qbit not in result:
            result.append(qbit)
    return result


def journal_text(title: str, description: str) -> str:
    normalized_description = "" if description == "blank" else description
    if title and normalized_description:
        return f"{title}\n\n{normalized_description}"
    return title or normalized_description


def generate_quest_overlay(source_path: Path) -> str:
    with source_path.open(newline="", encoding="latin-1") as source:
        rows = list(csv.reader(source))

    output_rows = [[
        "Q Bit",
        "Quest Note Text",
        "Notes",
        "Owner",
        "Required QBits",
        "Forbidden QBits",
    ]]
    seen_entry_ids: set[int] = set()

    for source_row, row in enumerate(rows, start=1):
        if len(row) < 30:
            raise ValueError(f"NPC997.rude row {source_row}: expected at least 30 columns")
        if row[0] != "997" or row[1] != "997":
            raise ValueError(f"NPC997.rude row {source_row}: unexpected RUDE identity {row[0:2]}")

        try:
            entry_id = int(row[2])
        except ValueError as exception:
            raise ValueError(f"NPC997.rude row {source_row}: invalid journal entry id {row[2]!r}") from exception

        if entry_id < 1 or entry_id > 9999 or entry_id in seen_entry_ids:
            raise ValueError(f"NPC997.rude row {source_row}: invalid or duplicate journal entry id {entry_id}")
        seen_entry_ids.add(entry_id)

        required_qbits = qbit_group(row, REQUIRED_KEY_COLUMNS, source_row)
        forbidden_qbits = qbit_group(row, FORBIDDEN_KEY_COLUMNS, source_row)
        if set(required_qbits).intersection(forbidden_qbits):
            raise ValueError(f"NPC997.rude row {source_row}: a QBit is both required and forbidden")

        output_rows.append([
            str(MM9_QBIT_BASE + entry_id),
            journal_text(row[3], row[4]),
            f"Generated from NPC997.rude row {source_row}, entry {entry_id}.",
            "Chedian",
            ";".join(str(qbit) for qbit in required_qbits),
            ";".join(str(qbit) for qbit in forbidden_qbits),
        ])

    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerows(output_rows)
    return stream.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an OpenYAMM journal overlay from MM9 NPC997.rude.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("assets_dev/worlds/mm9/dialogue/rude/NPC997.rude"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets_dev/worlds/mm9/data_tables/english/quests_overlay.txt"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        generated = generate_quest_overlay(args.source)
    except (OSError, ValueError) as exception:
        print(exception)
        return 1

    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != generated:
            print(f"stale generated MM9 quest overlay: {args.output}")
            return 1
        print(f"MM9 quest overlay is current: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated, encoding="utf-8")
    generated_rows = list(csv.reader(io.StringIO(generated), delimiter="\t"))
    print(f"wrote {args.output} ({len(generated_rows) - 1} quests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
