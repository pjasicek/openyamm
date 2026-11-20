#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import yaml
from PIL import Image

from convert_effect_dtx import convert_effect_texture
from compile_effect_library import compile_library, properties
from convert_abc_model import convert_model
from generate_effect_capability_report import (
    SUPPORTED_COMPONENTS,
    resource_references,
    visible_model_blockers,
    write_report as write_capability_report,
)
from generate_effect_resource_bindings import HARD_CODED_EFFECT_SPRITES, HARD_CODED_EXPLOSION_SPRITES


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "re_mm8" / "mm9_vfx"))

from inspect_assets import read_fxf  # noqa: E402


def load_restorations(repository_root: Path, bindings: dict, verify_artwork: bool = True) -> dict:
    path = repository_root / "tools/mm9_import_discovery/mm9_effect_restorations.yml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if document.get("schema") != "openyamm.mm9EffectRestorations.v1":
        raise ValueError(f"invalid restoration manifest: {path}")
    if not document["textures"]:
        return {}
    review = json.loads((repository_root / document["review"]).read_text(encoding="utf-8")) if verify_artwork else {}
    by_resource = {binding["resource"]: binding for binding in bindings.values()}
    result = {}
    for entry in document["textures"]:
        resource = entry["resource"]
        binding = by_resource.get(resource)
        if (not binding or binding["kind"] != "texture" or binding.get("origin") != "spells_fxf"
                or binding["status"] != "bound"):
            raise ValueError(f"restoration is not an FXF texture: {resource}")
        if resource in result:
            raise ValueError(f"duplicate restoration: {resource}")
        native_source = repository_root / binding["source"]["path"]
        if hashlib.sha256(native_source.read_bytes()).hexdigest() != entry["native_source_sha256"]:
            raise ValueError(f"restoration native source changed: {resource}")
        if verify_artwork:
            artwork = repository_root / entry["artwork"]
            if hashlib.sha256(artwork.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"restoration artwork changed: {resource}")
            if review.get("exports", {}).get(resource) != entry["sha256"]:
                raise ValueError(f"restoration has no matching artwork review: {resource}")
            with Image.open(artwork) as image:
                if image.mode != "RGBA" or list(image.size) != [2 * size for size in entry["native_size"]]:
                    raise ValueError(f"restoration must be RGBA at 2x native size: {resource}")
        result[resource] = dict(entry, review=document["review"])
    return result


