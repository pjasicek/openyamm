"""Verify the frozen session without changing any accepted family package."""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json

from PIL import Image
import session_workflow as w


STAGE = Path(__file__).resolve().parent.parent
FAMILIES = ("m596", "m600", "m604", "m608", "m612", "m616", "m620", "m624")


def audit_family(stem, inventory):
    root = STAGE / ("mm8_" + stem)
    out = root / "redo_2x"
    source = w.read(root / "sources.json")
    run = w.read(out / "run.json")
    manifest = w.read(out / "manifest.json")
    acceptance_path = out / "review/acceptance.json"
    acceptance = w.read(acceptance_path)
    row = next(v for v in inventory if v["world"] == "mm8" and v["label"] == source["label"])
    assert w.validate_native(source, row) == run["current_native_tables"]
    assert manifest["animations"] == source["bindings"]
    assert manifest["pixels_per_logical_pixel"] == 2
    assert not manifest["installed"] and not acceptance["installed"]

    mismatches = [name for name, digest in acceptance["artifact_sha256"].items()
                  if w.sha(w.REPO / name) != digest]
    assert not mismatches, (stem, mismatches)

    playback = {step["native_texture"] for actor in source["bindings"].values()
                for action in actor["actions"].values() for steps in action["views"].values()
                for step in steps}
    assert playback == {name for name, frame in source["sources"].items() if frame["referenced"]}
    assert playback <= set(manifest["frames"])
    assert set(manifest["frames"]) | set(manifest["missing_frames"]) == set(source["sources"])
    assert not (set(manifest["missing_frames"]) & playback)

    for name, frame in manifest["frames"].items():
        with Image.open(out / frame["physical_master"]) as image:
            assert image.mode == "RGBA" and list(image.size) == frame["aligned_canvas_size_px"], name
        with Image.open(out / "masks_2x" / (name + ".png")) as mask:
            assert mask.mode == "L" and list(mask.size) == frame["aligned_canvas_size_px"], name

    assert set(manifest["native_palettes"]) == set(source["palette_sources"])
    for palette, record in manifest["native_palettes"].items():
        assert w.sha(out / record["path"]) == record["sha256"] == source["palette_sources"][palette]["sha256"]
    for name, record in manifest["unrestored_native_art"].items():
        assert name in manifest["missing_frames"] and not record["referenced"] and not record["restored"]
        assert w.sha(out / record["path"]) == record["sha256"] == source["sources"][name]["sha256"]
        for preview in record["native_palette_previews"].values():
            assert preview["pixels_per_logical_pixel"] == 1
            assert w.sha(out / preview["path"]) == preview["sha256"]

    selected = {job["id"] for job in run["jobs"] if job.get("selected_raw")}
    assert selected == set(acceptance["review"]["reviewed_jobs"])
    statuses = Counter()
    bootstrap = []
    failed = []
    for job in run["jobs"]:
        for index, attempt in enumerate(job["attempts"], 1):
            statuses[attempt["status"]] += 1
            if attempt["status"] == "interrupted_before_imagegen_call":
                continue
            paths = attempt["referenced_image_paths"]
            inputs = attempt["submitted_inputs"]
            assert paths == [record["path"] for record in inputs]
            assert len(paths) in (2, 3)
            assert paths[0].endswith(job["id"] + "_native.png")
            assert paths[1].endswith(job["id"] + "_outline.png")
            assert inputs[0]["role"] == "untouched_native_complete_animation"
            assert inputs[1]["role"] == "outline_only_geometry_no_shading"
            for record in inputs:
                assert w.sha(Path(record["path"])) == record["sha256"]
            prompt_path = Path(attempt["prompt_path"])
            assert prompt_path.read_text().startswith(w.HEADER)
            assert w.sha(prompt_path) == attempt["prompt_sha256"]
            if len(paths) == 2:
                assert attempt["bootstrap_exception"] and job["id"] == "standing_0_sheet"
                bootstrap.append({"job": job["id"], "attempt": index})
        if not job.get("selected_raw"):
            assert job["status"] == "failed_tool"
            assert set(job["frames"]) <= set(manifest["missing_frames"])
            failed.append({"job": job["id"], "frames": job["frames"], "status": job["status"],
                           "last_failure": job["attempts"][-1].get("reason"),
                           "latest_submitted_prompt": job["attempts"][-1]["prompt_path"],
                           "latest_submitted_inputs": job["attempts"][-1]["submitted_inputs"],
                           "requested_retry_context": job.get("retry_context")})

    required = ("exact_atlas_extraction", "exact_crop_reconstruction", "exact_native_animation_bindings",
                "exact_fractional_anchor_mapping", "exact_mirrored_anchor_mapping", "variant_alpha_unchanged",
                "base_bypass_exact", "unused_art_excluded_from_playback", "actual_outline_attachment_validated")
    assert all(acceptance["checks"][key] for key in required)
    assert acceptance["scope_complete"] == (not manifest["missing_frames"])
    assert not acceptance["checks"]["timed_playback_viewed"]
    result = {
        "family": "mm8_" + stem,
        "label": source["label"],
        "descriptor_ids": [int(key) for key in source["bindings"]],
        "status": acceptance["status"],
        "scope_complete": acceptance["scope_complete"],
        "native_frame_names": len(source["sources"]),
        "enhanced_frame_names": len(manifest["frames"]),
        "unique_enhanced_frames": len(manifest["frames"]) - len(manifest["pixel_aliases"]),
        "native_playback_frame_names": len(playback),
        "unused_native_frame_names": len(source["sources"]) - len(playback),
        "all_native_playback_art_restored": manifest["all_playback_art_restored"],
        "selected_whole_animation_view_sheets": len(selected),
        "required_whole_animation_view_sheets": len(run["jobs"]),
        "actual_generated_sampling": manifest["actual_generated_sampling"],
        "physical_pixels_per_logical_pixel": 2,
        "native_palettes": sorted(int(key) for key in manifest["native_palettes"]),
        "atlas_base_mask_pairs": len(manifest["pages"]),
        "atlas_memory_bytes": acceptance["checks"]["memory_bytes"],
        "verified_frozen_artifact_hashes": len(acceptance["artifact_sha256"]),
        "frozen_hash_mismatches": mismatches,
        "attempt_status_counts": dict(statuses),
        "bootstrap_exceptions": bootstrap,
        "failed_jobs": failed,
        "missing_frames": manifest["missing_frames"],
        "timed_playback_viewed": False,
        "native_bindings_and_source_hashes_verified": True,
        "all_actual_submitted_attachment_and_prompt_hashes_verified": True,
        "acceptance": str(acceptance_path.relative_to(w.REPO)),
        "acceptance_sha256": w.sha(acceptance_path),
        "manifest": str((out / "manifest.json").relative_to(w.REPO)),
        "installed": False,
    }
    print(stem, result["status"], "verified", result["verified_frozen_artifact_hashes"], "hashes", flush=True)
    return result


