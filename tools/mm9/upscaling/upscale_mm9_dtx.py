#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageFilter


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MM9_TOOLS_DIR = REPO_ROOT / "tools" / "mm9_import_discovery"
DEFAULT_REALESRGAN_BIN = SCRIPT_DIR / "realesrgan-ncnn-vulkan"
sys.path.insert(0, MM9_TOOLS_DIR.as_posix())

from convert_abc_model import decode_dtx  # noqa: E402


DTX_HEADER_SIZE = 164
DTX_RESOURCE_TYPE = 0
DTX_VERSION_V2 = -5
DTX_SUPPORTED_VERSIONS = {DTX_VERSION_V2, -4}
DTX_BPP_8P = 0
DTX_BPP_32 = 3
DTX_BPP_DXT1 = 4
DTX_BPP_DXT3 = 5
DTX_BPP_DXT5 = 6


TYPE_POLICIES = {
    "default": {
        "tile": False,
        "sharpen_radius": 0.45,
        "sharpen_percent": 35,
        "sharpen_threshold": 1,
    },
    "actor": {
        "tile": False,
        "sharpen_radius": 0.45,
        "sharpen_percent": 35,
        "sharpen_threshold": 1,
    },
    "object": {
        "tile": False,
        "sharpen_radius": 0.45,
        "sharpen_percent": 35,
        "sharpen_threshold": 1,
    },
    "surface-tile": {
        "tile": True,
        "sharpen_radius": 0.55,
        "sharpen_percent": 40,
        "sharpen_threshold": 1,
    },
    "texture": {
        "tile": True,
        "sharpen_radius": 0.55,
        "sharpen_percent": 40,
        "sharpen_threshold": 1,
    },
}


@dataclass
class DtxHeader:
    resource_type: int
    version: int
    width: int
    height: int
    mipmap_count: int
    section_count: int
    flags: int
    user_flags: int
    extra: bytearray
    command_string: bytes

    @property
    def bpp(self) -> int:
        return self.extra[2]


