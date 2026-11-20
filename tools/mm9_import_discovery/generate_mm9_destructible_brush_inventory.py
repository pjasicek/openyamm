#!/usr/bin/env python3
"""Generate the checked-in MM9 destructible-brush inventory."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


OBJECT_INDEX_PATTERN = re.compile(r"^  - object_index: ([0-9]+)$")
OBJECT_CLASS_PATTERN = re.compile(r'^    name: "([^"]*)"$')
PROPERTY_NAME_PATTERN = re.compile(r'^      - name: "([^"]*)"$')
PROPERTY_VALUE_PREFIX = "        value_json: "
DEBRIS_MATERIAL_FIELDS = (
    "Stone",
    "Stone2",
    "Stone3",
    "Metal",
    "Glass",
    "Glass2",
    "Terrain",
    "Wood",
    "Wood2",
    "Wood3",
    "Custom",
)


@dataclass(frozen=True)
class DestructibleBrush:
    map_id: str
    source_dat: str
    source_object_index: int
    properties: dict[str, Any]
    coordinate_scale: float

    @property
    def source_name(self) -> str:
        return str(self.properties.get("Name", ""))

    @property
    def source_position(self) -> tuple[float, float, float]:
        position = self.properties.get("Pos")
        if not isinstance(position, list) or len(position) < 3:
            raise ValueError(
                f"{self.map_id} object {self.source_object_index} has no three-component Pos")
        return float(position[0]), float(position[1]), float(position[2])

    @property
    def openyamm_position(self) -> tuple[int, int, int]:
        source_x, source_y, source_z = self.source_position
        return (
            round(source_x * self.coordinate_scale),
            round(source_z * self.coordinate_scale),
            round(source_y * self.coordinate_scale),
        )


def parse_value_json(encoded_value: str) -> Any:
    """Decode the JSON value stored inside the sidecar's quoted value_json scalar."""
    return json.loads(json.loads(encoded_value))


def coordinate_scale(metadata_path: Path) -> float:
    for line in metadata_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("coordinate_scale:"):
            return float(stripped.split(":", 1)[1].strip())
    raise ValueError(f"{metadata_path} has no coordinate_scale")


def read_destructible_brushes(raw_objects_path: Path, metadata_path: Path) -> list[DestructibleBrush]:
    map_id = raw_objects_path.name[:-len(".raw_objects.yml")]
    scale = coordinate_scale(metadata_path)
    source_dat = ""
    object_index: int | None = None
    object_class = ""
    property_name = ""
    properties: dict[str, Any] = {}
    result: list[DestructibleBrush] = []

    def finish_object() -> None:
        if object_index is None or object_class != "DestructableBrush":
            return
        result.append(DestructibleBrush(
            map_id=map_id,
            source_dat=source_dat,
            source_object_index=object_index,
            properties=dict(properties),
            coordinate_scale=scale,
        ))

    with raw_objects_path.open(encoding="utf-8") as source_file:
        for line_number, line in enumerate(source_file, 1):
            line = line.rstrip("\n")
            if line.startswith("source_dat:"):
                source_dat = line.split(":", 1)[1].strip().strip('"')
                continue

            object_match = OBJECT_INDEX_PATTERN.match(line)
            if object_match is not None:
                finish_object()
                object_index = int(object_match.group(1))
                object_class = ""
                property_name = ""
                properties = {}
                continue

            class_match = OBJECT_CLASS_PATTERN.match(line)
            if class_match is not None and object_index is not None and not object_class:
                object_class = class_match.group(1)
                continue

            property_match = PROPERTY_NAME_PATTERN.match(line)
            if property_match is not None:
                property_name = property_match.group(1)
                continue

            if line.startswith(PROPERTY_VALUE_PREFIX) and property_name:
                try:
                    properties[property_name] = parse_value_json(
                        line[len(PROPERTY_VALUE_PREFIX):])
                except (json.JSONDecodeError, TypeError) as error:
                    raise ValueError(
                        f"{raw_objects_path}:{line_number}: invalid value_json for {property_name}") from error

    finish_object()
    for brush in result:
        if not brush.source_name:
            raise ValueError(
                f"{brush.map_id} object {brush.source_object_index} has no source Name")
        brush.source_position
    return result


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_number(value: float) -> str:
    return f"{value:g}"


def position_text(position: Iterable[float | int]) -> str:
    return "(" + ", ".join(format_number(float(value)) for value in position) + ")"


def source_identity(brush: DestructibleBrush) -> str:
    properties = brush.properties
    materials = [name for name in DEBRIS_MATERIAL_FIELDS if properties.get(name)]
    details: list[str] = []
    if materials:
        details.append("debris=" + ", ".join(materials))
    else:
        details.append("debris=unspecified")
    for label, property_name in (
        ("model", "CustomModel"),
        ("texture", "CustomTexture"),
        ("sound", "CustomSound"),
    ):
        value = properties.get(property_name)
        if value:
            details.append(f"{label}={value}")
    return "; ".join(details)


