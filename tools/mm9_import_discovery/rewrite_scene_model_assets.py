#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


def normalize_ref(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def source_skin_list(value: Any) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return []
    return [normalize_ref(item) for item in value.split(";") if item.strip()]


def lookup_key(source_model: str, source_skins: list[str]) -> str:
    return source_model + "|" + ";".join(source_skins)


def actor_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower()).rstrip("0123456789")


def type_picture_keys(value: str) -> list[str]:
    key = actor_key(value)
    if not key:
        return []

    keys = [key]
    if key.startswith("peasant"):
        keys.append(key[len("peasant"):])
    for prefix in ("peasant", ""):
        candidate = key[len(prefix):] if prefix and key.startswith(prefix) else key
        if candidate and candidate[-1:] in ("a", "b", "c", "d"):
            keys.append(candidate[:-1])

    return [item for index, item in enumerate(keys) if item and item not in keys[:index]]


def source_class_type_picture_keys(value: str) -> list[str]:
    source_key = actor_key(value)
    if not source_key:
        return []

    role_codes = {
        "commoner": "a",
        "town": "b",
        "shopkeeper": "c",
        "prisoner": "d",
    }

    role_code = ""
    remainder = source_key
    for role, code in role_codes.items():
        if source_key.startswith(role):
            role_code = code
            remainder = source_key[len(role):]
            break

    race = ""
    race_remainder = remainder
    for prefix, value in (
        ("human2", "human2"),
        ("human", "human1"),
        ("elf", "elf"),
        ("dwarf", "dwarf"),
        ("halforc", "halforc"),
    ):
        if race_remainder.startswith(prefix):
            race = value
            race_remainder = race_remainder[len(prefix):]
            break

    gender = ""
    gender_remainder = race_remainder
    for prefix in ("female", "male"):
        if gender_remainder.startswith(prefix):
            gender = prefix
            gender_remainder = gender_remainder[len(prefix):]
            break

    if not race or not gender or len(gender_remainder) != 1 or gender_remainder not in "abcd":
        return []

    variant_code = gender_remainder
    keys = []
    if race == "halforc":
        keys.append(f"peasant{race}{gender}{variant_code}")
    if role_code:
        keys.append(f"peasant{race}{gender}{role_code}{variant_code}")
    keys.extend(key[len("peasant"):] for key in list(keys))
    return [item for index, item in enumerate(keys) if item and item not in keys[:index]]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def remove_suffix(value: str, suffix: str) -> str:
    if value.endswith(suffix):
        return value[:-len(suffix)]
    return value


