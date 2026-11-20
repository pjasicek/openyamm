#!/usr/bin/env python3
"""Check the approved handoff against its sources and the real runtime layout parser."""
import hashlib
import json
import stat
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(nodes):
    for node in nodes:
        yield node
        yield from flatten(node.get("children", []))


def main():
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    receipts = {r["path"]: r for r in json.loads((HERE / "asset_receipts.json").read_text())}
    source_manifest = json.loads((HERE.parent / "asset_manifest.json").read_text())
    graphics = {Path(a["target"]).name: a for a in source_manifest["assets"]}
    files = []
    for path in sorted((HERE / "engine").rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(HERE))
        check(f"0644: {relative}", stat.S_IMODE(path.stat().st_mode) == 0o644)
        check(f"Recorded file hash: {relative}", digest(path) == receipts[relative]["sha256"])
        entry = dict(path=relative, sha256=digest(path), bytes=path.stat().st_size,
                     intended_target="assets_dev/" + relative, provenance=receipts[relative])
        if path.suffix == ".png":
            image = Image.open(path)
            alpha = image.getchannel("A")
            check(f"RGBA and lowercase: {path.name}", image.mode == "RGBA" and path.name == path.name.lower())
            check(f"Approved pixel dimensions: {path.name}", list(image.size) == graphics[path.name]["pixels"])
            check(f"Exact approved artwork: {path.name}", digest(path) == graphics[path.name]["sha256"])
            entry.update(pixels=list(image.size), alpha_range=list(alpha.getextrema()),
                         logical_size=graphics[path.name].get("logical_size"))
            if "_icon_" in path.stem:
                check(f"Real transparent icon: {path.name}", alpha.getextrema() == (0, 255))
        files.append(entry)

    layout = HERE / "engine/ui/gameplay/journal.yml"
    document = yaml.safe_load(layout.read_text())
    nodes = list(flatten(document["elements"]))
    index = {n["id"]: n for n in nodes}
    reference = HERE / "reference_layouts/journal.yml"
    original = list(flatten(yaml.safe_load(reference.read_text())["elements"]))
    check("All native IDs retained and unique", len(nodes) == len(index) and {n["id"] for n in original} <= index.keys())
    check("Mounted journal unchanged", digest(reference) == digest(ROOT / "assets_dev/engine/ui/gameplay/journal.yml"))
    check("Centered native 640x480 root", [index["JournalRoot"][k] for k in ["anchor", "width", "height"]]
          == ["center", 640, 480])
    check("Exact original 300x300 map rectangle", [index["JournalMapViewport"][k] for k in
          ["offset_x", "offset_y", "width", "height"]] == [131, 101, 300, 300])
    check("Refined body width with native height and font", index["JournalTextViewport"]["text"]["font"] == "AUTONOTE"
          and index["JournalTextViewport"]["text"]["scale"] == 0.9
          and [index["JournalTextViewport"][k] for k in ["width", "height"]] == [360, 293])
    assets = {p.stem for p in (HERE / "engine/icons_x2").glob("*.png")}
    check("Every layout asset resolves", all(name in assets for n in nodes for name in n.get("asset", {}).values()))
    check("Native input targets stay interactive", all(index[n["id"]].get("interactive")
          for n in original if n.get("interactive")))
    check("Icon/label children do not steal input", all(not n.get("interactive", False) for n in nodes
          if n["id"].endswith(("Icon", "Label"))))
    allowed_assets = {"default", "highlighted", "pressed", "selected", "frame", "health_bar", "mana_bar"}
    check("No silently ignored disabled YAML key", all(n.get("asset", {}).keys() <= allowed_assets for n in nodes))
    check("Map frame center remains transparent", Image.open(HERE / "engine/icons_x2/obsidian_journal_map_frame.png")
          .getpixel((325, 325))[3] == 0)
    frame = Image.open(HERE / "engine/icons_x2/obsidian_journal_map_frame.png")
    check("Map frame contains visible edges", frame.getchannel("A").getextrema()[1] > 100)

    for path in (HERE / "engine/fonts/truetype").glob("*.yml"):
        descriptor = yaml.safe_load(path.read_text())
        check(f"Font descriptor resolves: {path.name}", (path.parent / descriptor["file"]).is_file())
        if path.stem != "fondamento":
            original = yaml.safe_load((HERE / f"reference_fonts/{path.name}").read_text())
            if path.stem == "autonote":
                original["presentation"] = "tintable"
            check(f"Native font metrics preserved: {path.name}", original == descriptor)
    check("Tintable Autonote uses supported presentation", yaml.safe_load(
          (HERE / "engine/fonts/truetype/autonote.yml").read_text())["presentation"] == "tintable")
    check("Original black-ink descriptor preserved", yaml.safe_load(
          (HERE / "reference_fonts/autonote.yml").read_text())["presentation"] == "black-ink")
    font_differences = json.loads((HERE / "runtime_font_differences.json").read_text())
    recorded_differences = {entry["face"]: entry for entry in font_differences}
    for name in ["book2", "autonote", "create", "smallnum", "lucida"]:
        staged = HERE / f"engine/fonts/truetype/openyamm_{name}_faithful.ttf"
        live = ROOT / f"assets_dev/engine/fonts/truetype/openyamm_{name}_faithful.ttf"
        check(f"Exact approved font preserved: {name}", digest(staged) == digest(HERE.parent / f"assets/fonts/{name}.ttf"))
        if digest(staged) != digest(live):
            check(f"Later runtime font change explicitly recorded: {name}", name in recorded_differences
                  and recorded_differences[name]["current_runtime_sha256"] == digest(live)
                  and recorded_differences[name]["reviewed_sha256"] == digest(staged))
    for path in (HERE / "reference_fonts").glob("*.yml"):
        check(f"Mounted descriptor unchanged: {path.name}", digest(path)
              == digest(ROOT / f"assets_dev/engine/fonts/truetype/{path.name}"))
    states = yaml.safe_load((HERE / "design/button_states.yml").read_text())
    check("Four plate families with all five states", len(states["families"]) == 4
          and all(len(family) == 5 and set(family.values()) <= assets for family in states["families"].values()))
    pngs = [f for f in files if f["path"].endswith(".png")]
    check("Forty approved PNGs, including finishing pieces", len(pngs) == 40)
    check("Review fixtures excluded from runtime payload", not any(any(term in f["path"] for term in
          ["new-sorpigal", "content.js", "2090", "2091"]) for f in files))

    harness = ROOT / "level_generation/ui/obsidian_overlays_20260928/staging/validate_layouts.cpp"
    with tempfile.TemporaryDirectory(prefix="obsidian-journal-stage-") as temp:
        binary = Path(temp) / "check"
        subprocess.run(["c++", "-std=c++20", "-O1", "-ffunction-sections", "-fdata-sections", "-I", str(ROOT),
                        "-I", str(ROOT / "build/_deps/yaml-cpp-src/include"), str(harness),
                        str(ROOT / "game/ui/UiLayoutManager.cpp"),
                        str(ROOT / "build/_deps/yaml-cpp-build/libyaml-cpp.a"),
                        "-Wl,--gc-sections", "-o", str(binary)], check=True, capture_output=True, text=True)
        result = subprocess.run([str(binary), str(layout)], check=True, capture_output=True, text=True)
        check("Actual UiLayoutManager parsed staged journal", "PASS: 1 staged layouts" in result.stdout)

    browser = json.loads((HERE / "masters/browser_review.json").read_text())
    check("Approved browser interactions passed", browser["result"] == "PASS" and not browser["browserErrors"])
    approval = json.loads((HERE / "approval.json").read_text())
    for preview in approval["previews"]:
        check(f"Approval capture preserved: {preview['path']}", digest(HERE / preview["path"]) == preview["sha256"])
    manifest = dict(design=approval["design"], approval_date=approval["approved_date"],
                    status="approved-design-staged-unmounted", files=files, runtime_integrated=False,
                    renderer_requirements="INTEGRATION.md", design_contracts=["design/theme.yml", "design/button_states.yml"],
                    reference_graphics="../assets/generated/", prompt_set="masters/generation_prompts.json",
                    approval="approval.json", existing_runtime_dependencies=["Native journal data/unlocks", "Map renderer/pins/reveal"])
    manifest["runtime_font_differences"] = font_differences
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (HERE / "validation.json").write_text(json.dumps(dict(result="PASS", checks=checks,
        totals=dict(layouts=1, pngs=len(pngs), font_faces=6, payload_files=len(files), browser_checks=len(browser["checks"])),
        runtime_integrated=False, game_build_or_runtime_test=False,
        parser="Actual UiLayoutManager.cpp with the existing yaml-cpp library"), indent=2) + "\n")
    print(f"PASS: 1 runtime YAML draft, {len(pngs)} PNGs, 6 font faces; {len(checks)} staging checks.")


if __name__ == "__main__":
    main()
