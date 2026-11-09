#!/usr/bin/env python3
"""Extract retry returns without overwriting first-pass imagegen candidates."""

import json

from process_imagegen_regen import RUN, process_sheet


def main() -> None:
    plan = json.loads((RUN / "retry_plan.json").read_text())
    report = {"schema": 1, "tool": "built-in image_gen", "sheets": {}, "items": {}}
    for sheet in plan["sheets"]:
        record = process_sheet(sheet, "retry_returns", "retry_candidates")
        report["sheets"][sheet["id"]] = {key: value for key, value in record.items() if key != "items"}
        report["items"].update(record["items"])
    (RUN / "retry_report.json").write_text(json.dumps(report, indent=2) + "\n")
    counts = {}
    for item in report["items"].values():
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print(json.dumps({"returned_sheets": sum(s["status"] != "awaiting_imagegen_return"
                                              for s in report["sheets"].values()),
                      "candidate_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
