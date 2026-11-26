#!/usr/bin/env python3
"""Texture classes for the studio's texture checks (devdocs/xeen/formats/DOORS.md, TEXTURE_FIT.md): what each face
texture of the shipped MM6-MM8 maps and the Xeen maps is, by measurement, name and the hand-written overrides.

  tools/xeen/texture_classes.py [--root assets_dev] [--oymap <oymap>] [--out <file>] [--report <file>]
  tools/xeen/texture_classes.py --only NAME... [--root assets_dev]

`--only`: measure only the named textures and replace or add their lines, every other line as it stands (a full
rerun drifts from the committed classes: AGENT_GUIDE.md). A Xeen texture (worlds/xeen/textures_x2/<name>.png) goes to
worlds/xeen/models/texture_classes.yml, for textures no map lays yet (no `used`); an MM6-MM8 texture (its native
picture) to the engine file, keeping its committed `used` (an override changed, D-196's hkm1d and hkm3dr).

For every texture a face of those maps lays (and every texture of Xeen's own), from its native picture
(assets_source/textures/native_mm6_mm8/<world>/textures/*.bmp; Xeen's textures_x2/*.png):

- `seam`: [across, down], how far the picture's opposite edges are from meeting, as the mean step across the seam
  over the median step between neighbouring texel columns (rows) inside it: about 1 where the edges meet (the
  picture repeats without a line), 3 and more where they do not.
- `motif`: how much the picture's middle differs from its border (colour and detail, in the picture's own spread);
  measured only: it did not tell the shipped windows and signs from the walls the originals repeat (TEXTURE_FIT.md).
- `mirror`: how alike the picture is to its mirror image, 0 to 1.
- `tiles`: [across, down], whether it repeats cleanly that way: its edges meet (seam at or under SEAMLESS) or the
  shipped maps repeat it so (`used`).
- `class`: feature (meant once: a window, a sign, a picture, a panel, a door picture), by Xeen's registry
  (source/textures.yml `kind` picture or sign), the name, the door role, or edges clearly apart both ways
  (TRIM_SEAM) on a texture the originals lay whole once wherever they use it; flat (one colour: the dark faces of
  ways in, glow fills; never judged); else trim_u (repeats along
  its width only, its top and bottom clearly apart: a band, a frieze), trim_v (along its height only: a pillar strip)
  or tile.
- `door`: single (a door picture for one leaf), wing (one wing of a double door: a twin of mirrored pictures, or the
  two textures of a shipped pair of leaves), tile (a door surface that repeats: planks, bars).
- `border`: the mean colour of the picture's outer ring; `material`: the surface-material class most of that ring
  is made of (assets_source/worlds/<world>/surface_materials/<name>_m.png), where the texture has a class map.
- `storey_stack` (overrides only, decision D-41): edge (a footing or eaves panel meant once per wall: stacked whole
  once per storey up a wall it is an error) or module (made to repeat once per storey: no finding); unset: a warning.
- `used`: how the shipped maps lay it: the most copies across and down any face shows (the measured faces of
  `oymap audit --textures-measure`, with --oymap), which overrides the pixels where the originals repeat it.

The overrides (tools/xeen/texture_classes_overrides.yml, reviewed by A6) win over everything measured. Writes
assets_dev/engine/models/texture_classes.yml (MM6-MM8 textures) and assets_dev/worlds/xeen/models/
texture_classes.yml (Xeen's own), each by temp file and rename.
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "util"))
import map_export  # noqa: E402

NATIVE = ROOT / "assets_source" / "textures" / "native_mm6_mm8"
MATERIALS = ROOT / "tools" / "cook" / "surface_materials.yml"
OVERRIDES = Path(__file__).resolve().parent / "texture_classes_overrides.yml"
WORLDS = ("mm6", "mm7", "mm8")

# The measured limits (calibrated on the shipped maps: devdocs/xeen/formats/TEXTURE_FIT.md).
SEAMLESS = 3.0      # seam ratio at or under this: the edges meet (90 % of the textures the originals repeat across)
TRIM_SEAM = 5.0     # a band or strip: its other edges this far from meeting (the originals repeat 4-6 % past it)
SHIPPED_REPEAT = 1.6  # the originals lay it this many times across (down) a surface: it repeats that way
TWIN_MIRROR = 0.55  # a twin's mirror image this alike (and clearly more than the picture's own mirror): a wing
# Xeen's own textures by their kind in source/textures.yml: pictures and signs are meant once (cut-outs and derived
# cuts are measured: a portcullis or a cage's bars repeat across).
XEEN_FEATURE_KINDS = ("picture", "sign")

# A door picture by its name: door, dor, gate, MM6's t<n>d<n>, MM7's house doors (hkm2d, hwp1d, hhm1d2), drl/drr.
DOOR_NAME = re.compile(r"door|dor|gate|^t\dd\d|^h[a-z]{2}\d+d\d?[lr]?$|dr[lr]$|dr\d")
# A feature by its name: windows, signs, pictures, panels, banners, crests (not bookshelves or wine racks: the
# originals run them along whole walls).
FEATURE_NAME = re.compile(r"win|wndw|sign|sgn|pic|panel|banner|ban$|crest|notice|portrait|tapest")
NOT_FEATURE_NAME = re.compile(r"books|shelf|rack")


def is_door_name(name):
    return bool(DOOR_NAME.search(name)) and "trim" not in name


def native_index():
    """Lower-case texture name to its native picture (the first world that has it: MM6, MM7, MM8)."""
    index = {}
    for world in WORLDS:
        for path in sorted((NATIVE / world / "textures").glob("*.bmp")):
            index.setdefault(path.stem.lower(), (world, path))
    return index


def map_faces(path):
    kind = path.suffix.lower().lstrip(".")
    payload = map_export.export_file(kind, path, None)["payload"]
    if kind == "odm":
        return [face for bmodel in payload["bmodels"] for face in bmodel["faces"]]
    return payload["faces"]


def used_textures(root):
    names = set()
    for world in WORLDS + ("xeen",):
        for path in sorted((root / "worlds" / world / "maps").glob("*")):
            if path.suffix.lower() in (".blv", ".odm"):
                for face in map_faces(path):
                    name = str(face.get("texture_name", "")).strip().lower()
                    if name:
                        names.add(name)
    return names


def load_rgb(path, halve=False):
    image = Image.open(path).convert("RGB")
    if halve:
        image = image.resize((max(1, image.width // 2), max(1, image.height // 2)), Image.BOX)
    return np.asarray(image, dtype=np.float32)


def seam_ratio(pixels, axis):
    """Mean step across the wrap seam over the median step between neighbours, along `axis` (1: across)."""
    if pixels.shape[axis] < 4:
        return 0.0
    steps = np.abs(np.diff(pixels, axis=axis)).mean(axis=(1 - axis, 2))
    edge = np.abs(np.take(pixels, 0, axis=axis) - np.take(pixels, -1, axis=axis)).mean()
    inside = float(np.median(steps))
    return float(edge / max(inside, 1.0))


def motif_score(pixels):
    """How the middle differs from the border ring: mean colour and detail, in the picture's own spread."""
    height, width, _ = pixels.shape
    ring = max(2, min(width, height) // 8)
    middle = pixels[height // 4: height - height // 4, width // 4: width - width // 4]
    mask = np.zeros((height, width), dtype=bool)
    mask[:ring, :] = mask[-ring:, :] = True
    mask[:, :ring] = mask[:, -ring:] = True
    border = pixels[mask]
    spread = float(pixels.reshape(-1, 3).std(axis=0).mean()) + 1.0
    colour = float(np.abs(middle.reshape(-1, 3).mean(axis=0) - border.mean(axis=0)).mean()) / spread
    detail = abs(float(middle.reshape(-1, 3).std(axis=0).mean()) - float(border.std(axis=0).mean())) / spread
    return colour + detail


def likeness(a, b):
    """1 - mean difference over the mean difference to a half-turned copy of itself (0: unrelated, 1: equal)."""
    if a.shape != b.shape:
        return 0.0
    shifted = np.roll(np.roll(a, a.shape[1] // 2, axis=1), a.shape[0] // 2, axis=0)
    reference = float(np.abs(a - shifted).mean()) + 1.0
    return max(0.0, 1.0 - float(np.abs(a - b).mean()) / reference)


def border_colour(pixels):
    height, width, _ = pixels.shape
    ring = max(1, min(width, height) // 16)
    mask = np.zeros((height, width), dtype=bool)
    mask[:ring, :] = mask[-ring:, :] = True
    mask[:, :ring] = mask[:, -ring:] = True
    return [int(round(value)) for value in pixels[mask].mean(axis=0)]


def material_keys():
    data = yaml.safe_load(MATERIALS.read_text())
    return {name: np.array(entry["key"], dtype=np.float32) for name, entry in data["classes"].items()}


def border_material(name, world, keys):
    """The class most of the class map's outer ring is, or None without a class map."""
    for candidate in (world,) + WORLDS:
        path = ROOT / "assets_source" / "worlds" / candidate / "surface_materials" / f"{name}_m.png"
        if path.exists():
            pixels = load_rgb(path)
            height, width, _ = pixels.shape
            ring = max(1, min(width, height) // 16)
            mask = np.zeros((height, width), dtype=bool)
            mask[:ring, :] = mask[-ring:, :] = True
            mask[:, :ring] = mask[:, -ring:] = True
            texels = pixels[mask]
            names = list(keys)
            table = np.stack([keys[key] for key in names])
            nearest = np.argmin(((texels[:, None, :] - table[None, :, :]) ** 2).sum(axis=2), axis=1)
            counts = np.bincount(nearest, minlength=len(names))
            return names[int(counts.argmax())]
    return None


def run_oymap(oymap, root, measure_dir=None):
    """Runs `oymap audit --textures-measure --doors-measure` over every shipped and Xeen map: per texture the most
    copies across and down a surface shows, and the textures on the two leaves of each pair. With `measure_dir`, each
    map's output is kept there (<world>.<map>.txt) for the calibration."""
    used = {}
    pairs = {}
    if measure_dir and oymap is not None:
        measure_dir.mkdir(parents=True, exist_ok=True)
    for world in WORLDS + ("xeen",):
        for path in sorted((root / "worlds" / world / "maps").glob("*")):
            if path.suffix.lower() not in (".blv", ".odm"):
                continue
            kept = measure_dir / f"{world}.{path.name}.txt" if measure_dir else None
            if oymap is None:
                stdout = kept.read_text() if kept and kept.exists() else ""
            else:
                stdout = subprocess.run([str(oymap), "audit", path.name, "--world", world, "--assets", str(root),
                                         "--textures-measure", "--doors-measure"], capture_output=True,
                                        text=True).stdout
                if kept:
                    kept.write_text(stdout)
            for line in stdout.splitlines():
                match = re.search(r"textures\.measure: face \S+(?: \(\+\d+\))? tex (\S+) \S+ width \S+ height \S+ "
                                  r"copies (\S+) x (\S+)", line)
                if match and world != "xeen":
                    entry = used.setdefault(match.group(1), [0.0, 0.0])
                    entry[0] = max(entry[0], float(match.group(2)))
                    entry[1] = max(entry[1], float(match.group(3)))
                match = re.search(r"doors\.measure: .*? tex (\S+) .* partner .* tex (\S+)", line)
                if match and world != "xeen" and match.group(1) != match.group(2):
                    pairs.setdefault(match.group(1), set()).add(match.group(2))
    return used, pairs


def classify(name, pixels, used, xeen_kind):
    """The class and per-axis clean repeat of a texture: a feature by Xeen's registry or its name (a door picture's
    class is the door check's); else by its edges (and where the originals repeat it): tile, or a band (trim_u) or
    strip (trim_v) when one way meets and the other clearly does not."""
    seam_u = seam_ratio(pixels, 1)
    seam_v = seam_ratio(pixels, 0)
    motif = motif_score(pixels)
    across = seam_u <= SEAMLESS or (used is not None and used[0] >= SHIPPED_REPEAT)
    down = seam_v <= SEAMLESS or (used is not None and used[1] >= SHIPPED_REPEAT)
    if float(pixels.std()) < 1.0:
        # One colour (MM's solid01 voids, glow fills): nothing to fit.
        kind = "flat"
    elif xeen_kind in XEEN_FEATURE_KINDS or (FEATURE_NAME.search(name) and not NOT_FEATURE_NAME.search(name)):
        kind = "feature"
    elif seam_u >= TRIM_SEAM and seam_v >= TRIM_SEAM and (used is None or all(0.9 <= copies <= 1.1 for copies in used)):
        # Edges clearly apart both ways, and the originals lay it whole once wherever they use it: a panel meant
        # once (a wall's end post, a shop sign, a carved panel).
        kind = "feature"
    elif across and not down and seam_v >= TRIM_SEAM:
        kind = "trim_u"
    elif down and not across and seam_u >= TRIM_SEAM:
        kind = "trim_v"
    else:
        kind = "tile"
    return kind, seam_u, seam_v, motif, [bool(across), bool(down)]


def twin_of(name, names):
    """The other half's name of a pair named by its last letter: l/r, a/b."""
    for first, second in (("l", "r"), ("r", "l"), ("a", "b"), ("b", "a")):
        if name.endswith(first) and name[:-1] + second in names:
            return name[:-1] + second
    return None


def write_atomically(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    with os.fdopen(handle, "w") as stream:
        stream.write(text)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT / "assets_dev")
    parser.add_argument("--oymap", type=Path, help="measure the shipped maps' faces and pairs with this oymap")
    parser.add_argument("--out", type=Path, help="engine file (default <root>/engine/models/texture_classes.yml)")
    parser.add_argument("--report", type=Path, help="also write a table of every texture's numbers here")
    parser.add_argument("--measure-dir", type=Path, help="keep each map's measured output here (without --oymap: "
                        "read it from there)")
    parser.add_argument("--only", nargs="+", help="measure only these Xeen textures and update their lines")
    args = parser.parse_args()

    index = native_index()
    xeen_textures = {path.stem.lower(): path for path in (args.root / "worlds" / "xeen" / "textures_x2").glob("*.png")}
    engine_path = args.out or args.root / "engine" / "models" / "texture_classes.yml"
    used, pairs = {}, {}
    if args.only:
        only = {name.lower() for name in args.only}
        missing = sorted(only - set(xeen_textures) - set(index))
        if missing:
            print(f"neither in worlds/xeen/textures_x2 nor a native MM6-MM8 texture: {missing}", file=sys.stderr)
            return 1
        index = {name: index[name] for name in only if name in index and name not in xeen_textures}
        names = only
        # An engine texture keeps how the shipped maps lay it (its committed `used`, measured by a full run).
        committed = (yaml.safe_load(engine_path.read_text()) or {}).get("textures") or {}
        used = {name: committed[name]["used"] for name in index if "used" in (committed.get(name) or {})}
    else:
        names = used_textures(args.root) | set(xeen_textures)
    if args.oymap or args.measure_dir:
        # Without --oymap the measured output kept in --measure-dir is read again.
        used, pairs = run_oymap(args.oymap, args.root, args.measure_dir)
    registry = yaml.safe_load((args.root / "worlds" / "xeen" / "source" / "textures.yml").read_text()) or {}
    xeen_kinds = {str(entry["name"]).lower(): entry.get("kind") for entry in registry.get("textures") or []}
    overrides = yaml.safe_load(OVERRIDES.read_text()) or {}
    override_rows = {key.lower(): value for key, value in (overrides.get("textures") or {}).items()}
    keys = material_keys()

    pictures = {}
    sources = {}
    for name in sorted(names):
        if name in xeen_textures:
            pictures[name] = load_rgb(xeen_textures[name], halve=True)
            sources[name] = "xeen"
        elif name in index:
            pictures[name] = load_rgb(index[name][1])
            sources[name] = index[name][0]

    rows = {}
    for name, pixels in pictures.items():
        kind, seam_u, seam_v, motif, tiles = classify(name, pixels, used.get(name), xeen_kinds.get(name))
        mirror = likeness(pixels, pixels[:, ::-1])
        row = {
            "size": [int(pixels.shape[1]), int(pixels.shape[0])],
            "class": kind,
            "tiles": tiles,
            "seam": [round(seam_u, 2), round(seam_v, 2)],
            "motif": round(motif, 2),
            "mirror": round(mirror, 2),
            "border": border_colour(pixels),
        }
        if name in used:
            row["used"] = [round(used[name][0], 2), round(used[name][1], 2)]
        material = border_material(name, sources[name], keys) if sources[name] != "xeen" else None
        if material:
            row["material"] = material
        # Doors: the two textures of a shipped pair of leaves are wings (the originals never mirror a leaf: each
        # wing is a texture of its own); a door by name is a single leaf's picture, or a door surface that repeats
        # when it tiles. A twin by name whose mirror image it is (chb1dl, chb1dr) is only noted: the originals
        # name doors hinged left and right so too, and the overrides say which twins are wings.
        twin = twin_of(name, pictures)
        twin_mirror = likeness(pixels, pictures[twin][:, ::-1]) if twin else 0.0
        # A texture the originals repeat across a face is a surface, not a wing (MM7's a2b panels, 7d23).
        repeated = name in used and used[name][0] >= SHIPPED_REPEAT
        if name in pairs and not repeated:
            row["door"] = "wing"
            row["twin"] = sorted(pairs[name])[0]
        elif is_door_name(name):
            # A door surface that repeats: its edges meet and it tiles, or the originals repeat it (planks, the
            # Hive's ribs); else one leaf's picture.
            row["door"] = "tile" if (tiles[0] and kind in ("tile", "trim_u")) or repeated else "single"
        if row.get("door") in ("single", "wing"):
            row["class"] = "feature"
        if twin and twin_mirror >= TWIN_MIRROR and "twin" not in row:
            row["mirror_twin"] = twin
        rows[name] = row

    # A key with * or ? names every texture it matches (t07b0*); a texture's own key wins over a pattern.
    patterns = [(key, change) for key, change in override_rows.items() if any(c in key for c in "*?[")]
    for name in rows:
        for key, change in patterns:
            if fnmatch.fnmatchcase(name, key):
                rows[name].update(change)
                rows[name]["override"] = True
    for name, change in override_rows.items():
        if name in rows:
            rows[name].update(change)
            rows[name]["override"] = True

    header = ("# Written by tools/xeen/texture_classes.py (do not edit; overrides go in "
              "tools/xeen/texture_classes_overrides.yml).\n"
              "# Each face texture's class, door role, mirror likeness, border colour and material, as "
              "devdocs/xeen/formats/TEXTURE_FIT.md says.\n")

    def dump(selected):
        lines = [header, "textures:\n"]
        for name in sorted(selected):
            lines.append(f"  {name}: " + yaml.safe_dump(rows[name], default_flow_style=True, width=1000).strip()
                         + "\n")
        return "".join(lines)

    if args.only:
        # The named rows replace or join the committed lines of their file; nothing else changes.
        xeen_path = args.root / "worlds" / "xeen" / "models" / "texture_classes.yml"
        for path, selected in ((xeen_path, [n for n in rows if sources[n] == "xeen"]),
                               (engine_path, [n for n in rows if sources[n] != "xeen"])):
            if not selected:
                continue
            lines = {}
            for line in path.read_text().splitlines(keepends=True):
                if line.startswith("  ") and ":" in line:
                    lines[line.strip().split(":", 1)[0]] = line
            for name in selected:
                lines[name] = (f"  {name}: " + yaml.safe_dump(rows[name], default_flow_style=True, width=1000).strip()
                               + "\n")
            write_atomically(path, header + "textures:\n" + "".join(lines[name] for name in sorted(lines)))
            for name in sorted(selected):
                print(lines[name], end="")
        return 0

    engine_rows = [name for name in rows if sources[name] != "xeen"]
    xeen_rows = [name for name in rows if sources[name] == "xeen"]
    write_atomically(engine_path, dump(engine_rows))
    write_atomically(args.root / "worlds" / "xeen" / "models" / "texture_classes.yml", dump(xeen_rows))

    if args.report:
        with open(args.report, "w") as stream:
            for name in sorted(rows):
                row = rows[name]
                stream.write(f"{name} {sources[name]} {row['class']} seam {row['seam'][0]} {row['seam'][1]} motif "
                             f"{row['motif']} mirror {row['mirror']} door {row.get('door', '-')} twin "
                             f"{row.get('twin', '-')} mirror_twin {row.get('mirror_twin', '-')} used "
                             f"{row.get('used', '-')}\n")
    print(f"{len(rows)} textures: {len(engine_rows)} engine, {len(xeen_rows)} Xeen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
