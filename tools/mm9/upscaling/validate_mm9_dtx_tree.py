#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MM9_TOOLS_DIR = REPO_ROOT / "tools" / "mm9_import_discovery"
sys.path.insert(0, SCRIPT_DIR.as_posix())
sys.path.insert(0, MM9_TOOLS_DIR.as_posix())

from convert_abc_model import decode_dtx  # noqa: E402
from upscale_mm9_dtx import DTX_HEADER_SIZE, read_dtx  # noqa: E402


SOURCE_TO_X4_ROOTS = {
    "textures": "textures_x4",
    "sprite_textures": "sprite_textures_x4",
    "skins": "skins_x4",
}


@dataclass
class ValidationIssue:
    path: Path
    message: str


def parse_dtx_sections(path: Path, data: bytes, payload_end: int, section_count: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    offset = payload_end

    for section_index in range(section_count):
        if offset + 29 > len(data):
            issues.append(ValidationIssue(path, f"truncated section header {section_index}"))
            return issues

        payload_size = struct.unpack_from("<I", data, offset + 25)[0]
        offset += 29
        if offset + payload_size > len(data):
            issues.append(ValidationIssue(path, f"truncated section payload {section_index}"))
            return issues
        offset += payload_size

    if offset != len(data):
        issues.append(ValidationIssue(path, f"{len(data) - offset} trailing bytes after mip payload/sections"))

    return issues


def validate_dtx_file(path: Path, decode: bool, strict_sections: bool) -> tuple[int, int, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []

    try:
        dtx = read_dtx(path)
    except Exception as error:
        return 0, 0, [ValidationIssue(path, str(error))]

    if strict_sections:
        payload_end = DTX_HEADER_SIZE + dtx.mip_payload_size
        issues.extend(parse_dtx_sections(path, dtx.data, payload_end, dtx.header.section_count))

    if decode:
        try:
            if dtx.header.version == -5:
                image = decode_dtx(path)
            else:
                from upscale_mm9_dtx import decode_source_dtx

                image = decode_source_dtx(dtx)
            if image.size != (dtx.header.width, dtx.header.height):
                issues.append(
                    ValidationIssue(
                        path,
                        f"decoded size {image.width}x{image.height} != header "
                        f"{dtx.header.width}x{dtx.header.height}",
                    ),
                )
        except Exception as error:
            issues.append(ValidationIssue(path, f"decode failed: {error}"))

    return dtx.header.width, dtx.header.height, issues


def collect_dtx_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix.lower() == ".dtx":
            files.append(root)
        elif root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".dtx")
    return sorted(files, key=lambda path: path.as_posix().lower())


def expected_output_path(source_root: Path, source_path: Path) -> Path:
    relative = source_path.relative_to(source_root)
    destination_root_name = SOURCE_TO_X4_ROOTS[source_root.name]
    return source_root.parent / destination_root_name / relative


def validate_counterparts(args: argparse.Namespace, issues: list[ValidationIssue]) -> None:
    source_base = args.source_root
    for source_name in SOURCE_TO_X4_ROOTS:
        source_root = source_base / source_name
        if not source_root.exists():
            issues.append(ValidationIssue(source_root, "source root is missing"))
            continue

        for source_path in collect_dtx_files([source_root]):
            output_path = expected_output_path(source_root, source_path)
            if not output_path.exists():
                issues.append(ValidationIssue(output_path, f"missing x{args.scale} counterpart for {source_path}"))
                continue

            source_width, source_height, source_issues = validate_dtx_file(
                source_path,
                args.decode_source,
                args.strict_sections,
            )
            output_width, output_height, output_issues = validate_dtx_file(
                output_path,
                args.decode,
                args.strict_sections,
            )
            issues.extend(source_issues)
            issues.extend(output_issues)

            if source_width > 0 and output_width != source_width * args.scale:
                issues.append(
                    ValidationIssue(output_path, f"width {output_width} != source width {source_width} * {args.scale}"),
                )
            if source_height > 0 and output_height != source_height * args.scale:
                issues.append(
                    ValidationIssue(
                        output_path,
                        f"height {output_height} != source height {source_height} * {args.scale}",
                    ),
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MM9 LithTech DTX files and optional x4 output trees.")
    parser.add_argument(
        "roots",
        nargs="*",
        type=Path,
        help="DTX files or directories to validate. Defaults to existing MM9 source x4 roots.",
    )
    parser.add_argument("--source-root", type=Path, default=Path("assets_dev/worlds/mm9/source"))
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument(
        "--check-counterparts",
        action="store_true",
        help="Require textures_x4/sprite_textures_x4/skins_x4 counterparts for every source DTX.",
    )
    parser.add_argument("--decode", action="store_true", help="Decode each validated output DTX base image.")
    parser.add_argument("--decode-source", action="store_true", help="Decode source DTX files while checking pairs.")
    parser.add_argument("--strict-sections", action="store_true", help="Also parse DTX tail sections strictly.")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    roots = args.roots
    if not roots and not args.check_counterparts:
        roots = [args.source_root / output_name for output_name in SOURCE_TO_X4_ROOTS.values()]

    issues: list[ValidationIssue] = []

    for path in collect_dtx_files(roots):
        _width, _height, file_issues = validate_dtx_file(path, args.decode, args.strict_sections)
        issues.extend(file_issues)

    if args.check_counterparts:
        validate_counterparts(args, issues)

    if issues:
        for issue in issues[:200]:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        if len(issues) > 200:
            print(f"... {len(issues) - 200} more issues", file=sys.stderr)
        raise SystemExit(1)

    if not args.quiet:
        checked = len(collect_dtx_files(roots))
        print(f"validated {checked} DTX files")
        if args.check_counterparts:
            print(f"validated x{args.scale} counterparts under {args.source_root}")


if __name__ == "__main__":
    main()
