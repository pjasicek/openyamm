#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Any

import yaml


MODEL_SIDE_CAR_SUFFIX = ".model.yml"


def normalize_virtual_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip().lower()
    while normalized.startswith("/"):
        normalized = normalized[1:]
    parts = [part for part in normalized.split("/") if part and part != "."]
    if len(parts) >= 2 and parts[0] == parts[1]:
        parts = parts[1:]
    return "/".join(parts)


def source_path_to_virtual(value: str) -> str:
    normalized = normalize_virtual_path(value)
    marker = "mm9/extracted/models/models/"
    if marker in normalized:
        return "models/" + normalized.split(marker, 1)[1]
    marker = "models/models/"
    if marker in normalized:
        return "models/" + normalized.split(marker, 1)[1]
    return normalized


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def world_root_for_sidecar(sidecar_path: Path) -> Path:
    parts = sidecar_path.parts
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == "models":
            return Path(*parts[:index])
    return sidecar_path.parent


def index_exported_models(source_models_root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for sidecar_path in sorted(source_models_root.rglob(f"*{MODEL_SIDE_CAR_SUFFIX}")):
        sidecar = load_yaml(sidecar_path)
        source = sidecar.get("source")
        if not isinstance(source, dict):
            continue
        source_path = source.get("path")
        if not isinstance(source_path, str) or not source_path:
            continue
        model_file = sidecar.get("model")
        if not isinstance(model_file, str) or not model_file:
            continue
        glb_path = sidecar_path.parent / model_file
        if not glb_path.exists():
            continue
        if glb_path.with_suffix(MODEL_SIDE_CAR_SUFFIX) != sidecar_path:
            continue
        key = source_path_to_virtual(source_path)
        index.setdefault(key, []).append(sidecar_path)
    return index


def material_missing_count(sidecar_path: Path) -> int:
    sidecar = load_yaml(sidecar_path)
    materials = sidecar.get("materials")
    if not isinstance(materials, list):
        return 0

    world_root = world_root_for_sidecar(sidecar_path)
    missing = 0
    for material in materials:
        if not isinstance(material, dict):
            continue
        texture_value = material.get("texture")
        texture_path = world_root / normalize_virtual_path(texture_value) if isinstance(texture_value, str) else None
        if texture_path is not None and texture_value and not texture_path.exists():
            missing += 1
    return missing


def choose_sidecar(candidates: list[Path]) -> Path:
    return sorted(candidates, key=lambda path: (material_missing_count(path), len(path.parts), str(path)))[0]


def copy_asset(sidecar_path: Path, destination_root: Path, target_asset: str, dry_run: bool) -> None:
    sidecar = load_yaml(sidecar_path)
    model_file = sidecar["model"]
    source_glb = sidecar_path.parent / model_file
    target_glb = destination_root / normalize_virtual_path(target_asset)
    target_sidecar = target_glb.with_suffix(MODEL_SIDE_CAR_SUFFIX)

    if dry_run:
        print(f"would copy {source_glb} -> {target_glb}")
        print(f"would copy {sidecar_path} -> {target_sidecar}")
        return

    target_glb.parent.mkdir(parents=True, exist_ok=True)
    if not target_glb.exists() or not os.path.samefile(source_glb, target_glb):
        shutil.copy2(source_glb, target_glb)
    sidecar["id"] = target_glb.stem
    sidecar["model"] = target_glb.name
    write_yaml(target_sidecar, sidecar)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy converted MM9 GLBs into DAT-native model_asset paths used by .scene.yml files."
    )
    parser.add_argument("--model-assets", type=Path, default=Path("assets_dev/worlds/mm9/maps/guberland.model_assets.yml"))
    parser.add_argument("--source-models-root", type=Path, default=Path("assets_dev/worlds/mm9/models"))
    parser.add_argument(
        "--world-root",
        type=Path,
        action="append",
        default=[],
        help="Destination world root. May be supplied multiple times.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-missing", action="store_true", help="Report missing source conversions without failing.")
    args = parser.parse_args()

    model_assets = load_yaml(args.model_assets)
    required_models = model_assets.get("models")
    if not isinstance(required_models, list):
        raise ValueError(f"{args.model_assets} does not contain a models list")

    destination_roots = args.world_root or [
        Path("assets_dev/worlds/mm9"),
        Path("assets_editor_dev/worlds/mm9"),
    ]
    exported_model_index = index_exported_models(args.source_models_root)
    copied = 0
    missing = 0

    for entry in required_models:
        if not isinstance(entry, dict):
            continue
        source_model = entry.get("source_model")
        model_asset = entry.get("model_asset")
        if not isinstance(source_model, str) or not isinstance(model_asset, str):
            continue

        if any((destination_root / normalize_virtual_path(model_asset)).exists() for destination_root in destination_roots):
            copied += 1
            continue

        source_key = normalize_virtual_path(source_model)
        candidates = exported_model_index.get(source_key, [])
        if not candidates:
            print(f"missing converted model for {source_model} -> {model_asset}")
            missing += 1
            continue

        sidecar_path = choose_sidecar(candidates)
        for destination_root in destination_roots:
            copy_asset(sidecar_path, destination_root, model_asset, args.dry_run)
        copied += 1

    action = "would sync" if args.dry_run else "synced"
    print(f"{action} {copied} model assets; missing={missing}")
    return 1 if missing and not args.allow_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
