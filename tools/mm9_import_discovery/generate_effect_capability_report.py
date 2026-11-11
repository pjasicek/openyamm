#!/usr/bin/env python3
"""Publish per-recipe MM9 FXF runtime capability and blocking reasons."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

import yaml

from compile_effect_library import BODY_ANCHORS, effect_id, normalized_reference, properties
from convert_abc_model import read_abc, rigid_piece_node_indices


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "re_mm8" / "mm9_vfx"))

from inspect_assets import read_fxf  # noqa: E402


SUPPORTED_COMPONENTS = {"SpriteSystem", "Sprite", "PlaySound", "Model", "Null"}
def resource_references(group: dict) -> set[str]:
    result = set()
    for key in group["keys"]:
        for prop in key["properties"]:
            if prop["type"] == 7 and not str(prop["value"]).endswith("|..."):
                result.add(normalized_reference(str(prop["value"])))
    return result


def visible_model_blockers(group: dict, bindings: dict[str, dict]) -> tuple[list[str], list[dict]]:
    blockers = []
    models = []
    for key in group["keys"]:
        if key["component_ref"].split(";", 1)[0] != "Model":
            continue
        props = properties(key)
        legacy = normalized_reference(str(props["Model"]))
        visible = not str(props.get("Skin", "")).endswith("|...")
        record = {"componentId": key["id"], "legacy": legacy, "visible": visible}
        if not visible:
            record["mode"] = "animation_path"
            models.append(record)
            continue
        binding = bindings.get(legacy)
        if binding is None or binding.get("status") != "bound":
            record["mode"] = "missing"
            models.append(record)
            continue
        try:
            model = read_abc(REPOSITORY_ROOT / binding["source"]["path"])
            rigid_piece_node_indices(model, 0)
            record["mode"] = "rigid"
        except (OSError, ValueError) as exception:
            record["mode"] = "deforming"
            record["reason"] = str(exception)
            blockers.append("needs_mesh_deformation")
        models.append(record)
    return blockers, models


def generate_report(fxf_path: Path, manifest_path: Path, library_path: Path) -> dict:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    bindings = {entry["legacy"]: entry for entry in manifest["bindings"]}
    library = yaml.safe_load(library_path.read_text(encoding="utf-8"))
    packaged_ids = {entry["id"] for entry in library["effects"]}
    effects = []
    total_keys = 0
    for group in read_fxf(fxf_path):
        total_keys += len(group["keys"])
        component_types = sorted({key["component_ref"].split(";", 1)[0] for key in group["keys"]})
        blockers = []
        unsupported = sorted(set(component_types) - SUPPORTED_COMPONENTS)
        if unsupported:
            blockers.append("unsupported_component_type")

        missing_resources = []
        unpackaged_resources = []
        for legacy in sorted(resource_references(group)):
            binding = bindings.get(legacy)
            if binding is None or binding.get("status") != "bound":
                missing_resources.append(legacy)
                continue
            asset_path = REPOSITORY_ROOT / "assets_dev" / binding["asset"]
            if not asset_path.exists():
                unpackaged_resources.append(legacy)
        if missing_resources:
            blockers.append("missing_source_asset")

        body_anchors = []
        for key in group["keys"]:
            mode = int(properties(key).get("UpdatePos", 0))
            if mode >= 2:
                body_anchors.append(
                    {
                        "componentId": key["id"],
                        "mode": mode,
                        "anchor": BODY_ANCHORS.get(mode, f"user_node_{mode}"),
                    }
                )
        anchor_fallback = bool(body_anchors)

        model_blockers, models = visible_model_blockers(group, bindings)
        blockers.extend(model_blockers)
        blockers = sorted(set(blockers))
        identifier = effect_id(group["name"])
        if identifier in packaged_ids:
            status = "supported_one_shot"
            if blockers or missing_resources or unpackaged_resources:
                raise ValueError(f"packaged effect {identifier} has unresolved capability blockers")
        elif blockers:
            status = "unsupported"
        elif unpackaged_resources:
            status = "ready_needs_asset_import"
        else:
            status = "ready_not_packaged"

        effects.append(
            {
                "id": identifier,
                "sourceName": group["name"],
                "status": status,
                "componentCount": len(group["keys"]),
                "componentTypes": component_types,
                "capabilities": sorted(
                    {
                        {
                            "SpriteSystem": "sprite_emitter",
                            "Sprite": "fixed_sprite",
                            "PlaySound": "sound",
                            "Model": "model",
                            "Null": "null_transform",
                        }.get(component, component)
                        for component in component_types
                    }
                ),
                "blockers": blockers,
                "missingResources": missing_resources,
                "unpackagedResources": unpackaged_resources,
                "bodyAnchors": body_anchors,
                **({"anchorFallback": "origin"} if anchor_fallback else {}),
                "models": models,
                "looping": "unsupported_until_native_continuous_key_semantics_are_implemented",
            }
        )

    statuses = Counter(effect["status"] for effect in effects)
    blockers = Counter(blocker for effect in effects for blocker in effect["blockers"])
    return {
        "schema": "openyamm.mm9EffectCapabilities.v1",
        "source": {
            "fxf": "engine/effects/mm9/source/spells.fxf",
            "bindings": "engine/effects/mm9/resource_bindings.yml",
            "library": "engine/effects/mm9/library.yml",
        },
        "scope": {
            "spawnMode": "one_shot",
            "looping": "unsupported",
            "visibleDeformingModels": "unsupported",
            "actorBodyAnchors": "origin_fallback",
            "knownGlobalDifferences": [
                "Native continuous-key loop behavior remains unresolved.",
                "Legacy texture-stage state and source mip upload are approximated by PNG and generated mipmaps.",
                "The exact native spatial-audio attenuation curve remains unverified.",
            ],
        },
        "summary": {
            "recipes": len(effects),
            "componentKeys": total_keys,
            "statuses": dict(sorted(statuses.items())),
            "blockers": dict(sorted(blockers.items())),
        },
        "effects": effects,
    }


def write_report(fxf_path: Path, manifest_path: Path, library_path: Path, output_path: Path) -> dict:
    report = generate_report(fxf_path, manifest_path, library_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fxf", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = write_report(args.fxf, args.bindings, args.library, args.output)
    print(yaml.safe_dump(report["summary"], sort_keys=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
