"""Generate exact-2x Real-ESRGAN comparison art for existing paperdoll bodies and limbs."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageChops
from scipy.ndimage import distance_transform_edt


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
REVIEW = HERE.parent
INVENTORY = REVIEW.parent
OUT = HERE / "esrgan_baseline"
BINARY = ROOT / "tools/upscaling/realesrgan-ncnn-vulkan"
MODELS = ROOT / "tools/upscaling/models"
MODEL = "realesrgan-x4plus"
BORDER = 4
PROCESSING_VERSION = 2
sys.path.insert(0, str(INVENTORY))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def catalog():
    source = (REVIEW / "catalog.js").read_text()
    return json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))


def prepare_rgb(native):
    pixels = np.asarray(native.convert("RGBA"))
    visible = pixels[:, :, 3] >= 128
    if not visible.any():
        visible = pixels[:, :, 3] > 0
    if not visible.any():
        raise ValueError("Empty paperdoll sprite")
    _, nearest = distance_transform_edt(~visible, return_indices=True)
    filled = pixels[nearest[0], nearest[1], :3]
    bordered = np.pad(filled, ((BORDER, BORDER), (BORDER, BORDER), (0, 0)), mode="edge")
    return Image.fromarray(bordered, "RGB")


def sprite_names(prepared, doll):
    records = [record for record in prepared["records"] if record["status"] == "prepared"
               and (doll is None or record["character_id"] == doll)]
    if doll is not None and not records:
        raise ValueError(f"No prepared sprite references for character {doll}")
    return sorted({name for record in records for name in record["cells"]})


def current_record_valid(old, asset, paths, source_hash, preview_hash):
    if not old or old.get("source_sha256") != source_hash or old.get("native_preview_sha256") != preview_hash \
            or old.get("processing_version") != PROCESSING_VERSION:
        return False
    for key in ("input_rgb", "raw_bordered_x4", "master_rgb_x4", "candidate_x2"):
        path = paths[key]
        if not path.is_file() or digest(path) != old.get(key + "_sha256"):
            return False
    with Image.open(paths["candidate_x2"]) as opened:
        return opened.mode == "RGBA" and list(opened.size) == [size * 2 for size in asset["size"]]


def write_manifest(records, prepared_hash, tool_hashes):
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "openyamm-paperdoll-esrgan-baseline-v1",
        "status": "comparison_only_not_approved",
        "model": MODEL,
        **tool_hashes,
        "source_manifest_sha256": prepared_hash,
        "input_border_native_pixels": BORDER,
        "processing_version": PROCESSING_VERSION,
        "inference_scale": 4,
        "export_scale": 2,
        "alpha": "native preview alpha enlarged to x4, premultiplied downsample to x2, then clamped to "
        "the exact nearest-neighbor x2 native footprint to prevent interpolation fringe",
        "items": records,
    }
    (OUT / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n")


def write_viewer_data(data, prepared, records):
    ready = []
    names = set(records)
    assets = {}
    for character in prepared["records"]:
        if character["status"] != "prepared" or not set(character["cells"]).issubset(names):
            continue
        row = next(entry for entry in data["characters"] if entry["id"] == character["character_id"])
        portrait = data["assets"].get(row["portrait"])
        background_name = row["background"] or "backdolm"
        background = data["assets"].get(background_name)
        ready.append({
            "id": character["character_id"], "label": row["notes"] or row["facePrefix"] or row["body"],
            "kind": character["kind"], "portrait": row["portrait"],
            "portrait_native": os.path.relpath(REVIEW / unquote(portrait["native"]), OUT) if portrait else "",
            "portrait_current": os.path.relpath(REVIEW / unquote(portrait["candidate"]), OUT)
            if portrait and portrait.get("candidate") else "",
            "parts": list(character["cells"]), "poses": character["pose_layers"],
            "body": row["body"], "body_x": row["bodyX"], "body_y": row["bodyY"],
            "background": background_name,
            "background_native": os.path.relpath(REVIEW / unquote(background["native"]), OUT)
            if background else "",
        })
        for name in character["cells"]:
            asset = data["assets"][name]
            native = REVIEW / unquote(asset["native"])
            candidate = REVIEW / unquote(asset["candidate"]) if asset.get("candidate") else None
            enhanced = OUT / "candidate_x2" / (name + ".png")
            assets[name] = {
                "native": os.path.relpath(native, OUT),
                "current": os.path.relpath(candidate, OUT) if candidate else "",
                "esrgan": os.path.relpath(enhanced, OUT),
                "size": asset["size"], "status": asset.get("candidateStatus"),
                "registration_flags": records[name]["registration_flags"],
            }
    payload = {"schema": "openyamm-paperdoll-esrgan-viewer-v1", "characters": ready, "assets": assets}
    (OUT / "viewer_data.js").write_text("window.PAPERDOLL_ESRGAN_DATA = " + json.dumps(payload) + ";\n")
    return len(ready)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doll", type=int, help="Only one character row, for a focused pilot")
    group.add_argument("--all", action="store_true", help="All extant portrait-linked doll bodies and limbs")
    arguments = parser.parse_args()
    if not BINARY.is_file() or not (MODELS / (MODEL + ".bin")).is_file():
        raise FileNotFoundError("Repository Real-ESRGAN runner or x4plus model is missing")
    prepared_path = HERE / "prepared/manifest.json"
    prepared = json.loads(prepared_path.read_text())
    prepared_hash = digest(prepared_path)
    tool_hashes = {
        "model_param_sha256": digest(MODELS / (MODEL + ".param")),
        "model_bin_sha256": digest(MODELS / (MODEL + ".bin")),
        "runner_sha256": digest(BINARY),
    }
    data = catalog()
    names = sprite_names(prepared, arguments.doll)
    manifest_path = OUT / "manifest.json"
    prior = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
    if prior and any(prior.get(key) != value for key, value in tool_hashes.items()):
        raise ValueError("Real-ESRGAN model or runner changed; start a separate baseline directory")
    existing = prior["items"] if prior else {}
    records = dict(existing)
    queue = queue_module.Queue()
    source_info = {}
    preview_hashes = {}
    pending = []
    for name in names:
        asset = data["assets"][name]
        source = ROOT / asset["source"]
        if digest(source) != asset["sourceHash"]:
            raise ValueError(f"Original source changed: {name}")
        preview = REVIEW / unquote(asset["native"])
        preview_hash = digest(preview)
        preview_hashes[name] = preview_hash
        paths = {key: OUT / folder / (name + ".png") for key, folder in (
            ("input_rgb", "input_rgb"), ("raw_bordered_x4", "raw_bordered_x4"),
            ("master_rgb_x4", "master_rgb_x4"), ("candidate_x2", "candidate_x2"))}
        source_info[name] = (asset, preview, paths)
        if current_record_valid(records.get(name), asset, paths, asset["sourceHash"], preview_hash):
            continue
        with Image.open(preview) as opened:
            native = opened.convert("RGBA")
        if list(native.size) != asset["size"]:
            raise ValueError(f"Wrong native preview size: {name}")
        paths["input_rgb"].parent.mkdir(parents=True, exist_ok=True)
        prepare_rgb(native).save(paths["input_rgb"], optimize=True)
        pending.append(name)

    if pending:
        batch_tag = hashlib.sha256("\n".join(f"{name}:{preview_hashes[name]}" for name in pending).encode()
                                   ).hexdigest()[:12]
        batch_input = OUT / "batches" / batch_tag / "input"
        batch_output = OUT / "batches" / batch_tag / "output"
        batch_input.mkdir(parents=True, exist_ok=True)
        batch_output.mkdir(parents=True, exist_ok=True)
        for name in pending:
            path = batch_input / (name + ".png")
            if not path.exists():
                os.link(source_info[name][2]["input_rgb"], path)
            old = records.get(name)
            old_raw = source_info[name][2]["raw_bordered_x4"]
            reused = batch_output / (name + ".png")
            if not reused.exists() and old and old.get("source_sha256") == source_info[name][0]["sourceHash"] \
                    and old.get("native_preview_sha256") == preview_hashes[name] \
                    and old_raw.is_file() and digest(old_raw) == old.get("raw_bordered_x4_sha256"):
                os.link(old_raw, reused)
        missing_raw = [name for name in pending if not (batch_output / (name + ".png")).is_file()]
        if missing_raw:
            log_path = OUT / "batches" / batch_tag / "inference.log"
            command = [str(BINARY), "-i", str(batch_input), "-o", str(batch_output),
                       "-s", "4", "-n", MODEL, "-m", str(MODELS), "-g", "0"]
            print(f"Real-ESRGAN x4plus: {len(pending)} sprite(s), log {log_path}", flush=True)
            start = time.monotonic()
            with log_path.open("w") as log:
                subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
            print(f"Inference finished in {time.monotonic() - start:.1f}s", flush=True)
        for number, name in enumerate(pending, 1):
            asset, preview, paths = source_info[name]
            generated = batch_output / (name + ".png")
            if not generated.is_file():
                raise FileNotFoundError(f"Real-ESRGAN did not return {name}")
            paths["raw_bordered_x4"].parent.mkdir(parents=True, exist_ok=True)
            if not paths["raw_bordered_x4"].exists():
                os.link(generated, paths["raw_bordered_x4"])
            elif digest(paths["raw_bordered_x4"]) != digest(generated):
                replacement = paths["raw_bordered_x4"].with_suffix(".replacement.png")
                shutil.copyfile(generated, replacement)
                os.replace(replacement, paths["raw_bordered_x4"])
            with Image.open(preview) as opened:
                native = opened.convert("RGBA")
            with Image.open(generated) as opened:
                raw = opened.convert("RGB")
            expected = ((native.width + 2 * BORDER) * 4, (native.height + 2 * BORDER) * 4)
            if raw.size != expected:
                raise ValueError(f"Wrong ESRGAN return size for {name}: {raw.size} vs {expected}")
            master = raw.crop((BORDER * 4, BORDER * 4,
                               (BORDER + native.width) * 4, (BORDER + native.height) * 4))
            paths["master_rgb_x4"].parent.mkdir(parents=True, exist_ok=True)
            master.save(paths["master_rgb_x4"], optimize=True)
            enhanced = master.convert("RGBA")
            enhanced.putalpha(native.getchannel("A").resize(enhanced.size, Image.Resampling.LANCZOS))
            candidate = enhanced.convert("RGBa").resize((native.width * 2, native.height * 2),
                                                         Image.Resampling.LANCZOS).convert("RGBA")
            source_alpha_x2 = native.getchannel("A").resize(candidate.size, Image.Resampling.NEAREST)
            candidate.putalpha(ImageChops.darker(candidate.getchannel("A"), source_alpha_x2))
            paths["candidate_x2"].parent.mkdir(parents=True, exist_ok=True)
            candidate.save(paths["candidate_x2"], optimize=True)
            identifier = asset["id"]
            member = queue.members[identifier][1]
            target = queue.targets[member["target"]]
            measurements = registration.measurements(member, target, paths["candidate_x2"])
            flags = {profile: result["failures"] for profile, result in measurements["profiles"].items()
                     if result["failures"]}
            records[name] = {
                "processing_version": PROCESSING_VERSION,
                "source_path": asset["source"], "source_sha256": asset["sourceHash"],
                "native_preview_sha256": digest(preview), "native_size": asset["size"],
                "x2_size": list(candidate.size), "raw_bordered_size_x4": list(raw.size),
                **{key: str(path.relative_to(OUT)) for key, path in paths.items()},
                **{key + "_sha256": digest(path) for key, path in paths.items()},
                "registration_flags": flags,
                "visual_status": "pending_manual_comparison",
            }
            write_manifest(records, prepared_hash, tool_hashes)
            print(f"{number}/{len(pending)} {name} {'REGISTRATION FLAG' if flags else 'registration pass'}", flush=True)
    count = write_viewer_data(data, prepared, records)
    flagged = {name: records[name]["registration_flags"] for name in names
               if records[name]["registration_flags"]}
    (OUT / "summary.json").write_text(json.dumps({
        "schema": "openyamm-paperdoll-esrgan-summary-v1",
        "status": "comparison_only_not_approved",
        "requested_unique_sprites": len(names),
        "complete_dolls_in_viewer": count,
        "registration_passes": len(names) - len(flagged),
        "registration_flags": flagged,
    }, indent=2) + "\n")
    print(f"Ready: {len(names)} requested sprites, {count} complete doll(s) in comparison viewer", flush=True)


if __name__ == "__main__":
    main()