def main():
    inventory_path = w.CREATURES / "remaining_inventory.json"
    inventory = w.read(inventory_path)["families"]
    families = [audit_family(stem, inventory) for stem in FAMILIES]
    totals = {key: sum(family[key] for family in families) for key in (
        "native_frame_names", "enhanced_frame_names", "unique_enhanced_frames", "native_playback_frame_names",
        "unused_native_frame_names", "selected_whole_animation_view_sheets", "required_whole_animation_view_sheets",
        "atlas_base_mask_pairs", "verified_frozen_artifact_hashes")}
    totals["complete_families"] = sum(family["scope_complete"] for family in families)
    totals["partial_families"] = len(families) - totals["complete_families"]
    totals["unrestored_native_frame_names"] = totals["native_frame_names"] - totals["enhanced_frame_names"]
    totals["native_palette_files"] = sum(len(family["native_palettes"]) for family in families)
    totals["atlas_memory_bytes"] = sum(family["atlas_memory_bytes"]["total_base_mask_packing"] for family in families)
    totals["below_2x_enhanced_frame_names"] = sum(len(family["actual_generated_sampling"]["below_2x_frames"]) for family in families)
    report = {
        "session": "session_mm8_07",
        "status": "partial_generation_blocked",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "scope_complete": all(family["scope_complete"] for family in families),
        "all_native_playback_art_restored": all(family["all_native_playback_art_restored"] for family in families),
        "method": "one complete native animation/view sheet plus matching separate outline-only guide and same-family appearance",
        "inventory_path": str(inventory_path.relative_to(w.REPO)),
        "inventory_sha256": w.sha(inventory_path),
        "families": families,
        "totals": totals,
        "review_method": "Every selected pose inspected statically in native order with independent placement features, all palette/mask poses, representative unresized detail/alpha and final atlas edge contacts.",
        "timed_playback_viewed": False,
        "installed": False,
        "preserved": ["older accepted packages", "shared code and skills", "global ledgers", "runtime assets"],
    }
    destination = Path(__file__).resolve().parent
    w.save(destination / "SESSION_RESULTS.json", report)
    lines = ["# MM8 packed outline restoration — session 07", "",
             "Seven families are complete. Naga is partial: 156/160 native frame names and 36/37 complete animation/view sheets. All eight families have their entire native playback art restored. No gameplay installation.", "",
             "| Family | Merged IDs | Enhanced/native frames | Whole sheets | Minimum actual detail | Status |",
             "| --- | --- | ---: | ---: | ---: | --- |"]
    for family in families:
        prefix = Path("..") / family["family"]
        state = "Complete" if family["scope_complete"] else "Partial — imagegen blocked"
        lines.append(f"| [{family['label']}]({prefix}/README.md) | {family['descriptor_ids'][0]}–{family['descriptor_ids'][-1]} | {family['enhanced_frame_names']}/{family['native_frame_names']} | {family['selected_whole_animation_view_sheets']}/{family['required_whole_animation_view_sheets']} | {family['actual_generated_sampling']['minimum']:.4f}× | {state} |")
    lines.extend(["", f"Coverage: **{totals['enhanced_frame_names']}/{totals['native_frame_names']} native frame names**, **{totals['selected_whole_animation_view_sheets']}/{totals['required_whole_animation_view_sheets']} complete sheets**, and **{totals['native_playback_frame_names']}/{totals['native_playback_frame_names']} playback source names**. The Nightmare native `m600sa5` pixel alias of `m600sa4` is preserved, giving {totals['unique_enhanced_frames']} unique enhanced images.", "",
                  f"Checked physical masters are 2×. Actual generated sampling is measured independently per frame; {totals['below_2x_enhanced_frame_names']} enhanced frame names are below 2× and remain accepted after visual review to retain complete cycles. No animation was split for resolution. Full per-frame sampling is in each manifest and [the JSON report](SESSION_RESULTS.json).", "",
                  f"Exports include {totals['atlas_base_mask_pairs']} matching RGBA8 base/R8 mask atlas pairs and {totals['native_palette_files']} byte-exact native palette files, all enhanced frame masters and authored selective masks. Total uncompressed base/mask atlas packing is {totals['atlas_memory_bytes']:,} bytes ({totals['atlas_memory_bytes'] / (1024 ** 3):.3f} GiB), without mipmaps. Timing, native held occurrences, aliases, mirrors, flags and fractional anchors match current native data; unused art is excluded from playback.", "",
                  "Every selected complete sheet used an actually attached native-colour PNG and its matching separate outline-only PNG. Actual submitted paths, roles, prompt prefix and SHA-256 hashes were verified for every submitted attempt, including failures/retries. When no adequate older same-family detail existed, the first standing sheet used the recorded two-input bootstrap exception; subsequent calls attached selected detailed same-family appearance. Bone Dragon used adequate preserved older appearance art. Outline white interiors supplied no shading or material texture; recolour masks were authored after generation.", "",
                  "All selected poses and independent placement features were inspected against native pairs. Every native palette/mask pose, representative original-resolution material detail/alpha and final cleaned/atlas edge contacts were inspected. Review was static in native sequence order; timed playback was not viewed. The per-family acceptance records freeze selected raw returns, cleaned art, masters, masks, atlas pages and review evidence.", "",
                  f"Final verification rechecked **{totals['verified_frozen_artifact_hashes']:,} frozen artifact hashes** with zero mismatches, every actual submitted input/prompt hash, all current native source and palette hashes, descriptor IDs and exact animation records. Seven full acceptance records and Naga's generated-subset acceptance are frozen locally. Naga's full scoped acceptance is explicitly false.", "",
                  "The incomplete job is Naga `unused_f_3_sheet` (four frames: `m624fa3`–`m624fd3`). Built-in imagegen rejected this job at the input stage even with the user-approved shorter prompt and accepted rear-oblique appearance; request `b4a655d1-9948-4963-af5d-ce331b135567` and full tool errors remain in Naga's run record. These four unused originals and all three palette previews are preserved at native 1× resolution, excluded from restored coverage and playback. Earlier native archives for A4 are retained as history, but its eight poses now have accepted enhanced masters.", "",
                  "The user's first clarification retry explicitly stated **MM8 NAGA CREATURE WITH SCALES AND NO NUDITY**, retaining the native green costume; both calls were blocked. The subsequent approved shorter prompt used accepted matching rear-view appearance references, with the untouched native-colour and matching outline PNGs still actually attached. A4 returned one complete eight-pose sheet on attempt 6, delivered at 1246 × 1263; its minimum actual generated sampling is 1.6643356643×. All eight poses, native anatomy, independent placement features, material detail and palette/mask variants were reviewed. Final-row AG4/AH4 support drift was corrected with hash-bound whole-pose translations and one unchanged animation scale. The previously accepted 148 poses and masks remain byte-identical. Exact current prompt/input hashes and prior failures are recorded in the family run and acceptance records; see [the JSON report](SESSION_RESULTS.json).", "",
                  "All staging remains inside the eight requested family directories under `session_mm8_07/`. Older accepted packages, shared tools/skills, global ledgers and runtime assets were preserved. No gameplay installation.", ""])
    (destination / "SESSION_RESULTS.md").write_text("\n".join(lines))
    print(json.dumps(totals, indent=2))


if __name__ == "__main__":
    main()