def import_texture(repository_root: Path, binding: dict, restoration: dict | None) -> str:
    output = repository_root / "assets_dev" / binding["asset"]
    relative = Path(binding["asset"]).relative_to("engine/effects/mm9/textures")
    import_directory = repository_root / "assets_dev/engine/effects/mm9/import/textures" / relative.with_suffix("")
    report = convert_effect_texture(
        source=repository_root / binding["source"]["path"],
        output=output,
        import_directory=import_directory,
        color_space="srgb",
        alpha_usage="blend",
        min_filter="linear",
        mag_filter="linear",
        wrap_u="clamp",
        wrap_v="clamp",
        runtime_texture_path=binding["asset"],
    )
    if restoration is None:
        return "converted"
    if [report["dtx"]["width"], report["dtx"]["height"]] != restoration["native_size"]:
        raise ValueError(f"restoration native dimensions changed: {binding['resource']}")
    shutil.copyfile(repository_root / restoration["artwork"], output)
    report["restoration"] = restoration
    report["runtime"]["artwork"] = "reviewed-restoration"
    report["runtime"]["storageScale"] = 2
    (import_directory / "texture_import.yml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    return "restored"


def normalized_reference(reference: str) -> str:
    return reference.replace("\\", "/").lower()


def selected_references(group: dict) -> set[str]:
    references = set()
    for key in group["keys"]:
        for prop in key["properties"]:
            if prop["type"] != 7 or prop["value"].endswith("|..."):
                continue
            references.add(normalized_reference(prop["value"].split("|", 1)[-1]))
    return references


def supported_effect_names(repository_root: Path, manifest_path: Path) -> list[str]:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    bindings = {binding["legacy"]: binding for binding in manifest["bindings"]}
    source_fxf = Path(manifest["source"]["path"])
    if not source_fxf.is_absolute():
        source_fxf = repository_root / source_fxf

    result = []
    for group in read_fxf(source_fxf):
        component_types = {key["component_ref"].split(";", 1)[0] for key in group["keys"]}
        if component_types - SUPPORTED_COMPONENTS:
            continue
        if any(
            reference not in bindings or bindings[reference].get("status") != "bound"
            for reference in resource_references(group)
        ):
            continue
        model_blockers, _ = visible_model_blockers(group, bindings)
        if model_blockers:
            continue
        result.append(group["name"])
    return result


def import_effect_assets(
    repository_root: Path,
    manifest_path: Path,
    effect_names: list[str],
    native_textures: bool = False,
) -> dict:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    bindings = {binding["legacy"]: binding for binding in manifest["bindings"]}
    restorations = {} if native_textures else load_restorations(repository_root, bindings)
    source_fxf = Path(manifest["source"]["path"])
    if not source_fxf.is_absolute():
        source_fxf = repository_root / source_fxf
    groups = {group["name"]: group for group in read_fxf(source_fxf)}

    unknown = sorted(set(effect_names) - groups.keys())
    if unknown:
        raise ValueError(f"unknown FXF effect names: {unknown}")

    references = set()
    animation_path_models = set()
    for effect_name in effect_names:
        group = groups[effect_name]
        references.update(selected_references(group))
        for key in group["keys"]:
            if key["component_ref"].split(";", 1)[0] != "Model":
                continue
            props = properties(key)
            model_reference = normalized_reference(props["Model"].split("|", 1)[-1])
            if str(props.get("Skin", "")).endswith("|..."):
                animation_path_models.add(model_reference)
    references.update(HARD_CODED_EFFECT_SPRITES)
    references.update(HARD_CODED_EXPLOSION_SPRITES)
    for reference in list(references):
        binding = bindings[reference]
        if binding["kind"] == "sprite" and "sprite" in binding:
            references.update(frame["legacy"] for frame in binding["sprite"]["frames"])

    imported = []
    for reference in sorted(references):
        binding = bindings[reference]
        record = {
            "legacy": reference,
            "kind": binding["kind"],
            "asset": binding["asset"],
        }
        if binding["status"] != "bound":
            record["status"] = binding["status"]
            imported.append(record)
            continue

        source = repository_root / binding["source"]["path"]
        output = repository_root / "assets_dev" / binding["asset"]
        if binding["kind"] == "texture":
            record["status"] = import_texture(repository_root, binding, restorations.get(binding["resource"]))
        elif binding["kind"] == "sound":
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, output)
            record["status"] = "copied"
            record["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        elif binding["kind"] == "sprite":
            sprite = binding["sprite"]
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                yaml.safe_dump(
                    {
                        "schema": "openyamm.effectSprite.v2",
                        "id": binding["resource"],
                        "source": reference,
                        "framesPerSecond": sprite["framesPerSecond"],
                        "logicalWidth": sprite["logicalWidth"],
                        "logicalHeight": sprite["logicalHeight"],
                        "keyed": sprite["keyed"],
                        "translucent": sprite["translucent"],
                        "colorKey": sprite["colorKey"],
                        "frames": [frame["resource"] for frame in sprite["frames"]],
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            record["status"] = "compiled"
        elif binding["kind"] == "model" and reference in animation_path_models:
            convert_model(
                source_model=source,
                output_dir=output.parent,
                model_id=output.stem,
                textures=[],
                lod_index=0,
                export_mode="animation-path",
            )
            record["status"] = "converted-animation-path"
        else:
            record["status"] = "requires-model-export"
        imported.append(record)

    packaged_fxf = repository_root / "assets_dev/engine/effects/mm9/source/spells.fxf"
    packaged_fxf.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_fxf, packaged_fxf)
    library = compile_library(source_fxf, manifest_path, effect_names)
    library_path = repository_root / "assets_dev/engine/effects/mm9/library.yml"
    library_path.write_text(yaml.safe_dump(library, sort_keys=False), encoding="utf-8")
    report = {
        "schema": "openyamm.mm9EffectAssetImport.v1",
        "effects": effect_names,
        "sourceFxf": manifest["source"],
        "packagedFxf": packaged_fxf.relative_to(repository_root / "assets_dev").as_posix(),
        "resourceBindings": manifest_path.relative_to(repository_root / "assets_dev").as_posix(),
        "effectLibrary": library_path.relative_to(repository_root / "assets_dev").as_posix(),
        "resources": imported,
    }
    report_path = repository_root / "assets_dev/engine/effects/mm9/import/asset_import_report.yml"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    write_capability_report(
        packaged_fxf,
        manifest_path,
        library_path,
        repository_root / "assets_dev/engine/effects/mm9/capabilities.yml",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import modern packaged assets for selected MM9 FXF effects.")
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument(
        "--bindings",
        type=Path,
        default=Path("assets_dev/engine/effects/mm9/resource_bindings.yml"),
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--effect", action="append", help="Exact FXF group name; repeat as needed.")
    selection.add_argument(
        "--all-supported",
        action="store_true",
        help="Import every recipe whose components, resources, anchors, and models are currently supported.",
    )
    selection.add_argument("--restorations-only", action="store_true",
                           help="Install only the restoration manifest's textures; retain the existing effect library.")
    parser.add_argument("--native-textures", action="store_true",
                        help="Select original DTX-derived textures instead of restoration overlays.")
    args = parser.parse_args()
    bindings = args.bindings
    if not bindings.is_absolute():
        bindings = args.repository_root / bindings
    if args.restorations_only:
        document = yaml.safe_load(bindings.read_text(encoding="utf-8"))
        by_legacy = {binding["legacy"]: binding for binding in document["bindings"]}
        restorations = load_restorations(args.repository_root, by_legacy, verify_artwork=not args.native_textures)
        for binding in by_legacy.values():
            if binding["resource"] in restorations:
                restoration = None if args.native_textures else restorations[binding["resource"]]
                import_texture(args.repository_root, binding, restoration)
        print(f"Installed {len(restorations)} {'native' if args.native_textures else 'restored'} textures.")
        return 0
    effect_names = supported_effect_names(args.repository_root, bindings) if args.all_supported else args.effect
    report = import_effect_assets(args.repository_root, bindings, effect_names, args.native_textures)
    statuses: dict[str, int] = {}
    for resource in report["resources"]:
        statuses[resource["status"]] = statuses.get(resource["status"], 0) + 1
    print(yaml.safe_dump({"effects": effect_names, "resources": statuses}, sort_keys=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
