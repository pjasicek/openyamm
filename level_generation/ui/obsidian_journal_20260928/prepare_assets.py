#!/usr/bin/env python3
"""Local review fixtures from installed content. Does not modify runtime data or unlock entries."""
import csv
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
receipts = []


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copy(source, target, pinned=False):
    if pinned and target.exists() and digest(source) != digest(target):
        raise RuntimeError(f"Approved source changed: {target}. Rebase explicitly before preparing again.")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(0o644)
    receipts.append(dict(source=str(source.relative_to(ROOT)),target=str(target.relative_to(HERE)),sha256=digest(source)))


for name in ["autonote", "book2", "create", "smallnum", "lucida"]:
    copy(ROOT / f"assets_dev/engine/fonts/truetype/openyamm_{name}_faithful.ttf",
         HERE / f"assets/fonts/{name}.ttf", pinned=True)
copy(ROOT / "level_generation/ui/hud_overlay_study_20260927/assets/fonts/Fondamento-Regular.ttf",
     HERE / "assets/fonts/fondamento.ttf", pinned=True)
copy(ROOT / "level_generation/ui/hud_overlay_study_20260927/assets/fonts/fondamento-OFL.txt",
     HERE / "assets/fonts/fondamento-ofl.txt", pinned=True)
copy(ROOT / "level_generation/ui/hud_concepts_20260927/assets/generated/obsidian-books-v2.png",
     HERE / "assets/generated/journal-notes-v1.png", pinned=True)
copy(ROOT / "assets_dev/engine/icons_x2/divbar.png",HERE / "assets/divbar.png")
source = ROOT / "assets_dev/worlds/mm6/icons_x2/oute3.bmp"
Image.open(source).convert("RGB").save(HERE / "assets/new-sorpigal.png")
receipts.append(dict(source=str(source.relative_to(ROOT)),target="assets/new-sorpigal.png",sha256=digest(source),
                     operation="Lossless format conversion of the installed map; no terrain or geometry edits."))
for name in ["journal", "character_creation"]:
    copy(ROOT / f"assets_dev/engine/ui/gameplay/{name}.yml",HERE / f"reference_layouts/{name}.yml", pinned=True)


def table(name):
    source=ROOT / f"assets_dev/engine/data_tables/english/{name}.txt"
    receipts.append(dict(source=str(source.relative_to(ROOT)),sha256=digest(source),operation="Read-only review text fixtures"))
    return list(csv.reader(source.open(encoding="cp1252"),delimiter="\t"))[1:]


quests=table("quests")
notes=table("autonote")
history=table("history")
categories={"potion":"potion","fountain":"stat","obelisk":"obelisk","seer":"seer","misc":"misc","trainer":"teacher"}
data={
    "quests":[dict(id=r[0],text=r[1]) for r in quests if len(r)>1 and r[1] and r[0].isdigit() and 1105<=int(r[0])<=1140],
    "notes":{key:[dict(id=r[0],text=r[1]) for r in notes if len(r)>2 and r[2].lower()==category and r[1] not in ("", "0")][:24]
             for key,category in categories.items()},
    "story":[dict(id=r[0],text=r[1],title=r[3]) for r in history if len(r)>3 and r[0].isdigit()][:3],
    "status":"1 adventurer needs a name, all points spent, and two extra skills.",
}
(HERE / "content.js").write_text("// Read-only fixtures from installed global tables; not the user's unlocked journal.\nconst JOURNAL_CONTENT = "
                                 +json.dumps(data,ensure_ascii=False,indent=2)+";\n")
(HERE / "asset_sources.json").write_text(json.dumps(receipts,indent=2)+"\n")
print("Prepared native fonts, installed map and actual journal strings.")