class ModelRegistry:
    def __init__(self, data: dict[str, Any]) -> None:
        self.by_source_model: dict[str, list[dict[str, Any]]] = {}
        self.by_source_model_and_skins: dict[str, dict[str, Any]] = {}
        self.by_source_model_and_actor_key: dict[str, list[dict[str, Any]]] = {}
        self.type_keys_by_source_model: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self.by_actor_key: dict[str, list[dict[str, Any]]] = {}
        self.by_type_picture_key: dict[str, list[dict[str, Any]]] = {}
        self.by_model_stem: dict[str, list[dict[str, Any]]] = {}

        for model in data.get("models") or []:
            source_model = normalize_ref(str(model.get("source_model") or ""))
            if not source_model:
                continue
            model_asset = model.get("model_asset")
            if not isinstance(model_asset, str) or not model_asset:
                continue
            model_id = str(model.get("model_id") or Path(model_asset).stem)
            model_entry = {
                "id": model_id,
                "model_asset": model_asset,
                "source_skins": [normalize_ref(str(skin)) for skin in model.get("source_skins") or []],
                "skin_bindings": [],
            }
            self.by_source_model.setdefault(source_model, []).append(model_entry)
            self.by_model_stem.setdefault(Path(source_model).stem, []).append(model_entry)
            if model_entry["source_skins"]:
                self.by_source_model_and_skins[lookup_key(source_model, model_entry["source_skins"])] = model_entry

            for binding in model.get("skin_bindings") or []:
                if not isinstance(binding, dict):
                    continue
                binding_id = str(binding.get("id") or model_id)
                entry = {
                    "id": binding_id,
                    "model_asset": model_asset,
                    "source_skins": [normalize_ref(str(skin)) for skin in binding.get("source_skins") or []],
                    "skin_binding": binding_id,
                    "has_base_name": False,
                }
                model_entry["skin_bindings"].append(entry)
                if entry["source_skins"]:
                    self.by_source_model_and_skins[lookup_key(source_model, entry["source_skins"])] = entry
                for row in binding.get("actor_rows") or []:
                    if not isinstance(row, dict):
                        continue

                    row_entry = dict(entry)
                    row_entry["has_base_name"] = bool(str(row.get("base_name") or "").strip())
                    key = actor_key(str(row.get("monster_name") or ""))
                    if key:
                        self.by_source_model_and_actor_key.setdefault(
                            lookup_key(source_model, [key]),
                            [],
                        ).append(row_entry)
                        self.by_actor_key.setdefault(key, []).append(row_entry)

                    for key in type_picture_keys(str(row.get("type_picture") or "")):
                        self.type_keys_by_source_model.setdefault(source_model, {}).setdefault(key, []).append(
                            row_entry
                        )
                        self.by_type_picture_key.setdefault(key, []).append(row_entry)

    @staticmethod
    def unique_entry(entries: list[dict[str, Any]], prefer_base_name: bool = False) -> dict[str, Any] | None:
        unique: dict[str, dict[str, Any]] = {}
        for entry in entries:
            unique[entry["id"]] = entry
        if len(unique) == 1:
            return next(iter(unique.values()))
        if prefer_base_name:
            preferred = {
                entry_id: entry
                for entry_id, entry in unique.items()
                if entry.get("has_base_name")
            }
            if len(preferred) == 1:
                return next(iter(preferred.values()))
        return None

    def resolve(
        self,
        source_model: str,
        source_skin: Any,
        source_class: Any = "",
    ) -> tuple[str, str, dict[str, Any] | None]:
        normalized_model = normalize_ref(source_model)
        normalized_skins = source_skin_list(source_skin)

        if normalized_skins:
            exact = self.by_source_model_and_skins.get(lookup_key(normalized_model, normalized_skins))
            if exact is not None:
                return exact["model_asset"], str(exact.get("skin_binding") or ""), None

        class_key = actor_key(str(source_class or ""))
        if class_key:
            class_entry = self.unique_entry(self.by_actor_key.get(class_key, []))
            if class_entry is not None:
                return class_entry["model_asset"], str(class_entry.get("skin_binding") or ""), None

            type_matches: list[dict[str, Any]] = []
            for type_key in source_class_type_picture_keys(str(source_class or "")):
                type_matches.extend(self.by_type_picture_key.get(type_key, []))
            type_entry = self.unique_entry(type_matches, prefer_base_name=True)
            if type_entry is not None:
                return type_entry["model_asset"], str(type_entry.get("skin_binding") or ""), None

            class_matches = self.by_source_model_and_actor_key.get(lookup_key(normalized_model, [class_key]), [])
            class_entry = self.unique_entry(class_matches)
            if class_entry is not None:
                return class_entry["model_asset"], str(class_entry.get("skin_binding") or ""), None

            type_matches = []
            for type_key, entries in self.type_keys_by_source_model.get(normalized_model, {}).items():
                if class_key.endswith(type_key):
                    type_matches.extend(entries)
            type_entry = self.unique_entry(type_matches)
            if type_entry is not None:
                return type_entry["model_asset"], str(type_entry.get("skin_binding") or ""), None

        candidates = self.by_source_model.get(normalized_model, [])
        if not candidates:
            candidates = self.by_model_stem.get(Path(normalized_model).stem, [])
        if len(candidates) == 1:
            bindings = candidates[0].get("skin_bindings") or []
            if len(bindings) == 1:
                return candidates[0]["model_asset"], str(bindings[0].get("skin_binding") or ""), None
            if len(bindings) > 1:
                return candidates[0]["model_asset"], "", {
                    "status": "skin_ambiguous",
                    "source_model": normalized_model,
                    "source_skins": normalized_skins,
                    "candidates": [
                        {
                            "id": str(binding.get("skin_binding") or binding.get("id") or ""),
                            "source_skins": binding.get("source_skins") or [],
                        }
                        for binding in bindings
                    ],
                }
            return candidates[0]["model_asset"], "", None

        if not candidates:
            return "", "", {
                "status": "missing",
                "source_model": normalized_model,
                "source_skins": normalized_skins,
            }

        return "", "", {
            "status": "ambiguous",
            "source_model": normalized_model,
            "source_skins": normalized_skins,
            "candidates": candidates,
        }


