"""Publish and verify the approved MM7/MM8 portal revision; preserve earlier artwork."""

import argparse
import copy
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image


OUT = Path(__file__).resolve().parent
HUD = OUT.parent
sys.path.insert(0, str(HUD))
from deploy_icons import INDEX, ROOT, accepted_cell, read, save, sha

REVIEW = HUD / "town_portal_fixup_review"
STATE = HUD / "checkpoint/state.json"
METHOD = "user_approved_mm7_mm8_town_portal_20261004"


def verified(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], path
    return path


def selection():
    selected = {}
    for world, name in [("mm7", "antagrich"), ("mm8", "townport")]:
        manifest_path = REVIEW / world / "details_20261004/manifest.json"
        manifest = read(manifest_path)
        spec = importlib.util.spec_from_file_location("portal_buttons", REVIEW / world / "prepare_buttons.py")
        recipe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recipe)
        assert {item["id"]: item["rect"] for item in recipe.destinations()} == {
            item["id"]: item["rect"] for item in manifest["buttons"]}
        assert manifest["validation"]["result"] == manifest["browser_validation"]["result"] == "PASS"
        assert manifest["validation"]["destinations"] == manifest["browser_validation"]["destinations"] == 6
        verified(manifest["raw"])
        verified(manifest["prompt"])
        verified(manifest["tool_args"])
        verified(manifest["browser_validation"]["capture"])
        for item in manifest["inputs"]:
            verified(item)
        background = verified(manifest["export"])
        with Image.open(background) as image:
            assert image.mode == "RGB" and image.size == (1280, 960)
            pixels = np.asarray(image)
        selected[name] = dict(source=background, sha256=sha(background), world=world, kind="background",
                              rect=dict(x=0, y=0, width=640, height=480), manifest=manifest_path)
        for item in manifest["buttons"]:
            normal = np.asarray(Image.open(verified(item["exports"]["default"])))
            hover_path = verified(item["exports"]["hover"])
            hover = np.asarray(Image.open(hover_path))
            mask = np.asarray(Image.open(verified(item["exports"]["masks"])))
            rect = item["rect"]
            x, y, w, h = (rect[key] for key in ["x", "y", "width", "height"])
            assert normal.shape == hover.shape == (h * 2, w * 2, 3)
            assert np.array_equal(normal, pixels[y * 2:(y + h) * 2, x * 2:(x + w) * 2])
            delta = np.any(normal != hover, axis=2)
            assert delta.any() and not np.any(delta & (mask == 0))
            assert not delta[:4].any() and not delta[-4:].any()
            assert not delta[:, :4].any() and not delta[:, -4:].any()
            selected[item["id"]] = dict(source=hover_path, sha256=sha(hover_path), world=world,
                                        kind="destination", rect=rect, manifest=manifest_path)
    assert len(selected) == 14
    return selected


def verify():
    publication = read(OUT / "accepted.json")
    current, previous = read(INDEX), read(OUT / "previous_accepted_index.json")
    state, before = read(STATE), read(OUT / "checkpoint.before.json")
    assert sha(INDEX) == state["accepted_icon_index"]["sha256"]
    assert current["count"] == previous["count"] == len(current["records"])
    assert current["records"].keys() == previous["records"].keys()
    scope, cells = set(publication["records"]), set(publication["cells"])
    authority = read(OUT / "authority.json")
    assert all(sha(path) == expected for path, expected in authority["evidence_hashes"].items())
    selection()
    for target, old in previous["records"].items():
        if target not in scope:
            assert current["records"][target] == old, target
    for key in before:
        if key not in {"cells", "staged_targets", "reconstructed_targets", "restoration_inventory",
                       "accepted_icon_index", "runtime_icon_installation"}:
            assert state[key] == before[key], key
    for key in ["cells", "staged_targets", "reconstructed_targets", "restoration_inventory"]:
        for name, old in before.get(key, {}).items():
            if name not in (cells if key == "cells" else scope):
                assert state[key][name] == old, name
    for target, record in publication["records"].items():
        assert current["records"][target] == record
        runtime = ROOT / record["runtime_output_path"]
        assert sha(runtime) == sha(record["artifact"]) == sha(record["reviewed_artifact"]) == record["sha256"]
        assert sha(record["previous_artifact"]) == record["previous_sha256"]
        assert runtime.stat().st_mode & 0o777 == 0o644
        assert state["staged_targets"][target]["status"] == "accepted_installed"
        with Image.open(runtime) as image:
            assert image.mode == "RGB" and list(image.size) == record["x2_size"]
    assert all(accepted_cell(state["cells"], cell, lambda _: None) for cell in cells)
    assert all(sha(ROOT / path) == expected for path, expected in publication["preserved"].items())
    result = dict(result="PASS", installed_images=len(scope), backgrounds=2, destination_buttons=12,
                  unrelated_acceptance_and_ledger_records_preserved=True)
    save(OUT / "validation.json", result)
    print(json.dumps(result, indent=2))