@dataclass
class DtxFile:
    path: Path
    data: bytes
    header: DtxHeader
    mip_payload_size: int
    tail: bytes


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dtx_mip_dimensions(width: int, height: int, mipmap_count: int) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    current_width = width
    current_height = height
    for _index in range(mipmap_count):
        result.append((current_width, current_height))
        current_width = max(1, current_width // 2)
        current_height = max(1, current_height // 2)
    return result


def full_mipmap_count(width: int, height: int) -> int:
    count = 1
    current_width = width
    current_height = height
    while current_width > 1 or current_height > 1:
        current_width = max(1, current_width // 2)
        current_height = max(1, current_height // 2)
        count += 1
    return count


def dtx_mip_payload_size(bpp: int, width: int, height: int) -> int:
    if bpp in (DTX_BPP_8P, DTX_BPP_32):
        return width * height * 4
    if bpp == DTX_BPP_DXT1:
        return math.ceil(width / 4) * math.ceil(height / 4) * 8
    if bpp in (DTX_BPP_DXT3, DTX_BPP_DXT5):
        return math.ceil(width / 4) * math.ceil(height / 4) * 16
    raise ValueError(f"unsupported DTX BPP {bpp}")


def dtx_total_mip_payload_size(bpp: int, width: int, height: int, mipmap_count: int) -> int:
    return sum(dtx_mip_payload_size(bpp, mip_width, mip_height)
               for mip_width, mip_height in dtx_mip_dimensions(width, height, mipmap_count))


def read_dtx(path: Path) -> DtxFile:
    data = path.read_bytes()
    if len(data) < DTX_HEADER_SIZE:
        raise ValueError(f"DTX is too small: {path}")

    resource_type, version, height, width, mipmap_count, section_count, flags, user_flags = struct.unpack_from(
        "<IiHHHHii",
        data,
        0,
    )
    if resource_type != DTX_RESOURCE_TYPE or version not in DTX_SUPPORTED_VERSIONS:
        raise ValueError(f"not a supported MM9/LithTech DTX file: {path}")
    if width <= 0 or height <= 0 or mipmap_count <= 0:
        raise ValueError(f"invalid DTX dimensions/mips in {path}: {width}x{height}, mips={mipmap_count}")

    extra = bytearray(data[24:36])
    command_string = data[36:DTX_HEADER_SIZE]
    payload_size = dtx_total_mip_payload_size(extra[2], width, height, mipmap_count)
    tail_offset = DTX_HEADER_SIZE + payload_size
    if len(data) < tail_offset:
        raise ValueError(f"truncated DTX mip payload in {path}")

    return DtxFile(
        path=path,
        data=data,
        header=DtxHeader(
            resource_type=resource_type,
            version=version,
            width=width,
            height=height,
            mipmap_count=mipmap_count,
            section_count=section_count,
            flags=flags,
            user_flags=user_flags,
            extra=extra,
            command_string=command_string,
        ),
        mip_payload_size=payload_size,
        tail=data[tail_offset:],
    )


def decode_source_dtx(source: DtxFile) -> Image.Image:
    if source.header.version == DTX_VERSION_V2:
        return decode_dtx(source.path).convert("RGBA")

    if source.header.bpp not in (DTX_BPP_8P, DTX_BPP_32):
        raise ValueError(f"DTX version {source.header.version} decode only supports raw BPP, got {source.header.bpp}")

    pixel_count = source.header.width * source.header.height
    pixel_bytes = source.data[DTX_HEADER_SIZE:DTX_HEADER_SIZE + pixel_count * 4]
    if len(pixel_bytes) != pixel_count * 4:
        raise ValueError(f"{source.path} is truncated: expected {pixel_count * 4} base pixel bytes")

    image = Image.frombytes("RGBA", (source.header.width, source.header.height), pixel_bytes, "raw", "BGRA")
    if source.header.bpp == DTX_BPP_8P or image.getchannel("A").getextrema() == (0, 0):
        image.putalpha(255)
    return image


def output_path_for(source: Path, scale: int, output: Path | None) -> Path:
    if output is not None:
        if output.is_dir() or output.suffix.lower() != ".dtx":
            return output / f"{source.stem}_x{scale}{source.suffix}"
        return output
    return source.with_name(f"{source.stem}_x{scale}{source.suffix}")


def rgba_to_bgra_bytes(image: Image.Image, force_opaque_alpha: bool) -> bytes:
    rgba = image.convert("RGBA")
    pixels = bytearray()
    for red, green, blue, alpha in rgba.getdata():
        if force_opaque_alpha:
            alpha = 255
        pixels += bytes((blue, green, red, alpha))
    return bytes(pixels)


def build_mip_payload(base_image: Image.Image, bpp: int, mipmap_count: int) -> bytes:
    if bpp not in (DTX_BPP_8P, DTX_BPP_32):
        raise ValueError(f"DTX writing currently supports raw 32-bit-like BPP only, got {bpp}")

    payload = bytearray()
    force_opaque_alpha = bpp == DTX_BPP_8P
    for mip_index, (width, height) in enumerate(dtx_mip_dimensions(base_image.width, base_image.height, mipmap_count)):
        if mip_index == 0:
            mip_image = base_image.convert("RGBA")
        else:
            mip_image = base_image.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
        payload += rgba_to_bgra_bytes(mip_image, force_opaque_alpha)
    return bytes(payload)


def parse_sharpen(value: str) -> tuple[float, int, int]:
    pieces = value.split(",")
    if len(pieces) != 3:
        raise argparse.ArgumentTypeError("--sharpen must be radius,percent,threshold")
    try:
        return float(pieces[0]), int(pieces[1]), int(pieces[2])
    except ValueError as error:
        raise argparse.ArgumentTypeError("--sharpen must be radius,percent,threshold") from error


def resolve_realesrgan_binary(value: str) -> Path:
    candidate = Path(value)
    if candidate.exists():
        return candidate
    found = shutil.which(value)
    if found:
        return Path(found)
    raise FileNotFoundError(f"Real-ESRGAN binary not found: {value}")


def ensure_realesrgan_model(binary: Path, model: str) -> None:
    model_dir = binary.resolve().parent / "models"
    param = model_dir / f"{model}.param"
    blob = model_dir / f"{model}.bin"
    if not param.exists() or not blob.exists():
        raise FileNotFoundError(f"Real-ESRGAN model '{model}' not found under {model_dir}")


def run_realesrgan(binary: Path, model: str, scale: int, source_png: Path, output_png: Path) -> None:
    command = [
        binary.as_posix(),
        "-i",
        source_png.as_posix(),
        "-o",
        output_png.as_posix(),
        "-n",
        model,
        "-s",
        str(scale),
    ]
    subprocess.run(command, check=True)


def upscale_image(
    image: Image.Image,
    args: argparse.Namespace,
    policy: dict[str, Any],
    work_dir: Path,
) -> Image.Image:
    source_png = work_dir / "source.png"
    realesrgan_input = source_png
    expected_width = image.width * args.scale
    expected_height = image.height * args.scale

    if policy["tile"]:
        tiled = Image.new("RGBA", (image.width * 3, image.height * 3))
        for y in range(3):
            for x in range(3):
                tiled.paste(image, (x * image.width, y * image.height))
        tiled.save(source_png)
        expected_realesrgan = work_dir / "upscaled_tiled.png"
        run_realesrgan(args.realesrgan_bin, args.model, args.scale, realesrgan_input, expected_realesrgan)
        upscaled_tiled = Image.open(expected_realesrgan).convert("RGBA")
        left = expected_width
        top = expected_height
        result = upscaled_tiled.crop((left, top, left + expected_width, top + expected_height))
    else:
        image.save(source_png)
        expected_realesrgan = work_dir / "upscaled.png"
        run_realesrgan(args.realesrgan_bin, args.model, args.scale, realesrgan_input, expected_realesrgan)
        result = Image.open(expected_realesrgan).convert("RGBA")

    if result.size != (expected_width, expected_height):
        result = result.resize((expected_width, expected_height), Image.Resampling.LANCZOS)

    sharpen = args.sharpen
    if sharpen is None and not args.no_sharpen:
        sharpen = (
            float(policy["sharpen_radius"]),
            int(policy["sharpen_percent"]),
            int(policy["sharpen_threshold"]),
        )
    if sharpen is not None and not args.no_sharpen:
        result = result.filter(ImageFilter.UnsharpMask(radius=sharpen[0], percent=sharpen[1], threshold=sharpen[2]))

    return result


def output_bpp_for(input_bpp: int, output_format: str) -> int:
    if output_format == "rgba32":
        return DTX_BPP_32
    if output_format == "preserve":
        if input_bpp in (DTX_BPP_8P, DTX_BPP_32):
            return input_bpp
        raise ValueError(
            f"cannot preserve compressed DTX BPP {input_bpp}; use --format rgba32 to intentionally convert it",
        )
    if output_format == "auto":
        if input_bpp in (DTX_BPP_8P, DTX_BPP_32):
            return input_bpp
        return DTX_BPP_32
    raise ValueError(f"unsupported output format policy: {output_format}")


def write_dtx(
    source: DtxFile,
    output_path: Path,
    image: Image.Image,
    output_bpp: int,
    mipmap_count: int,
) -> bytes:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = bytearray(source.data[:DTX_HEADER_SIZE])

    # MM9 DTX v2 stores height before width in the header.
    struct.pack_into("<HH", header, 8, image.height, image.width)
    struct.pack_into("<H", header, 12, mipmap_count)
    header[26] = output_bpp

    payload = build_mip_payload(image, output_bpp, mipmap_count)
    output_data = bytes(header) + payload + source.tail
    output_path.write_bytes(output_data)
    return payload


def command_string_text(raw: bytes) -> str:
    if not raw or raw[0] == 0:
        return ""
    return raw.rstrip(b"\0").decode("latin-1", errors="replace")


def metadata_dict(header: DtxHeader) -> dict[str, Any]:
    return {
        "resource_type": header.resource_type,
        "version": header.version,
        "width": header.width,
        "height": header.height,
        "mipmap_count": header.mipmap_count,
        "section_count": header.section_count,
        "flags": header.flags,
        "user_flags": header.user_flags,
        "texture_group": header.extra[0],
        "mipmaps_used": header.extra[1],
        "bpp": header.bpp,
        "non_s3tc_offset": header.extra[3],
        "ui_mipmap_offset": header.extra[4],
        "texture_priority": header.extra[5],
        "detail_scale": struct.unpack_from("<f", bytes(header.extra), 6)[0],
        "detail_angle": struct.unpack_from("<h", bytes(header.extra), 10)[0],
        "command_string": command_string_text(header.command_string),
    }


def write_sidecar(
    path: Path,
    source: DtxFile,
    output_path: Path,
    output_data: bytes,
    output_payload: bytes,
    output_bpp: int,
    output_mipmap_count: int,
    args: argparse.Namespace,
    changed_fields: list[str],
) -> None:
    sidecar = {
        "source_dtx": source.path.as_posix(),
        "upscaled_dtx": output_path.as_posix(),
        "scale": args.scale,
        "type": args.type,
        "model": args.model,
        "format_policy": args.format,
        "mip_policy": args.mip_policy,
        "metadata_policy": "copied_except_dimensions_and_mips",
        "changed_fields": changed_fields,
        "source": metadata_dict(source.header),
        "upscaled": {
            **metadata_dict(source.header),
            "width": source.header.width * args.scale,
            "height": source.header.height * args.scale,
            "mipmap_count": output_mipmap_count,
            "bpp": output_bpp,
        },
        "hashes": {
            "source_file_sha256": sha256_bytes(source.data),
            "source_payload_sha256": sha256_bytes(
                source.data[DTX_HEADER_SIZE:DTX_HEADER_SIZE + source.mip_payload_size],
            ),
            "upscaled_file_sha256": sha256_bytes(output_data),
            "upscaled_payload_sha256": sha256_bytes(output_payload),
        },
    }
    path.write_text(yaml.safe_dump(sidecar, sort_keys=False), encoding="utf-8")


def changed_fields_for(source: DtxFile, output_bpp: int, output_mipmap_count: int) -> list[str]:
    fields = ["width", "height", "mip_payloads", "payload_hash"]
    if output_mipmap_count != source.header.mipmap_count:
        fields.append("mipmap_count")
    if output_bpp != source.header.bpp:
        fields.append("bpp")
    return fields


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upscale an MM9/LithTech DTX with Real-ESRGAN and rebuild DTX mip payloads.",
    )
    parser.add_argument("input", type=Path, help="Source .dtx file.")
    parser.add_argument("-s", "--scale", type=int, choices=(2, 3, 4), default=4, help="Upscale factor.")
    parser.add_argument("-o", "--output", type=Path, help="Output .dtx path or directory.")
    parser.add_argument(
        "--type",
        choices=sorted(TYPE_POLICIES),
        default="default",
        help=(
            "Upscale policy. surface-tile/texture tile and crop to reduce seam artifacts; "
            "actor/object/default use direct upscale."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("auto", "preserve", "rgba32"),
        default="auto",
        help="Output pixel format policy. auto preserves raw DTX BPP and converts DXT sources to raw RGBA32.",
    )
    parser.add_argument(
        "--mip-policy",
        choices=("full", "preserve"),
        default="full",
        help="full writes a complete mip chain for the new dimensions; preserve keeps the source mip count.",
    )
    parser.add_argument(
        "--realesrgan-bin",
        default=os.environ.get("REALESRGAN_BIN", DEFAULT_REALESRGAN_BIN.as_posix()),
        help="Path to realesrgan-ncnn-vulkan.",
    )
    parser.add_argument("--model", default=os.environ.get("MODEL", "realesrgan-x4plus"), help="Real-ESRGAN model.")
    parser.add_argument("--sharpen", type=parse_sharpen, help="Optional PIL unsharp mask as radius,percent,threshold.")
    parser.add_argument("--no-sharpen", action="store_true", help="Disable post-upscale sharpen.")
    parser.add_argument("--sidecar", type=Path, help="Output sidecar path. Default: <output>.upscale.yml.")
    parser.add_argument("--no-sidecar", action="store_true", help="Do not write an upscale sidecar.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output.")
    parser.add_argument("--keep-work", type=Path, help="Keep temporary PNGs in this directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.input = args.input.resolve()
    if not args.input.exists():
        raise FileNotFoundError(args.input)

    args.realesrgan_bin = resolve_realesrgan_binary(str(args.realesrgan_bin))
    ensure_realesrgan_model(args.realesrgan_bin, args.model)

    source = read_dtx(args.input)
    output_path = output_path_for(args.input, args.scale, args.output).resolve()
    if output_path.exists() and not args.force:
        raise FileExistsError(f"output exists, pass --force to overwrite: {output_path}")

    output_bpp = output_bpp_for(source.header.bpp, args.format)
    if args.mip_policy == "full":
        output_mipmap_count = full_mipmap_count(source.header.width * args.scale, source.header.height * args.scale)
    else:
        output_mipmap_count = source.header.mipmap_count

    decoded = decode_source_dtx(source)
    if decoded.size != (source.header.width, source.header.height):
        raise ValueError(
            f"decoded image size {decoded.size} does not match DTX header "
            f"{source.header.width}x{source.header.height}: {args.input}",
        )

    policy = TYPE_POLICIES[args.type]
    if args.keep_work is not None:
        work_dir = args.keep_work.resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
        upscaled = upscale_image(decoded, args, policy, work_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="openyamm_dtx_upscale_") as temp_dir:
            upscaled = upscale_image(decoded, args, policy, Path(temp_dir))

    payload = write_dtx(source, output_path, upscaled, output_bpp, output_mipmap_count)
    output_data = output_path.read_bytes()
    changed_fields = changed_fields_for(source, output_bpp, output_mipmap_count)

    if not args.no_sidecar:
        sidecar_path = args.sidecar.resolve() if args.sidecar is not None else output_path.with_suffix(
            output_path.suffix + ".upscale.yml",
        )
        write_sidecar(
            sidecar_path,
            source,
            output_path,
            output_data,
            payload,
            output_bpp,
            output_mipmap_count,
            args,
            changed_fields,
        )

    print(f"source: {args.input}")
    print(f"output: {output_path}")
    print(f"scale: x{args.scale}")
    print(f"size: {source.header.width}x{source.header.height} -> {upscaled.width}x{upscaled.height}")
    print(f"bpp: {source.header.bpp} -> {output_bpp}")
    print(f"mips: {source.header.mipmap_count} -> {output_mipmap_count}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