def rewrite_entry(entry: dict[str, Any], registry: ModelRegistry) -> bool:
    source_model = entry.get("source_model")
    if not isinstance(source_model, str) or not source_model:
        return False

    model_asset, skin_binding, resolution = registry.resolve(
        source_model,
        entry.get("source_skin", ""),
        entry.get("source_class", ""),
    )
    changed = False
    if resolution is None:
        changed = entry.get("model_asset") != model_asset
        entry["model_asset"] = model_asset
        if skin_binding:
            changed = changed or entry.get("model_skin_binding") != skin_binding
            entry["model_skin_binding"] = skin_binding
        else:
            changed = changed or "model_skin_binding" in entry
            entry.pop("model_skin_binding", None)
        changed = changed or "model_resolution" in entry
        entry.pop("model_resolution", None)
    else:
        if model_asset:
            changed = changed or entry.get("model_asset") != model_asset
            entry["model_asset"] = model_asset
        else:
            changed = changed or "model_asset" in entry
            entry.pop("model_asset", None)
        changed = changed or "model_skin_binding" in entry
        entry.pop("model_skin_binding", None)
        changed = changed or entry.get("model_resolution") != resolution
        entry["model_resolution"] = resolution
    return changed


def rewrite_scene(path: Path, registry: ModelRegistry) -> tuple[int, int]:
    data = load_yaml(path)
    changed = 0
    unresolved = 0
    for entry in data.get("model_instances") or []:
        if not isinstance(entry, dict):
            continue
        if rewrite_entry(entry, registry):
            changed += 1
        if not entry.get("model_asset"):
            unresolved += 1
    if changed:
        write_yaml(path, data)
    return changed, unresolved


def rewrite_model_assets(path: Path, registry: ModelRegistry) -> tuple[int, int]:
    data = load_yaml(path)
    changed = 0
    unresolved = 0
    for entry in data.get("models") or []:
        if not isinstance(entry, dict):
            continue
        if rewrite_entry(entry, registry):
            changed += 1
        if not entry.get("model_asset"):
            unresolved += 1
    if changed:
        write_yaml(path, data)
    return changed, unresolved


def rewrite_model_assets_from_scene(path: Path, scene_path: Path) -> tuple[int, int]:
    scene_data = load_yaml(scene_path)
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for entry in scene_data.get("model_instances") or []:
        if not isinstance(entry, dict):
            continue

        source_model = entry.get("source_model")
        model_asset = entry.get("model_asset")
        source_object_index = entry.get("source_object_index")
        source_class = entry.get("source_class")

        if not isinstance(source_model, str) or not isinstance(model_asset, str):
            continue

        group = grouped.setdefault(
            (source_model, model_asset),
            {
                "source_model": source_model,
                "model_asset": model_asset,
                "instance_count": 0,
                "source_object_indices": [],
                "source_classes": [],
            },
        )
        group["instance_count"] += 1
        if isinstance(source_object_index, int):
            group["source_object_indices"].append(source_object_index)
        if isinstance(source_class, str) and source_class and source_class not in group["source_classes"]:
            group["source_classes"].append(source_class)

    models = []
    unresolved = 0
    for group in sorted(grouped.values(), key=lambda value: (value["model_asset"], value["source_model"])):
        if not group["model_asset"]:
            unresolved += 1
        group["source_object_indices"].sort()
        group["source_classes"].sort()
        if not group["source_classes"]:
            group.pop("source_classes")
        models.append(group)

    existing = load_yaml(path) if path.exists() else {}
    data = {
        "format_version": existing.get("format_version", 1),
        "kind": existing.get("kind", "mm9_model_assets"),
        "source_dat": existing.get("source_dat", ""),
        "unique_model_count": len(models),
        "models": models,
    }

    changed = existing != data
    if changed:
        write_yaml(path, data)
    return len(models) if changed else 0, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite MM9 scene model_asset paths through model_registry.yml.")
    parser.add_argument("--maps-root", type=Path, default=Path("assets_dev/worlds/mm9/maps"))
    parser.add_argument("--registry", type=Path, default=Path("assets_dev/worlds/mm9/models/model_registry.yml"))
    args = parser.parse_args()

    registry = ModelRegistry(load_yaml(args.registry))
    total_changed = 0
    total_unresolved = 0
    scene_paths_by_stem: dict[str, Path] = {}
    for path in sorted(args.maps_root.glob("*.scene.yml")):
        scene_paths_by_stem[remove_suffix(path.name, ".scene.yml")] = path
        changed, unresolved = rewrite_scene(path, registry)
        total_changed += changed
        total_unresolved += unresolved
        print(f"{path}: {changed} changed, {unresolved} unresolved")
    for path in sorted(args.maps_root.glob("*.model_assets.yml")):
        scene_path = scene_paths_by_stem.get(remove_suffix(path.name, ".model_assets.yml"))
        if scene_path is not None:
            changed, unresolved = rewrite_model_assets_from_scene(path, scene_path)
        else:
            changed, unresolved = rewrite_model_assets(path, registry)
        total_changed += changed
        total_unresolved += unresolved
        print(f"{path}: {changed} changed, {unresolved} unresolved")

    print(f"total: {total_changed} changed, {total_unresolved} unresolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