def publish():
    assert not (OUT / "accepted.json").exists(), "Already published; use --check or the current-index installer."
    selected = selection()
    current, state = read(INDEX), read(STATE)
    assert sha(INDEX) == state["accepted_icon_index"]["sha256"]
    jobs, frozen = read(HUD / "jobs.json"), read(HUD / "expected_targets.json")
    assert sha(HUD / "jobs.json") == state["jobs_sha256"]
    assert sha(HUD / "expected_targets.json") == jobs["source_manifest_sha256"]
    contracts = {item["id"]: item for item in frozen["targets"]}
    members = [item for job in jobs["jobs"] for item in job["members"]]
    layout = read(state["layout_revision"]["path"]) if state.get("layout_revision") else {"targets": {}}
    selected_cells = {}
    for name, item in selected.items():
        target = "engine--icons--" + name + ".bmp"
        prior = current["records"][target]
        cells = [member["id"] for member in members if member["target"] == target]
        assert len(cells) == 1 and target not in layout["targets"]
        assert all(accepted_cell(state["cells"], cell, lambda _: None) for cell in cells)
        assert sha(ROOT / prior["runtime_output_path"]) == sha(prior["artifact"]) == prior["sha256"]
        assert state["staged_targets"][target]["sha256"] == prior["sha256"]
        assert prior["source_sha256"] == contracts[target]["source_sha256"]
        assert prior["runtime_output_path"] == "assets_dev/engine/icons_x2/" + name + ".png"
        with Image.open(item["source"]) as image:
            assert image.mode == "RGB" and list(image.size) == prior["x2_size"] == contracts[target]["x2_size"]
        selected_cells[target] = cells
    cells = {cell for group in selected_cells.values() for cell in group}
    assert not any(cells.intersection(record.get("dependency_cells", {}))
                   for cell, record in state["cells"].items() if cell not in cells)
    preserved_paths = [ROOT / "assets_dev/engine/ui/gameplay/town_portal.yml",
                       ROOT / "assets_dev/engine/data_tables/town_portal_switch.txt",
                       HUD / "jobs.json", HUD / "expected_targets.json"]
    preserved = {str(path.relative_to(ROOT)): sha(path) for path in preserved_paths}
    for source, destination in [(INDEX, "previous_accepted_index.json"), (STATE, "checkpoint.before.json")]:
        shutil.copyfile(source, OUT / destination)
    for world in ["mm7", "mm8"]:
        for name in ["data.js", "index.html", "README.md", "details_20261004/manifest.json"]:
            destination = OUT / "review_before" / world / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REVIEW / world / name, destination)
    authority = dict(schema="openyamm-icon-revision-authority-v1", method=METHOD,
                     instruction="ok can you also fix the buttons now with the new background and deploy to assets_dev/* ?",
                     approved_sha256={name: item["sha256"] for name, item in selected.items()},
                     scope=dict(worlds=["mm7", "mm8"], backgrounds=2, destination_hover_buttons=12),
                     publication="Exact reviewed PNG bytes; matching crops and native rectangles verified",
                     evidence_hashes={str(path): sha(path) for path in (OUT / "review_before").rglob("*")
                                      if path.is_file()})
    save(OUT / "authority.json", authority)
    records = {}
    for name, item in selected.items():
        target = "engine--icons--" + name + ".bmp"
        prior = current["records"][target]
        destination = OUT / "accepted/engine/icons_x2" / (name + ".png")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item["source"], destination)
        destination.chmod(0o644)
        assert sha(destination) == item["sha256"]
        record = dict(target=target, artifact=str(destination), sha256=item["sha256"],
                      source=prior["source"], source_sha256=prior["source_sha256"],
                      source_native_size=contracts[target]["native_size"], x2_size=prior["x2_size"],
                      runtime_output_path=prior["runtime_output_path"], previous_artifact=prior["artifact"],
                      previous_sha256=prior["sha256"], reviewed_artifact=str(item["source"]),
                      authority=str(OUT / "authority.json"), review_manifest=str(item["manifest"]),
                      acceptance="explicit_user_review_approval", world=item["world"], kind=item["kind"],
                      state="default" if item["kind"] == "background" else "highlighted",
                      logical_draw_rect=item["rect"], placement_changes=False, canvas_migration=None)
        receipt = OUT / "receipts" / (target + ".json")
        save(receipt, record)
        evidence = {str(receipt): sha(receipt), str(OUT / "authority.json"): sha(OUT / "authority.json")}
        review = dict(authority=str(OUT / "authority.json"), decision=str(receipt))
        cell_hashes = {cell: item["sha256"] for cell in selected_cells[target]}
        for cell in cell_hashes:
            state["cells"][cell] = dict(status="accepted", artifact=str(destination), sha256=item["sha256"],
                                       acceptance_method=METHOD, layout_sha256=None, dependency_cells={},
                                       evidence_hashes=evidence, review=review)
        staged = state["staged_targets"][target]
        staged.update(artifact=str(destination), sha256=item["sha256"], cells=cell_hashes,
                      status="accepted_staged", evidence_hashes=evidence, review=review)
        state["reconstructed_targets"][target] = dict(target=target, path=str(destination), sha256=item["sha256"],
                                                     size=prior["x2_size"], cells=cell_hashes,
                                                     status="accepted_full_canvas")
        if target in state.get("restoration_inventory", {}):
            state["restoration_inventory"][target].update(status="accepted", canonical_artifact=str(destination),
                                                         canonical_sha256=item["sha256"],
                                                         acceptance_receipt=str(receipt))
        records[target] = record
    updated = copy.deepcopy(current)
    updated["records"].update(records)
    updated.update(latest_revision=str((OUT / "accepted.json").relative_to(ROOT)),
                   updated_at=datetime.now(timezone.utc).isoformat())
    save(INDEX, updated)
    state["accepted_icon_index"] = dict(path=str(INDEX.relative_to(ROOT)), sha256=sha(INDEX), targets=len(updated["records"]))
    save(STATE, state)
    storage = Path(state["layout_revision"]["path"]).parent if state.get("layout_revision") else STATE.parent
    save(storage / "exports/manifest.json", dict(targets=list(state["staged_targets"].values())))
    save(OUT / "accepted.json", dict(schema="openyamm-accepted-town-portal-revision-v1", records=records,
                                     cells=sorted(cells), authority=str(OUT / "authority.json"), preserved=preserved,
                                     canonical_index_sha256=sha(INDEX), published_at=updated["updated_at"]))
    print(json.dumps(dict(accepted=True, targets=14, backgrounds=2, destination_buttons=12,
                         changed_runtime_images=sum(r["sha256"] != r["previous_sha256"] for r in records.values())),
                     indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with (HUD / "checkpoint/state.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        verify() if args.check else publish()
