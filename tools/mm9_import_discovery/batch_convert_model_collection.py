#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from convert_abc_model import TextureInput, convert_model, read_abc
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


CATEGORY_MAP = {
    "GIBS": "gibs",
    "MODELPROPS": "modelprops",
    "PICKUPITEMS": "pickups",
    "PLAYER": "player",
    "PROJECTILES": "projectiles",
    "PROPS": "props",
    "SAVE": "save",
    "SPELLS": "spells",
    "WEAPONS": "weapons",
}


@dataclass
class TextureResolution:
    material_index: int
    source: Path | None
    texture_id: str
    candidates: list[Path] = field(default_factory=list)
    version: int | None = None
    bpp: int | None = None
    warning: str | None = None
    error: str | None = None


@dataclass
class ModelJob:
    source: Path
    relative: Path
    category: str
    output_dir: Path
    model_id: str
    variant_id: str = ""
    piece_materials: dict[int, list[str]] = field(default_factory=dict)
    textures: list[TextureResolution] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    converted: bool = False


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


def index_skins(root: Path) -> dict[str, list[Path]]:
    indexed: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*.dtx"):
        indexed[path.name.lower()].append(path)
    for paths in indexed.values():
        paths.sort(key=lambda value: (len(value.parts), str(value).lower()))
    return indexed


def index_skin_paths(root: Path) -> dict[str, Path]:
    indexed = {}
    for path in root.rglob("*.dtx"):
        indexed[path.relative_to(root).as_posix().lower()] = path
    return indexed


