#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPO_ROOT / "tools/mm9_import_discovery/generate_mm9_events.py"

spec = importlib.util.spec_from_file_location("generate_mm9_events", GENERATOR_PATH)
assert spec is not None
generate_mm9_events = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = generate_mm9_events
spec.loader.exec_module(generate_mm9_events)


def prop(name: str, value_json: str, code: int = 0, decoded: bool = True) -> dict[str, object]:
    return {
        "name": name,
        "code": code,
        "flags": 0,
        "declared_data_length": 0,
        "consumed_data_length": 0,
        "decoded": decoded,
        "raw_hex": "",
        "value_json": value_json,
    }


class Mm9EventsGeneratorTests(unittest.TestCase):
    def test_preserves_raw_objects_properties_and_trigger_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            maps_root = root / "maps"
            scripts_root = root / "scripts"
            events_root = root / "events"
            maps_root.mkdir()
            scripts_root.mkdir()
            (scripts_root / "DOORLOCK.scr").write_text(
                """
#include globals.inc
:OnUse
SetStat g_hmyobject,Locked,FALSE
Exit TRUE
:Main
AddTrigger use OnUse
Exit
""".strip(),
                encoding="utf-8",
            )
            raw_path = maps_root / "test.raw_objects.yml"
            raw_path.write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_raw_world_objects",
                        "source_dat": "TEST.dat",
                        "object_count": 2,
                        "objects": [
                            {
                                "object_index": 0,
                                "name": "Door",
                                "property_count": 8,
                                "data_length": 0,
                                "properties": [
                                    prop("Name", '"DoorA"'),
                                    prop("Pos", "[1.0, 2.0, 3.0]", 1),
                                    prop("MoveDir", "[0.0, -1.0, 0.0]", 1),
                                    prop("MoveDist", "160.0", 3),
                                    prop("Speed", "40.0", 3),
                                    prop("ScriptName", '"scripts\\\\DOORLOCK.scr"'),
                                    prop("OpenTriggerTarget0", '"TriggerA"'),
                                    prop("OpenTrigger0", '"Go"'),
                                ],
                            },
                            {
                                "object_index": 1,
                                "name": "Trigger",
                                "property_count": 4,
                                "data_length": 0,
                                "properties": [
                                    prop("Name", '"TriggerA"'),
                                    prop("Dims", "[10.0, 20.0, 30.0]", 1),
                                    prop("TargetName1", '"MissingTarget"'),
                                    prop("MessageName1", '"Use"'),
                                ],
                            },
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            event_data, script_irs = generate_mm9_events.build_events_for_map(raw_path, scripts_root, events_root)
            self.assertEqual(generate_mm9_events.validate_event_data(raw_path, event_data), [])
            self.assertEqual(event_data["kind"], "mm9_events")
            self.assertEqual(event_data["generated"]["script_ir"], "../events/test.script_ir.yml")
            self.assertEqual(event_data["validation"]["raw_object_count"], 2)
            self.assertEqual(event_data["validation"]["event_object_count"], 2)
            self.assertEqual(len(event_data["objects"][0]["raw_properties"]), 8)
            self.assertEqual(event_data["objects"][0]["normalized_properties"]["MoveDist"], 160.0)
            self.assertEqual(event_data["mechanisms"][0]["mechanism"]["kind"], "linear_door")
            self.assertEqual(event_data["mechanisms"][0]["trigger_outputs"][0]["target_name"], "TriggerA")
            self.assertEqual(event_data["mechanisms"][0]["trigger_outputs"][0]["resolution"], "resolved")
            self.assertEqual(event_data["triggers"][0]["outputs"][0]["target_name"], "MissingTarget")
            self.assertEqual(event_data["triggers"][0]["outputs"][0]["resolution"], "unresolved")
            self.assertEqual(event_data["scripts"][0]["registered_triggers"][0]["message"], "use")
            self.assertIn("doorlock.scr", script_irs)

            lua_path = events_root / "test.lua"
            generate_mm9_events.write_map_lua(lua_path, "test", script_irs)
            lua_text = lua_path.read_text(encoding="utf-8")
            self.assertIn("map.map_id = \"test\"", lua_text)
            self.assertIn("registered_triggers", lua_text)
            self.assertIn("return map", lua_text)

            script_ir_path = events_root / "test.script_ir.yml"
            generate_mm9_events.write_map_script_ir(script_ir_path, "test", scripts_root, script_irs)
            script_ir_data = yaml.safe_load(script_ir_path.read_text(encoding="utf-8"))
            self.assertEqual(script_ir_data["kind"], "mm9_script_ir")
            self.assertEqual(script_ir_data["map_id"], "test")
            self.assertEqual(script_ir_data["validation"]["script_count"], 1)
            self.assertEqual(script_ir_data["scripts"][0]["script_id"], "doorlock.scr")

    def test_scene_model_instance_binding_is_opt_in_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            maps_root = root / "maps"
            scripts_root = root / "scripts"
            events_root = root / "events"
            maps_root.mkdir()
            scripts_root.mkdir()
            raw_path = maps_root / "test.raw_objects.yml"
            raw_path.write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_raw_world_objects",
                        "source_dat": "TEST.dat",
                        "objects": [
                            {
                                "object_index": 7,
                                "name": "Prop",
                                "property_count": 2,
                                "data_length": 0,
                                "properties": [
                                    prop("Name", '"PropA"'),
                                    prop("ScriptName", '"missing.scr"'),
                                ],
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (maps_root / "test.scene.yml").write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "model_instances": [
                            {
                                "instance_id": "mm9:test:model_instance:0",
                                "source_object_index": 7,
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            event_data, _ = generate_mm9_events.build_events_for_map(raw_path, scripts_root, events_root)
            self.assertEqual(event_data["bindings"][0]["targets"][0]["target_kind"], "model_instance")
            self.assertEqual(event_data["bindings"][0]["targets"][0]["confidence"], "exact_source_object_index")
            self.assertEqual(event_data["unresolved"][0]["kind"], "missing_script")

    def test_mm9_bmodel_binding_uses_exact_source_model_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            maps_root = root / "maps"
            scripts_root = root / "scripts"
            events_root = root / "events"
            maps_root.mkdir()
            scripts_root.mkdir()
            raw_path = maps_root / "test.raw_objects.yml"
            raw_path.write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_raw_world_objects",
                        "source_dat": "TEST.dat",
                        "objects": [
                            {
                                "object_index": 3,
                                "name": "Door",
                                "properties": [
                                    prop("Name", '"DoorA"'),
                                    prop("MoveDir", "[1.0, 0.0, 0.0]", 1),
                                    prop("MoveDist", "64.0", 3),
                                    prop("Speed", "32.0", 3),
                                ],
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (maps_root / "test.mm9.yml").write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "outdoor_source_metadata",
                        "bmodels": [
                            {
                                "bmodel_index": 12,
                                "name": "DoorA",
                                "source_model_name": "DoorA",
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            event_data, _ = generate_mm9_events.build_events_for_map(raw_path, scripts_root, events_root)
            self.assertEqual(event_data["bindings"][0]["targets"][0]["target_kind"], "odm_bmodel")
            self.assertEqual(event_data["bindings"][0]["targets"][0]["bmodel_index"], 12)
            self.assertEqual(event_data["bindings"][0]["targets"][0]["confidence"], "exact_source_model_name")

    def test_unresolved_rotating_door_binding_keeps_nearest_world_model_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            maps_root = root / "maps"
            scripts_root = root / "scripts"
            events_root = root / "events"
            maps_root.mkdir()
            scripts_root.mkdir()
            raw_path = maps_root / "test.raw_objects.yml"
            raw_path.write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_raw_world_objects",
                        "source_dat": "TEST.dat",
                        "objects": [
                            {
                                "object_index": 5,
                                "name": "RotatingDoor",
                                "properties": [
                                    prop("Name", '"MissingDoor"'),
                                    prop("Pos", "[100.0, 0.0, 0.0]", 1),
                                    prop("RotationPoint", "[0.0, 0.0, 0.0]", 1),
                                    prop("RotationAngles", "[0.0, 90.0, 0.0]", 1),
                                ],
                            },
                            {
                                "object_index": 6,
                                "name": "RotatingDoor",
                                "properties": [
                                    prop("Name", '"NearDoor"'),
                                ],
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (maps_root / "test.dat_world.yml").write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_dat_world",
                        "world_models": [
                            {
                                "source_model_index": 3,
                                "source_name": "NearDoor",
                                "world_translation_lt": [8.0, 0.0, 0.0],
                                "roles": {"movable": True},
                            },
                            {
                                "source_model_index": 4,
                                "source_name": "FarDoor",
                                "world_translation_lt": [256.0, 0.0, 0.0],
                                "roles": {"movable": True},
                            },
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (maps_root / "test.mm9.yml").write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "outdoor_source_metadata",
                        "bmodels": [
                            {
                                "bmodel_index": 3,
                                "name": "NearDoor",
                                "source_model_name": "NearDoor",
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            event_data, _ = generate_mm9_events.build_events_for_map(raw_path, scripts_root, events_root)
            binding_target = event_data["bindings"][0]["targets"][0]
            self.assertEqual(binding_target["target_kind"], "unresolved")
            self.assertEqual(
                binding_target["nearest_movable_world_models_by_rotation_point"][0]["source_name"],
                "NearDoor",
            )
            self.assertEqual(
                binding_target["nearest_movable_world_models_by_rotation_point"][0]["claimed_by_exact_bindings"][0]
                ["source_object_index"],
                6,
            )
            self.assertEqual(
                event_data["unresolved"][0]["evidence"]["nearest_movable_world_models_by_position"][0]["source_name"],
                "NearDoor",
            )

    def test_rotating_door_can_share_exact_target_when_rotation_point_matches_claimed_object_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            maps_root = root / "maps"
            scripts_root = root / "scripts"
            events_root = root / "events"
            maps_root.mkdir()
            scripts_root.mkdir()
            raw_path = maps_root / "test.raw_objects.yml"
            raw_path.write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_raw_world_objects",
                        "source_dat": "TEST.dat",
                        "objects": [
                            {
                                "object_index": 5,
                                "name": "RotatingDoor",
                                "properties": [
                                    prop("Name", '"SharedDoorController"'),
                                    prop("Pos", "[96.0, 0.0, 0.0]", 1),
                                    prop("RotationPoint", "[8.0, 0.0, 0.0]", 1),
                                    prop("RotationAngles", "[0.0, 90.0, 0.0]", 1),
                                ],
                            },
                            {
                                "object_index": 6,
                                "name": "RotatingDoor",
                                "properties": [
                                    prop("Name", '"NearDoor"'),
                                    prop("Pos", "[8.0, 0.0, 0.0]", 1),
                                ],
                            },
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (maps_root / "test.dat_world.yml").write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_dat_world",
                        "world_models": [
                            {
                                "source_model_index": 3,
                                "source_name": "NearDoor",
                                "poly_count": 9,
                                "surface_count": 4,
                                "bounds_min_lt": [0.0, 0.0, 0.0],
                                "bounds_max_lt": [16.0, 8.0, 4.0],
                                "world_translation_lt": [8.0, 0.0, 0.0],
                                "roles": {"movable": True},
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (maps_root / "test.mm9.yml").write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "outdoor_source_metadata",
                        "bmodels": [
                            {
                                "bmodel_index": 3,
                                "name": "NearDoor",
                                "source_model_name": "NearDoor",
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            event_data, _ = generate_mm9_events.build_events_for_map(raw_path, scripts_root, events_root)
            shared_binding = event_data["bindings"][0]["targets"][0]
            self.assertEqual(shared_binding["target_kind"], "odm_bmodel")
            self.assertEqual(shared_binding["bmodel_index"], 3)
            self.assertEqual(shared_binding["source_model_name"], "NearDoor")
            self.assertEqual(shared_binding["source_polygon_group"]["source_model_index"], 3)
            self.assertEqual(shared_binding["source_polygon_group"]["source_poly_count"], 9)
            self.assertEqual(shared_binding["source_polygon_group"]["source_surface_count"], 4)
            self.assertTrue(shared_binding["source_polygon_group"]["roles"]["movable"])
            self.assertEqual(
                shared_binding["confidence"],
                "shared_rotation_point_exact_source_object_position",
            )
            self.assertEqual(shared_binding["shared_with_source_object_index"], 6)
            self.assertEqual(event_data["unresolved"], [])

    def test_check_idempotent_detects_stale_generated_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            maps_root = root / "maps"
            scripts_root = root / "scripts"
            events_root = root / "events"
            maps_root.mkdir()
            scripts_root.mkdir()
            raw_path = maps_root / "test.raw_objects.yml"
            raw_path.write_text(
                yaml.safe_dump(
                    {
                        "format_version": 1,
                        "kind": "mm9_raw_world_objects",
                        "source_dat": "TEST.dat",
                        "objects": [
                            {
                                "object_index": 0,
                                "name": "Terrain",
                                "properties": [
                                    prop("Name", '"Terrain0"'),
                                ],
                            }
                        ],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            generate_args = SimpleNamespace(
                maps_root=maps_root,
                scripts_root=scripts_root,
                events_root=events_root,
                only_map=["test"],
                validate_only=False,
                check_idempotent=False,
            )
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(generate_mm9_events.run_generation(generate_args), 0)

            check_args = SimpleNamespace(
                maps_root=maps_root,
                scripts_root=scripts_root,
                events_root=events_root,
                only_map=["test"],
                validate_only=False,
                check_idempotent=True,
            )
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(generate_mm9_events.run_generation(check_args), 0)

            (events_root / "test.lua").write_text("-- stale\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(generate_mm9_events.run_generation(check_args), 1)


if __name__ == "__main__":
    unittest.main()
