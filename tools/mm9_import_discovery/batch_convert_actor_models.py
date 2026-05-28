#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from convert_abc_model import DTX_BPP_8P, DTX_BPP_32, DTX_BPP_DXT1, DTX_BPP_DXT3, DTX_BPP_DXT5
from convert_abc_model import TextureInput, convert_model, read_abc, write_yaml
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


SKIN_COLUMNS = ["SkinName", "SkinName2", "SkinName3"]
SUPPORTED_DTX_BPP = {DTX_BPP_8P, DTX_BPP_32, DTX_BPP_DXT1, DTX_BPP_DXT3, DTX_BPP_DXT5}


def source_model_ref(model_name: str) -> str:
    return f"models/{Path(model_name).name.lower()}"


def source_skin_ref(source: Path, skins_root: Path) -> str:
    try:
        return "skins/" + source.resolve().relative_to(skins_root.resolve()).as_posix().lower()
    except ValueError:
        return "skins/" + source.name.lower()


@dataclass
class SourceRow:
    table_name: str
    row_number: int
    number: str
    name: str
    model_name: str
    skins: list[str]
    base_name: str
    type_picture: str


@dataclass
class ResolvedTexture:
    material_index: int
    table_name: str
    source: Path | None
    texture_id: str
    version: int | None = None
    bpp: int | None = None
    error: str | None = None


@dataclass
class Variant:
    model_name: str
    skins: tuple[str, ...]
    rows: list[SourceRow] = field(default_factory=list)
    model_path: Path | None = None
    output_dir: Path | None = None
    model_id: str = ""
    variant_id: str = ""
    textures: list[ResolvedTexture] = field(default_factory=list)
    material_indices: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    converted: bool = False


