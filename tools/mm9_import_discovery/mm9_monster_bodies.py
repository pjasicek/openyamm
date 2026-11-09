#!/usr/bin/env python3
"""MM9's monster collision bodies, by MM9's own rule (devdocs/mm9_rework/MM9_MONSTER_COLLISION_RE.md).

A monster's body is the box whose half extents are its model's animation dims (the `static_model` animation, else
animation 0) times its scale. The scale is the MONSTERS.txt `Scale` column, unless the DAT object has a `Scale`
other than 1.0, which then replaces it. In native units: radius = the larger horizontal half extent x scale x 2.56,
height = 2 x the vertical half extent x scale x 2.56.

Run from the repository root to rewrite the table overrides that generate_mm9_monster_tables.py applies:

    python3 tools/mm9_import_discovery/mm9_monster_bodies.py --write-overrides
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert_abc_model as abc  # noqa: E402
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MONSTERS_TXT = ROOT / "mm9/extracted/DATA/DATA/MONSTERS.txt"
MODELS_DIR = ROOT / "mm9/extracted/MODELS/MODELS"
OVERRIDES_TSV = Path(__file__).resolve().parent / "mm9_monster_body_overrides.tsv"
STATIC_ANIMATION = "static_model"
# Deliberate exceptions to MM9's rule (2026-11-02, the user's "Refresh all" decision): models whose sizing animation's
# box lies on its side, so the rule's height and radius swap (a person taller than wide comes out wide and flat).
# - SVEN.abc's static_model (34, 12, 16) is the seated scene pose; his standing animation `Sven` has the upright
#   (12, 34, 12) box of every MM9 townsman, which the rule then sizes as usual (Scale 1.25: 218 / 38; our mm9_sven GLB
#   stands 222 units in its Standing clip, as Annud's 178 against the rule's 174).
SIZING_ANIMATION_OVERRIDES = {"sven.abc": "Sven"}
# - The children's only animation (PEASANTBOY1/2/1E, PEASANTGIRL2/3/1E) has a (128, 16, 16) box: the rule gives 82 / 328.
#   Height and radius measured on our installed models instead (mm9_peasantboy_claude, mm9_peasantgirl_claude READMEs):
#   boys 1.36 m, MM9's (10, 26, 10) LT body -> 133 / 26; girls 1.294 m soles to crown, hem half-width 0.21 m -> 130 / 21.
BODY_EXCEPTIONS = {
    69: (133, 26, "boy, PeasantBoy1 measured (mm9_peasantboy)"),
    70: (133, 26, "boy, PeasantBoy2 = PeasantBoy1 body, measured (mm9_peasantboy)"),
    73: (133, 26, "boy, PeasantBoy1e = PeasantBoy1 body, measured (mm9_peasantboy)"),
    71: (130, 21, "girl, PeasantGirl2 measured (mm9_peasantgirl)"),
    72: (130, 21, "girl, PeasantGirl3 = PeasantGirl2 body, measured (mm9_peasantgirl)"),
    74: (130, 21, "girl, PeasantGirl1e = PeasantGirl2 body, measured (mm9_peasantgirl1e)"),
}


def initial_half_extents(path: Path, animation: str | None = None) -> tuple[str, tuple[float, float, float]]:
    """The animation MM9 sizes a new object by (`static_model`, else the first; `animation` names a deliberate other
    one, SIZING_ANIMATION_OVERRIDES) and its half extents in LT."""
    reader = abc.BinaryReader(path.read_bytes())
    sections = abc.read_sections(reader)
    reader.seek(sections["Header"])
    version = reader.read_u32()
    reader.skip(8)
    node_count = reader.read_u32()
    animations = []
    reader.seek(sections["Animation"])
    for _ in range(reader.read_u32()):
        dims = reader.read_vec3()
        name = reader.read_string()
        reader.skip(4)
        if version >= 12:
            reader.read_u32()
        keyframe_count = reader.read_u32()
        for _ in range(keyframe_count):
            reader.read_u32()
            reader.read_string()
        for _ in range(node_count):
            if version == 13:
                reader.skip(4)
            for _ in range(keyframe_count):
                reader.skip(12 + 16 + (8 if version == 13 else 0))
        animations.append((name, dims))
    bindings = {}
    if "AnimBindings" in sections:
        reader.seek(sections["AnimBindings"])
        for _ in range(reader.read_u32()):
            binding = abc.read_anim_binding(reader)
            bindings[binding.name.lower()] = binding.extents
    if animation is not None:
        name, dims = next(a for a in animations if a[0].lower() == animation.lower())
    else:
        name, dims = next((a for a in animations if a[0].lower() == STATIC_ANIMATION), animations[0])
    return name, tuple(bindings.get(name.lower()) or dims)


def effective_scale(row_scale: float, object_scale: float = 1.0) -> float:
    """MM9's actor setup: a DAT Scale other than 1.0 replaces the MONSTERS.txt Scale (it does not multiply)."""
    return object_scale if object_scale != 1.0 else row_scale


