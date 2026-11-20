#!/usr/bin/env python3
"""Prepare the approved journal layout using native IDs and content-free exported assets."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STAGE=HERE.parent/"obsidian_overlays_20260928/staging"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def flat(elements):
    for e in elements:
        yield e
        yield from flat(e.get("children",[]))


def place(e,r):
    e.update(anchor="top_left",offset_x=round(r[0],6),offset_y=round(r[1],6),width=round(r[2],6),height=round(r[3],6))


def plate(e,family,text,icon=None,font_size=25,icon_size=(99,100)):
    e["asset"]={k:f"obsidian_journal_{family}_{v}" for k,v in
                [("default","normal"),("highlighted","hover"),("pressed","pressed"),("selected","selected")]}
    e["children"]=[]
    if icon:
        e["children"].append(dict(id=e["id"]+"Icon",anchor="top_center",offset_y=4,
            width=icon_size[0]/1.875,height=icon_size[1]/1.875,asset={"default":icon}))
    e["children"].append(dict(id=e["id"]+"Label",anchor="bottom_center",offset_y=-4,
        width=e["width"]-4,height=font_size/1.875*1.15,
        text=dict(value=text,font="Fondamento",scale=font_size/1.875/32,color="#e8d1a4",align_x="center",align_y="middle")))
    e["notes"]="APPROVED DESIGN DRAFT: preserve action. Shared renderer must draw plate, live label and icon children; use semantic state colours and disabled plate from design/button_states.yml. No legacy animated texture-name override."


def align_children(element, measured):
    for child, geometry in zip(element["children"], measured["children"]):
        place(child, geometry["rect"])
        child["z_index"] = element.get("z_index", 30) + 1
        if geometry["kind"] == "label":
            child["text"]["scale"] = geometry["font_size"] / 32


geometry=json.loads((HERE/"review_geometry.json").read_text())
exports=json.loads((HERE/"exported_assets.json").read_text())
for e in exports:
    path=HERE/"assets/exported"/(e["name"]+".png")
    image=Image.open(path).convert("RGBA")
    w,h=e["pixel_size"]
    assert image.width>=w and image.height>=h
    image.crop((0,0,w,h)).save(path)
    path.chmod(0o644)

source=HERE/"reference_layouts/journal.yml"
assert sha(source)==sha(ROOT/"assets_dev/engine/ui/gameplay/journal.yml"),"Live journal changed; rebase explicitly."
doc=yaml.safe_load(source.read_text())
index={e["id"]:e for e in flat(doc["elements"])}
root=doc["elements"][0]
index["JournalBackground"]["asset"]={"default":"obsidian_journal_background"}
for id in ["JournalTitleText","JournalMapTitleText"]:
    place(index[id],geometry["#page-title"][0]["rect"])
    index[id]["text"].update(color="#e4c793",font="Book2",scale=1)
    index[id]["notes"]="Keep recreated Book2. Fit long titles only down to 22.4 logical; preserve native title binding."
place(index["JournalTextViewport"],geometry["#text-viewport"][0]["rect"])
index["JournalTextViewport"]["text"].update(color="#e5dcc7",font="AUTONOTE",scale=.9,align_x="left")
index["JournalTextViewport"]["notes"]=("USER REFINEMENT: justify body paragraphs to both edges using inter-word spacing; "
    "leave paragraph final lines and single-line entries left aligned. A paragraph continuing on the next page stays justified. "
    "The current parser only supports left/center/right, so align_x stays parseable until native justification is added. "
    "See design/theme.yml body_alignment. Use the 360-logical-wide text block and 28-logical gap to submenu controls "
    "from reference 2105. Preserve original font/scale, native pagination and tintable Autonote.")
for key,e in zip(["Map","Quests","Story","Notes"],geometry["#main-navigation button"]):
    target=index["JournalMainView"+key];place(target,e["rect"])
    plate(target,"main",key,"obsidian_journal_icon_"+key.lower())
    align_children(target,e)
for key in ["Quests","Story","Notes"]:
    target=index[f"Journal{key}TopLeftArt"]
    place(target,geometry["#view-emblem"][0]["rect"])
    target["asset"]={"default":"obsidian_journal_icon_"+key.lower()}
    target["notes"]="Use staged icon at this restrained size; retain conditional view visibility."
for n,(suffix,label,glyph) in enumerate([("PrevPageButton","Previous","previous"),("NextPageButton","Next","next"),
                                       ("MapZoomInButton","Zoom in","zoom_in"),("MapZoomOutButton","Zoom out","zoom_out")]):
    target=index["Journal"+suffix];place(target,geometry["#page-controls button"][n%2]["rect"])
    plate(target,"page",label,"obsidian_journal_"+glyph,20,(38,30))
    align_children(target,geometry["#page-controls button" if n<2 else "map_controls"][n%2])
for suffix,key,label,e in zip(["Potion","Fountain","Obelisk","Seer","Misc","Trainer"],
    ["potion","fountain","obelisk","seer","misc","trainer"],
    ["Potions","Fountains","Obelisks","Seer","Misc.","Trainers"],geometry["#note-categories button"]):
    target=index[f"JournalNotes{suffix}Button"];place(target,e["rect"])
    plate(target,"category",label,"obsidian_journal_icon_"+key,19,(53,53))
    align_children(target,e)
place(index["JournalCloseButton"],geometry["#close"][0]["rect"])
plate(index["JournalCloseButton"],"close","Close",None,30)
align_children(index["JournalCloseButton"],geometry["#close"][0])
index["JournalMapNoteTextBackground"]["asset"]={"default":"obsidian_journal_note_bar"}
for id in ["JournalMapCoordinatesText","JournalMapNoteText"]:
    index[id]["text"]["color"]="#d0c7b0" if id == "JournalMapCoordinatesText" else "#e5dcc7"
    index[id]["notes"]="Keep live coordinates / selected or hovered note; no fixture text enters runtime."
root["children"].append(dict(id="JournalPageNumber",anchor="top_left",offset_x=101,offset_y=792/1.875,
    width=360,height=18,text=dict(value="{page} / {pages}",font="SMALLNUM",scale=1,color="#b4ad95",align_x="center"),
    notes="Approved page-count binding; hidden on map and empty journal. The review hides it in reference mode."))
place(root["children"][-1],geometry["#page-number"][0]["rect"])
root["children"].append(dict(id="JournalMapFrame",anchor="top_left",offset_x=118.2,offset_y=88.2,
    width=325.6,height=325.6,z_index=16,asset={"default":"obsidian_journal_map_frame"},
    notes="Transparent frame drawn over the map only. Keep JournalMapViewport and its hit region unchanged."))
destination=HERE/"drafts/journal.yml"
destination.parent.mkdir(exist_ok=True)
destination.write_text("# APPROVED DESIGN 01 / 2026-09-28 / UNMOUNTED RUNTIME DRAFT. Reuses native actions and IDs.\n"
                       "# See README.md for font, animated-icon and child drawing hooks.\n"
                       +yaml.safe_dump(doc,sort_keys=False,width=112))

assets=[]
for e in exports:
    file=HERE/"assets/exported"/(e["name"]+".png")
    assets.append(dict(id=e["name"],path=str(file.relative_to(HERE)),sha256=sha(file),
                       logical_size=e["logical_size"],pixels=e["pixel_size"],kind="CSS/SVG raster export",target=f"assets_dev/engine/icons_x2/{file.name}"))
for name in ["map","quests","story","notes","potion","fountain","obelisk","seer","misc","trainer"]:
    file=HERE/f"assets/generated/journal-{name}-v1.png"
    image=Image.open(file)
    assert image.mode=="RGBA" and image.getchannel("A").getextrema()==(0,255)
    assets.append(dict(id="obsidian_journal_icon_"+name,path=str(file.relative_to(HERE)),sha256=sha(file),pixels=list(image.size),
        alpha="true RGBA, preserved",kind="reused approved Books v2" if name=="notes" else "built-in imagegen v1",
        target=f"assets_dev/engine/icons_x2/obsidian_journal_icon_{name}.png"))
ids={e["id"] for e in flat(doc["elements"])}
assert len(ids)==len(list(flat(doc["elements"])))
assert {e["id"] for e in flat(yaml.safe_load(source.read_text())["elements"])}<=ids
asset_ids={a["id"] for a in assets}
assert all(name in asset_ids for e in flat(doc["elements"]) for name in e.get("asset",{}).values())
viewport=index["JournalMapViewport"]
assert [viewport[k] for k in ["offset_x","offset_y","width","height"]]==[131,101,300,300]
with tempfile.TemporaryDirectory(prefix="obsidian-journal-yaml-") as temp:
    binary=Path(temp)/"check"
    subprocess.run(["c++","-std=c++20","-O1","-ffunction-sections","-fdata-sections","-I",str(ROOT),
        "-I",str(ROOT/"build/_deps/yaml-cpp-src/include"),str(STAGE/"validate_layouts.cpp"),
        str(ROOT/"game/ui/UiLayoutManager.cpp"),str(ROOT/"build/_deps/yaml-cpp-build/libyaml-cpp.a"),
        "-Wl,--gc-sections","-o",str(binary)],check=True,capture_output=True)
    result=subprocess.run([str(binary),str(destination)],check=True,capture_output=True,text=True)
report=dict(status="approved-design-01-unmounted-runtime-draft",approval_date="2026-09-28",result="PASS",assets=assets,
            yaml_parser=result.stdout.strip(),original_ids_retained=True,native_map_viewport_retained=True,
            source_layout_sha256=sha(source),draft_layout_sha256=sha(destination))
(HERE/"asset_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"PASS: journal draft parsed; {len(assets)} staged asset mappings; original IDs and 300×300 map retained.")
