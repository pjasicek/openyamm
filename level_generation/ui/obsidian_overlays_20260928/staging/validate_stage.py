#!/usr/bin/env python3
"""Validate handoff invariants and produce its manifest; never modify live assets."""
import hashlib
import json
import re
import stat
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
checks = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(elements):
    for e in elements:
        yield e
        yield from flatten(e.get("children", []))


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    receipts = {r["path"]: r for r in json.loads((HERE / "asset_receipts.json").read_text())}
    layouts = sorted((HERE / "engine/ui/gameplay").glob("*.yml"))
    check("Eleven overlay/shared-chrome layout drafts",len(layouts) == 11)
    dependencies = set()
    docs = {}
    allowed = {"id","anchor","anchor_space","offset_x","offset_y","width","height","bottom_to","bottom_gap",
               "z_index","scale","visible","interactive","asset","text","notes","children"}
    for file in layouts:
        doc = yaml.safe_load(file.read_text())
        original = yaml.safe_load((HERE / "reference_layouts" / file.name).read_text())
        live = ROOT / "assets_dev/engine/ui/gameplay" / file.name
        check(f"Live {file.name} unchanged", sha(live) == sha(HERE / "reference_layouts" / file.name))
        nodes = list(flatten(doc["elements"]))
        idx = {e["id"]: e for e in nodes}
        docs[file.stem] = idx
        check(f"{file.name}: unique IDs, every original ID retained",
              len(idx) == len(nodes) and {e["id"] for e in flatten(original["elements"])} <= idx.keys())
        check(f"{file.name}: no invented runtime layout keys",all(not (e.keys() - allowed) for e in nodes))
        for e in nodes:
            for name in e.get("asset", {}).values():
                if name.startswith("obsidian_"):
                    check(f"Resolved staged asset {name}",(HERE / f"engine/icons_x2/{name}.png").is_file())
                else:
                    dependencies.add(name)
    inv = docs["character"]
    grid = inv["CharacterInventoryGrid"]
    page = inv["CharacterInventoryPage"]
    check("Inventory native origin, dimensions and 32px cells",
          [page.get("offset_x",0)+grid["offset_x"], page["offset_y"]+grid["offset_y"], grid["width"],grid["height"]] == [7,32,448,288])
    check("Inventory footer hidden", inv["CharacterInventoryInfo"]["visible"] is False)
    for key, rect in [("RestButton8Hours",[61,155,272,42]),("RestButtonUntilDawn",[100,239,188,30]),
                      ("RestButton1Hour",[100,271,188,30]),("RestButton5Minutes",[100,303,188,30]),
                      ("RestButtonExit",[361,299,185,43])]:
        e=docs["rest"][key]
        check(f"Unchanged rest action rectangle {key}",[e["offset_x"],e["offset_y"],e["width"],e["height"]] == rect)
    check("Item value bottom anchored",docs["item_inspect"]["ItemInspectValue"]["anchor"] == "bottom_left")
    check("Item footer divider present", "ItemInspectValueDivider" in docs["item_inspect"])
    check("Quickref has reputation/fame and five column regions",all(k in docs["quick_reference"] for k in
          ["QuickReferenceReputation","QuickReferenceFame"] + [f"QuickReferenceMemberColumn{i}" for i in range(1,6)]))
    files=[]
    for path in sorted((HERE / "engine").rglob("*")):
        if not path.is_file():
            continue
        rel=str(path.relative_to(HERE))
        entry=dict(path=rel,sha256=sha(path),bytes=path.stat().st_size,
                   intended_target="assets_dev/"+rel,provenance=receipts.get(rel))
        check(f"0644: {rel}",stat.S_IMODE(path.stat().st_mode)==0o644)
        if path.suffix == ".png":
            im=Image.open(path)
            check(f"RGBA PNG: {path.name}",im.mode == "RGBA")
            check(f"Lowercase: {path.name}",path.name==path.name.lower())
            alpha=im.getchannel("A")
            entry.update(pixels=list(im.size),alpha_range=list(alpha.getextrema()),
                         fully_transparent_pixels=alpha.histogram()[0])
            if path.stem.startswith("obsidian_buff_"):
                check(f"Uniform alpha buff: {path.name}",im.size==(128,128) and alpha.getextrema()[0]==0
                      and alpha.getextrema()[1]>=250)
        files.append(entry)
    pngs=[f for f in files if f["path"].endswith(".png")]
    buffs=[f for f in pngs if "/obsidian_buff_" in f["path"]]
    check("All 22 glyph-free buff illustrations exported",len(buffs)==22)
    for part in ["tl","tr","bl","br","top","bottom","left","right"]:
        file=HERE/f"engine/icons_x2/obsidian_frame_{part}.png"
        check(f"Unchanged true-alpha frame {part}",sha(file)==sha(HERE.parent/f"assets/generated/frame-{part}.png")
              and Image.open(file).getchannel("A").getextrema()[0]==0)
    check("Inventory raster exactly 2x logical",Image.open(HERE/"engine/icons_x2/obsidian_inventory_surface.png").size==(936,692))
    check("No vellum or comparison reading fonts in payload",not any(re.search("vellum|source(?:serif|sans)",f["path"],re.I) for f in files))
    # The actual C++ parser is small; compile only it and this harness, never the game or Vulkan targets.
    with tempfile.TemporaryDirectory(prefix="openyamm-obsidian-layout-") as temp:
        binary=Path(temp)/"validate-layouts"
        command=["c++","-std=c++20","-O1","-ffunction-sections","-fdata-sections","-I",str(ROOT),
                 "-I",str(ROOT/"build/_deps/yaml-cpp-src/include"),str(HERE/"validate_layouts.cpp"),
                 str(ROOT/"game/ui/UiLayoutManager.cpp"),str(ROOT/"build/_deps/yaml-cpp-build/libyaml-cpp.a"),
                 "-Wl,--gc-sections","-o",str(binary)]
        subprocess.run(command,check=True,capture_output=True,text=True)
        result=subprocess.run([str(binary),*[str(p) for p in layouts]],check=True,capture_output=True,text=True)
        check("All drafts accepted by actual UiLayoutManager::loadLayoutText", "PASS: 11" in result.stdout)
    captures=[]
    for name in ["inventory","stats","skills","awards","rest","quickref","dialogue","inspect-potion","buffs","type"]:
        f=HERE.parent/f"previews/r03/{name}.png"
        captures.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f)))
    f=HERE.parent/"previews/r02/inspect-monster.png"
    captures.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f)))
    manifest=dict(design="obsidian-overlays-r03",approval_date="2026-09-28",status="approved-visual-design-unmounted-runtime-drafts",
                  baselines=["gameplay-obsidian-r04","fullscreen-carved-obsidian-r06","overlays-r03"],
                  files=files,existing_runtime_asset_dependencies=sorted(dependencies),approved_reference_captures=captures,
                  renderer_requirements="INTEGRATION.md",design_contracts=["design/theme.yml","design/frame.yml","design/font_registration.yml"])
    write("manifest.json",manifest)
    write("validation.json",dict(result="PASS",date="2026-09-28",checks=checks,
          totals=dict(layouts=len(layouts),pngs=len(pngs),buffs=len(buffs),payload_files=len(files)),
          runtime_integrated=False,game_build_or_runtime_test=False,
          parser="Actual UiLayoutManager.cpp compiled with staging-only harness and existing yaml-cpp library."))
    print(f"PASS: {len(layouts)} parsed layouts, {len(pngs)} PNGs, {len(buffs)} buffs; {len(checks)} checks.")


if __name__=="__main__":
    main()
