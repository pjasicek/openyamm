#!/usr/bin/env python3
"""Consolidate reviewed art and rebase candidate layouts without touching mounted assets."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
UI = HERE.parent
PACKS = [UI / "obsidian_overlays_20260928/staging", UI / "obsidian_journal_20260928/staging"]
receipts = []
rebases = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def write_yaml(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# STAGED CANDIDATE; requires the renderer/input work in INTEGRATION.md.\n" +
                    yaml.safe_dump(value, sort_keys=False, width=110, allow_unicode=True))


def copy_file(source, target, role):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(0o644)
    receipts.append(dict(path=str(target.relative_to(HERE)), source=str(source.relative_to(ROOT)),
                         sha256=sha(target), role=role))


def merge(base, approved, current, location=""):
    """Three-way merge with ID-based child matching; conflicting changes require an explicit decision."""
    if approved == base:
        if current != base:
            rebases.append(location)
        return copy.deepcopy(current)
    if current == base or current == approved:
        return copy.deepcopy(approved)
    if all(isinstance(v, dict) for v in [base, approved, current]):
        result = {}
        for key in dict.fromkeys([*approved, *current, *base]):
            if key not in approved and key in base and current.get(key) == base[key]:
                continue
            if key not in current and key in base and approved.get(key) == base[key]:
                continue
            result[key] = merge(base.get(key), approved.get(key), current.get(key), location + "/" + key)
        return result
    if all(isinstance(v, list) for v in [base, approved, current]) and all(
            isinstance(n, dict) and "id" in n for v in [base, approved, current] for n in v):
        maps = [{n["id"]: n for n in v} for v in [base, approved, current]]
        return [merge(maps[0].get(key), maps[1].get(key), maps[2].get(key), location + "/" + key)
                for key in dict.fromkeys([*maps[1], *maps[2]])]
    raise ValueError(f"Unresolved layout rebase at {location}: {base!r} / {approved!r} / {current!r}")


def flatten(nodes):
    for node in nodes:
        yield node
        yield from flatten(node.get("children", []))


def element(id, x, y, w, h, asset=None, children=None, interactive=False, text=None, **extra):
    result = dict(id=id, anchor="top_left", offset_x=round(x / 1.875, 6), offset_y=round(y / 1.875, 6),
                  width=round(w / 1.875, 6), height=round(h / 1.875, 6))
    if asset:
        result["asset"] = {"default": asset}
    if children is not None:
        result["children"] = children
    if interactive:
        result["interactive"] = True
    if text:
        label, font, size = text
        native = dict(Lucida=17, SMALLNUM=14, Fondamento=32, Create=18)[font]
        result["text"] = dict(value=label, font=font, color="#e5dcc7", align_x="center", align_y="middle",
                              scale=round(size / 1.875 / native, 8))
    result.update(extra)
    return result


def root(id, x, y, w, h, anchor="top_left", **kwargs):
    result = element(id, x, y, w, h, **kwargs)
    result.update(anchor=anchor, anchor_space="screen", scale=dict(min=0.5, max=8.0), z_index=200)
    return result


def hud_layout(overlay):
    exported = {Path(e["file"]).stem: e for e in json.loads((HERE / "hud_exports.json").read_text())["exports"]}

    def plate(id, name, x, y):
        entry = exported["obsidian_hud_" + name]
        pad_x, pad_y, _, _ = entry["content_rect"]
        return dict(id=id, anchor="top_left", offset_x=round(x/1.875-pad_x, 6),
                    offset_y=round(y/1.875-pad_y, 6), width=entry["logical_size"][0],
                    height=entry["logical_size"][1], asset={"default": "obsidian_hud_" + name})

    def pc(index, fullscreen=False):
        prefix = ("ObsidianOverlayPc" if fullscreen else "ObsidianPc") + str(index+1)
        x = 39.1 + index*181.2 if fullscreen else index*125
        y = 59 if fullscreen else 0
        face_x, face_y, face_w, face_h = (16, 0, 85, 113) if fullscreen else (12, 5, 81, 109)
        rim = "fullscreen_rim_normal" if fullscreen else "portrait_rim_normal"
        vital_y, vital_w, vital_h = (124,107,6) if fullscreen else (147,103,7)
        children = [element(prefix+"Face",face_x,face_y,face_w,face_h,
                            notes="Existing animated PC portrait; native expression/condition logic. Apply ellipse alpha mask."),
                    plate(prefix+"Rim",rim,face_x,face_y),
                    plate(prefix+"Selection","selection_diamond",52 if fullscreen else 46,-14 if fullscreen else -15),
                    element(prefix+"Health",5 if fullscreen else 1,vital_y,vital_w,vital_h,
                            notes="Horizontal shaded meter; crop fill at live HP/max HP. See design/gameplay.yml."),
                    element(prefix+"Mana",5 if fullscreen else 1,vital_y+(11 if fullscreen else 12),vital_w,vital_h,
                            notes="Horizontal shaded meter; crop fill at live SP/max SP."),
                    element(prefix+"Readiness",0,89 if fullscreen else 87,22,25,
                            notes="Plain green/yellow/red diamond; recovery arc when recovering, dim when incapacitated."),
                    element(prefix+"PersonalBuffs",89 if fullscreen else 78,89 if fullscreen else 87,28,28,
                            "obsidian_personal_buffs",interactive=True,visible=False,
                            notes="Visible only with active individual effects; consumes click before portrait selection.")]
        if not fullscreen:
            children += [element(prefix+"Name",0,125,105,20,text=("", "Lucida",15)),
                         element(prefix+"Condition",0,171,105,12,text=("","SMALLNUM",8),
                                 notes="Recovery/incapacity text only; no idle Ready label.")]
        return element(prefix,x,y,117 if fullscreen else 105,145 if fullscreen else 185,
                       children=children,interactive=True,notes="Repeated live party slot; hide unused slots.")

    basebar = copy.deepcopy(overlay["elements"][0])
    basebar["asset"] = {"default":"obsidian_hud_fullscreen_basebar"}
    basebar["notes"] = "Carved Obsidian status revision from 2116. Fixed 640x114; clear status/input rail, 22.4 high."
    strip = basebar["children"][0]
    strip.pop("asset",None)
    strip["notes"] = "Modern portrait templates; dedicated renderer must use children instead of old ManaFRM/selring path."
    strip["children"] = [pc(i,True) for i in range(5)]
    status = next(n for n in basebar["children"] if n["id"] == "OutdoorStatusBar")
    status.update(anchor="top_left",offset_x=14.4,offset_y=2.666667,width=454.933333,height=17.066667)
    status["notes"] = "Reserved clear rail. Native Lucida 17; input/caret takes priority over event and hover text. No Ui-FrSp ornament."
    for i,node in enumerate(n for n in basebar["children"] if n["id"].startswith("CharShield_")):
        node.update(offset_x=(45.6+181.2*i)/1.875,offset_y=62/1.875,width=98/1.875,height=136/1.875)
        node["asset"] = {"default":f"obsidian_empty_slot_{max(1,i):02d}"}
        node["notes"] = "Empty party slot only; never cover an occupied portrait. Approved banner colour treatment applies."

    party = root("OutdoorGameplayBasebar",0,-23,605,185,"bottom_center",children=[
        element("OutdoorGameplayPartyStrip",0,0,605,185,children=[pc(i) for i in range(5)])],
        notes="Layout-only floating party; width = 105*n+20*(n-1) review px, n=1..5. No backing plate.")
    commands = root("OutdoorOptionsBar",28,-29,284,68,"bottom_left",children=[plate("ObsidianCommandPlate","command_plate",0,0)])
    for i,(suffix,icon,label) in enumerate([("Books","books","Books"),("QuickReference","party","Party"),
                                          ("Rest","rest","Rest"),("Options","options","Options")]):
        commands["children"].append(element("OutdoorButton"+suffix,i*72,9,68,59,interactive=True,children=[
            element("ObsidianCommandIcon"+suffix,13,0,42,38,"obsidian_"+icon),
            element("ObsidianCommandLabel"+suffix,0,39,68,17,text=(label,"Fondamento",11))]))
    resources = root("OutdoorGoldBar",28,26,267,43,children=[plate("ObsidianResourcePlate","resource_plate",0,0),
        element("OutdoorGoldIcon",5,8,37,27,"scorebg_gold"),
        element("OutdoorGoldLabel",44,0,81,43,text=("{gold}","Lucida",21)),
        element("OutdoorFoodIcon",143,8,37,27,"scorebg_food"),
        element("OutdoorFoodLabel",183,0,77,43,text=("{food}","Lucida",21))])
    buffs=root("ObsidianPartyBuffStrip",28,91,268,122,children=[],
               notes="Compact 4 + N default. Optional 8 + N in two rows; bounded width, stable expiry sort.")
    for i in range(8):
        buffs["children"].append(element(f"ObsidianPartyBuff{i+1}",(i%4)*55,(i//4)*65,48,57,
            "obsidian_hud_buff_normal",visible=i<4,interactive=True,children=[
                element(f"ObsidianPartyBuffArt{i+1}",6,3,36,36,notes="Glyph-free icon resolved by enum from design/buffs.yml."),
                element(f"ObsidianPartyBuffTimer{i+1}",0,42,48,12,text=("","SMALLNUM",9))]))
    buffs["children"].append(element("ObsidianPartyBuffOverflow",220,0,48,57,"obsidian_hud_buff_overflow",
        interactive=True,text=("","Lucida",17),notes="Live +N hidden count; no fixture count in runtime."))
    minimap=root("OutdoorMinimapFrame",-28,26,224,279,"top_right",children=[
        element("OutdoorMinimap",12,25,200,200,interactive=True,notes="Live circular map clip; keep Wizard Eye semantics and picking."),
        plate("ObsidianMinimapRim","minimap_rim",10,23),
        element("ObsidianMapNorth",0,0,224,18,text=("N","Lucida",13)),
        element("ObsidianMapLocation",-16,244,256,28,text=("","Lucida",16),notes="Live location; pale ivory, strong shadow, no baked place name.")])
    for sign,x,suffix in [("−",0,"Out"),("+",200,"In")]:
        minimap["children"].append(element("OutdoorMinimapZoom"+suffix,x,207,24,24,interactive=True,
            children=[plate("ObsidianMapZoomPlate"+suffix,"zoom_normal",0,0),
                      element("ObsidianMapZoomLabel"+suffix,0,0,24,24,text=(sign,"Lucida",14))]))
    followers=root("OutdoorFollowerToggle",-42,308,193,33,"top_right",interactive=True,children=[
        plate("ObsidianFollowersPlate","followers_normal",0,0),element("ObsidianFollowersArt",12,2,29,29,"obsidian_followers"),
        element("ObsidianFollowersLabel",45,0,140,33,text=("Followers {count}","Fondamento",13))])
    follower_panel=copy.deepcopy(next(n for n in overlay["elements"] if n["id"]=="OutdoorFollowerPanel"))
    follower_panel.update(anchor="top_right",anchor_space="screen",offset_x=-22.4,offset_y=188.8,visible=False)
    follower_panel.pop("asset",None)
    follower_panel["notes"]="Follower popup; retain live slot/action IDs and scroll behaviour. Shared obsidian popup frame."
    for n in flatten(follower_panel.get("children",[])):
        if n.get("asset"):
            n.pop("asset")
            n["notes"]="Live follower portrait or stateful scroll control; render with shared popup/button treatment."
    return dict(screen="OutdoorHud",elements=[basebar,party,commands,resources,buffs,minimap,followers,follower_panel,
        root("OutdoorGameplayStatusBar",0,-240,620,48,"bottom_center",visible=False,
             text=("","Lucida",16),notes="Content-sized plate, 620x148 review maximum. Hide empty; see responsive collision rule."),
        root("ObsidianTurnDock",329,-29,130,62,"bottom_left",visible=False,interactive=True,children=[
            plate("ObsidianTurnPlate","turn_normal",0,0),
            element("ObsidianTurnPhase",8,8,114,24,text=("","Lucida",13)),
            element("ObsidianTurnDetail",8,34,114,18,text=("","SMALLNUM",8))]),
        root("ObsidianPartyBuffPopup",28,162,360,180,visible=False,notes="Measured, scrollable remaining effects; popup style and input rules in design/gameplay.yml."),
        root("ObsidianPersonalBuffPopup",0,-244,345,180,"bottom_center",visible=False,
             notes="Live selected owner's effects. Opens from medallion without changing selection.")])


def main():
    for pack in PACKS:
        for source in sorted((pack/"engine/icons_x2").glob("*.png")):
            target = HERE/"engine/icons_x2"/source.name
            if target.exists() and sha(target)!=sha(source):
                raise ValueError(f"Conflicting approved graphics: {source.name}")
            copy_file(source,target,"Approved artwork")
        for source in (pack/"design").glob("*"):
            if source.is_file():
                copy_file(source,HERE/"design"/(pack.parent.name+"-"+source.name),"Frozen reviewed design contract")
        for name in ["INTEGRATION.md","manifest.json","asset_receipts.json"]:
            copy_file(pack/name,HERE/"sources"/pack.parent.name/name,"Historical package contract; current README takes precedence")
        for source in (pack/"masters").rglob("*"):
            if source.is_file():
                copy_file(source,HERE/"sources"/pack.parent.name/"masters"/source.relative_to(pack/"masters"),"Source master")

    source_layouts=ROOT/"assets_dev/engine/ui/gameplay"
    for source in sorted(source_layouts.glob("*.yml")):
        target=HERE/"reference_runtime/ui/gameplay"/source.name
        if not target.exists():
            copy_file(source,target,"Pinned current runtime layout before integration")
    for pack in PACKS:
        for approved in (pack/"engine/ui/gameplay").glob("*.yml"):
            base=yaml.safe_load((pack/"reference_layouts"/approved.name).read_text())
            live=yaml.safe_load((HERE/"reference_runtime/ui/gameplay"/approved.name).read_text())
            draft=merge(base,yaml.safe_load(approved.read_text()),live,approved.name)
            if approved.name=="gameplay.yml":
                draft=hud_layout(draft)
            write_yaml(HERE/"engine/ui/gameplay"/approved.name,draft)
    # Chest shares inventory geometry and fullscreen chrome; chest contents remain native data.
    chest=yaml.safe_load((HERE/"reference_runtime/ui/gameplay/chest.yml").read_text())
    replacements={"fr_inven":"obsidian_inventory_surface","topbar":"obsidian_topbar",
                  "IB-8pxbar":"obsidian_left_edge","Ib-Mb-A":"obsidian_house_sidebar"}
    for n in flatten(chest["elements"]):
        for key,value in n.get("asset",{}).items():
            n["asset"][key]=replacements.get(value,value)
        if n["id"]=="ChestCloseButton":
            n["asset"]={"default":"obsidian_button_close_normal","highlighted":"obsidian_button_close_hover",
                        "pressed":"obsidian_button_close_pressed"}
            n["text"]={"value":"Close","font":"Fondamento","align_x":"center","align_y":"middle",
                       "color":"#e8d1a4","scale":13.333333/32}
            n["notes"]="Shared blank plate at the native hit rectangle; preserve end caps, render localized label."
        elif n["id"]=="ChestIconBackground":
            n.pop("asset",None)
            n["notes"]="Icon now sits directly on the carved sidebar, without the legacy plaque."
    write_yaml(HERE/"engine/ui/gameplay/chest.yml",chest)

    # The old composite resource strip contains another skin. Keep counters and individual icons.
    for name,prefix in [("character","Character"),("dialogue","Dialogue"),("chest","Chest")]:
        path=HERE/"engine/ui/gameplay"/(name+".yml")
        document=yaml.safe_load(path.read_text())
        nodes={n["id"]:n for n in flatten(document["elements"])}
        node=nodes[prefix+"GoldFoodIcon"]
        node.pop("asset",None)
        node.update(anchor="top_left",offset_x=0,offset_y=0,width=180,height=29)
        node["children"]=[dict(id=prefix+suffix,anchor="top_left",offset_x=x,offset_y=7,width=22,height=14,
                               asset={"default":asset}) for suffix,x,asset in
                              [("GoldArt",18,"scorebg_gold"),("FoodArt",107,"scorebg_food")]]
        for suffix,x,w in [("GoldLabel",44,59),("FoodLabel",132,40)]:
            n=nodes[prefix+suffix]
            n.update(anchor="top_left",offset_x=x,offset_y=0,width=w,height=29)
            n["text"].update(font="Lucida",color="#e5dcc7",scale=11.2/17)
        if name=="dialogue":
            nodes["DialogueFrameEndCap"].pop("asset",None)
            nodes["DialogueFrameEndCap"]["notes"]="Retired decorative end cap; shared alpha frame owns the top edge."
        write_yaml(path,document)

    # Preserve contemporary font improvements; never downgrade global TTFs from historical studies.
    differences=[]
    for face in ["arrus","comic","create","lucida","smallnum","book2","autonote","fondamento"]:
        source=ROOT/"assets_dev/engine/fonts/truetype"/(face+".yml")
        descriptor=yaml.safe_load(source.read_text())
        copy_file(source,HERE/"engine/fonts/truetype"/source.name,"Current native font descriptor")
        target=HERE/"engine/fonts/truetype"/descriptor["file"]
        copy_file(source.parent/descriptor["file"],target,"Current native font binary; no historical downgrade")
        for pack in PACKS:
            old=pack/"engine/fonts/truetype"/descriptor["file"]
            if old.exists() and sha(old)!=sha(target):
                differences.append(dict(face=face,review_source=str(old.relative_to(ROOT)),review_sha256=sha(old),
                                        selected_sha256=sha(target),policy="Keep newer current native font; verify wrapping at integration."))
        if face=="autonote":
            descriptor["presentation"]="tintable"
            write_yaml(HERE/"engine/fonts/truetype/autonote.yml",descriptor)
    copy_file(ROOT/"assets_dev/engine/fonts/truetype/fondamento_ofl.txt",
              HERE/"engine/fonts/truetype/fondamento_ofl.txt","Fondamento SIL OFL")
    for pack in PACKS:
        for source in (pack/"engine/fonts").rglob("*"):
            if source.is_file() and source.suffix.lower()==".fnt":
                relative=source.relative_to(pack)
                live=ROOT/"assets_dev"/relative
                copy_file(live if live.exists() else source,HERE/relative,"Native authoritative FNT metrics")
    for name in ["scorebg_gold","scorebg_food"]:
        source=ROOT/"assets_dev/engine/icons_x2"/(name+".png")
        copy_file(source,HERE/"engine/icons_x2"/source.name,"Retained resource illustration")
    copy_file(UI/"hud_overlay_study_20260927/assets/generated/carved-obsidian-basebar-status-v3.png",
              HERE/"sources/basebar-status-v3.png","Built-in imagegen status rail edit; other art remains v2")
    for folder in ["hud_concepts_20260927","hud_overlay_study_20260927","obsidian_overlays_20260928","obsidian_journal_20260928"]:
        for name in ["README.md","app.js","style.css","index.html"]:
            copy_file(UI/folder/name,HERE/"sources"/folder/name,"Design source snapshot; live preview remains in sibling study")
        for source in (UI/folder/"approved").glob("*.png"):
            copy_file(source,HERE/"sources"/folder/"approved"/source.name,"Original approval capture")
    # Normalize the encoding of opaque browser exports; no painting, resizing or alpha-keying.
    for path in (HERE/"engine/icons_x2").glob("*.png"):
        image=Image.open(path)
        if image.mode!="RGBA":
            image.convert("RGBA").save(path)
    for receipt in receipts:
        receipt["source_sha256"]=sha(ROOT/receipt["source"])
        receipt["sha256"]=sha(HERE/receipt["path"])
    write_json(HERE/"source_receipts.json",list({r["path"]:r for r in receipts}.values()))
    write_json(HERE/"font_resolution.json",differences)
    write_json(HERE/"layout_rebase.json",dict(preserved_current_changes=rebases,unresolved_conflicts=[]))
    for path in (HERE/"engine").rglob("*"):
        if path.is_file():
            path.chmod(0o644)
    print(f"Prepared {len(list((HERE/'engine/ui/gameplay').glob('*.yml')))} layout candidates; {len(differences)} font-version decisions.")


if __name__=="__main__":
    main()