def clean_field(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    return "" if value == "0" else value


def slug(value: str) -> str:
    output = []
    previous_underscore = False
    for char in value.lower():
        if char.isalnum():
            output.append(char)
            previous_underscore = False
        else:
            if not previous_underscore:
                output.append("_")
                previous_underscore = True
    return "".join(output).strip("_")


def stem_id(filename: str) -> str:
    return slug(Path(filename).stem)


def read_actor_rows(table_path: Path, table_name: str) -> list[SourceRow]:
    rows = []
    with table_path.open(newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row_number, row in enumerate(reader, start=2):
            model_name = clean_field(row.get("ModelName"))
            if not model_name:
                continue
            skins = [clean_field(row.get(column)) for column in SKIN_COLUMNS]
            while skins and not skins[-1]:
                skins.pop()
            rows.append(
                SourceRow(
                    table_name=table_name,
                    row_number=row_number,
                    number=clean_field(row.get("Number")),
                    name=clean_field(row.get("Monster Name")),
                    model_name=model_name,
                    skins=skins,
                    base_name=clean_field(row.get("BaseName")),
                    type_picture=clean_field(row.get("Type/Picture")),
                )
            )
    return rows


def index_files(root: Path, suffix: str) -> dict[str, list[Path]]:
    indexed: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob(f"*{suffix}"):
        indexed[path.name.lower()].append(path)
    for paths in indexed.values():
        paths.sort(key=lambda value: (len(value.parts), str(value).lower()))
    return indexed


def resolve_indexed(index: dict[str, list[Path]], name: str) -> tuple[Path | None, list[Path]]:
    candidates = index.get(name.lower(), [])
    if not candidates:
        return None, []
    return candidates[0], candidates


def read_dtx_info(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    version = struct.unpack_from("<i", data, 4)[0]
    bpp = struct.unpack_from("<12B", data, 24)[2]
    return version, bpp


def build_variants(rows: list[SourceRow]) -> list[Variant]:
    variants: dict[tuple[str, tuple[str, ...]], Variant] = {}
    for row in rows:
        key = (row.model_name.lower(), tuple(skin.lower() for skin in row.skins))
        if key not in variants:
            variants[key] = Variant(model_name=row.model_name, skins=tuple(row.skins))
        variants[key].rows.append(row)
    return sorted(variants.values(), key=lambda value: (value.model_name.lower(), value.skins))


def assign_output_paths(variants: list[Variant], output_root: Path) -> None:
    by_model: dict[str, list[Variant]] = defaultdict(list)
    for variant in variants:
        variant.model_id = stem_id(variant.model_name)
        skin_part = "_".join(stem_id(skin) for skin in variant.skins if skin)
        variant.variant_id = variant.model_id if not skin_part else f"{variant.model_id}_{skin_part}"
        by_model[variant.model_id].append(variant)

    for model_id, model_variants in by_model.items():
        for variant in model_variants:
            variant.output_dir = output_root


def resolve_variant(
    variant: Variant,
    model_index: dict[str, list[Path]],
    skin_index: dict[str, list[Path]],
) -> None:
    model_path, model_candidates = resolve_indexed(model_index, variant.model_name)
    variant.model_path = model_path
    if model_path is None:
        variant.errors.append(f"missing model {variant.model_name}")
        return
    if len(model_candidates) > 1:
        variant.warnings.append(
            "duplicate model basename candidates: " + ", ".join(str(path) for path in model_candidates)
        )

    try:
        model = read_abc(model_path)
        variant.material_indices = sorted({piece.material_index for piece in model.pieces})
    except Exception as error:
        variant.errors.append(f"failed to read model: {error}")
        return

    effective_skins = list(variant.skins)
    if not effective_skins and variant.material_indices:
        fallback_skin = Path(variant.model_name).with_suffix(".dtx").name
        fallback_path, fallback_candidates = resolve_indexed(skin_index, fallback_skin)
        if fallback_path is not None:
            effective_skins = [fallback_skin]
            variant.warnings.append(f"using model-name texture fallback {fallback_skin}")
            if len(fallback_candidates) > 1:
                variant.warnings.append(
                    "duplicate texture basename candidates for "
                    + fallback_skin
                    + ": "
                    + ", ".join(str(path) for path in fallback_candidates)
                )

    for material_index, skin_name in enumerate(effective_skins):
        if not skin_name:
            continue
        texture_path, texture_candidates = resolve_indexed(skin_index, skin_name)
        texture = ResolvedTexture(
            material_index=material_index,
            table_name=skin_name,
            source=texture_path,
            texture_id=stem_id(skin_name),
        )
        if texture_path is None:
            texture.error = f"missing texture {skin_name}"
            variant.errors.append(texture.error)
        else:
            if len(texture_candidates) > 1:
                variant.warnings.append(
                    "duplicate texture basename candidates for "
                    + skin_name
                    + ": "
                    + ", ".join(str(path) for path in texture_candidates)
                )
            try:
                texture.version, texture.bpp = read_dtx_info(texture_path)
                if texture.version != -5 or texture.bpp not in SUPPORTED_DTX_BPP:
                    texture.error = f"unsupported DTX version/bpp {texture.version}/{texture.bpp}"
                    variant.errors.append(f"{skin_name}: {texture.error}")
            except Exception as error:
                texture.error = f"failed to read texture header: {error}"
                variant.errors.append(f"{skin_name}: {texture.error}")
        variant.textures.append(texture)

    supplied_materials = {texture.material_index for texture in variant.textures if texture.source is not None}
    used_materials = set(variant.material_indices)
    missing_materials = sorted(used_materials - supplied_materials)
    if missing_materials:
        if variant.skins or supplied_materials:
            variant.errors.append(f"model uses material indices without resolved skins: {missing_materials}")
        else:
            variant.errors.append(
                "missing actor skin binding for material indices "
                + str(missing_materials)
                + "; no table skins or exact model-name DTX fallback"
            )

    extra_materials = sorted(supplied_materials - used_materials)
    if extra_materials:
        variant.warnings.append(f"table provides skins for unused material indices: {extra_materials}")


def convert_variant(
    variant: Variant,
    lod_index: int,
    shared_skins_dir: Path,
    source_skins_root: Path,
    coordinate_scale: float,
) -> None:
    if variant.model_path is None or variant.output_dir is None or variant.errors:
        return

    textures = [
        TextureInput(
            material_index=texture.material_index,
            source=texture.source,
            texture_id=texture.texture_id,
        )
        for texture in variant.textures
        if texture.source is not None and texture.error is None
    ]
    convert_model(
        source_model=variant.model_path,
        output_dir=variant.output_dir,
        model_id=variant.model_id,
        textures=textures,
        lod_index=lod_index,
        shared_skins_dir=shared_skins_dir,
        preview_skins_dir=shared_skins_dir.parent / "skins_preview",
        source_skins_root=source_skins_root,
        coordinate_scale=coordinate_scale,
    )
    variant.converted = True


def convert_models(
    variants: list[Variant],
    lod_index: int,
    shared_skins_dir: Path,
    source_skins_root: Path,
    coordinate_scale: float,
) -> None:
    by_model: dict[str, list[Variant]] = defaultdict(list)
    for variant in variants:
        by_model[variant.model_id].append(variant)

    for model_variants in by_model.values():
        conversion_source = next(
            (
                variant
                for variant in model_variants
                if variant.model_path is not None and variant.output_dir is not None and not variant.errors
            ),
            None,
        )
        if conversion_source is None:
            continue
        convert_variant(conversion_source, lod_index, shared_skins_dir, source_skins_root, coordinate_scale)
        for variant in model_variants:
            if variant.model_path == conversion_source.model_path:
                variant.converted = True


def variant_report(variant: Variant) -> dict:
    return {
        "modelName": variant.model_name,
        "skins": list(variant.skins),
        "modelPath": str(variant.model_path) if variant.model_path is not None else None,
        "outputDir": str(variant.output_dir) if variant.output_dir is not None else None,
        "modelId": variant.model_id,
        "variantId": variant.variant_id,
        "materials": variant.material_indices,
        "textures": [
            {
                "materialIndex": texture.material_index,
                "tableName": texture.table_name,
                "path": str(texture.source) if texture.source is not None else None,
                "textureId": texture.texture_id,
                "version": texture.version,
                "bpp": texture.bpp,
                "error": texture.error,
            }
            for texture in variant.textures
        ],
        "rows": [
            {
                "table": row.table_name,
                "row": row.row_number,
                "number": row.number,
                "name": row.name,
                "baseName": row.base_name,
                "typePicture": row.type_picture,
            }
            for row in variant.rows
        ],
        "warnings": variant.warnings,
        "errors": variant.errors,
        "converted": variant.converted,
    }


def write_report(path: Path, table_path: Path, variants: list[Variant]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "openyamm.mm9ActorModelBatchReport.v1",
        "table": str(table_path),
        "summary": {
            "variants": len(variants),
            "converted": sum(1 for variant in variants if variant.converted),
            "withWarnings": sum(1 for variant in variants if variant.warnings),
            "withErrors": sum(1 for variant in variants if variant.errors),
        },
        "variants": [variant_report(variant) for variant in variants],
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def write_model_sidecar_bindings(output_root: Path, skins_root: Path, variants: list[Variant]) -> None:
    by_model: dict[str, list[Variant]] = defaultdict(list)
    for variant in variants:
        if variant.converted and variant.output_dir is not None:
            by_model[variant.model_id].append(variant)

    for model_id, model_variants in sorted(by_model.items()):
        first = model_variants[0]
        sidecar_path = output_root / f"{model_id}.model.yml"
        if not sidecar_path.exists():
            continue
        sidecar = yaml.safe_load(sidecar_path.read_text(encoding="utf-8")) or {}
        sidecar["roles"] = sorted(set(sidecar.get("roles") or []) | {"actor_model"})
        sidecar["source_model"] = source_model_ref(first.model_name)
        sidecar["source_tables"] = sorted({str(row.table_name) for variant in model_variants for row in variant.rows})
        sidecar["skin_bindings"] = []
        for variant in sorted(model_variants, key=lambda value: value.variant_id):
            sidecar["skin_bindings"].append(
                {
                    "id": variant.variant_id,
                    "source_skins": [
                        source_skin_ref(texture.source, skins_root)
                        for texture in variant.textures
                        if texture.source is not None and texture.error is None
                    ],
                    "actor_rows": [
                        {
                            "table": row.table_name,
                            "row": row.row_number,
                            "number": row.number,
                            "monster_name": row.name,
                            "type_picture": row.type_picture,
                            "base_name": row.base_name,
                        }
                        for row in variant.rows
                    ],
                }
            )
        write_yaml(sidecar_path, sidecar)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-convert MM9 actor model variants from ACTOR/MONSTERS tables.")
    parser.add_argument(
        "--table",
        type=Path,
        action="append",
        help="Input tab-delimited actor table. Defaults to ACTOR.txt and MONSTERS.txt.",
    )
    parser.add_argument(
        "--models-root",
        type=Path,
        default=Path("mm9/extracted/MODELS/MODELS"),
        help="Root containing extracted .abc model files.",
    )
    parser.add_argument(
        "--skins-root",
        type=Path,
        default=Path("mm9/extracted/SKINS/SKINS"),
        help="Root containing extracted .dtx skin files.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("assets_dev/worlds/mm9/models"),
        help="Output source-shaped model root.",
    )
    parser.add_argument("--world-root", type=Path, default=Path("assets_dev/worlds/mm9"))
    parser.add_argument(
        "--shared-skins-dir",
        type=Path,
        default=Path("assets_dev/worlds/mm9/skins"),
        help="World-level runtime DTX skin root.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("assets_dev/worlds/mm9/models/import/actor_batch_report.yml"),
        help="Output batch report.",
    )
    parser.add_argument("--report-only", action="store_true", help="Resolve and report without converting.")
    parser.add_argument("--lod", type=int, default=0, help="LOD index to export.")
    parser.add_argument(
        "--scale",
        type=float,
        default=MM9_TO_OPENYAMM_COORDINATE_SCALE,
        help="Coordinate scale from LithTech units to OpenYAMM units.",
    )
    parser.add_argument("--limit", type=int, help="Convert/report only the first N variants after filtering.")
    parser.add_argument(
        "--model",
        action="append",
        help="Optional model filename or stem filter. Can be passed multiple times.",
    )
    args = parser.parse_args()

    tables = args.table or [Path("mm9/extracted/DATA/DATA/ACTOR.txt"), Path("mm9/extracted/DATA/DATA/MONSTERS.txt")]
    rows = []
    for table_path in tables:
        rows.extend(read_actor_rows(table_path, table_path.stem.upper()))
    variants = build_variants(rows)
    if args.model:
        allowed = {value.lower() for value in args.model}
        allowed.update({Path(value).stem.lower() for value in args.model})
        variants = [
            variant
            for variant in variants
            if variant.model_name.lower() in allowed or Path(variant.model_name).stem.lower() in allowed
        ]
    if args.limit is not None:
        variants = variants[: args.limit]

    assign_output_paths(variants, args.output_root)
    model_index = index_files(args.models_root, ".abc")
    skin_index = index_files(args.skins_root, ".dtx")

    for variant in variants:
        resolve_variant(variant, model_index, skin_index)

    if not args.report_only:
        try:
            convert_models(variants, args.lod, args.shared_skins_dir, args.skins_root, args.scale)
        except Exception as error:
            for variant in variants:
                if not variant.converted:
                    variant.errors.append(f"conversion failed: {error}")
        write_model_sidecar_bindings(args.output_root, args.skins_root, variants)

    write_report(args.report, Path(";".join(str(table) for table in tables)), variants)
    print(
        f"{len(tables)} tables: {len(variants)} variants, "
        f"{sum(1 for variant in variants if variant.converted)} converted, "
        f"{sum(1 for variant in variants if variant.errors)} with errors, "
        f"{sum(1 for variant in variants if variant.warnings)} with warnings"
    )
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