def read_dtx_info(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return struct.unpack_from("<i", data, 4)[0], struct.unpack_from("<12B", data, 24)[2]


def texture_id_for(path: Path) -> str:
    return slug(path.stem)


def output_subpath(relative: Path) -> Path:
    parts = relative.parent.parts
    return Path(*[slug(part) for part in parts]) if parts else Path()


def source_model_ref(relative: Path) -> str:
    return "models/" + relative.as_posix().lower()


def category_for(relative: Path) -> str | None:
    if len(relative.parts) == 1:
        return "root"
    if len(relative.parts) < 2:
        return None
    return CATEGORY_MAP.get(relative.parts[0].upper())


def exact_skin_candidate(skins_root: Path, relative: Path) -> Path:
    return skins_root / relative.with_suffix(".dtx")


def candidate_from_piece_name(
    skin_index: dict[str, list[Path]],
    piece_names: list[str],
) -> list[Path]:
    candidates = []
    seen = set()
    for piece_name in piece_names:
        key = f"{piece_name}.dtx".lower()
        for path in skin_index.get(key, []):
            if path not in seen:
                candidates.append(path)
                seen.add(path)
    return candidates


def candidate_from_model_name(skin_index: dict[str, list[Path]], relative: Path) -> list[Path]:
    return skin_index.get(f"{relative.stem}.dtx".lower(), [])


def normalized_model_key(source_model: str) -> str | None:
    value = source_model.replace("\\", "/").strip()
    lower = value.lower()
    if lower.startswith("models/"):
        value = value[len("models/") :]
    if not value.lower().endswith(".abc"):
        return None
    return value.lower()


def source_skin_path(skin_paths: dict[str, Path], source_skin: str) -> Path | None:
    value = source_skin.replace("\\", "/").strip()
    lower = value.lower()
    if lower.startswith("skins/"):
        value = value[len("skins/") :]
    if not value.lower().endswith(".dtx"):
        return None
    return skin_paths.get(value.lower())


def collect_scene_skin_defaults(map_root: Path, skins_root: Path) -> dict[str, list[Path]]:
    counts: dict[str, Counter[tuple[str, ...]]] = defaultdict(Counter)
    skin_path_index = index_skin_paths(skins_root)
    for scene_path in sorted(map_root.glob("*.scene.yml")):
        data = yaml.safe_load(scene_path.read_text(encoding="utf-8")) or {}
        for instance in data.get("model_instances", []):
            model_key = normalized_model_key(str(instance.get("source_model", "")))
            source_skin = str(instance.get("source_skin", "")).strip()
            if model_key is None or not source_skin:
                continue
            resolved_skin_paths = []
            for raw_skin in source_skin.split(";"):
                skin_path = source_skin_path(skin_path_index, raw_skin)
                if skin_path is not None:
                    resolved_skin_paths.append(str(skin_path))
            if resolved_skin_paths:
                counts[model_key][tuple(resolved_skin_paths)] += 1

    defaults = {}
    for model_key, variants in counts.items():
        skin_paths, _ = variants.most_common(1)[0]
        defaults[model_key] = [Path(path) for path in skin_paths]
    return defaults


def candidate_from_scene_skin_default(
    scene_skin_defaults: dict[str, list[Path]],
    relative: Path,
    material_index: int,
) -> list[Path]:
    skin_paths = scene_skin_defaults.get(relative.as_posix().lower(), [])
    if material_index >= len(skin_paths):
        return []
    return [skin_paths[material_index]]


def resolve_texture_for_material(
    job: ModelJob,
    material_index: int,
    skins_root: Path,
    skin_index: dict[str, list[Path]],
    scene_skin_defaults: dict[str, list[Path]],
) -> TextureResolution:
    candidates = []
    exact = exact_skin_candidate(skins_root, job.relative)
    if material_index == 0 and exact.exists():
        candidates.append(exact)

    if material_index == 0:
        candidates.extend(candidate_from_model_name(skin_index, job.relative))

    candidates.extend(candidate_from_piece_name(skin_index, job.piece_materials.get(material_index, [])))
    candidates.extend(candidate_from_scene_skin_default(scene_skin_defaults, job.relative, material_index))

    deduped = []
    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            deduped.append(candidate)
            seen.add(candidate)

    if not deduped:
        return TextureResolution(
            material_index=material_index,
            source=None,
            texture_id=f"{job.model_id}_{material_index}",
            warning="missing texture",
        )

    chosen = deduped[0]
    result = TextureResolution(
        material_index=material_index,
        source=chosen,
        texture_id=texture_id_for(chosen),
        candidates=deduped,
    )
    if len(deduped) > 1:
        result.warning = "multiple texture candidates; chose " + str(chosen)
    try:
        result.version, result.bpp = read_dtx_info(chosen)
    except Exception as error:
        result.error = f"failed to read DTX header: {error}"
    return result


def build_jobs(
    models_root: Path,
    skins_root: Path,
    output_root: Path,
    categories: set[str] | None,
    map_root: Path,
) -> list[ModelJob]:
    skin_index = index_skins(skins_root)
    scene_skin_defaults = collect_scene_skin_defaults(map_root, skins_root)
    jobs = []
    for source in sorted(models_root.rglob("*.abc")):
        relative = source.relative_to(models_root)
        category = category_for(relative)
        if category is None:
            continue
        if categories is not None and category not in categories:
            continue

        subpath = output_subpath(relative)
        model_id = slug(relative.stem)
        model_dir = output_root / subpath
        job = ModelJob(
            source=source,
            relative=relative,
            category=category,
            output_dir=model_dir,
            model_id=model_id,
        )

        try:
            model = read_abc(source)
            for piece in model.pieces:
                job.piece_materials.setdefault(piece.material_index, []).append(piece.name)
            for material_index in sorted(job.piece_materials):
                texture = resolve_texture_for_material(
                    job,
                    material_index,
                    skins_root,
                    skin_index,
                    scene_skin_defaults,
                )
                job.textures.append(texture)
                if texture.warning:
                    job.warnings.append(f"material {material_index}: {texture.warning}")
                if texture.error:
                    job.errors.append(f"material {material_index}: {texture.error}")
            job.variant_id = model_id
            job.output_dir = model_dir
        except Exception as error:
            job.errors.append(f"failed to read model: {error}")
            job.variant_id = model_id
        jobs.append(job)
    return jobs


def convert_job(
    job: ModelJob,
    lod: int,
    shared_skins_dir: Path,
    source_skins_root: Path,
    coordinate_scale: float,
) -> None:
    sidecar_path = job.output_dir / f"{job.model_id}.model.yml"
    if sidecar_path.exists():
        sidecar = yaml.safe_load(sidecar_path.read_text(encoding="utf-8")) or {}
        if "actor_model" in (sidecar.get("roles") or []):
            job.converted = True
            job.warnings.append("already converted by actor table; preserved actor sidecar")
            return

    if job.errors:
        return

    textures = [
        TextureInput(
            material_index=texture.material_index,
            source=texture.source,
            texture_id=texture.texture_id,
        )
        for texture in job.textures
        if texture.source is not None and texture.error is None
    ]
    convert_model(
        source_model=job.source,
        output_dir=job.output_dir,
        model_id=job.variant_id,
        textures=textures,
        lod_index=lod,
        shared_skins_dir=shared_skins_dir,
        preview_skins_dir=shared_skins_dir.parent / "skins_preview",
        source_skins_root=source_skins_root,
        coordinate_scale=coordinate_scale,
    )
    if sidecar_path.exists():
        sidecar = yaml.safe_load(sidecar_path.read_text(encoding="utf-8")) or {}
        sidecar["roles"] = sorted(set(sidecar.get("roles") or []) | {model_kind_for(job.category)})
        sidecar["source_model"] = source_model_ref(job.relative)
        sidecar_path.write_text(yaml.safe_dump(sidecar, sort_keys=False), encoding="utf-8")
    job.converted = True


def job_report(job: ModelJob) -> dict:
    return {
        "source": str(job.source),
        "relative": str(job.relative),
        "category": job.category,
        "outputDir": str(job.output_dir),
        "modelId": job.model_id,
        "variantId": job.variant_id,
        "pieceMaterials": job.piece_materials,
        "textures": [
            {
                "materialIndex": texture.material_index,
                "path": str(texture.source) if texture.source is not None else None,
                "textureId": texture.texture_id,
                "candidates": [str(candidate) for candidate in texture.candidates],
                "version": texture.version,
                "bpp": texture.bpp,
                "warning": texture.warning,
                "error": texture.error,
            }
            for texture in job.textures
        ],
        "warnings": job.warnings,
        "errors": job.errors,
        "converted": job.converted,
    }


def write_report(path: Path, jobs: list[ModelJob]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "openyamm.mm9ModelCollectionBatchReport.v1",
        "summary": {
            "models": len(jobs),
            "converted": sum(1 for job in jobs if job.converted),
            "withWarnings": sum(1 for job in jobs if job.warnings),
            "withErrors": sum(1 for job in jobs if job.errors),
        },
        "jobs": [job_report(job) for job in jobs],
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def model_kind_for(category: str) -> str:
    return "static_model"


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-convert non-actor MM9 ABC model collections.")
    parser.add_argument("--models-root", type=Path, default=Path("mm9/extracted/MODELS/MODELS"))
    parser.add_argument("--skins-root", type=Path, default=Path("mm9/extracted/SKINS/SKINS"))
    parser.add_argument("--map-root", type=Path, default=Path("assets_dev/worlds/mm9/maps"))
    parser.add_argument("--output-root", type=Path, default=Path("assets_dev/worlds/mm9/models"))
    parser.add_argument("--world-root", type=Path, default=Path("assets_dev/worlds/mm9"))
    parser.add_argument("--shared-skins-dir", type=Path, default=Path("assets_dev/worlds/mm9/skins"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("assets_dev/worlds/mm9/models/import/model_collection_batch_report.yml"),
    )
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--lod", type=int, default=0)
    parser.add_argument(
        "--scale",
        type=float,
        default=MM9_TO_OPENYAMM_COORDINATE_SCALE,
        help="Coordinate scale from LithTech units to OpenYAMM units.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--category",
        action="append",
        choices=sorted(set(CATEGORY_MAP.values()) | {"root"}),
        help="Restrict conversion to one or more normalized categories.",
    )
    args = parser.parse_args()

    categories = set(args.category) if args.category else None
    jobs = build_jobs(args.models_root, args.skins_root, args.output_root, categories, args.map_root)
    if args.limit is not None:
        jobs = jobs[: args.limit]

    if not args.report_only:
        for job in jobs:
            try:
                convert_job(job, args.lod, args.shared_skins_dir, args.skins_root, args.scale)
            except Exception as error:
                job.errors.append(f"conversion failed: {error}")

    write_report(args.report, jobs)
    print(
        f"{len(jobs)} models, {sum(1 for job in jobs if job.converted)} converted, "
        f"{sum(1 for job in jobs if job.errors)} with errors, "
        f"{sum(1 for job in jobs if job.warnings)} with warnings"
    )
    print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