def native_body(half_extents: tuple[float, float, float], scale: float) -> tuple[int, int]:
    """(height, radius) in native units of a box with these half extents (LT) at this scale."""
    half_width = max(half_extents[0], half_extents[2])
    return (int(round(2 * half_extents[1] * scale * MM9_TO_OPENYAMM_COORDINATE_SCALE)),
            int(round(half_width * scale * MM9_TO_OPENYAMM_COORDINATE_SCALE)))


class Mm9MonsterBodies:
    """MONSTERS.txt rows (by MM9 number) with their model's initial half extents."""

    def __init__(self, monsters_txt: Path = MONSTERS_TXT, models_dir: Path = MODELS_DIR):
        with monsters_txt.open(newline="", encoding="cp1252") as input_file:
            rows = list(csv.reader(input_file, delimiter="\t"))
        column = {heading: index for index, heading in enumerate(rows[0])}
        self.rows = {}
        for row in rows[1:]:
            if row and row[0].strip().isdigit():
                scale = row[column["Scale"]].strip()
                self.rows[int(row[0])] = (row[column["Monster Name"]].strip(), row[column["ModelName"]].strip(),
                                          float(scale) if scale else 1.0)
        # MODELS/ itself only: PROPS/MUMMY.abc (a prop) and SAVE/SKELETON.abc share names with the monster models.
        self.models = {p.name.lower(): p for p in models_dir.glob("*") if p.suffix.lower() == ".abc"}
        self._extents = {}

    def model_extents(self, model: str) -> tuple[str, tuple[float, float, float]] | None:
        key = model.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if key not in self._extents:
            path = self.models.get(key)
            self._extents[key] = (initial_half_extents(path, SIZING_ANIMATION_OVERRIDES.get(key))
                                  if path is not None else None)
        return self._extents[key]

    def row_scale(self, source_number: int) -> float:
        return self.rows[source_number][2]

    def body(self, source_number: int, object_scale: float = 1.0) -> tuple[int, int] | None:
        """(height, radius) of MM9 row source_number placed with this DAT Scale; None without a shipped model."""
        _, model, row_scale = self.rows[source_number]
        if source_number in BODY_EXCEPTIONS:
            height, radius, _ = BODY_EXCEPTIONS[source_number]
            factor = effective_scale(row_scale, object_scale) / row_scale
            return int(round(height * factor)), int(round(radius * factor))
        extents = self.model_extents(model)
        if extents is None:
            return None
        return native_body(extents[1], effective_scale(row_scale, object_scale))

    def override_rows(self, source_numbers) -> list[list[str]]:
        out = []
        for number in sorted(source_numbers):
            name, model, row_scale = self.rows[number]
            extents = self.model_extents(model)
            if extents is None:
                continue
            height, radius = native_body(extents[1], row_scale)
            anim, (x, y, z) = extents
            source = f"{name}, {model} {anim} ({x:g}, {y:g}, {z:g}), Scale {row_scale:g}"
            if number in BODY_EXCEPTIONS:
                height, radius, reason = BODY_EXCEPTIONS[number]
                source += f"; exception: {reason}"
            elif model.lower() in SIZING_ANIMATION_OVERRIDES:
                source += "; exception: sized by the standing animation"
            # ToHitRadius 0: projectiles hit the actor's own (placed) radius.
            out.append([str(9000 + number), source, str(height), str(radius), "0"])
        return out


def write_overrides(path: Path, rows: list[list[str]]) -> None:
    header = [
        "# MM9 monster bodies by MM9's rule (devdocs/mm9_rework/MM9_MONSTER_COLLISION_RE.md), written by",
        "# mm9_monster_bodies.py --write-overrides and applied by generate_mm9_monster_tables.py after it copies the",
        "# legacy descriptor row. Columns are monster_descriptors.txt columns (Height = 3rd, Radius = 4th,",
        "# ToHitRadius = 6th; 0 = the actor's own radius); an empty cell keeps the copied value. Do not edit by hand:",
        "# rerun the writer (a deliberate exception belongs in mm9_monster_bodies.py, with its reason).",
    ]
    with path.open("w", newline="", encoding="utf-8") as output_file:
        output_file.write("\n".join(header) + "\n")
        writer = csv.writer(output_file, delimiter="\t", lineterminator="\n")
        writer.writerow(["row", "source", "Height", "Radius", "ToHitRadius"])
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-overrides", nargs="?", const=OVERRIDES_TSV, type=Path)
    parser.add_argument("--npc-actors", type=Path,
                        default=Path(__file__).resolve().parent / "mm9_npc_actor_rows.tsv")
    args = parser.parse_args()
    import generate_mm9_monster_tables as generator
    numbers = generator.source_monsters(MONSTERS_TXT, frozenset(generator.npc_actor_ids(args.npc_actors)))
    bodies = Mm9MonsterBodies()
    rows = bodies.override_rows(numbers)
    if args.write_overrides:
        write_overrides(args.write_overrides, rows)
        print(f"Wrote {len(rows)} MM9 monster body overrides to {args.write_overrides}")
    else:
        csv.writer(sys.stdout, delimiter="\t", lineterminator="\n").writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