def source_behavior(brush: DestructibleBrush) -> str:
    properties = brush.properties
    details = [f"HP={format_number(float(properties.get('HitPoints', 0)))}"]
    if "CanDamage" in properties:
        details.append("ordinary-damage=" + ("enabled" if properties["CanDamage"] else "disabled"))
    if "Destructable" in properties and not properties["Destructable"]:
        details.append("source-destructible-flag=disabled")
    if properties.get("Exploding"):
        details.append(
            "explodes "
            f"damage={format_number(float(properties.get('ExplodeDamage', 0)))} "
            f"radius={format_number(float(properties.get('DamageRadius', 0)))}")
    if properties.get("TriggerDestroyOnly"):
        details.append("trigger-destroy-only")
    if properties.get("ShouldMiniSave"):
        details.append("mini-save")
    for label, property_name in (
        ("script", "ScriptName"),
        ("script params", "ScriptParams"),
        ("damage target", "DamageTriggerTarget"),
        ("damage message", "DamageTriggerMessage"),
        ("death target", "DeathTriggerTarget"),
        ("death message", "DeathTriggerMessage"),
        ("spawns", "SpawnObject"),
    ):
        value = properties.get(property_name)
        if value:
            details.append(f"{label}={value}")
    return "; ".join(details)


def generate_document(maps_directory: Path) -> str:
    raw_paths = sorted(maps_directory.glob("*.raw_objects.yml"))
    if not raw_paths:
        raise ValueError(f"no MM9 raw object sidecars found under {maps_directory}")

    brushes_by_map: dict[str, list[DestructibleBrush]] = {}
    source_dat_by_map: dict[str, str] = {}
    for raw_path in raw_paths:
        map_id = raw_path.name[:-len(".raw_objects.yml")]
        metadata_path = maps_directory / f"{map_id}.mm9.yml"
        if not metadata_path.is_file():
            raise ValueError(f"{raw_path} has no matching {metadata_path.name}")
        brushes = read_destructible_brushes(raw_path, metadata_path)
        brushes_by_map[map_id] = brushes
        source_dat_by_map[map_id] = brushes[0].source_dat if brushes else ""

    total_count = sum(len(brushes) for brushes in brushes_by_map.values())
    populated_count = sum(bool(brushes) for brushes in brushes_by_map.values())
    lines = [
        "# MM9 Destructible Brush Inventory",
        "",
        "This file is generated by "
        "`tools/mm9_import_discovery/generate_mm9_destructible_brush_inventory.py`; do not edit it by hand.",
        "It inventories the source objects whose MM9 class is spelled `DestructableBrush`.",
        "",
        "Positions labeled **MM9 LT** are the exact LithTech `Pos` values retained in each "
        "`*.raw_objects.yml` sidecar. **OpenYAMM** positions apply the map's declared coordinate scale and "
        "axis mapping `(x, y, z) = (LT.x, LT.z, LT.y) * scale`.",
        "The identity and behavior columns report source properties; `HP=0` is retained literally and is not "
        "interpreted here as indestructible or one-hit.",
        "",
        f"Total: **{total_count} brushes** across **{populated_count} maps**, with "
        f"**{len(brushes_by_map)} map sidecars checked**.",
        "",
        "## Map coverage",
        "",
        "| Map | Destructible brushes | Source DAT |",
        "| --- | ---: | --- |",
    ]
    for map_id, brushes in brushes_by_map.items():
        source_dat = source_dat_by_map[map_id]
        if not source_dat:
            source_dat = f"mm9/extracted/WORLDS/WORLDS/{map_id.upper()}.dat"
        lines.append(f"| `{map_id}` | {len(brushes)} | `{markdown_cell(source_dat)}` |")

    for map_id, brushes in brushes_by_map.items():
        if not brushes:
            continue
        lines.extend([
            "",
            f"## {map_id}",
            "",
            "| Source object | Source name | MM9 LT position | OpenYAMM position | What it is | Source behavior |",
            "| ---: | --- | --- | --- | --- | --- |",
        ])
        for brush in sorted(brushes, key=lambda entry: entry.source_object_index):
            lines.append(
                f"| {brush.source_object_index} | `{markdown_cell(brush.source_name)}` | "
                f"`{position_text(brush.source_position)}` | `{position_text(brush.openyamm_position)}` | "
                f"{markdown_cell(source_identity(brush))} | {markdown_cell(source_behavior(brush))} |")

    return "\n".join(lines) + "\n"


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    root = default_root()
    parser = argparse.ArgumentParser()
    parser.add_argument("--maps-directory", type=Path, default=root / "assets_editor_dev/worlds/mm9/maps")
    parser.add_argument("--output", type=Path, default=root / "devdocs/mm9/MM9_DESTRUCTIBLE_BRUSH_INVENTORY.md")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    document = generate_document(args.maps_directory)
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != document:
            print(f"{args.output} is missing or stale")
            return 1
        return 0
    args.output.write_text(document, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
