#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


MODEL_SIDECAR_SUFFIX = ".model.yml"


def normalize_ref(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def source_path_to_virtual(value: str) -> str:
    normalized = normalize_ref(value)
    marker = "mm9/extracted/models/models/"
    if marker in normalized:
        return "models/" + normalized.split(marker, 1)[1]
    marker = "models/models/"
    if marker in normalized:
        return "models/" + normalized.split(marker, 1)[1]
    if normalized.startswith("models/"):
        return normalized
    return normalized


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def lookup_key(source_model: str, source_skins: list[str]) -> str:
    return source_model + "|" + ";".join(source_skins)


def source_skin_to_virtual(value: str) -> str:
    normalized = normalize_ref(value)
    marker = "mm9/extracted/skins/skins/"
    if marker in normalized:
        return "skins/" + normalized.split(marker, 1)[1]
    marker = "skins/skins/"
    if marker in normalized:
        return "skins/" + normalized.split(marker, 1)[1]
    if normalized.startswith("skins/"):
        return normalized
    return normalized


def load_source_asset_aliases(path: Path) -> dict[str, dict[str, str]]:
    aliases = {
        "source_models": {},
        "source_skins": {},
    }
    if not path.exists():
        return aliases

    data = load_yaml(path)
    for alias in data.get("aliases") or []:
        if not isinstance(alias, dict):
            continue

        source_family = str(alias.get("source_family") or "").strip().lower()
        requested = str(alias.get("requested") or "")
        resolved = str(alias.get("resolved") or "")
        if not requested or not resolved:
            continue

        if source_family == "models":
            aliases["source_models"][source_path_to_virtual(requested)] = source_path_to_virtual(resolved)
        elif source_family == "skins":
            aliases["source_skins"][source_skin_to_virtual(requested)] = source_skin_to_virtual(resolved)

    return aliases


def sidecar_model_asset(path: Path, models_root: Path) -> str:
    model_file = load_yaml(path).get("model")
    if isinstance(model_file, str) and model_file:
        return (path.parent / model_file).relative_to(models_root.parent).as_posix()
    return path.with_suffix("").relative_to(models_root.parent).as_posix()


def source_model_for_sidecar(sidecar: dict[str, Any]) -> str:
    source_model = sidecar.get("source_model")
    if isinstance(source_model, str) and source_model:
        return normalize_ref(source_model)
    source = sidecar.get("source")
    if isinstance(source, dict):
        source_path = source.get("path")
        if isinstance(source_path, str) and source_path:
            return source_path_to_virtual(source_path)
    return ""


def material_source_skins(sidecar: dict[str, Any]) -> list[str]:
    skins = []
    for material in sidecar.get("materials") or []:
        if not isinstance(material, dict):
            continue
        runtime_texture = material.get("runtime_texture")
        if isinstance(runtime_texture, str) and runtime_texture:
            skins.append(normalize_ref(runtime_texture))
    return skins


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate MM9 model_registry.yml from source-shaped model sidecars.")
    parser.add_argument("--models-root", type=Path, default=Path("assets_dev/worlds/mm9/models"))
    parser.add_argument("--output", type=Path, default=Path("assets_dev/worlds/mm9/models/model_registry.yml"))
    parser.add_argument(
        "--source-asset-aliases",
        type=Path,
        default=Path("assets_dev/worlds/mm9/import/overrides/mm9_active_slice.source_asset_aliases.yml"),
    )
    args = parser.parse_args()

    sidecar_paths = sorted(
        path
        for path in args.models_root.rglob(f"*{MODEL_SIDECAR_SUFFIX}")
        if "/import/" not in path.as_posix()
    )
    models = []
    by_source_model: dict[str, str] = {}
    by_source_model_and_skins: dict[str, str] = {}
    by_actor_table_row: dict[str, str] = {}

    for sidecar_path in sidecar_paths:
        sidecar = load_yaml(sidecar_path)
        source_model = source_model_for_sidecar(sidecar)
        if not source_model:
            continue

        model_asset = sidecar_model_asset(sidecar_path, args.models_root)
        model_id = str(sidecar.get("id") or sidecar_path.name.removesuffix(MODEL_SIDECAR_SUFFIX))
        skin_bindings = sidecar.get("skin_bindings") or []
        source_skins = material_source_skins(sidecar)
        entry = {
            "model_id": model_id,
            "roles": sidecar.get("roles") or [],
            "source_model": source_model,
            "model_asset": model_asset,
            "model_sidecar": sidecar_path.relative_to(args.models_root.parent).as_posix(),
        }
        if source_skins:
            entry["source_skins"] = source_skins
        if sidecar.get("source_tables"):
            entry["source_tables"] = sidecar["source_tables"]
        if skin_bindings:
            entry["skin_bindings"] = skin_bindings
        models.append(entry)
        by_source_model[source_model] = model_asset

        if source_skins:
            by_source_model_and_skins[lookup_key(source_model, source_skins)] = model_asset
        for binding in skin_bindings:
            if not isinstance(binding, dict):
                continue
            binding_id = str(binding.get("id") or "")
            binding_skins = [normalize_ref(str(skin)) for skin in binding.get("source_skins") or []]
            if binding_skins:
                by_source_model_and_skins[lookup_key(source_model, binding_skins)] = binding_id
            for row in binding.get("actor_rows") or []:
                if not isinstance(row, dict):
                    continue
                table = row.get("table")
                number = row.get("number")
                if table and number and binding_id:
                    by_actor_table_row[f"{table}:{number}"] = binding_id

    aliases = load_source_asset_aliases(args.source_asset_aliases)
    registry = {
        "schema": "openyamm.mm9.model_registry.v2",
        "world": "mm9",
        "models": sorted(models, key=lambda value: value["source_model"]),
        "lookup": {
            "by_source_model": dict(sorted(by_source_model.items())),
            "by_source_model_and_skins": dict(sorted(by_source_model_and_skins.items())),
            "by_actor_table_row": dict(sorted(by_actor_table_row.items())),
        },
    }
    if aliases["source_models"] or aliases["source_skins"]:
        registry["aliases"] = {
            key: dict(sorted(value.items()))
            for key, value in aliases.items()
            if value
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    print(f"{len(models)} models")
    print(f"registry: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
