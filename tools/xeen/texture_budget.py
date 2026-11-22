#!/usr/bin/env python3
"""The Xeen texture budget (devdocs/xeen/ROADMAP.md section 5.2): each installed map against its class's cap, the
new textures per map and per kit, and the world's new textures against 450.

  tools/xeen/texture_budget.py [--root <asset root>] [--map <key or stem> ...]

Reads source/maps.yml (each map's class from its kind and role) and source/textures.yml (every new texture, its
family: a kit or "map <key>; ..."), and counts the distinct face textures of every map file found in
<root>/worlds/*/maps (assets_dev by default: the world's own maps, and stand-ins still played from another world).
Prints one line per map and the totals; exits 1 when anything is over its cap.
"""

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "util"))
import map_export  # noqa: E402

# Distinct face textures per map, and new textures per map (beyond its kit for outdoor maps).
CAPS = {
    "S": (30, 4),
    "M": (45, 8),
    "L": (70, 14),
    "ODM": (120, 12),
}
KIT_CAP = 30
WORLD_CAP = 450
# Maps allowed over their class's caps (decisions D-3.4, 2026-11-20: the Act I dungeons' textures made on 2026-11-13;
# D-22: XD-04; D-56, 2026-11-21: P5's board, ten lettered faces, sign and shrine stone):
# up to these counts (distinct faces, new) they are reported as grandfathered, not failed; their new textures still
# count toward the world's 450. None: the class's cap.
GRANDFATHERED = {
    "XD-01": (46, 12),
    "XD-02": (None, 15),
    "XD-03": (None, 12),
    "XD-04": (None, 13),
    "XD-05": (None, 11),
    "P5": (None, 13),
}


# Maps whose role names no class but which take one (D-50, 2026-11-21: the sky map X9 and the hidden town XD-17, both
# open-air BLVs, as Dungeon L; D-56: the finale P5 as Dungeon M).
CLASS_OF_MAP = {
    "X9": "L",
    "XD-17": "L",
    "P5": "M",
}


def map_class(entry):
    """S, M, L or ODM, or None for a map with no cap of its own (arena, planes, sky maps, the finale)."""
    if str(entry.get("key", "")) in CLASS_OF_MAP:
        return CLASS_OF_MAP[str(entry.get("key"))]
    if entry.get("kind") == "odm":
        return "ODM"
    role = str(entry.get("role", ""))
    if role.startswith("dungeon "):
        size = role.split()[1][0]
        return size if size in CAPS else None
    return None


def face_textures(path):
    """The distinct face texture names of an ODM or BLV (lower case, empty names left out)."""
    kind = path.suffix.lower().lstrip(".")
    payload = map_export.export_file(kind, path, None)["payload"]
    faces = []
    if kind == "odm":
        for bmodel in payload["bmodels"]:
            faces.extend(bmodel["faces"])
    else:
        faces = payload["faces"]
    return {str(face.get("texture_name", "")).strip().lower() for face in faces} - {""}


def find_map(root, stem):
    for path in sorted((root / "worlds").glob(f"*/maps/{stem}")):
        return path
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT / "assets_dev", help="asset root (default assets_dev)")
    parser.add_argument("--map", action="append", default=[], help="only these maps (key or stem)")
    args = parser.parse_args()

    source = ROOT / "assets_dev" / "worlds" / "xeen" / "source"
    maps = yaml.safe_load((source / "maps.yml").read_text())["maps"]
    registry = yaml.safe_load((source / "textures.yml").read_text())
    kits = set((registry.get("kits") or {}).keys())
    textures = registry.get("textures") or []

    new_by_map = {}
    new_by_kit = {}
    for texture in textures:
        family = str(texture.get("family", ""))
        head = family.split(";")[0].strip()
        if head.startswith("map "):
            new_by_map.setdefault(head[4:].strip(), set()).add(texture["name"])
        elif head in kits:
            new_by_kit.setdefault(head, set()).add(texture["name"])
        else:
            new_by_map.setdefault("?", set()).add(texture["name"])

    over = []
    wanted = {name.lower() for name in args.map}
    print(f"{'map':8} {'class':5} {'faces':>9} {'new':>7}  file")
    for entry in maps:
        key, stem = entry["key"], entry["stem"]
        if wanted and key.lower() not in wanted and stem.lower() not in wanted:
            continue
        path = find_map(args.root, stem)
        if path is None:
            continue
        size = map_class(entry)
        cap, new_cap = CAPS.get(size, (None, None))
        count = len(face_textures(path))
        new = len(new_by_map.get(key, ()))
        allowed_faces, allowed_new = GRANDFATHERED.get(key, (None, None))
        flags = []
        kept = []
        if cap is not None and count > cap:
            (kept if allowed_faces is not None and count <= allowed_faces else flags).append(f"faces over {cap}")
        if new_cap is not None and new > new_cap:
            (kept if allowed_new is not None and new <= allowed_new else flags).append(f"new over {new_cap}")
        over.extend(f"{key}: {flag}" for flag in flags)
        faces_text = f"{count}/{cap}" if cap else f"{count}/-"
        new_text = f"{new}/{new_cap}" if new_cap is not None else f"{new}/-"
        note = ("  OVER: " + ", ".join(flags)) if flags else ""
        if kept:
            note += "  allowed (D-3.4, D-22, D-56): " + ", ".join(kept)
        print(f"{key:8} {size or '-':5} {faces_text:>9} {new_text:>7}  {path.relative_to(args.root)}{note}")

    for kit in sorted(kits):
        count = len(new_by_kit.get(kit, ()))
        print(f"kit {kit}: {count}/{KIT_CAP}")
        if count > KIT_CAP:
            over.append(f"kit {kit}: over {KIT_CAP}")
    if "?" in new_by_map:
        print(f"textures with neither a kit nor a map family: {', '.join(sorted(new_by_map['?']))}")
    total = len({texture["name"] for texture in textures})
    print(f"world: {total}/{WORLD_CAP} new textures")
    if total > WORLD_CAP:
        over.append(f"world: over {WORLD_CAP}")
    for line in over:
        print("OVER " + line)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
