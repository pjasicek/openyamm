#!/usr/bin/env python3
"""Preserve the 2026-09-23 pasted browser feedback against the verified catalog."""

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPORTED_AT = "2026-09-23T18:58:07.263Z"

DETAIL = """
item339 6cape6 7item146 7item261 7item290 ankh cndlabra item318 item326 tarot
item165 item167 item073
""".split()
CROP = """
7item252 7item253 7item254 7item255 7item256 7item257 7item258
7item265 7item266 7item267
""".split()
RAW_CROP_ALPHA = """
7item134 7item285 amulet1 item150 item151
6chain1 6chain2 6chain3 6chain4 6chain5 6chain7
7item071 7item072 7item073 7item074 7item075
item089 item090 item091 item092
""".split()
EMPTY_FLAGS = "item157 item249 6chain6".split()
NOTES = {
    "item066": "original is higher?",
    "item070": "original is higher?",
    "item078": "original is higher?",
    "item247": "original is higher?",
    "item249": "original is higher?",
    "7item235": "?",
    "7item245": "?",
    "item089": "?",
    "item092": "?",
}


def main() -> None:
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].rstrip(" \n;"))
    by_name = {item["name"]: item for item in catalog["items"]}
    groups = [DETAIL, CROP, RAW_CROP_ALPHA, EMPTY_FLAGS]
    all_flags = [name for group in groups for name in group]
    if len(all_flags) != len(set(all_flags)) or len(all_flags) != 46:
        raise ValueError("Pasted flag set was transcribed incorrectly")
    note_only = set(NOTES) - set(all_flags)
    if note_only != {"item066", "item070", "item078", "item247", "7item235", "7item245"}:
        raise ValueError("Pasted note-only set was transcribed incorrectly")
    saved = HERE / "user_review_2026-09-23.json"
    if saved.is_file():
        # Keep the user's original candidate hashes frozen when the catalog changes.
        output = json.loads(saved.read_text())
    else:
        decisions = {}
        for name in all_flags + sorted(note_only):
            item = by_name[name]
            if name in DETAIL:
                reasons = ["detail / pixels"]
            elif name in CROP:
                reasons = ["crop / placement"]
            elif name in RAW_CROP_ALPHA:
                reasons = ["crop / placement", "alpha / edge"]
            else:
                reasons = []
            candidate = item["candidates"][0] if item["candidates"] else None
            if name in RAW_CROP_ALPHA and candidate:
                raise ValueError(f"Previously raw-only target now has a candidate: {name}")
            decisions[item["id"]] = {
                "decision": "flag" if name in all_flags else "unreviewed",
                "reasons": reasons,
                "note": NOTES.get(name, ""),
                "candidate_index": 0 if candidate else -1,
                "candidate_sha256": candidate["sha256"] if candidate else None,
                "source_sha256": item["source_sha256"],
            }
        output = {
            "schema": 1,
            "scope": "remaining_ui_art",
            "catalog_total": catalog["summary"]["total"],
            "exported_at": EXPORTED_AT,
            "decisions": decisions,
        }
        saved.write_text(json.dumps(output, indent=2) + "\n")
    expected_ids = {by_name[name]["id"] for name in all_flags + sorted(note_only)}
    if (set(output["decisions"]) != expected_ids or len(output["decisions"]) != 52
            or sum(row["decision"] == "flag" for row in output["decisions"].values()) != 46):
        raise ValueError("Saved user review no longer matches the pasted decisions")
    (HERE / "user_review.js").write_text("window.REMAINING_USER_REVIEW = " +
                                         json.dumps(output, separators=(",", ":")) + ";\n")
    print("Verified 46 frozen flags and six note-only entries")


if __name__ == "__main__":
    main()
