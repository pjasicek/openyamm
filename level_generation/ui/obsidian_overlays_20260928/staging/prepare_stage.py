#!/usr/bin/env python3
"""Rebuild the unmounted handoff from approved browser exports and pinned source layouts."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image
import yaml

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
ICONS = HERE / "engine/icons_x2"
NATIVE = ROOT / "assets_dev/engine"
LAYOUT_NAMES = ["character", "rest", "quick_reference", "dialogue", "item_inspect", "actor_inspect",
                "character_inspect", "character_detail", "spell_inspect", "buff_inspect", "gameplay"]
INK = "#e5dcc7"
HEADING = "#e4c793"
receipts = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def copy(source, destination, role):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    destination.chmod(0o644)
    receipts.append({"path": str(destination.relative_to(HERE)), "source": str(source.relative_to(ROOT)),
                     "source_sha256": sha(source), "method": "unchanged-copy", "role": role})


def flatten(elements):
    for element in elements:
        yield element
        yield from flatten(element.get("children", []))


def place(element, x, y, width, height, anchor="top_left"):
    element.update(anchor=anchor, offset_x=round(x, 6), offset_y=round(y, 6),
                   width=round(width, 6), height=round(height, 6))


def label(id, value, x, y, width, height, font="Create", colour=INK):
    return dict(id=id, anchor="top_left", offset_x=x, offset_y=y, width=width, height=height,
                text=dict(value=value, font=font, color=colour, align_x="left", align_y="top"))


def button(element, family, text, size=25 / 1.875):
    element["asset"] = {key: f"obsidian_button_{family}_{state}" for key, state in
                        [("default", "normal"), ("highlighted", "hover"), ("pressed", "pressed"),
                         ("selected", "selected")]}
    element["text"] = dict(value=text, font="Fondamento", color="#e8d1a4", align_x="center",
                           align_y="middle", scale=round(size / 32, 6))
    element["notes"] = ("Draft: retain the existing action/hit target. Draw a live localized Fondamento label. "
                        "Font registration, state text colours and disabled plate selection require renderer wiring; "
                        "see design/theme.yml and INTEGRATION.md.")


def frame(root, index):
    corner = 58 / 1.875
    width, height = root["width"], root["height"]
    root["asset"] = {"default": "obsidian_reading_surface"}
    root["notes"] = (root.get("notes", "") + " Approved r03 skin draft. Surface must be sampled/cropped at fixed scale "
                      "and inset 8.533333 logical units; do not stretch this texture. Frame edges repeat, with "
                      "a clipped final tile. Dynamic height remains runtime-owned. See design/frame.yml.").strip()
    corners = {"UR": ("tr", "top_right"), "UL": ("tl", "top_left"),
               "LR": ("br", "bottom_right"), "LL": ("bl", "bottom_left")}
    for element in index.values():
        if "Corner_" not in element["id"]:
            continue
        suffix = element["id"].split("Corner_")[-1]
        if suffix in corners:
            part, anchor = corners[suffix]
            place(element, 0, 0, corner, corner, anchor)
        else:
            part = {"TopEdge": "top", "BottomEdge": "bottom", "LeftEdge": "left", "RightEdge": "right"}[suffix]
            if part in ("top", "bottom"):
                place(element, corner, 0, width - 2 * corner, corner,
                      "top_left" if part == "top" else "bottom_left")
            else:
                place(element, 0, corner, corner, height - 2 * corner,
                      "top_left" if part == "left" else "top_right")
            element["notes"] = "Draft edge bounds; repeat at 48.286179 logical length, recompute for actual root height."
        element["asset"] = {"default": f"obsidian_frame_{part}"}


def main():
    ICONS.mkdir(parents=True, exist_ok=True)
    export_data = json.loads((HERE / "browser_exports.json").read_text())
    geometry = json.loads((HERE / "review_geometry.json").read_text())
    # Chrome floors fractional clip extents. The exporter captures the enclosing rectangle; trim excess only.
    # Never resize a grid or texture to correct a one-pixel rounding discrepancy.
    for record in export_data["exports"]:
        file = HERE / record["file"]
        im = Image.open(file).convert("RGBA")
        size = tuple(record["pixel_size"])
        assert im.width >= size[0] and im.height >= size[1], (file.name, im.size, size)
        im.crop((0, 0, *size)).save(file)
        file.chmod(0o644)
        sources = [{"path": str((HERE / s).resolve().relative_to(ROOT)),
                    "sha256": sha((HERE / s).resolve())} for s in record["source"]]
        receipts.append({"path": record["file"], "method": record["method"], "sources": sources,
                         "logical_size": record["logical_size"], "role": "content-free UI skin",
                         "note": record.get("note", "Fixed plate; rounded raster bounds, no resampling.")})
    for part in ["tl", "tr", "bl", "br", "top", "bottom", "left", "right"]:
        copy(STUDY / f"assets/generated/frame-{part}.png", ICONS / f"obsidian_frame_{part}.png", "true-alpha frame slice")
    copy(STUDY / "assets/generated/frame-v1.png", HERE / "masters/frame.png", "transparent unsliced frame master")
    copy(STUDY / "assets/generated/frame-cropped.png", HERE / "masters/frame-cropped.png", "frame slicing source")
    for name in ["frame_slices.json", "alpha_verification.json", "buff_art.json", "generated_prompts.json"]:
        copy(STUDY / name, HERE / "masters" / name, "original generation/crop provenance")
    fullscreen = STUDY.parent / "hud_overlay_study_20260927"
    hud = STUDY.parent / "hud_concepts_20260927"
    for name, version in [("books", 2), ("party", 1), ("rest", 1), ("options", 1), ("followers", 1), ("personal-buffs", 1)]:
        copy(hud / f"assets/generated/obsidian-{name}-v{version}.png",
             ICONS / f"obsidian_{name.replace('-', '_')}.png", "approved gameplay icon master")
    for i in range(1, 5):
        copy(fullscreen / f"assets/generated/carved-obsidian-empty-slot-{i:02d}-v1.png",
             ICONS / f"obsidian_empty_slot_{i:02d}.png", "approved empty party banner; draw with recorded tint")
    for name in ["basebar-v2", "sidebar-v1"]:
        copy(fullscreen / f"assets/generated/carved-obsidian-{name}.png",
             HERE / f"masters/carved-obsidian-{name}.png", "approved artwork before fitting/colour treatment")
    copy(fullscreen / "assets/material-evt.png", HERE / "masters/stone.png", "original stone grain, fixed-scale sampling source")
    for folder, prefix, names in [(STUDY,"overlays",["app.js","style.css"]),
                                  (fullscreen,"fullscreen",["app.js","style.css","button-theme.css"]),
                                  (hud,"hud",["app.js","style.css"])]:
        for name in names:
            copy(folder / name,HERE / f"masters/review_source/{prefix}-{name}","frozen approved CSS/SVG recipe; source-relative URLs")
    for name in ["arrus", "create", "lucida", "smallnum", "comic"]:
        for file in [f"{name}.yml", f"openyamm_{name}_faithful.ttf"]:
            copy(NATIVE / "fonts/truetype" / file, HERE / "engine/fonts/truetype" / file, "existing faithful font; unchanged")
        for folder in ["icons", "english_text"]:
            fnt = next(p for p in (NATIVE / "fonts" / folder).iterdir() if p.name.lower() == name + ".fnt")
            copy(fnt, HERE / "engine/fonts" / folder / fnt.name, "existing FNT metrics; pair with faithful TTF")
    copy(fullscreen / "assets/fonts/Fondamento-Regular.ttf", HERE / "engine/fonts/truetype/fondamento-regular.ttf",
         "approved button outline font; existing independent loader must be wired to gameplay")
    descriptor = yaml.safe_load((NATIVE / "fonts/truetype/fondamento.yml").read_text())
    descriptor["file"] = "fondamento-regular.ttf"
    target = HERE / "engine/fonts/truetype/fondamento.yml"
    target.write_text(yaml.safe_dump(descriptor, sort_keys=False))
    target.chmod(0o644)
    receipts.append({"path":str(target.relative_to(HERE)),"source":"assets_dev/engine/fonts/truetype/fondamento.yml",
        "source_sha256":sha(NATIVE / "fonts/truetype/fondamento.yml"),"method":"descriptor-copy-filename-adjustment",
        "role":"reuse existing independent FreeType atlas descriptor; gameplay loader hook required"})
    copy(fullscreen / "assets/fonts/fondamento-OFL.txt", HERE / "engine/fonts/truetype/fondamento-ofl.txt", "Fondamento OFL license")

    for name in LAYOUT_NAMES:
        source = NATIVE / f"ui/gameplay/{name}.yml"
        snapshot = HERE / f"reference_layouts/{name}.yml"
        if not snapshot.exists():
            copy(source, snapshot, "pinned runtime layout before skin changes")
        else:
            assert sha(snapshot) == sha(source), f"Runtime layout changed since staging: {source}; review/rebase explicitly."
            receipts.append({"path": str(snapshot.relative_to(HERE)), "source": str(source.relative_to(ROOT)),
                             "source_sha256": sha(source), "method": "unchanged-copy", "role": "pinned runtime layout"})
        doc = yaml.safe_load(snapshot.read_text())
        elements = list(flatten(doc["elements"]))
        idx = {e["id"]: e for e in elements}
        root = doc["elements"][0]
        for e in elements:
            if "text" in e:
                old = e["text"].get("color", "white").lower()
                e["text"]["color"] = HEADING if old in ("#ffff9b", "eastern_blue") else INK

        if name == "character":
            idx["CharacterTopBar"]["asset"] = {"default": "obsidian_topbar"}
            for page in ["Stats", "Skills", "Inventory", "Awards"]:
                idx[f"Character{page}Page"]["asset"] = {"default": f"obsidian_{page.lower()}_surface"}
                for suffix in ["NameLabel", "SkillPointsTextLabel", "SkillPointsValue"]:
                    e = idx.get(f"Character{page}{suffix}")
                    if e:
                        e["notes"] = "Preserve Create. Name/class share one line; point count uses positive colour only if available."
                if page in ["Stats", "Skills"]:
                    root_page = idx[f"Character{page}Page"]
                    class_label = label(f"Character{page}ClassLabel", "{character_class}", 4, 0, 145, 22,
                                        colour=HEADING)
                    class_label.update(anchor="right_of", notes="New binding: measure name width, then place class on same baseline; include localized article.")
                    idx[f"Character{page}NameLabel"].setdefault("children", []).append(class_label)
            for page, text in [("Stats", "Stats"), ("Skills", "Skills"), ("Inventory", "Inventory"), ("Awards", "Awards"), ("Exit", "Exit")]:
                button(idx[f"Character{page}Button"], "tab", text)
            button(idx["CharacterDismissButton"], "tab", "Dismiss")
            idx["CharacterInventoryInfo"]["visible"] = False
            idx["CharacterInventoryInfo"]["notes"] = "Approved: no hover label above Stats; no ordinary inventory hover overlay."
            idx["CharacterAwardDetail"]["visible"] = False
            # Original inventory coordinates and ownership are deliberately retained exactly.
            idx["CharacterInventoryGrid"]["notes"] = "14 columns × 9 rows; each 32×32 logical. Parent (0,24), grid (7,8): screen (7,32). Held RMB only; release closes."
            stat_ids = ["Might","Intellect","Personality","Endurance","Accuracy","Speed","Luck","HitPoints",
                        "SpellPoints","ArmorClass","Condition","QuickSpell","Age","Level","Experience","Attack",
                        "MeleeDamage","Shoot","RangedDamage","FireResistance","AirResistance","WaterResistance",
                        "EarthResistance","MindResistance","BodyResistance"]
            rows = [e for e in geometry["stats"] if e["classes"].split()[:1] == ["stat-row"]]
            assert len(rows) == len(stat_ids)
            for key, row in zip(stat_ids, rows):
                x, y, w, h = row["logical_rect"]
                for suffix, left, width in [("Label", x, w - 85), ("Value", x + w - 85, 85)]:
                    element = idx[f"CharacterStat{key}{suffix}"]
                    place(element, left, y - 24.533333, width, h)
                    element["text"].update(scale=18 / 17, align_x="right" if suffix == "Value" else "left")
                    element["notes"] = "Approved section geometry; retain dynamic original content/formatting and semantic colour runs."
            for key, e in idx.items():
                if key.startswith("CharacterSkills") and key.endswith("LevelHeader"):
                    e["visible"] = False
                if key.startswith("CharacterSkills") and key.endswith("ListRegion"):
                    e["notes"] = "Native Lucida 17 logical; row pitch 14; blue eligible whole-row clicks; held RMB inspects any row. Runtime owns row count."
            idx["CharacterAwardsList"]["notes"] = "Original priority palette; plain scrolling Arrus text, no nested border/bullets/rules."

        elif name == "rest":
            idx["RestBackground"].update(height=368, asset={"default": "obsidian_rest_surface"})
            for key, family, text, size in [
                ("RestButton8Hours","rest","Rest & Heal 8 Hours",31/1.875),
                ("RestButtonUntilDawn","wait","Wait until Dawn",16),
                ("RestButton1Hour","wait","Wait 1 Hour",16),
                ("RestButton5Minutes","wait","Wait 5 Minutes",16),
                ("RestButtonExit","rest_exit","Exit Rest",33/1.875)]:
                button(idx[key], family, text, size)
            idx["RestButton8Hours"]["text"].update(align_x="left", pad_x=16/1.875)
            idx["RestButton8Hours"]["notes"] += " Reserve the right-hand food icon/cost area; label must fit left of it."
            idx["RestHourglass"]["asset"] = {"default": "hglas060"}
            idx["RestHourglass"]["notes"] = "Keep native upright hourglass animation 060–119; this is its initial frame only."
            place(idx["RestHourglass"],715/1.875,305.625/1.875,125/1.875,114)
            place(idx["RestTimeText"],864/1.875,313.625/1.875,213/1.875,19)
            idx["RestTimeText"]["text"]["align_x"] = "center"
            for n, key in enumerate(["Day", "Month", "Year"]):
                place(idx[f"Rest{key}Text"],460.8,193.2+n*32,56,19)
                idx[f"Rest{key}Text"]["text"]["align_x"] = "right"
                place(idx[f"Rest{key}ValueText"],520,193.2+n*32,54.4,19)
                idx[f"Rest{key}ValueText"]["text"]["align_x"] = "center"
            root["children"].append(label("RestWaitHeading", "Wait",173/1.875,391/1.875,383/1.875,46/1.875,colour=HEADING))
            root["children"][-1]["text"]["align_x"] = "center"
            root["children"].append(dict(id="RestFoodCostIcon",anchor="top_left",offset_x=278,offset_y=166,
                width=47/1.875,height=35/1.875,asset={"default":"scorebg_food"},
                notes="New icon binding for the existing dynamic food cost, not carried food. No standalone Food label."))
            place(idx["RestFoodCostText"],305,167,19,20)
            idx["RestSkyAnimation"]["notes"] = "Preserve the live time-of-day panorama; no static review sky installed."

        elif name == "quick_reference":
            idx["QuickReferenceBackground"].update(height=368,asset={"default":"obsidian_quickref_surface"})
            button(idx["QuickReferenceExitButton"],"quick_exit","Exit")
            place(idx["QuickReferenceExitButton"], (1170-155)/1.875,(690-29-53)/1.875,155/1.875,53/1.875)
            rows = [e for e in geometry["quickref"] if e["tag"] == "TR"]
            keys = ["Name","Level","Class","Hp","Sp","Ac","Attack","MeleeDamage","Shoot","RangedDamage","Skills","Points","Condition","QuickSpell"]
            for key, row in zip(keys, rows):
                x,y,w,h=row["logical_rect"]
                place(idx[f"QuickReference{key}Label"],x+10/1.875,y+2/1.875,(184-20)/1.875,h-4/1.875)
            for n in range(5):
                root["children"].append(dict(id=f"QuickReferenceMemberColumn{n+1}",anchor="top_left",
                    offset_x=round((30+184+n*(1140-184)/5)/1.875,6),offset_y=25/1.875,
                    width=round((1140-184)/5/1.875,6),height=308,
                    notes="New region for renderer binding; 14 live cells aligned to label rows. No HP/SP bars. Arrus 19, per-cell fit floor 14."))
            for id, value, x, width in [("Reputation","Reputation: {reputation}",20.266667,250),
                                        ("Fame","Fame: {fame}",290,220)]:
                root["children"].append(label("QuickReference"+id,value,x,330, width,22,"Arrus"))
                root["children"][-1]["notes"] = "New layout field for existing runtime footer; bind live value and suppress duplicate hard-coded draw."

        elif name in ["item_inspect","actor_inspect","character_inspect","character_detail","spell_inspect","buff_inspect"]:
            frame(root, idx)
            if name == "item_inspect":
                title=idx["ItemInspectName"]
                place(title,0,12.8,root["width"]-38.4,22,"top_center")
                title["notes"]="Centred Arrus item name; type/detail/value remain Comic, description remains Smallnum."
                value=idx["ItemInspectValue"]
                place(value,115,-16,root["width"]-134.2,19,"bottom_left")
                value["notes"]="Pinned footer outside the scrollable description; retain literal Value: and the live value."
                root["children"].append(dict(id="ItemInspectValueDivider",anchor="bottom_left",offset_x=115,
                    offset_y=-42, width=root["width"]-134.2,height=1/1.875,z_index=560,
                    asset={"default":"obsidian_value_divider"},notes="Resize width only. Footer and divider never scroll with body."))
            elif name == "actor_inspect":
                idx["ActorInspectPreviewFrame"]["asset"]={"default":"obsidian_reading_surface"}
                idx["ActorInspectPreviewFrame"]["notes"]="Keep square 140×140 preview, existing actor rendering and identification gates. Fixed-scale surface sample."

        elif name == "dialogue":
            idx["DialogueTopBar"]["asset"]={"default":"obsidian_topbar"}
            idx["DialogueLeftBar"]["asset"]={"default":"obsidian_left_edge"}
            idx["DialogueEventDialog"]["asset"]={"default":"obsidian_house_sidebar"}
            idx["DialogueFrame"]["asset"]={"default":"obsidian_reading_surface"}
            idx["DialogueFrame"]["notes"]="Body-only sheet. Runtime measures text/height, samples the surface, draws top/side frame slices; open bottom meets party bar."
            idx["DialogueFrameEndCap"].update(visible=False)
            for e in elements:
                if e["id"].startswith("DialogueTopicRow"):
                    e["text"].update(font="Fondamento",color="#e8d1a4",scale=25/1.875/32)
                    e["notes"]="Fondamento open topic row; no plate. Keep live choices and action conditions."
            for key in ["DialogueGoodbyeButton","DialogueOkButton"]:
                button(idx[key],"close","Close" if "Goodbye" in key else "OK")
            idx["DialogueText"]["notes"]="Body only; preserve native formatting. Arrus 19→18, then Create 18→17, scroll only if still too long. No topic heading or Continue."

        elif name == "gameplay":
            # Only shared full-screen chrome is drafted here. The responsive HUD requires a separate renderer pass.
            idx["OutdoorBasebar"]["asset"]={"default":"obsidian_basebar"}
            idx["OutdoorBasebar"]["notes"]="Approved full-screen Carved Obsidian basebar; portrait/bars review shift (+3,+5) equals (+1.6,+2.666667) logical. Other gameplay branches remain reference-only."
            for key,e in idx.items():
                if key.startswith("CharShield_"):
                    i=key[-1]
                    if i in "2345":
                        e["asset"]={"default":f"obsidian_empty_slot_{int(i)-1:02d}"}
                        e["width"],e["height"]=98/1.875,136/1.875
                        e["notes"]="Empty slot only; approved master requires .7 saturation/.86 brightness/.88 opacity; see shared HUD contract."
        destination = HERE / f"engine/ui/gameplay/{name}.yml"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("# APPROVED VISUAL DESIGN / RUNTIME DRAFT. Not mounted. See staging/INTEGRATION.md.\n"
                               "# Keep existing IDs, actions and dynamic content. New bindings are explicitly noted.\n"
                               + yaml.safe_dump(doc, sort_keys=False, width=112, allow_unicode=True))
        destination.chmod(0o644)
        receipts.append({"path":str(destination.relative_to(HERE)),"source":str(source.relative_to(ROOT)),
                         "source_sha256":sha(source),"method":"layout-draft", "role":"existing loader schema; renderer wiring required"})

    dump(HERE / "asset_receipts.json", receipts)
    print(f"Prepared {len(receipts)} asset/layout/font receipts. Live assets unchanged.")


if __name__ == "__main__":
    main()
