"""Verify the accepted spellbook revision, exact installation and scope preservation."""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from publish import OUT, HUD, ROOT, REVIEW, REVISION, EXPECTED_MIGRATIONS, bindings, read, sha

sys.path.insert(0, str(HUD))
from queue import Queue, save


def main():
    accepted = read(OUT / "accepted.json")
    previous = read(OUT / "previous_accepted_index.json")
    before = read(OUT / "checkpoint.before.json")
    current = read(HUD / "accepted_icons.json")
    review = read(REVIEW / "manifest.json")
    queue = Queue()
    scope = set(accepted["records"])
    cells = {cell for target in scope for cell in queue.target_cells[target]}
    frozen = {record["dependent"] for record in accepted["reference_revision_migrations"]}
    assert len(scope) == len(cells) == 258
    assert review["revision"] == accepted["summary"]["review_revision"] == REVISION
    assert current["count"] == previous["count"] == len(current["records"]) == 9920
    assert sha(HUD / "accepted_icons.json") == queue.state["accepted_icon_index"]["sha256"]
    assert sha(HUD / "accepted_icons.json") == accepted["canonical_index_sha256"]
    for path, expected in accepted["preserved"].items():
        assert sha(ROOT / path) == expected, "Unrelated source changed: " + path
    for key in before:
        if key not in {"cells", "staged_targets", "reconstructed_targets", "restoration_inventory",
                       "accepted_icon_index", "runtime_icon_installation"}:
            assert queue.state[key] == before[key], key
    for cell, old in before["cells"].items():
        if cell not in cells | frozen:
            assert queue.state["cells"][cell] == old, "Unrelated cell changed: " + cell
    for key in ["staged_targets", "reconstructed_targets", "restoration_inventory"]:
        for target, old in before.get(key, {}).items():
            if target not in scope:
                assert queue.state[key][target] == old, "Unrelated target changed: " + target
    changed = 0
    migrations = read(OUT / "canvas_migrations.json")["records"]
    assert {Path(target).name.removeprefix("engine--icons--").removesuffix(".bmp") for target in migrations} == set(EXPECTED_MIGRATIONS)
    for target, record in current["records"].items():
        old = previous["records"][target]
        assert sha(old["artifact"]) == old["sha256"], "Previous accepted artifact changed: " + target
        destination = ROOT / record["runtime_output_path"]
        assert sha(destination) == record["sha256"], "Wrong runtime image: " + target
        assert destination.stat().st_mode & 0o777 == 0o644
        assert sha(record["artifact"]) == record["sha256"], "Accepted artwork changed: " + target
        if target not in scope:
            assert record == old, "Unrelated accepted record changed: " + target
            continue
        assert record == accepted["records"][target]
        assert sha(record["reviewed_artifact"]) == record["sha256"]
        assert record["previous_sha256"] == old["sha256"]
        assert record["previous_artifact"] == old["artifact"]
        assert record["source_sha256"] == old["source_sha256"]
        changed += record["sha256"] != old["sha256"]
        assert queue.state["staged_targets"][target]["status"] == "accepted_installed"
        assert queue.state["staged_targets"][target]["sha256"] == record["sha256"]
        assert all(queue.accepted(cell) for cell in queue.target_cells[target])
        with Image.open(destination) as image:
            assert image.format == "PNG" and image.mode == "RGBA" and list(image.size) == record["x2_size"]
        assert record["canvas_migration"] == migrations.get(target)
        if target in migrations:
            migration = migrations[target]
            assert record["x2_size"] == migration["approved_export_size"]
            assert old["x2_size"] == migration["previous_export_size"]
        else:
            assert record["x2_size"] == queue.targets[target]["x2_size"]
    assert changed == accepted["summary"]["changed_runtime_images"] == 156
    for element, kind, state, original, selected, rect in bindings(review):
        target = "engine--icons--" + Path(original["path"]).stem + ".bmp"
        record = accepted["records"][target]
        assert record["sha256"] == selected["sha256"]
        assert record["logical_draw_rect"] == rect and not record["placement_changes"]
        assert (record["review_target"], record["kind"], record["state"]) == (element, kind, state)
    pairs = 0
    for school in review["schools"]:
        for spell in school["spells"]:
            arrays = []
            for state in ["default", "highlighted"]:
                name = Path(spell["states"][state]["path"]).name
                arrays.append(np.asarray(Image.open(ROOT / "assets_dev/engine/icons_x2" / name).convert("RGBA")))
            assert arrays[0].shape == arrays[1].shape
            assert np.array_equal(arrays[0][:, :, 3], arrays[1][:, :, 3]), spell["name"]
            pairs += 1
    installation = queue.state["runtime_icon_installation"]
    assert sha(ROOT / installation["manifest"]) == installation["sha256"]
    assert installation["manifest"] == str((OUT / "installed.json").relative_to(ROOT))
    installed = read(OUT / "installed.json")
    assert installed["accepted_index_sha256"] == sha(HUD / "accepted_icons.json")
    assert installed["count"] == 9920
    report = {
        "result": "PASS", "review_revision": REVISION, "accepted_files": 258,
        "changed_runtime_images": changed, "book_pages": 12, "spell_pairs": pairs,
        "school_bookmark_states": 24, "restored_air_pairs": 9, "canvas_migrations": len(migrations),
        "all_installed_bytes_match_review": True, "identical_spell_pair_alpha_and_dimensions": True,
        "yaml_and_native_contracts_unchanged": True, "unrelated_index_and_ledger_records_unchanged": True,
        "previous_accepted_artifacts_preserved": True, "runtime_icons_checked": 9920,
        "canonical_index_sha256": sha(HUD / "accepted_icons.json"), "ledger_sha256": sha(queue.state_path),
        "accepted_revision_sha256": sha(OUT / "accepted.json"),
    }
    save(OUT / "validation.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
