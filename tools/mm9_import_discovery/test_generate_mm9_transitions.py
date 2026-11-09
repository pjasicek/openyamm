#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import struct
import tempfile
import unittest
from pathlib import Path

import yaml

from generate_mm9_transitions import GenerationError, generate, property_value


def prop(name: str, value: object, code: int = 0, raw_hex: str = "") -> dict[str, object]:
    return {
        "name": name,
        "code": code,
        "decoded": True,
        "raw_hex": raw_hex,
        "value_json": json.dumps(value),
    }


def write_map(root: Path, stem: str, objects: list[dict[str, object]]) -> None:
    data = {
        "format_version": 1,
        "kind": "mm9_raw_world_objects",
        "source_dat": f"WORLDS/{stem.upper()}.dat",
        "objects": objects,
    }
    (root / f"{stem}.raw_objects.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    (root / f"{stem}.odm").write_bytes(b"map")


class GenerateMm9TransitionsTests(unittest.TestCase):
    def test_travel_days_uses_float_payload_instead_of_uint_bit_pattern(self) -> None:
        property_node = prop("TravelDays", 0x40000000, 6, struct.pack("<f", 2.0).hex())

        self.assertEqual(property_value(property_node), 2)

    def test_generation_resolves_case_insensitive_start_and_reviewed_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_map(root, "source", [{
                "object_index": 7,
                "name": "ExitTrigger",
                "properties": [
                    prop("Name", "Exit0"),
                    prop("Pos", [10.0, 20.0, 30.0]),
                    prop("Dims", [1.0, 2.0, 3.0]),
                    prop("DestinationWorld", "TARGET"),
                    prop("StartPointName", "SourceTypo"),
                    prop("AskPlayer", 1),
                    prop("TravelDays", 0x40400000, 6, struct.pack("<f", 3.0).hex()),
                ],
            }])
            write_map(root, "target", [{
                "object_index": 2,
                "name": "StartPoint",
                "properties": [
                    prop("Name", "Arrival"),
                    prop("Pos", [-10.0, 40.0, 20.0]),
                    prop("Rotation", [0.0, 3.141592653589793, 0.0, 0.0]),
                    prop("MovePlayerToFloor", 1),
                ],
            }])
            overrides = root / "overrides.yml"
            overrides.write_text(yaml.safe_dump({
                "format_version": 1,
                "transitions": [{
                    "id": "fix",
                    "source_map": "source",
                    "source_object_index": 7,
                    "disposition": "supported",
                    "resolved_start_point": "arrival",
                    "review_state": "reviewed",
                    "reason": "fixture correction",
                }],
            }), encoding="utf-8")

            records, audit = generate(root, overrides)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["CanonicalId"], "mm9:transition/source/7")
            self.assertEqual(records[0]["TravelDays"], 3)
            self.assertEqual((records[0]["ArrivalX"], records[0]["ArrivalY"], records[0]["ArrivalZ"]), (-26, 51, 102))
            self.assertEqual(records[0]["FacingYawUnits"], 1024)
            self.assertEqual(audit["summary"]["error_count"], 0)

    def test_unresolved_start_is_a_content_error_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_map(root, "source", [{
                "object_index": 1,
                "name": "ExitTrigger",
                "properties": [
                    prop("Name", "Exit0"),
                    prop("Pos", [0.0, 0.0, 0.0]),
                    prop("Dims", [1.0, 1.0, 1.0]),
                    prop("DestinationWorld", "target"),
                    prop("StartPointName", "missing"),
                ],
            }])
            write_map(root, "target", [])
            overrides = root / "overrides.yml"
            overrides.write_text("format_version: 1\ntransitions: []\n", encoding="utf-8")

            with self.assertRaisesRegex(GenerationError, "transition audit contains 1 errors"):
                generate(root, overrides)

    def test_guberland_gate_mechanisms_remain_separate_from_exit_volume(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        maps_root = repository_root / "assets_editor_dev/worlds/mm9/maps"
        with (repository_root / "assets_dev/worlds/mm9/data_tables/map_transitions.txt").open(
                encoding="utf-8", newline="") as stream:
            transition = next(
                record for record in csv.DictReader(stream, delimiter="\t")
                if record["CanonicalId"] == "mm9:transition/guberlandcity/185"
            )
        raw = yaml.safe_load((maps_root / "guberlandcity.raw_objects.yml").read_text(encoding="utf-8"))
        objects = {entry["object_index"]: entry for entry in raw["objects"]}

        self.assertEqual(transition["SourceClass"], "ExitTrigger")
        self.assertEqual(objects[185]["name"], "ExitTrigger")
        self.assertEqual((objects[847]["name"], objects[848]["name"]), ("Door", "Door"))
        self.assertEqual(objects[849]["name"], "Trigger")


if __name__ == "__main__":
    unittest.main()
