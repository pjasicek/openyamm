#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import sys

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "re_mm8" / "mm9_vfx"))

from inspect_assets import asset_index, read_dtx_header, read_fxf, read_sprite  # noqa: E402


HARD_CODED_EFFECT_SPRITES = (
    "sprites/bloodhit1.spr",
    "sprites/bloodspray1.spr",
)
# The projectile explosion "Sparks" (PROJECTILE.txt): cshell's base explosion skins its sphere with one of these
# (re_mm8/mm9_vfx/README.md, "Projectile explosions"); its spark shower uses weapons/blurredwhitestar's texture.
HARD_CODED_EXPLOSION_SPRITES = (
    "sprites/weapons/explosion1.spr",
)


def normalized_legacy_reference(reference: str) -> str:
    return reference.replace("\\", "/").lower()


def without_prefix(path: str, prefix: str) -> str:
    return path[len(prefix) :] if path.startswith(prefix) else path


def binding_target(reference: str) -> tuple[str, str, str]:
    suffix = PurePosixPath(reference).suffix.lower()
    if suffix == ".dtx":
        relative = without_prefix(reference, "spritetextures/")
        relative = str(PurePosixPath(relative).with_suffix(".png"))
        return "texture", f"mm9:effect-texture/{relative[:-4]}", f"engine/effects/mm9/textures/{relative}"
    if suffix == ".spr":
        relative = without_prefix(reference, "sprites/")
        relative = str(PurePosixPath(relative).with_suffix(".yml"))
        return "sprite", f"mm9:effect-sprite/{relative[:-4]}", f"engine/effects/mm9/sprites/{relative}"
    if suffix == ".abc":
        relative = without_prefix(reference, "models/")
        relative = str(PurePosixPath(relative).with_suffix(".glb"))
        return "model", f"mm9:model/{relative[:-4]}", f"engine/effects/mm9/models/{relative}"
    if suffix == ".wav":
        relative = without_prefix(reference, "sounds/")
        return "sound", f"mm9:sound/{relative[:-4]}", f"engine/effects/mm9/audio/{relative}"
    raise ValueError(f"unsupported effect resource reference: {reference}")


def fingerprint(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def collect_references(groups: list[dict]) -> list[str]:
    references = set()
    for group in groups:
        for key in group["keys"]:
            for prop in key["properties"]:
                if prop["type"] != 7 or prop["value"].endswith("|..."):
                    continue
                value = prop["value"].split("|", 1)[-1]
                references.add(normalized_legacy_reference(value))
    return sorted(references)


def generate_bindings(original_root: Path) -> dict:
    extracted = original_root / "extracted"
    fxf_path = extracted / "CLIENTFX" / "CLIENTFX" / "SPELLS.fxf"
    groups = read_fxf(fxf_path)
    source_assets = asset_index(extracted)
    bindings = []

    def make_binding(reference: str) -> dict:
        kind, resource_id, asset_path = binding_target(reference)
        source_path = source_assets.get(reference)
        binding = {
            "legacy": reference,
            "kind": kind,
            "resource": resource_id,
            "asset": asset_path,
            "status": "bound" if source_path is not None else "missing-source",
        }
        if source_path is not None:
            binding["source"] = fingerprint(source_path)
        return binding

    known_bindings: dict[str, dict] = {}

    def add_binding(reference: str, origin: str) -> None:
        if reference in known_bindings:
            return
        binding = make_binding(reference)
        binding["origin"] = origin
        known_bindings[reference] = binding
        bindings.append(binding)
        if binding["kind"] != "sprite" or binding["status"] != "bound":
            return
        sprite = read_sprite(source_assets[reference])
        frame_bindings = []
        frame_dimensions = set()
        for frame_index, raw_frame in enumerate(sprite["frames"]):
            frame_reference = normalized_legacy_reference(raw_frame)
            frame_binding = known_bindings.get(frame_reference)
            if frame_binding is None:
                frame_binding = make_binding(frame_reference)
                frame_binding["origin"] = origin
                known_bindings[frame_reference] = frame_binding
                bindings.append(frame_binding)
            if frame_binding["status"] == "bound":
                header = read_dtx_header(source_assets[frame_reference])
                frame_dimensions.add((header["width"], header["height"]))
            frame_bindings.append(
                {
                    "index": frame_index,
                    "legacy": frame_reference,
                    "resource": frame_binding["resource"],
                }
            )
        if len(frame_dimensions) != 1:
            raise ValueError(
                f"effect sprite {reference} must have one logical frame size, found {sorted(frame_dimensions)}"
            )
        logical_width, logical_height = frame_dimensions.pop()
        binding["sprite"] = {
            "framesPerSecond": sprite["fps"],
            "logicalWidth": logical_width,
            "logicalHeight": logical_height,
            "keyed": bool(sprite["keyed"]),
            "translucent": bool(sprite["translucent"]),
            "colorKey": sprite["color_key"],
            "frames": frame_bindings,
        }

    for reference in collect_references(groups):
        add_binding(reference, "spells_fxf")
    for reference in HARD_CODED_EFFECT_SPRITES:
        add_binding(reference, "hardcoded_melee_contact")
    for reference in HARD_CODED_EXPLOSION_SPRITES:
        add_binding(reference, "hardcoded_projectile_explosion")

    bindings.sort(key=lambda value: value["legacy"])
    missing = [binding["legacy"] for binding in bindings if binding["status"] != "bound"]
    return {
        "schema": "openyamm.effectResourceBindings.v1",
        "namespace": "mm9",
        "source": fingerprint(fxf_path),
        "supplementalSources": {
            "hardcodedMeleeContact": {
                "evidence": "re_mm8/mm9_vfx/MELEE_HIT_EFFECTS.md",
                "sprites": list(HARD_CODED_EFFECT_SPRITES),
            },
            "hardcodedProjectileExplosion": {
                "evidence": "re_mm8/mm9_vfx/README.md",
                "sprites": list(HARD_CODED_EXPLOSION_SPRITES),
            },
        },
        "rules": {
            "lookup": "exact normalized legacy reference",
            "case": "ASCII lowercase",
            "extensionGuessing": False,
            "externalFallback": False,
        },
        "summary": {
            "effectGroups": len(groups),
            "effectKeys": sum(len(group["keys"]) for group in groups),
            "bindings": len(bindings),
            "missingSources": len(missing),
        },
        "missingSources": missing,
        "bindings": bindings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate exact MM9 FXF/SPR to packaged-resource bindings.")
    parser.add_argument("--original-root", type=Path, default=Path("mm9"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets_dev/engine/effects/mm9/resource_bindings.yml"),
    )
    args = parser.parse_args()

    manifest = generate_bindings(args.original_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    print(
        f"{manifest['summary']['bindings']} bindings, "
        f"{manifest['summary']['missingSources']} missing sources: {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
