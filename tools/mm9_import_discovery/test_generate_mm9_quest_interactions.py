#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path

import yaml

from generate_mm9_quest_interactions import generate, key_deal_candidates, yaml_text


def rude_row(
    rude_id: int,
    node_id: int,
    choice_slot: int,
    next_node: int,
    fields: dict[int, int] | None = None,
) -> list[str]:
    columns = ["0"] * 30
    columns[0] = str(rude_id)
    columns[1] = str(node_id)
    columns[2] = str(choice_slot)
    columns[3] = "localized prompt is not classification input"
    columns[4] = "localized response is not classification input"
    columns[5] = str(next_node)
    for index, value in (fields or {}).items():
        columns[index] = str(value)
    return columns


def write_rude(path: Path, rows: list[list[str]]) -> None:
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(rows)
    path.write_text(stream.getvalue(), encoding="latin-1")


class Mm9QuestInteractionGeneratorTests(unittest.TestCase):
    def test_combines_nested_rude_paths_journal_transitions_bindings_and_scr_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rude_root = root / "rude"
            maps_root = root / "maps"
            raw_maps_root = root / "raw_maps"
            events_root = root / "events"
            scripts_root = root / "scripts"
            for path in (rude_root, maps_root, raw_maps_root, events_root, scripts_root):
                path.mkdir()

            write_rude(rude_root / "NPC997.rude", [
                rude_row(997, 997, 1, 997, {6: 10, 20: 20}),
                rude_row(997, 997, 2, 997, {6: 20, 20: 30}),
            ])
            write_rude(rude_root / "NPC1.rude", [
                rude_row(1, 1, 1, 5),
                rude_row(1, 5, 1, -1, {15: 10}),
                rude_row(1, 5, 2, -1, {6: 10, 15: 20}),
                rude_row(1, 5, 3, -4, {15: 30}),
            ])
            (maps_root / "sample.scene.yml").write_text(
                "initial_state:\n"
                "  actors:\n"
                "    - name: Quest NPC\n"
                "      mm9_rude_id: 1\n"
                "      mm9_source_object_index: 7\n",
                encoding="utf-8",
            )
            (raw_maps_root / "sample.raw_objects.yml").write_text(
                "objects:\n"
                "  - object_index: 7\n"
                "    properties:\n"
                "      - name: \"ScriptName\"\n"
                "        value_json: \"\\\"NPC1.scr\\\"\"\n"
                "      - name: \"ScriptParams\"\n"
                "        value_json: \"\\\"quest_mode\\\"\"\n",
                encoding="utf-8",
            )
            (events_root / "sample.events.yml").write_text(
                "format_version: 1\n"
                "dialogue_callbacks:\n"
                "- source_object_index: 7\n"
                "  script_name: NPC1.scr\n"
                "  callback_routine: onrude\n"
                "unresolved: []\n",
                encoding="utf-8",
            )
            (scripts_root / "NPC1.scr").write_text(
                ":Main\nOnRudeExit OnRude\n:OnRude\nGiveKey 30\n",
                encoding="latin-1",
            )
            overrides = root / "overrides.yml"
            overrides.write_text("format_version: 1\noverrides: []\n", encoding="utf-8")

            metadata, report = generate(
                rude_root,
                maps_root,
                raw_maps_root,
                events_root,
                scripts_root,
                overrides,
            )

            self.assertEqual(len(metadata["interactions"]), 2)
            offer, handoff = metadata["interactions"]
            self.assertEqual(offer["roles"], ["offer"])
            self.assertEqual(offer["conditions"]["reachable_path_rows"], [1])
            self.assertEqual(offer["conditions"]["available"]["activates_journal_entries"], [90001])
            self.assertEqual(offer["bindings"][0]["source_object_index"], 7)
            self.assertEqual(offer["bindings"][0]["script_name"], "NPC1.scr")
            self.assertEqual(handoff["roles"], ["offer", "handoff"])
            self.assertEqual(handoff["conditions"]["ready"]["active_journal_entries"], [90001])
            self.assertEqual(handoff["conditions"]["available"]["activates_journal_entries"], [90002])
            self.assertEqual(report["inventory"]["normal_dialogue_rows"], 4)
            self.assertEqual(report["inventory"]["generated_interactions"], 2)
            self.assertEqual(report["inventory"]["journal_keys_granted_only_by_literal_scr"], 1)
            self.assertEqual(report["inventory"]["unresolved_candidates"], 1)
            self.assertEqual(report["unresolved_candidates"][0]["relevant_operations"][0]["qbit"], 90030)
            self.assertNotIn("localized prompt", yaml_text(metadata))

    def test_game_scenes_in_json_bind_scripted_npcs_the_event_inventories_lack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("rude", "maps", "raw_maps", "events", "scripts"):
                (root / name).mkdir()
            write_rude(root / "rude/NPC997.rude", [rude_row(997, 997, 1, 997, {6: 30})])
            write_rude(root / "rude/NPC1.rude", [rude_row(1, 1, 1, -1)])
            # The converters write scenes as JSON; the editor import's events.yml has no callback for this NPC.
            (root / "maps/town.scene.yml").write_text(
                '{"initial_state": {"actors": [{"name": "Guard"}, '
                '{"name": "Quest NPC", "mm9_source_object_index": 9, "mm9_rude_id": 1}]}}\n',
                encoding="utf-8",
            )
            (root / "raw_maps/town.raw_objects.yml").write_text(
                "objects:\n"
                "  - object_index: 9\n"
                "    properties:\n"
                "      - name: \"ScriptName\"\n"
                "        value_json: \"\\\"NPC1.scr\\\"\"\n",
                encoding="utf-8",
            )
            (root / "scripts/NPC1.scr").write_text(":Main\nOnRudeExit OnRude\n:OnRude\nGiveKey 30\n",
                                                   encoding="latin-1")
            overrides = root / "overrides.yml"
            overrides.write_text("format_version: 1\noverrides: []\n", encoding="utf-8")

            _, report = generate(root / "rude", root / "maps", root / "raw_maps", root / "events", root / "scripts",
                                 overrides)

        self.assertEqual(report["inventory"]["imported_dialogue_actor_bindings"], 1)
        self.assertEqual(report["binding_coverage"][0]["actor_index"], 1)
        self.assertEqual(report["binding_coverage"][0]["script_name"], "NPC1.scr")
        self.assertEqual([candidate["id"] for candidate in report["unresolved_candidates"]], ["mm9.scr.town.9"])
        self.assertEqual(report["unresolved_candidates"][0]["callback_routine"], "onrude")

    def test_narrow_override_can_explicitly_exclude_a_generated_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("rude", "maps", "raw_maps", "events", "scripts"):
                (root / name).mkdir()
            write_rude(root / "rude/NPC997.rude", [rude_row(997, 997, 1, 997, {6: 10})])
            write_rude(root / "rude/NPC1.rude", [rude_row(1, 1, 1, -1, {15: 10})])
            overrides = root / "overrides.yml"
            overrides.write_text(
                "format_version: 1\n"
                "overrides:\n"
                "  - interaction_id: mm9.rude.1.row.1\n"
                "    classification: excluded\n"
                "    reason: Test fixture proves this source row is not an actor quest interaction.\n",
                encoding="utf-8",
            )

            metadata, report = generate(
                root / "rude",
                root / "maps",
                root / "raw_maps",
                root / "events",
                root / "scripts",
                overrides,
            )

            self.assertEqual(metadata["interactions"], [])
            self.assertEqual(report["inventory"]["explicit_exclusions"], 1)
            self.assertEqual(report["explicit_exclusions"][0]["id"], "mm9.rude.1.row.1")

    def test_key_deal_candidates_keep_keys_tested_outside_their_own_dialogue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rude, scripts, lua = root / "rude", root / "scripts", root / "events"
            for folder in (rude, scripts, lua / "maps"):
                folder.mkdir(parents=True)
            # NPC1 grants key 500 (tested by NPC2's dialogue) and its script grants 700 (a #number constant tested by
            # another script); NPC3 grants 600, tested only by its own root row (a talked-once flag); 800 is a
            # journal key; NPC2's 900 is tested by map Lua.
            write_rude(rude / "NPC1.rude", [rude_row(1, 1, 1, -1, {15: 500, 16: 800})])
            write_rude(rude / "NPC2.rude", [rude_row(2, 2, 1, -1, {6: 500, 15: 900})])
            write_rude(rude / "NPC3.rude", [rude_row(3, 3, 1, -1, {15: 600, 20: 600})])
            (scripts / "NPC1.scr").write_text("givekey 700\n", encoding="latin-1")
            (scripts / "Other.scr").write_text("#number KEY_DEAL = 700\nHasKey KEY_DEAL, g_ntemp\n", encoding="latin-1")
            (lua / "maps" / "town.lua").write_text("if MM9.hasKey(900) == 1 then end\n", encoding="utf-8")
            binding = {"map_id": "town", "source_object_index": 5}
            review = key_deal_candidates(rude, scripts, lua, root, {90800}, {1: [binding], 2: [binding], 3: [binding]},
                                         {2}, set())

        candidates = {candidate["rude_id"]: candidate for candidate in review["candidates"]}
        self.assertEqual(sorted(candidates), [1, 2])
        keys = {entry["key"]: entry for entry in candidates[1]["keys"]}
        self.assertEqual(sorted(keys), [500, 700])
        self.assertEqual(keys[500]["tested_by_dialogues"], [2])
        self.assertEqual(keys[700]["tested_by_scripts"], ["other.scr"])
        self.assertEqual(candidates[2]["keys"][0]["tested_by_lua"], ["maps/town.lua"])
        self.assertTrue(candidates[2]["journal_markers"])
        self.assertEqual(review["counts"]["self_or_untested_only"], 1)

    def test_checked_in_inventory_matches_the_source_audit_baseline(self) -> None:
        source_root = Path(__file__).resolve().parents[2]
        report_path = source_root / "assets_dev/worlds/mm9/state/quest_interaction_coverage.yml"
        report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
        inventory = report["inventory"]
        self.assertEqual(inventory["normal_rude_graphs"], 436)
        self.assertEqual(inventory["normal_dialogue_rows"], 4215)
        self.assertEqual(inventory["reachable_journal_grant_rude_ids"], 59)
        self.assertEqual(inventory["root_journal_grant_rude_ids"], 28)
        self.assertEqual(inventory["journal_condition_raw_keys"], 208)
        self.assertEqual(inventory["journal_keys_granted_by_ordinary_rude_rows"], 144)
        self.assertEqual(inventory["journal_keys_granted_only_by_literal_scr"], 57)
        self.assertEqual(inventory["generated_interactions"], 199)
        self.assertEqual(inventory["explicit_exclusions"], 42)
        self.assertEqual(inventory["unresolved_candidates"], 0)
        self.assertEqual(inventory["validated_non_qbit_dependencies"], {"carried_gold": 3})
        metadata_path = source_root / "assets_dev/worlds/mm9/state/quest_interactions.yml"
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        self.assertTrue(all(interaction["bindings"] for interaction in metadata["interactions"]))
        self.assertTrue(all(
            binding["map_id"] and "source_object_index" in binding
            for interaction in metadata["interactions"]
            for binding in interaction["bindings"]
        ))


if __name__ == "__main__":
    unittest.main()
