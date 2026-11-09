#!/usr/bin/env python3
"""Install the MM9 player characters: portrait families, grafted doll bodies, NPC pictures, character_data rows.

  python3 install.py --plan     # what would be written
  python3 install.py            # write (refuses to overwrite a file it did not write before)

Per character (dolls.json order of PC ids):
- assets_dev/engine/icons_x2/9pcNN-01..56.png from ../mm9_pc_portraits/pcNN/frames/
- assets_dev/engine/icons_x2/9pcNNbod.png from pcNN/9pcNNbod.png (the donor body with the MM9 head)
- assets_dev/engine/icons_x2/npc91NN.png: frame 01 on the NPC-picture backdrop, the face the Adventurer's Guild shows
- a character_data.txt row 90NN (9000 + the MM9 PC number; MAW appends rows from 78): the donor row's doll type, class, voice, sex, offsets, background, hand layers and attack
  columns, with the new body, face prefix 9pcNN-, NPC picture 91NN, the MM9 race and a note. Liches are not
  available at start (as MM6-MM8's), the others are.
Then run tools/cook_ui_textures.py to cook the faces_9pcNN atlases.
"""

import argparse
import csv
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ICONS = ROOT / "assets_dev/engine/icons_x2"
TABLE = ROOT / "assets_dev/engine/data_tables/character_data.txt"
PORTRAITS = HERE.parent / "mm9_pc_portraits"
RECEIPT = HERE / "install_receipt.json"
ROW_BASE = 9000  # row id = 9000 + MM9 PC number; MMerge rulesets (MAW) append their own rows from 78 up
NPC_PICTURE_BASE = 9100
RACE_IDS = {"human": 0, "elf": 7, "dwarf": 9, "half-orc": 8, "lich": 6}


def npc_picture(frame_path):
    """126x146 opaque face like the MM8 NPC pictures: the portrait head enlarged on a dim green backdrop."""
    frame = Image.open(frame_path).convert("RGBA")
    size = (126, 146)
    y = np.linspace(0, 1, size[1])[:, None]
    x = np.linspace(-1, 1, size[0])[None, :]
    glow = np.clip(1 - 0.55 * (x ** 2 + (y - 0.35) ** 2), 0, 1)
    base = np.array([34, 52, 38])[None, None, :] + glow[..., None] * np.array([46, 58, 42])[None, None, :]
    backdrop = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    scale = 1.18
    head = frame.resize((round(frame.width * scale), round(frame.height * scale)), Image.Resampling.LANCZOS)
    backdrop.alpha_composite(head, ((size[0] - head.width) // 2, -10))
    picture = backdrop.convert("RGB")
    ImageDraw.Draw(picture).rectangle([0, 0, size[0] - 1, size[1] - 1], outline=(24, 16, 26), width=2)
    return picture


def rows_to_add(header, rows):
    ix = {name: i for i, name in enumerate(header)}
    by_body = {r[ix["bod"]]: r for r in rows}
    dolls = json.loads((HERE / "dolls.json").read_text())["characters"]
    portraits = json.loads((PORTRAITS / "characters.json").read_text())["characters"]
    order = sorted(dolls, key=lambda cid: int(cid[2:]))
    plan = []
    for k, cid in enumerate(order):
        doll, portrait = dolls[cid], portraits[cid]
        n = cid[2:]
        row = list(by_body[doll["donor_body"]])
        row += [""] * (len(header) - len(row))
        row[ix["StatsUI"]] = str(ROW_BASE + int(n))
        row[ix["Available at start"]] = "-" if portrait["race"] == "lich" else "x"
        row[ix["bod"]] = doll["body_asset"]
        row[ix["head"]] = "none"
        row[ix["Face pics prefix"]] = portrait["prefix"]
        row[ix["NPCPic"]] = str(NPC_PICTURE_BASE + int(n))
        row[ix["Race"]] = str(RACE_IDS[portrait["race"]])
        row[ix["Notes"]] = f"MM9 {cid} {portrait['race']} {portrait['sex']} (body {doll['donor_body']})"
        plan.append((cid, n, doll, portrait, row))
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", action="store_true")
    arguments = parser.parse_args()
    text = TABLE.read_text()
    lines = text.splitlines()
    table = list(csv.reader(lines, delimiter="\t"))
    header, rows = table[0], [r for r in table[1:] if r and r[0].strip().isdigit()]
    if any(int(r[0]) > ROW_BASE for r in rows):
        raise SystemExit(f"character_data.txt already has rows above {ROW_BASE}; nothing written")
    previous = json.loads(RECEIPT.read_text())["files"] if RECEIPT.exists() else {}
    plan = rows_to_add(header, rows)
    writes = []
    for cid, n, doll, portrait, row in plan:
        frames = PORTRAITS / cid.lower() / "frames"
        for s in range(1, 57):
            writes.append((frames / f"{portrait['prefix']}{s:02d}.png", ICONS / f"{portrait['prefix']}{s:02d}.png"))
        writes.append((HERE / cid.lower() / f"{doll['body_asset']}.png", ICONS / f"{doll['body_asset']}.png"))
        writes.append((frames / f"{portrait['prefix']}01.png", ICONS / f"npc{NPC_PICTURE_BASE + int(n):04d}.png"))
    clashes = [str(t) for _, t in writes if t.exists() and str(t) not in previous]
    if clashes:
        raise SystemExit(f"Refusing to overwrite {len(clashes)} existing files, e.g. {clashes[:3]}")
    missing = [str(s) for s, _ in writes if not s.exists()]
    if missing:
        raise SystemExit(f"Missing sources: {missing[:5]}")
    if arguments.plan:
        print(f"{len(writes)} files into {ICONS}, {len(plan)} rows {plan[0][4][0]}-{plan[-1][4][0]}:")
        for cid, _, doll, portrait, row in plan:
            print("  " + "\t".join(row[:10]) + "\t" + row[header.index("Face pics prefix")] + "\t" + row[-1])
        return
    receipt = {}
    for source, target in writes:
        temporary = target.with_suffix(".tmp")
        if target.name.startswith("npc"):
            npc_picture(source).save(temporary, format="PNG")
        else:
            shutil.copyfile(source, temporary)
        temporary.chmod(0o644)
        temporary.replace(target)
        receipt[str(target)] = str(source)
    ending = "" if text.endswith("\n") else "\n"
    added = "\n".join("\t".join(row) for *_, row in plan) + "\n"
    TABLE.write_text(text + ending + added)
    RECEIPT.write_text(json.dumps({"rows": [int(row[0]) for *_, row in plan], "files": receipt}, indent=1) + "\n")
    print(f"Wrote {len(writes)} files and {len(plan)} rows; now run tools/cook_ui_textures.py")


if __name__ == "__main__":
    main()
