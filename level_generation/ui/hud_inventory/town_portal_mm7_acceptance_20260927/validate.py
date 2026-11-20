"""Verify exact MM7 Town Portal deployment and preservation of all other accepted icons."""

import json

from PIL import Image

from publish import APPROVED, CURRENT, HUD, OUT, ROOT, Queue, check_review, read, save, sha


def main():
    accepted = read(OUT / "accepted.json")
    current = read(CURRENT)
    previous = read(OUT / "previous_accepted_index.json")
    before = read(OUT / "checkpoint.before.json")
    queue = Queue()
    scope = set(accepted["records"])
    cells = {cell for target in scope for cell in queue.target_cells[target]}
    assert len(scope) == len(cells) == 7
    assert sha(CURRENT) == queue.state["accepted_icon_index"]["sha256"] == accepted["canonical_index_sha256"]
    assert set(current["records"]) == set(previous["records"])
    assert current["count"] == previous["count"] == len(current["records"]) == 9920
    for path, expected in accepted["preserved"].items():
        assert sha(ROOT / path) == expected, path
    for path, expected in read(OUT / "authority.json")["evidence_hashes"].items():
        assert sha(path) == expected, path
    for key in before:
        if key not in {"cells", "staged_targets", "reconstructed_targets", "restoration_inventory",
                       "accepted_icon_index", "runtime_icon_installation"}:
            assert queue.state[key] == before[key], key
    for cell, old in before["cells"].items():
        if cell not in cells:
            assert queue.state["cells"][cell] == old, "Unrelated cell changed: " + cell
    for key in ["staged_targets", "reconstructed_targets", "restoration_inventory"]:
        for target, old in before.get(key, {}).items():
            if target not in scope:
                assert queue.state[key][target] == old, "Unrelated target changed: " + target
    changed = 0
    for target, record in current["records"].items():
        old = previous["records"][target]
        runtime = ROOT / record["runtime_output_path"]
        assert sha(old["artifact"]) == old["sha256"], "Earlier artwork changed: " + target
        assert sha(record["artifact"]) == sha(runtime) == record["sha256"], target
        assert runtime.stat().st_mode & 0o777 == 0o644, target
        if target not in scope:
            assert record == old, "Unrelated accepted record changed: " + target
            continue
        assert record == accepted["records"][target]
        assert record["sha256"] == APPROVED[runtime.stem] == sha(record["reviewed_artifact"])
        assert record["previous_artifact"] == old["artifact"] and record["previous_sha256"] == old["sha256"]
        assert record["source_sha256"] == old["source_sha256"]
        assert record["x2_size"] == old["x2_size"] == queue.targets[target]["x2_size"]
        assert record["canvas_migration"] is None and not record["placement_changes"]
        assert queue.state["staged_targets"][target]["status"] == "accepted_installed"
        assert queue.state["staged_targets"][target]["sha256"] == record["sha256"]
        assert all(queue.accepted(cell) for cell in queue.target_cells[target])
        with Image.open(runtime) as image:
            assert image.format == "PNG" and image.mode == "RGB" and list(image.size) == record["x2_size"]
        changed += record["sha256"] != old["sha256"]
    assert changed == accepted["summary"]["changed_runtime_images"] == 7
    check_review()
    installation = queue.state["runtime_icon_installation"]
    assert installation["manifest"] == str((OUT / "installed.json").relative_to(ROOT))
    assert sha(ROOT / installation["manifest"]) == installation["sha256"]
    installed = read(OUT / "installed.json")
    assert installed["accepted_index_sha256"] == sha(CURRENT) and installed["count"] == 9920
    report = {
        "result": "PASS", "accepted_files": 7, "backgrounds": 1, "hover_buttons": 6,
        "changed_runtime_images": changed, "all_installed_bytes_match_review": True,
        "native_dimensions_and_placement_unchanged": True, "exact_background_crops": True,
        "highlight_changes_confined_to_masks": True, "seamless_four_pixel_borders": True,
        "unrelated_index_and_ledger_records_unchanged": True, "previous_accepted_artifacts_preserved": True,
        "runtime_icons_checked": 9920, "canonical_index_sha256": sha(CURRENT),
        "ledger_sha256": sha(queue.state_path), "accepted_revision_sha256": sha(OUT / "accepted.json"),
    }
    save(OUT / "validation.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
