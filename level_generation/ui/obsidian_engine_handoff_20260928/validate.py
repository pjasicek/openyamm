#!/usr/bin/env python3
"""Validate the staged handoff; write checksummed manifests and a portable, unmounted archive."""
import json
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml
from PIL import Image

sys.dont_write_bytecode=True
from prepare import HERE, ROOT, UI, flatten, sha, write_json, write_yaml


def main():
    checks=[]

    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    layouts={p.name:yaml.safe_load(p.read_text()) for p in (HERE/"engine/ui/gameplay").glob("*.yml")}
    images={p.stem.lower():p for p in (HERE/"engine/icons_x2").glob("*.png")}
    native={p.stem.lower():p for p in (ROOT/"assets_dev/engine/icons_x2").glob("*.png")}
    dependencies={}
    all_ids=set()
    allowed_asset_keys={"default","highlighted","pressed","selected","frame","health_bar","mana_bar"}
    allowed_align={"left","center","right"}
    allowed_fonts={p.stem for p in (HERE/"engine/fonts/truetype").glob("*.yml")}
    for filename,document in layouts.items():
        nodes=list(flatten(document["elements"]))
        ids=[n["id"] for n in nodes]
        check(f"Unique IDs: {filename}",len(ids)==len(set(ids)))
        check(f"Unique IDs across candidate files: {filename}",not all_ids.intersection(ids))
        all_ids.update(ids)
        for node in nodes:
            check(f"Asset schema: {node['id']}",node.get("asset",{}).keys()<=allowed_asset_keys)
            if node.get("text"):
                check(f"Alignment schema: {node['id']}",node["text"].get("align_x","left") in allowed_align)
                check(f"Font descriptor: {node['id']}",node["text"].get("font","lucida").lower() in allowed_fonts)
            for name in node.get("asset",{}).values():
                if not name:
                    continue
                if name.lower() not in images:
                    check(f"Native dependency exists: {name}",name.lower() in native)
                    path=native[name.lower()]
                    dependency=dependencies.setdefault(name,dict(path=str(path.relative_to(ROOT)),sha256=sha(path),uses=[]))
                    dependency["uses"].append(filename+":"+node["id"])

    manifest=[]
    export_entries={e["file"]:e for e in json.loads((HERE/"hud_exports.json").read_text())["exports"]}
    receipts={r["path"]:r for r in json.loads((HERE/"source_receipts.json").read_text())}
    inherited={}
    for package in ["obsidian_overlays_20260928","obsidian_journal_20260928"]:
        folder=HERE/"sources"/package
        inherited.update({f["path"]:f for f in json.loads((folder/"manifest.json").read_text())["files"]})
        for r in json.loads((folder/"asset_receipts.json").read_text()):
            inherited.setdefault(r["path"],{}).update(r)
    for path in sorted((HERE/"engine").rglob("*")):
        if not path.is_file():
            continue
        relative=str(path.relative_to(HERE))
        check(f"Readable mode: {relative}",stat.S_IMODE(path.stat().st_mode)==0o644)
        row=dict(path=relative,sha256=sha(path),bytes=path.stat().st_size,intended_target="assets_dev/"+relative)
        if relative in receipts:
            check(f"Receipt: {relative}",row["sha256"]==receipts[relative]["sha256"])
            row["provenance"]=receipts[relative]["source"]
        if path.suffix==".png":
            im=Image.open(path)
            check(f"RGBA/lowercase: {path.name}",im.mode=="RGBA" and path.name==path.name.lower())
            row.update(pixels=list(im.size),alpha_range=list(im.getchannel("A").getextrema()))
            for key in ["logical_size","role","note","method"]:
                if key in inherited.get(relative,{}):
                    row[key]=inherited[relative][key]
            if path.stem=="obsidian_basebar":
                row.update(install=False,superseded_by="obsidian_hud_fullscreen_basebar",
                           note="Historical r06 comparison only; requested 2116 revision is the candidate layout binding.")
            check(f"Nonempty artwork: {path.name}",im.getchannel("A").getextrema()[1]>0)
            if path.stem.startswith("obsidian_hud_meter_") and not path.stem.endswith("track"):
                check(f"Meter fill covers full strip: {path.name}",im.getchannel("A").getextrema()[0]>0)
            if relative in export_entries:
                entry=export_entries[relative]
                row["geometry"]=entry
                # Chromium encloses fractional raster rectangles. Keep exact measured logical bounds, not filename-derived scale.
                check(f"Raster dimensions: {path.name}",all(abs(a-b*2)<=1.1 for a,b in zip(im.size,entry["logical_size"])))
            if any(token in path.stem for token in ["portrait_rim","fullscreen_rim","minimap_rim"]):
                check(f"Transparent rim centre: {path.name}",im.getpixel((im.width//2,im.height//2))[3]==0)
            if path.stem.startswith("obsidian_frame_") or path.stem.startswith("obsidian_buff_"):
                check(f"True alpha: {path.name}",im.getchannel("A").getextrema()[0]==0)
        manifest.append(row)

    for path in (HERE/"engine/fonts/truetype").glob("*.yml"):
        descriptor=yaml.safe_load(path.read_text())
        check(f"Font binary resolves: {path.name}",(path.parent/descriptor["file"]).is_file())
        live=ROOT/"assets_dev/engine/fonts/truetype"/descriptor["file"]
        check(f"No font downgrade: {path.name}",sha(path.parent/descriptor["file"])==sha(live))
    check("Autonote tintable",yaml.safe_load((HERE/"engine/fonts/truetype/autonote.yml").read_text())["presentation"]=="tintable")
    check("Fondamento OFL",(HERE/"engine/fonts/truetype/fondamento_ofl.txt").is_file())

    indices={name:{n["id"]:n for n in flatten(doc["elements"])} for name,doc in layouts.items()}
    # Match the authoritative grid element by its geometry, not by a guessed renderer alias.
    grids=[n for n in indices["character.yml"].values() if n.get("width")==448 and n.get("height")==288]
    check("Inventory 14x9 of 32logical cells",len(grids)==1 and grids[0].get("offset_x")==7 and grids[0].get("offset_y")==8)
    check("Inventory surface is exact 2x raster",Image.open(images["obsidian_inventory_surface"]).size==(936,692))
    journal=indices["journal.yml"]
    rect=lambda n:[n.get(k,0) for k in ["offset_x","offset_y","width","height"]]
    check("Journal native map rectangle",rect(journal["JournalMapViewport"])==[131,101,300,300])
    check("Journal widened body gutter",rect(journal["JournalTextViewport"])==[101,96,360,293])
    check("Journal justification retained","justif" in journal["JournalTextViewport"]["notes"].lower())
    hud=indices["gameplay.yml"]
    check("Blank revised fullscreen status bar",hud["OutdoorBasebar"]["asset"]["default"]=="obsidian_hud_fullscreen_basebar")
    check("Fullscreen basebar exact 640x114 at 2x",Image.open(images["obsidian_hud_fullscreen_basebar"]).size==(1280,228))
    check("Status font and reserved space",hud["OutdoorStatusBar"]["text"]["font"]=="Lucida" and
          hud["OutdoorStatusBar"]["height"]>=17 and hud["OutdoorStatusBar"]["width"]>450)
    check("No legacy HUD art or placeholders",not any(v.lower() in {"facemask","selring","manafrm","manag","manab","basebar_cut"}
          for n in hud.values() for v in n.get("asset",{}).values()))
    check("Five gameplay and five fullscreen templates",all(f"ObsidianPc{i}" in hud and f"ObsidianOverlayPc{i}" in hud for i in range(1,6)))
    check("Gameplay names retained; fullscreen names omitted",all(f"ObsidianPc{i}Name" in hud and
          f"ObsidianOverlayPc{i}Name" not in hud for i in range(1,6)))

    source=(UI/"hud_concepts_20260927/buffs.js").read_text()
    mapping=[dict(id=id,icon="obsidian_buff_"+art) for id,art in re.findall(r'id: "([^"]+)", name: "[^"]+", art: "([^"]+)"',source)]
    party_header=(ROOT/"game/party/Party.h").read_text()
    def enum(name):
        block=re.search(r"enum class "+name+r"[^\{]+\{([^}]+)\}",party_header).group(1)
        return [part.strip().split("=")[0].strip() for part in block.split(",") if part.strip() and part.strip()!="Count"]
    check("All 22 party buff enum slots covered in order",[m["id"] for m in mapping]==enum("PartyBuffId") and len(mapping)==22)
    check("Every buff uniform RGBA128",all(Image.open(images[m["icon"]]).size==(128,128) for m in mapping))
    write_yaml(HERE/"design/buffs.yml",dict(party_effects=mapping,character_effects=enum("CharacterBuffId"),
        character_button="obsidian_personal_buffs",note="Use live effects; glyph-free top-left strip covers party enums, personal effects stay owner-scoped."))

    old=yaml.safe_load((HERE/"reference_runtime/ui/gameplay/gameplay.yml").read_text())
    old_ids={n["id"] for n in flatten(old["elements"])}
    retired=[]
    for name in sorted(old_ids-hud.keys()):
        if "Buff" in name or "Fly" in name:
            target="ObsidianPartyBuffStrip / ObsidianPartyBuffPopup; preserve stable buff IDs and inspection"
        elif "Standard" in name:
            target="Unified responsive desktop HUD; retire legacy Standard renderer/input branch"
        elif "Food" in name:
            target="OutdoorGoldBar contains both resources; OutdoorButtonRest is in OutdoorOptionsBar"
        elif "Mobile" in name:
            target="Mobile migration required; preserve native contextual action semantics"
        else:
            target="Remove legacy decorative draw/lookup; modern children own visual state (see design/gameplay.yml)"
        retired.append(dict(id=name,replacement=target))
    write_json(HERE/"legacy_id_migration.json",dict(retained=sorted(old_ids&hud.keys()),
               added=sorted(hud.keys()-old_ids),retired=retired,activate_atomically=True))
    write_json(HERE/"runtime_dependencies.json",dict(static_asset_references=dependencies,
        dynamic_content=["Native PC/NPC portraits and animation","Paperdolls/equipment/items","Chest types and layouts",
            "House videos","Native minimap renderer, reveal, markers and world map labels","Native spellbook restoration",
            "Rest sky/hourglass animations","Localized tables, quest/autonote/history content"],
        retained_layouts="reference_runtime/ui/gameplay",install_scope="Base engine skin; retain native/world content"))

    coverage=[]
    retained_reference_changes=[]
    menu_names={"menu","controls","keyboard","video_options","load_game","save_game","character_creation","continent_selection"}
    for path in sorted((HERE/"reference_runtime/ui/gameplay").glob("*.yml")):
        live=ROOT/"assets_dev/engine/ui/gameplay"/path.name
        if path.name in layouts:
            check(f"Candidate baseline still current: {path.name}",sha(path)==sha(live))
        elif sha(path)!=sha(live):
            retained_reference_changes.append(dict(layout=path.name,snapshot_sha256=sha(path),
                current_sha256=sha(live),disposition="Separate retained screen changed during preparation; never part of the install payload."))
        name=path.stem
        if path.name in layouts:
            role="candidate" if name!="chest" else "inherited shared chrome candidate; chest art/geometry retained"
        elif name=="gameplay_mobile":
            role="pinned; explicit mobile renderer/input migration required before enabling skin"
        elif name=="spellbook":
            role="retained; separately approved and installed spellbook restoration"
        elif name in menu_names or name.startswith("settings_"):
            role="separate accepted menu work; preserve current implementation"
        else:
            role="retained current screen; no new standalone visual approval in this handoff"
        coverage.append(dict(layout=path.name,disposition=role,reference=str(path.relative_to(HERE))))
    write_json(HERE/"coverage.json",coverage)
    write_json(HERE/"runtime_reference_changes.json",retained_reference_changes)

    # Geometry checks for the specified responsive rule, including the turn dock and long status.
    responsive=[]
    for width in [1200,1600,2100]:
        for count in range(1,6):
            for turn in [False,True]:
                party_left=(width-(105*count+20*(count-1)))/2-12
                right=459 if turn else 312
                raised=right+16>party_left
                dock_bottom=900-(239 if raised else 29)
                dock_top=dock_bottom-68
                status_bottom=min(660,dock_top-16) if raised and (width-620)/2<right else 660
                check(f"Responsive vertical clearance: {width}/{count}/{turn}",not raised or dock_bottom+16<=677)
                responsive.append(dict(review_width=width,party=count,turn=turn,dock_raised=raised,
                                       status_bottom=status_bottom))
    write_json(HERE/"responsive_checks.json",responsive)

    harness=UI/"obsidian_overlays_20260928/staging/validate_layouts.cpp"
    with tempfile.TemporaryDirectory(prefix="obsidian-handoff-") as temp:
        binary=Path(temp)/"layout-check"
        built=subprocess.run(["c++","-std=c++20","-O1","-ffunction-sections","-fdata-sections","-I",str(ROOT),
            "-I",str(ROOT/"build/_deps/yaml-cpp-src/include"),str(harness),str(ROOT/"game/ui/UiLayoutManager.cpp"),
            str(ROOT/"build/_deps/yaml-cpp-build/libyaml-cpp.a"),"-Wl,--gc-sections","-o",str(binary)],
            check=True,capture_output=True,text=True)
        parsed=subprocess.run([str(binary),*[str(HERE/"engine/ui/gameplay"/name) for name in sorted(layouts)]],
                              check=True,capture_output=True,text=True)
        check("Actual UiLayoutManager parsed all candidate files",f"PASS: {len(layouts)} staged layouts" in parsed.stdout)
    browser=json.loads((HERE/"hud_exports.json").read_text())
    check("Browser exports and status specimens",not browser["errors"] and len(browser["checks"])==25)
    review=json.loads((HERE/"browser_review.json").read_text())
    check("Consolidated browser controls, editable inputs and complete gallery",review["result"]=="PASS" and
          not review["errors"] and len(review["checks"])==7)
    report=dict(result="PASS",checks=len(checks),layouts=len(layouts),pngs=len(images),fonts=len(allowed_fonts),
                party_buffs=len(mapping),browser_cases=len(browser["checks"]),responsive_cases=len(responsive),
                handoff_browser_cases=len(review["checks"]),
                separately_changed_retained_references=len(retained_reference_changes),
                parser=parsed.stdout.strip(),runtime_integrated=False,checks_detail=checks)
    write_json(HERE/"validation.json",report)
    write_json(HERE/"manifest.json",dict(revision="obsidian-consolidated-01",runtime_integrated=False,
        status="staged-for-engine-integration",status_rail="2116 requested refinement, browser review included",
        files=manifest,required_engine_work="INTEGRATION.md",coverage="coverage.json",validation="validation.json"))
    archive=HERE/"obsidian-runtime-preparation.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for path in sorted(HERE.rglob("*")):
            if not path.is_file() or path==archive or path.name=="archive.sha256" or "__pycache__" in path.parts:
                continue
            info=zipfile.ZipInfo(str(path.relative_to(HERE)),date_time=(2026,9,28,0,0,0))
            info.external_attr=(0o100644<<16)
            out.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
    (HERE/"archive.sha256").write_text(sha(archive)+"  "+archive.name+"\n")
    print(json.dumps({key:value for key,value in report.items() if key!="checks_detail"},indent=2))


if __name__=="__main__":
    main()
