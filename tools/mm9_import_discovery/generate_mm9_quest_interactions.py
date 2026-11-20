#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mm9_scr_to_lua import parse_scr

YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


MM9_QBIT_BASE = 90000
KEY_COLUMNS = {
    "required": (6, 8, 10, 12, 14),
    "granted": (15, 16, 17, 18, 19),
    "forbidden": (20, 21, 22, 23, 24),
    "removed": (25, 26, 27, 28, 29),
}


class StableDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


@dataclass(frozen=True)
class RudeRow:
    row_index: int
    rude_id: int
    node_id: int
    choice_slot: int
    next_node: int
    source_line: int
    required: tuple[int, ...]
    granted: tuple[int, ...]
    forbidden: tuple[int, ...]
    removed: tuple[int, ...]


def qbit(raw_key: str, source: str) -> int | None:
    try:
        value = int(raw_key)
    except ValueError as exception:
        raise ValueError(f"{source}: invalid quest key {raw_key!r}") from exception
    if value == 0:
        return None
    if value < 1 or value > 9999:
        raise ValueError(f"{source}: quest key {value} is outside 1-9999")
    return MM9_QBIT_BASE + value


def key_group(columns: list[str], indices: tuple[int, ...], source: str) -> tuple[int, ...]:
    result: list[int] = []
    for index in indices:
        value = qbit(columns[index], source)
        if value is not None and value not in result:
            result.append(value)
    return tuple(result)


def load_rude_file(path: Path) -> list[RudeRow]:
    with path.open(newline="", encoding="latin-1") as source_file:
        records = list(csv.reader(source_file))
    rows: list[RudeRow] = []
    for row_index, columns in enumerate(records):
        source_line = row_index + 1
        source = f"{path.as_posix()}:{source_line}"
        if len(columns) < 30:
            raise ValueError(f"{source}: expected at least 30 columns")
        try:
            rude_id = int(columns[0])
            node_id = int(columns[1])
            choice_slot = int(columns[2])
            next_node = int(columns[5])
        except ValueError as exception:
            raise ValueError(f"{source}: invalid row identity or action") from exception
        rows.append(RudeRow(
            row_index=row_index,
            rude_id=rude_id,
            node_id=node_id,
            choice_slot=choice_slot,
            next_node=next_node,
            source_line=source_line,
            required=key_group(columns, KEY_COLUMNS["required"], source),
            granted=key_group(columns, KEY_COLUMNS["granted"], source) if next_node >= -1 else (),
            forbidden=key_group(columns, KEY_COLUMNS["forbidden"], source),
            removed=key_group(columns, KEY_COLUMNS["removed"], source) if next_node >= -1 else (),
        ))
    return rows


def load_journal_stages(path: Path) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    for row in load_rude_file(path):
        if row.rude_id != 997 or row.node_id != 997:
            raise ValueError(f"{path.as_posix()}:{row.source_line}: unexpected journal RUDE identity")
        stages.append({
            "entry_qbit": MM9_QBIT_BASE + row.choice_slot,
            "required_qbits": list(row.required),
            "forbidden_qbits": list(row.forbidden),
            "provenance": {
                "source": "dialogue/rude/NPC997.rude",
                "source_line": row.source_line,
                "entry_id": row.choice_slot,
            },
        })
    return stages


def structural_paths(rude_id: int, rows: list[RudeRow]) -> dict[int, list[int]]:
    rows_by_node: dict[int, list[RudeRow]] = {}
    for row in rows:
        rows_by_node.setdefault(row.node_id, []).append(row)
    paths: dict[int, list[int]] = {rude_id: []}
    pending: deque[int] = deque([rude_id])
    while pending:
        node_id = pending.popleft()
        for row in rows_by_node.get(node_id, []):
            if row.next_node < 0 or row.next_node in paths:
                continue
            paths[row.next_node] = paths[node_id] + [row.source_line]
            pending.append(row.next_node)
    return paths


def remove_suffix(value: str, suffix: str) -> str:
    return value[:-len(suffix)] if suffix and value.endswith(suffix) else value


def scene_actors(path: Path) -> list[dict[str, Any]]:
    """The placed actors of a scene, in runtime order: the converters write JSON, older scenes are YAML."""
    text = path.read_text(encoding="utf-8")
    scene = json.loads(text) if text.lstrip().startswith("{") else yaml.load(text, Loader=YAML_LOADER)
    return list(((scene or {}).get("initial_state") or {}).get("actors") or [])


def scene_actor_bindings(path: Path) -> list[dict[str, int]]:
    bindings: list[dict[str, int]] = []
    for actor_index, actor in enumerate(scene_actors(path)):
        rude_id = int(actor.get("mm9_rude_id") or 0)
        if rude_id <= 0:
            continue
        source_object_index = actor.get("mm9_source_object_index")
        if source_object_index is None:
            raise ValueError(f"{path.as_posix()}: actor {actor_index} has RUDE {rude_id} without source identity")
        bindings.append({
            "actor_index": actor_index,
            "rude_id": rude_id,
            "source_object_index": int(source_object_index),
        })
    return bindings


def raw_script_properties(path: Path, source_indices: set[int]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    current_index: int | None = None
    current_property = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- object_index:"):
            current_index = int(stripped.split(":", 1)[1].strip())
            current_property = ""
        elif current_index in source_indices and stripped in {'- name: "ScriptName"', '- name: "ScriptParams"'}:
            current_property = stripped.split('"', 2)[1]
        elif current_index in source_indices and current_property and stripped.startswith("value_json:"):
            yaml_value = yaml.safe_load(stripped.split(":", 1)[1].strip())
            try:
                result.setdefault(current_index, {})[current_property] = json.loads(yaml_value)
            except (json.JSONDecodeError, TypeError):
                result.setdefault(current_index, {})[current_property] = yaml_value
            current_property = ""
    return result


def load_bindings(maps_root: Path, raw_maps_root: Path) -> tuple[dict[int, list[dict[str, Any]]], list[dict[str, Any]]]:
    by_rude_id: dict[int, list[dict[str, Any]]] = {}
    all_bindings: list[dict[str, Any]] = []
    for scene_path in sorted(maps_root.glob("*.scene.yml")):
        if scene_path.name.endswith("_authored.scene.yml"):
            continue
        scene_bindings = scene_actor_bindings(scene_path)
        map_id = remove_suffix(scene_path.name, ".scene.yml")
        raw_path = raw_maps_root / f"{map_id}.raw_objects.yml"
        source_indices = {binding["source_object_index"] for binding in scene_bindings}
        raw_properties = raw_script_properties(raw_path, source_indices) if raw_path.is_file() else {}
        for actor in scene_bindings:
            rude_id = actor["rude_id"]
            source_object_index = actor["source_object_index"]
            actor_index = actor["actor_index"]
            properties = raw_properties.get(source_object_index, {})
            binding = {
                "map_id": map_id,
                "actor_index": actor_index,
                "source_object_index": source_object_index,
                "script_name": properties.get("ScriptName", ""),
                "script_params": properties.get("ScriptParams", ""),
                "provenance": {
                    "scene": f"maps/{scene_path.name}",
                    "raw_object": f"maps/{raw_path.name}" if raw_path.is_file() else "",
                },
            }
            by_rude_id.setdefault(rude_id, []).append(binding)
            all_bindings.append({"rude_id": rude_id, **binding})
    for bindings in by_rude_id.values():
        bindings.sort(key=lambda value: (value["map_id"], value["source_object_index"], value["actor_index"]))
    all_bindings.sort(key=lambda value: (value["map_id"], value["source_object_index"], value["actor_index"]))
    return by_rude_id, all_bindings


def stage_transitions(row: RudeRow, stages: list[dict[str, Any]]) -> tuple[list[int], list[int]]:
    starts: list[int] = []
    completes: list[int] = []
    granted = set(row.granted)
    removed = set(row.removed)
    for stage in stages:
        required = set(stage["required_qbits"])
        forbidden = set(stage["forbidden_qbits"])
        if granted.intersection(required) or removed.intersection(forbidden):
            starts.append(stage["entry_qbit"])
        if granted.intersection(forbidden) or removed.intersection(required):
            completes.append(stage["entry_qbit"])
    return starts, completes


def load_overrides(path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.is_file():
        return {}, [], []
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    overrides = document.get("overrides", [])
    result: dict[str, dict[str, Any]] = {}
    for override in overrides:
        interaction_id = override.get("interaction_id")
        reason = override.get("reason")
        if not isinstance(interaction_id, str) or not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{path.as_posix()}: every override needs interaction_id and reason")
        if interaction_id in result:
            raise ValueError(f"{path.as_posix()}: duplicate override {interaction_id}")
        result[interaction_id] = override
    scr_interactions = document.get("scr_interactions", [])
    if not isinstance(scr_interactions, list):
        raise ValueError(f"{path.as_posix()}: scr_interactions must be a sequence")
    seen_scr_ids: set[str] = set()
    for interaction in scr_interactions:
        interaction_id = interaction.get("interaction_id")
        source_candidate_id = interaction.get("source_candidate_id")
        reason = interaction.get("reason")
        if (not isinstance(interaction_id, str)
                or not isinstance(source_candidate_id, str)
                or not isinstance(reason, str)
                or not reason.strip()):
            raise ValueError(
                f"{path.as_posix()}: every SCR interaction needs interaction_id, source_candidate_id, and reason")
        if interaction_id in seen_scr_ids:
            raise ValueError(f"{path.as_posix()}: duplicate SCR interaction {interaction_id}")
        seen_scr_ids.add(interaction_id)
    key_interactions = document.get("key_interactions", [])
    if not isinstance(key_interactions, list):
        raise ValueError(f"{path.as_posix()}: key_interactions must be a sequence")
    for interaction in key_interactions:
        states = interaction.get("states")
        if (not isinstance(interaction.get("interaction_id"), str)
                or not isinstance(interaction.get("rude_id"), int)
                or not isinstance(interaction.get("map_id"), str)
                or not isinstance(interaction.get("source_object_index"), int)
                or not isinstance(states, dict) or not states
                or set(states).difference({"available", "in_progress", "ready"})
                or not isinstance(interaction.get("reason"), str) or not interaction["reason"].strip()):
            raise ValueError(f"{path.as_posix()}: every key interaction needs interaction_id, rude_id, map_id, "
                             "source_object_index, states (available, in_progress, ready) and reason")
        for state in states.values():
            if (not isinstance(state, dict) or set(state) != {"required_qbits", "forbidden_qbits"}
                    or not all(isinstance(qbit, int) and qbit > 0 for key in state for qbit in state[key])):
                raise ValueError(f"{path.as_posix()}: {interaction['interaction_id']}: a state is "
                                 "{required_qbits, forbidden_qbits} of QBit ids")
    return result, scr_interactions, key_interactions


def load_key_deal_reviews(path: Path) -> dict[int, str]:
    """The overrides' key_deal_reviews: candidates reviewed and left without a marker, with the reason."""
    if not path.is_file():
        return {}
    reviews = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("key_deal_reviews", [])
    result: dict[int, str] = {}
    for review in reviews:
        if (not isinstance(review.get("rude_id"), int) or not isinstance(review.get("reason"), str)
                or not review["reason"].strip() or review["rude_id"] in result):
            raise ValueError(f"{path.as_posix()}: every key deal review needs a unique rude_id and a reason")
        result[review["rude_id"]] = review["reason"].strip()
    return result


def key_interaction_record(authored: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    """A journal-less MM9 quest kept in quest keys only (a deal with no journal entry): its marker states are the
    authored key conditions (Mm9QuestMarkers.cpp source_kind keys)."""
    states = authored["states"]
    return {
        "id": authored["interaction_id"],
        "source_kind": "keys",
        "rude_id": authored["rude_id"],
        "bindings": [{key: value for key, value in binding.items() if key != "rude_id"}],
        "journal_entries": [],
        "roles": (["offer"] if "available" in states else []) + (["handoff"] if "ready" in states else []),
        "conditions": {"keys": states},
        "effects": {"granted_qbits": [], "removed_qbits": []},
        "non_qbit_dependencies": [],
        "justification": "authored_key_states_for_journal_less_quest",
        "classification": "authored_override",
        "override_reason": authored["reason"],
        "provenance": {"source": f"dialogue/rude/NPC{authored['rude_id']}.rude"},
    }


def interaction_record(
    row: RudeRow,
    path_rows: list[int],
    starts: list[int],
    completes: list[int],
    bindings: list[dict[str, Any]],
    override: dict[str, Any] | None,
) -> dict[str, Any] | None:
    interaction_id = f"mm9.rude.{row.rude_id}.row.{row.source_line}"
    if override and override.get("classification") == "excluded":
        return None
    roles = (["offer"] if starts else []) + (["handoff"] if completes else [])
    if override and isinstance(override.get("roles"), list):
        roles = override["roles"]
    associated = sorted(set(starts + completes))
    record: dict[str, Any] = {
        "id": interaction_id,
        "rude_id": row.rude_id,
        "bindings": bindings,
        "journal_entries": associated,
        "roles": roles,
        "conditions": {
            "reachable_path_rows": path_rows,
            "row_required_qbits": list(row.required),
            "row_forbidden_qbits": list(row.forbidden),
            "available": {"activates_journal_entries": starts},
            "in_progress": {"active_journal_entries": completes, "row_not_yet_reachable": True},
            "ready": {"active_journal_entries": completes, "row_reachable": True},
        },
        "effects": {
            "granted_qbits": list(row.granted),
            "removed_qbits": list(row.removed),
        },
        "non_qbit_dependencies": [],
        "justification": "journal_condition_transition_from_reachable_ordinary_rude_row",
        "classification": "authored_override" if override else "generated",
        "provenance": {
            "source": f"dialogue/rude/NPC{row.rude_id}.rude",
            "source_line": row.source_line,
            "row_index": row.row_index,
            "node_id": row.node_id,
            "choice_slot": row.choice_slot,
        },
    }
    if override:
        record["override_reason"] = override["reason"]
        if isinstance(override.get("non_qbit_dependencies"), list):
            record["non_qbit_dependencies"] = override["non_qbit_dependencies"]
    return record


def callback_routine_lines(script_text: str, script_name: str, callback_routine: str) -> set[int]:
    program = parse_scr(script_text, script_name)
    pending = [callback_routine.lower()]
    visited: set[str] = set()
    source_lines: set[int] = set()
    while pending:
        routine = pending.pop()
        if routine in visited:
            continue
        visited.add(routine)
        for line in program.routines.get(routine, []):
            source_lines.add(line.number)
            match = re.match(r"^gosub\s+([A-Za-z_][A-Za-z0-9_]*)", line.code, re.IGNORECASE)
            if match:
                pending.append(match.group(1).lower())
    return source_lines


def find_script(scripts_root: Path, script_name: str) -> Path:
    script_path = scripts_root / script_name
    if script_path.is_file():
        return script_path
    return next(
        (candidate for candidate in scripts_root.glob("*.scr") if candidate.name.lower() == script_name.lower()),
        script_path,
    )


# The routines MM9 runs when a dialogue closes, in the order a script is searched for one.
RUDE_EXIT_ROUTINES = ("onrude", "onrudeexit", "onexit")


def dialogue_callbacks(
    events_root: Path,
    scripts_root: Path,
    bindings: list[dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    """(map, inventory, callback) for every dialogue-closing script: the editor import's event inventories, plus the
    scripted NPCs of the game's scenes that those inventories lack (their script's first RUDE-exit routine)."""
    callbacks: list[tuple[str, str, dict[str, Any]]] = []
    covered: set[tuple[str, int]] = set()
    for path in sorted(events_root.glob("*.events.yml")):
        text = path.read_text(encoding="utf-8")
        separator = "\ndialogue_callbacks:\n"
        if separator not in text:
            continue
        map_id = remove_suffix(path.stem, ".events")
        callback_text = text.split(separator, 1)[1].split("\nunresolved:", 1)[0]
        callback_document = yaml.safe_load("dialogue_callbacks:\n" + callback_text) or {}
        for callback in callback_document.get("dialogue_callbacks", []):
            callbacks.append((map_id, f"maps/{path.name}", callback))
            covered.add((map_id, int(callback.get("source_object_index"))))
    for binding in bindings:
        script_name = str(binding.get("script_name", ""))
        identity = (binding["map_id"], binding["source_object_index"])
        if not script_name or identity in covered:
            continue
        script_path = find_script(scripts_root, script_name)
        if not script_path.is_file():
            continue
        routines = parse_scr(script_path.read_text(encoding="latin-1"), script_path.name).routines
        routine = next((name for name in RUDE_EXIT_ROUTINES if name in routines), "")
        if routine:
            covered.add(identity)
            callbacks.append((binding["map_id"], binding["provenance"]["scene"], {
                "source_object_index": binding["source_object_index"],
                "script_name": script_name,
                "callback_routine": routine,
            }))
    return callbacks


def scr_candidates(
    events_root: Path,
    scripts_root: Path,
    journal_keys: set[int],
    bindings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for map_id, inventory, callback in dialogue_callbacks(events_root, scripts_root, bindings):
        script_name = str(callback.get("script_name", ""))
        relevant_operations: list[dict[str, Any]] = []
        script_path = find_script(scripts_root, script_name)
        script_text = script_path.read_text(encoding="latin-1") if script_path.is_file() else ""
        reachable_lines = callback_routine_lines(
            script_text,
            script_path.name if script_path.is_file() else script_name,
            str(callback.get("callback_routine", "")),
        )
        unreachable_operations: list[dict[str, Any]] = []
        for source_line, source_text in enumerate(script_text.splitlines(), start=1):
            match = re.match(
                r"^\s*(givekey|takekey)\s*,?\s*([0-9]+)(?:\s|,|;|$)",
                source_text,
                re.IGNORECASE,
            )
            if not match:
                continue
            operation_qbit = MM9_QBIT_BASE + int(match.group(2))
            if operation_qbit in journal_keys:
                operation = {
                    "command": match.group(1).lower(),
                    "qbit": operation_qbit,
                    "source_line": source_line,
                }
                if source_line in reachable_lines:
                    relevant_operations.append(operation)
                else:
                    unreachable_operations.append(operation)
        candidate_id = f"mm9.scr.{map_id}.{callback.get('source_object_index')}"
        if relevant_operations:
            candidates.append({
                "id": candidate_id,
                "map_id": map_id,
                "source_object_index": callback.get("source_object_index"),
                "script_name": script_name,
                "callback_routine": callback.get("callback_routine", ""),
                "relevant_operations": relevant_operations,
                "status": "unresolved",
                "reason": "SCR control-flow predicates are not yet represented as pure marker metadata",
                "provenance": {
                    "event_inventory": inventory,
                    "source": script_path.as_posix() if script_path.is_file() else script_name,
                },
            })
        if unreachable_operations:
            exclusions.append({
                "id": candidate_id + ".unreachable_operations",
                "reason": "journal-key operations are outside the registered RUDE-exit callback call graph",
                "relevant_operations": unreachable_operations,
                "provenance": {
                    "event_inventory": inventory,
                    "source": script_path.as_posix() if script_path.is_file() else script_name,
                },
            })
    return candidates, exclusions


def literal_scr_journal_keys(scripts_root: Path, journal_keys: set[int]) -> set[int]:
    result: set[int] = set()
    for path in sorted(scripts_root.glob("*.scr"), key=lambda value: value.name.lower()):
        for source_text in path.read_text(encoding="latin-1").splitlines():
            match = re.match(r"^\s*givekey\s*,?\s*([0-9]+)(?:\s|,|;|$)", source_text, re.IGNORECASE)
            if not match:
                continue
            operation_qbit = MM9_QBIT_BASE + int(match.group(1))
            if operation_qbit in journal_keys:
                result.add(operation_qbit)
    return result


# --- Key-only deals (the review list of journal-less quests: mm9_quest_interaction_overrides.yml key_interactions) ---

SCR_HAS_KEY = re.compile(r"^\s*haskey\s*,?\s*([A-Za-z_][A-Za-z0-9_]*|[0-9]+)", re.IGNORECASE)
SCR_GIVE_KEY = re.compile(r"^\s*givekey\s*,?\s*([A-Za-z_][A-Za-z0-9_]*|[0-9]+)", re.IGNORECASE)
SCR_NUMBER = re.compile(r"^\s*#number\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+)", re.IGNORECASE)
LUA_HAS_KEY = re.compile(r"MM9\.hasKey\(\s*([0-9]+)\s*\)")
LUA_HAS_QBIT = re.compile(r"evt\.HasQuestBit\(\s*(9[0-9]{4})\s*\)")


def scr_key_uses(scripts_root: Path) -> tuple[dict[int, set[str]], dict[str, set[int]]]:
    """Every MM9 script's literal (or #number-constant) HasKey keys, by QBit, and each script's GiveKey keys."""
    paths = sorted([*scripts_root.glob("*.scr"), *scripts_root.glob("*.inc")], key=lambda value: value.name.lower())
    texts = {path: path.read_text(encoding="latin-1").splitlines() for path in paths}
    constants: dict[str, int] = {}
    for lines in texts.values():
        for line in lines:
            match = SCR_NUMBER.match(line)
            if match:
                constants.setdefault(match.group(1).lower(), int(match.group(2)))

    def key_of(token: str) -> int | None:
        value = int(token) if token.isdigit() else constants.get(token.lower())
        return MM9_QBIT_BASE + value if value is not None and 1 <= value <= 9999 else None

    tested: dict[int, set[str]] = {}
    given: dict[str, set[int]] = {}
    for path, lines in texts.items():
        for line in lines:
            for pattern, sink in ((SCR_HAS_KEY, "tested"), (SCR_GIVE_KEY, "given")):
                match = pattern.match(line)
                key = key_of(match.group(1)) if match else None
                if key is None:
                    continue
                if sink == "tested":
                    tested.setdefault(key, set()).add(path.name.lower())
                else:
                    given.setdefault(path.name.lower(), set()).add(key)
    return tested, given


def lua_key_tests(lua_root: Path) -> dict[int, set[str]]:
    """The map and common Lua's literal MM9.hasKey / evt.HasQuestBit tests, by QBit."""
    tested: dict[int, set[str]] = {}
    for path in sorted(lua_root.rglob("*.lua")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in LUA_HAS_KEY.finditer(text):
            value = int(match.group(1))
            if 1 <= value <= 9999:
                tested.setdefault(MM9_QBIT_BASE + value, set()).add(path.relative_to(lua_root).as_posix())
        for match in LUA_HAS_QBIT.finditer(text):
            tested.setdefault(int(match.group(1)), set()).add(path.relative_to(lua_root).as_posix())
    return tested


def scene_actor_names(maps_root: Path) -> dict[tuple[str, int], str]:
    """(map, source object index) to the placed NPC's name, read from the game's scenes."""
    names: dict[tuple[str, int], str] = {}
    for path in sorted(maps_root.glob("*.scene.yml")):
        if path.name.endswith("_authored.scene.yml"):
            continue
        map_id = remove_suffix(path.name, ".scene.yml")
        for actor in scene_actors(path):
            if actor.get("name") and actor.get("mm9_source_object_index") is not None:
                names[(map_id, int(actor["mm9_source_object_index"]))] = str(actor["name"])
    return names


def rude_texts(path: Path) -> list[tuple[str, str]]:
    with path.open(newline="", encoding="latin-1") as source_file:
        return [(columns[3], columns[4]) for columns in csv.reader(source_file)]


def key_deal_candidates(
    rude_root: Path,
    scripts_root: Path,
    lua_root: Path,
    maps_root: Path,
    journal_keys: set[int],
    bindings_by_rude_id: dict[int, list[dict[str, Any]]],
    marked_rude_ids: set[int],
    authored_key_rude_ids: set[int],
    reviews: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Dialogues on placed NPCs that grant quest keys the journal does not use, with where each key is tested. A key
    tested outside its own dialogue and NPC script (another dialogue, map Lua, another MM9 script) is a deal's step; one
    tested only by its own dialogue is mostly a talked-once flag. Literal keys only: computed keys are not seen."""
    graphs: dict[int, tuple[Path, list[RudeRow]]] = {}
    for path in sorted(rude_root.glob("NPC[0-9]*.rude"), key=lambda value: value.name.lower()):
        if path.name in {"NPC997.rude", "NPC998.rude", "NPC999.rude"}:
            continue
        rows = load_rude_file(path)
        if rows:
            graphs[rows[0].rude_id] = (path, rows)
    scr_tested, scr_given = scr_key_uses(scripts_root)
    lua_tested = lua_key_tests(lua_root)
    names = scene_actor_names(maps_root)
    rude_tested: dict[int, set[int]] = {}
    for rude_id, (_, rows) in graphs.items():
        for row in rows:
            for key in row.required + row.forbidden:
                rude_tested.setdefault(key, set()).add(rude_id)

    candidates, self_only, counts = [], 0, {"placed_dialogues_granting_keys": 0}
    for rude_id, (path, rows) in sorted(graphs.items()):
        bindings = bindings_by_rude_id.get(rude_id, [])
        own_script = f"npc{rude_id}.scr"
        grants: dict[int, list[str]] = {}
        texts = None
        for row in rows:
            for key in row.granted:
                if key not in journal_keys:
                    texts = texts or rude_texts(path)
                    prompt = texts[row.row_index][0].strip()
                    grants.setdefault(key, []).append(f"row {row.source_line}: \"{prompt[:60]}\"")
        for key in sorted(scr_given.get(own_script, ())):
            if key not in journal_keys:
                grants.setdefault(key, []).append(f"{own_script}")
        if not grants or not bindings:
            continue
        counts["placed_dialogues_granting_keys"] += 1
        keys = []
        for key, sources in sorted(grants.items()):
            other_rude = sorted(rude_tested.get(key, set()) - {rude_id})
            scripts = sorted(scr_tested.get(key, set()) - {own_script})
            lua = sorted(lua_tested.get(key, set()))
            cross = bool(other_rude or scripts or lua)
            own = rude_id in rude_tested.get(key, set()) or own_script in scr_tested.get(key, set())
            keys.append({"key": key - MM9_QBIT_BASE, "granted_by": sources, "tested_by_dialogues": other_rude,
                         "tested_by_lua": lua, "tested_by_scripts": scripts, "tested_by_own_dialogue": own,
                         "scope": "cross" if cross else "self" if own else "untested"})
        if not any(entry["scope"] == "cross" for entry in keys):
            self_only += 1
            continue
        candidates.append({
            "rude_id": rude_id,
            "npcs": [{"map_id": b["map_id"], "source_object_index": b["source_object_index"],
                      "name": names.get((b["map_id"], b["source_object_index"]), "")} for b in bindings],
            "journal_markers": rude_id in marked_rude_ids,
            "authored_key_interaction": rude_id in authored_key_rude_ids,
            "review": (reviews or {}).get(rude_id, ""),
            "keys": keys,
        })
    counts.update(candidates=len(candidates), self_or_untested_only=self_only,
                  without_any_marker=sum(1 for c in candidates if not c["journal_markers"]
                                         and not c["authored_key_interaction"] and not c["review"]))
    return {"counts": counts, "candidates": candidates}


def key_deal_review_text(review: dict[str, Any]) -> str:
    counts = review["counts"]
    lines = [
        "# MM9 key-only deal candidates",
        "",
        "Generated by `tools/mm9_import_discovery/generate_mm9_quest_interactions.py` (`--key-deal-review`); do not edit.",
        "Each entry is a dialogue on a placed NPC that grants MM9 quest keys the journal does not use, where some key is",
        "tested outside that dialogue and its NPC script: a step of a deal that may deserve a quest marker. Review each",
        "against its dialogue and scripts; author real deals as `key_interactions` in",
        "`tools/mm9_import_discovery/mm9_quest_interaction_overrides.yml` (devdocs/mm9/MM9_NPC_QUEST_MARKERS_GOAL.md).",
        "Literal keys only: keys a script computes are not seen.",
        "",
        f"- Placed dialogues granting non-journal keys: {counts['placed_dialogues_granting_keys']}",
        f"- Candidates (a key tested elsewhere): {counts['candidates']}, of which not reviewed and with no marker: "
        f"{counts['without_any_marker']}",
        f"- Left out (keys tested only by their own dialogue, or never): {counts['self_or_untested_only']}",
        "",
        "Status: **none** (no marker, not reviewed), **journal** (journal markers on other rows), **authored** (a key",
        "interaction), **reviewed** (no marker on purpose: the overrides' `key_deal_reviews`).",
        "",
    ]
    by_map: dict[str, list[dict[str, Any]]] = {}
    for candidate in review["candidates"]:
        by_map.setdefault(candidate["npcs"][0]["map_id"], []).append(candidate)
    for map_id in sorted(by_map):
        lines += [f"## {map_id}", ""]
        for candidate in by_map[map_id]:
            npcs = ", ".join(
                f"{npc['name'] or '?'} ({npc['map_id']} #{npc['source_object_index']})" for npc in candidate["npcs"])
            status = ("authored" if candidate["authored_key_interaction"]
                      else f"reviewed** ({candidate['review']})" if candidate["review"]
                      else "journal" if candidate["journal_markers"] else "none")
            status = status if status.startswith("reviewed") else status + "**"
            lines += [f"### Dialogue {candidate['rude_id']}: {npcs}", "", f"Status: **{status}", "",
                      "| Key | Granted by | Tested elsewhere | Own dialogue |", "| --- | --- | --- | --- |"]
            for key in candidate["keys"]:
                elsewhere = ([f"NPC{value}.rude" for value in key["tested_by_dialogues"]] + key["tested_by_lua"]
                             + key["tested_by_scripts"])
                lines.append(f"| {key['key']} | {'; '.join(key['granted_by'])} | "
                             f"{', '.join(elsewhere) if elsewhere else '-'} | "
                             f"{'yes' if key['tested_by_own_dialogue'] else 'no'} |")
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def scr_interaction_record(
    authored: dict[str, Any],
    candidate: dict[str, Any],
    binding: dict[str, Any],
    stages: list[dict[str, Any]],
) -> dict[str, Any]:
    granted_qbits = authored.get("granted_qbits", [])
    removed_qbits = authored.get("removed_qbits", [])
    if not isinstance(granted_qbits, list) or not isinstance(removed_qbits, list):
        raise ValueError(f"{authored.get('interaction_id')}: SCR effects must be QBit sequences")
    source_qbits = {
        operation["qbit"]
        for operation in candidate["relevant_operations"]
    }
    if not set(granted_qbits + removed_qbits).issubset(source_qbits):
        raise ValueError(f"{authored.get('interaction_id')}: SCR effects do not match callback source operations")

    starts: list[int] = []
    completes: list[int] = []
    granted = set(granted_qbits)
    removed = set(removed_qbits)
    for stage in stages:
        required = set(stage["required_qbits"])
        forbidden = set(stage["forbidden_qbits"])
        if granted.intersection(required) or removed.intersection(forbidden):
            starts.append(stage["entry_qbit"])
        if granted.intersection(forbidden) or removed.intersection(required):
            completes.append(stage["entry_qbit"])
    if not starts and not completes:
        raise ValueError(f"{authored.get('interaction_id')}: SCR effects do not transition a journal stage")

    predicate = authored.get("predicate", {})
    required_qbits = predicate.get("required_qbits", [])
    forbidden_qbits = predicate.get("forbidden_qbits", [])
    any_required_qbits = predicate.get("any_required_qbits", [])
    minimum_gold = predicate.get("minimum_gold", 0)
    if (not isinstance(required_qbits, list)
            or not isinstance(forbidden_qbits, list)
            or not isinstance(any_required_qbits, list)
            or not isinstance(minimum_gold, int)
            or minimum_gold < 0):
        raise ValueError(f"{authored.get('interaction_id')}: invalid pure SCR predicate")
    non_qbit_dependencies = []
    if minimum_gold > 0:
        non_qbit_dependencies.append({"kind": "carried_gold", "minimum": minimum_gold})

    return {
        "id": authored["interaction_id"],
        "source_kind": "scr",
        "rude_id": binding["rude_id"],
        "bindings": [{key: value for key, value in binding.items() if key != "rude_id"}],
        "journal_entries": sorted(set(starts + completes)),
        "roles": (["offer"] if starts else []) + (["handoff"] if completes else []),
        "conditions": {
            "scr_predicate": {
                "required_qbits": required_qbits,
                "forbidden_qbits": forbidden_qbits,
                "any_required_qbits": any_required_qbits,
                "minimum_gold": minimum_gold,
            },
            "available": {"activates_journal_entries": starts},
            "in_progress": {"active_journal_entries": completes, "scr_predicate_not_met": True},
            "ready": {"active_journal_entries": completes, "scr_predicate_met": True},
        },
        "effects": {
            "granted_qbits": granted_qbits,
            "removed_qbits": removed_qbits,
        },
        "non_qbit_dependencies": non_qbit_dependencies,
        "justification": "authored_pure_predicate_for_dialogue_linked_scr_callback",
        "classification": "authored_override",
        "override_reason": authored["reason"],
        "provenance": {
            "source": candidate["provenance"]["source"],
            "source_lines": authored.get("source_lines", []),
            "event_inventory": candidate["provenance"]["event_inventory"],
            "callback_routine": candidate["callback_routine"],
        },
    }


def generate(
    rude_root: Path,
    maps_root: Path,
    raw_maps_root: Path,
    events_root: Path,
    scripts_root: Path,
    overrides_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    stages = load_journal_stages(rude_root / "NPC997.rude")
    journal_keys = {
        value
        for stage in stages
        for value in stage["required_qbits"] + stage["forbidden_qbits"]
    }
    bindings_by_rude_id, all_bindings = load_bindings(maps_root, raw_maps_root)
    overrides, authored_scr_interactions, authored_key_interactions = load_overrides(overrides_path)
    interactions: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    normal_graph_count = 0
    normal_row_count = 0
    reachable_grant_rude_ids: set[int] = set()
    root_grant_rude_ids: set[int] = set()
    ordinary_granted_journal_keys: set[int] = set()
    seen_candidate_ids: set[str] = set()

    for path in sorted(rude_root.glob("NPC[0-9]*.rude"), key=lambda value: value.name.lower()):
        # NPC997 is the journal, NPC998 is the quest-history list, and NPC999 is the debug/status list.
        if path.name in {"NPC997.rude", "NPC998.rude", "NPC999.rude"}:
            continue
        rows = load_rude_file(path)
        if not rows:
            continue
        rude_id = rows[0].rude_id
        normal_graph_count += 1
        normal_row_count += len(rows)
        paths = structural_paths(rude_id, rows)
        for row in rows:
            if row.node_id not in paths or row.next_node < -1:
                continue
            relevant_grants = set(row.granted).intersection(journal_keys)
            if relevant_grants:
                reachable_grant_rude_ids.add(rude_id)
                ordinary_granted_journal_keys.update(relevant_grants)
                if row.node_id == rude_id:
                    root_grant_rude_ids.add(rude_id)
            starts, completes = stage_transitions(row, stages)
            if not starts and not completes:
                continue
            interaction_id = f"mm9.rude.{rude_id}.row.{row.source_line}"
            seen_candidate_ids.add(interaction_id)
            override = overrides.get(interaction_id)
            if override and override.get("classification") == "excluded":
                exclusions.append({
                    "id": interaction_id,
                    "reason": override["reason"],
                    "provenance": f"dialogue/rude/{path.name}:{row.source_line}",
                })
                continue
            record = interaction_record(
                row,
                paths[row.node_id],
                starts,
                completes,
                bindings_by_rude_id.get(rude_id, []),
                override,
            )
            if not bindings_by_rude_id.get(rude_id):
                exclusions.append({
                    "id": interaction_id,
                    "reason": "the RUDE graph has no imported actor, so no loaded NPC can own this marker",
                    "provenance": f"dialogue/rude/{path.name}:{row.source_line}",
                })
            elif record:
                interactions.append(record)

    unused_overrides = sorted(set(overrides).difference(seen_candidate_ids))
    if unused_overrides:
        raise ValueError("unused quest-interaction overrides: " + ", ".join(unused_overrides))

    scr_source_candidates, scr_source_exclusions = scr_candidates(events_root, scripts_root, journal_keys, all_bindings)
    exclusions.extend(scr_source_exclusions)
    source_candidates_by_id = {candidate["id"]: candidate for candidate in scr_source_candidates}
    authored_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for authored in authored_scr_interactions:
        authored_by_candidate.setdefault(authored["source_candidate_id"], []).append(authored)
    unknown_scr_sources = sorted(set(authored_by_candidate).difference(source_candidates_by_id))
    if unknown_scr_sources:
        raise ValueError(
            "authored SCR interactions have no reachable source candidate: " + ", ".join(unknown_scr_sources))
    bindings_by_identity = {
        (binding["map_id"], binding["source_object_index"]): binding
        for binding in all_bindings
    }
    for candidate in scr_source_candidates:
        authored_records = authored_by_candidate.get(candidate["id"], [])
        excluded = [record for record in authored_records if record.get("classification") == "excluded"]
        classified = [record for record in authored_records if record.get("classification") != "excluded"]
        if excluded:
            if len(excluded) != 1 or classified:
                raise ValueError(f"{candidate['id']}: SCR candidate exclusion cannot be combined with classifications")
            exclusions.append({
                "id": candidate["id"],
                "reason": excluded[0]["reason"],
                "provenance": candidate["provenance"],
            })
            continue
        binding = bindings_by_identity.get((candidate["map_id"], candidate["source_object_index"]))
        if binding is None:
            unresolved.append({**candidate, "reason": "dialogue-linked SCR callback has no imported actor binding"})
            continue
        if not classified:
            unresolved.append(candidate)
            continue
        for authored in classified:
            interactions.append(scr_interaction_record(authored, candidate, binding, stages))
    for authored in authored_key_interactions:
        binding = bindings_by_identity.get((authored["map_id"], authored["source_object_index"]))
        if binding is None or binding.get("rude_id") != authored["rude_id"]:
            raise ValueError(f"{authored['interaction_id']}: no imported actor binding with dialogue "
                             f"{authored['rude_id']} at {authored['map_id']} object {authored['source_object_index']}")
        interactions.append(key_interaction_record(authored, binding))

    literal_scr_keys = literal_scr_journal_keys(scripts_root, journal_keys)
    scr_only_journal_keys = literal_scr_keys.difference(ordinary_granted_journal_keys)
    interactions.sort(key=lambda value: value["id"])
    exclusions.sort(key=lambda value: value["id"])
    unresolved.sort(key=lambda value: value["id"])
    dependency_counts: dict[str, int] = {}
    for interaction in interactions:
        for dependency in interaction["non_qbit_dependencies"]:
            kind = str(dependency["kind"])
            dependency_counts[kind] = dependency_counts.get(kind, 0) + 1
    metadata = {
        "format_version": 1,
        "world": "mm9",
        "generated_by": "tools/mm9_import_discovery/generate_mm9_quest_interactions.py",
        "journal_stages": stages,
        "interactions": interactions,
    }
    report = {
        "format_version": 1,
        "world": "mm9",
        "generated_by": "tools/mm9_import_discovery/generate_mm9_quest_interactions.py",
        "inventory": {
            "normal_rude_graphs": normal_graph_count,
            "normal_dialogue_rows": normal_row_count,
            "reachable_journal_grant_rude_ids": len(reachable_grant_rude_ids),
            "root_journal_grant_rude_ids": len(root_grant_rude_ids),
            "journal_condition_raw_keys": len(journal_keys),
            "journal_keys_granted_by_ordinary_rude_rows": len(ordinary_granted_journal_keys),
            "journal_keys_granted_only_by_literal_scr": len(scr_only_journal_keys),
            "imported_dialogue_actor_bindings": len(all_bindings),
            "generated_interactions": len(interactions),
            "explicit_exclusions": len(exclusions),
            "unresolved_candidates": len(unresolved),
            "validated_non_qbit_dependencies": dict(sorted(dependency_counts.items())),
        },
        "binding_coverage": all_bindings,
        "explicit_exclusions": exclusions,
        "unresolved_candidates": unresolved,
    }
    return metadata, report


def yaml_text(document: dict[str, Any]) -> str:
    return yaml.dump(document, Dumper=StableDumper, sort_keys=False, allow_unicode=True, width=120)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic MM9 NPC quest-interaction metadata.")
    parser.add_argument("--rude-root", type=Path, default=Path("assets_dev/worlds/mm9/dialogue/rude"))
    parser.add_argument("--maps-root", type=Path, default=Path("assets_dev/worlds/mm9/maps"))
    parser.add_argument("--raw-maps-root", type=Path, default=Path("assets_editor_dev/worlds/mm9/maps"))
    parser.add_argument("--events-root", type=Path, default=Path("assets_editor_dev/worlds/mm9/maps"))
    parser.add_argument("--scripts-root", type=Path, default=Path("mm9/extracted/SCRIPTS/SCRIPTS"))
    parser.add_argument(
        "--overrides",
        type=Path,
        default=Path("tools/mm9_import_discovery/mm9_quest_interaction_overrides.yml"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets_dev/worlds/mm9/state/quest_interactions.yml"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("assets_dev/worlds/mm9/state/quest_interaction_coverage.yml"),
    )
    parser.add_argument("--lua-root", type=Path, default=Path("assets_dev/worlds/mm9/events"))
    parser.add_argument(
        "--key-deal-review",
        type=Path,
        default=Path("devdocs/mm9_rework/MM9_KEY_DEAL_CANDIDATES.md"),
        help="the review list of journal-less key deals (candidates for key_interactions)",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        metadata, report = generate(
            args.rude_root,
            args.maps_root,
            args.raw_maps_root,
            args.events_root,
            args.scripts_root,
            args.overrides,
        )
        stages = load_journal_stages(args.rude_root / "NPC997.rude")
        review = key_deal_candidates(
            args.rude_root, args.scripts_root, args.lua_root, args.maps_root,
            {value for stage in stages for value in stage["required_qbits"] + stage["forbidden_qbits"]},
            load_bindings(args.maps_root, args.raw_maps_root)[0],
            {i["rude_id"] for i in metadata["interactions"] if i.get("source_kind") != "keys"},
            {i["rude_id"] for i in metadata["interactions"] if i.get("source_kind") == "keys"},
            load_key_deal_reviews(args.overrides),
        )
    except (OSError, ValueError, yaml.YAMLError) as exception:
        print(exception)
        return 1
    outputs = ((args.output, yaml_text(metadata)), (args.report, yaml_text(report)),
               (args.key_deal_review, key_deal_review_text(review)))
    if args.check:
        stale = [str(path) for path, text in outputs if not path.is_file() or path.read_text(encoding="utf-8") != text]
        if stale:
            print("stale generated MM9 quest-interaction files: " + ", ".join(stale))
            return 1
        print("MM9 quest-interaction metadata and coverage are current")
        return 0
    for path, text in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
