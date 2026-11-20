#!/usr/bin/env python3
"""
MM9 prop skins at 4x with Codex image generation (devdocs/mm9_rework/DECORATIONS_AND_GRASS.md, step 2).

The MM9 decorations (`assets_source/worlds/mm9/models/mm9_deco_*.glb`, built by level_generation/props/mm9_<map>_claude/)
carry MM9's skins enlarged x4 by Real-ESRGAN or Lanczos; nearly all are 128 x 128 natively. This redraws each skin as
fresh 4x art that keeps its UV layout exactly (the mesh's UVs stay), then restores its cut-out alpha from the native.

    python3 skins.py inventory                 # every distinct native skin -> work/inventory.json
    python3 skins.py gen NAME... [--parallel N] [--version V]   # Codex workers -> work/raw/NAME_vV.png
    python3 skins.py finish NAME... [--version V]               # size, alpha, checks -> work/x4/NAME.png + metrics
    python3 skins.py sheet NAME... --out PNG   # native | ESRGAN/Lanczos x4 now | new x4, with the checks

Workers are `codex exec` with the built-in image_gen tool (the surface textures' worker, textures_x4/tex.py), at most
16 at a time. Nothing is installed here; installing (swapping a skin into its models) is a later step.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = HERE / "work"
SCALE = 4
MAGENTA = np.array([255, 0, 255])

WORKER_PROMPT = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image as the reference image and the IMAGE PROMPT below.
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""

PROMPT = """Redraw this square game texture atlas as a sharp, high-detail version of itself, at four times its
detail. It is the texture sheet of a {subject} in a medieval fantasy role-playing game: each region of the sheet is
painted onto one part of the 3D model, so the layout must stay exactly as it is.
- Keep every region, edge, border, stripe, board, rivet, book spine, ornament and object exactly where it is, at the
  same size and proportions; do not move, add, remove, crop, rotate or rearrange anything.
- Keep the colours, brightness and material of each region; invent only the fine detail inside them: real wood grain,
  fibres, metal wear, cloth weave, paper and leather, painted at about four pixels per centimetre.
- Flat magenta (pure #FF00FF) regions are transparent cut-outs: keep them flat pure magenta with the same shapes.
  Purple, violet, pink or lilac regions that are not flat pure magenta are real colours (glass, gems, cloth,
  paint): keep their hue exactly.
- Very dark or black regions (soot, iron, shadowed insides) stay just as dark.
- No lighting, shadows, glare, vignette, frame, text or labels; even, flat illumination like a texture scan.
- Fill the whole square, edge to edge.{note}"""


def load(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


_STEMS: dict | None = None
_IMAGES: dict | None = None


def skin_stems(entry: dict) -> set[str]:
    """The file stems of every native file with this skin's content (raw/<prop>/skins/<stem>.png): a prop's model
    names the skin's image `<stem>_basecolor`, so a second skin is `<prop>_1`, never the prop's name (before
    2026-11-04 install keyed by prop names: the aged suit of armour's body took its halberd skin)."""
    global _STEMS
    if _STEMS is None:
        _STEMS = {}
        for path in glob.glob(str(ROOT / "level_generation/props/mm9_*_claude/work/raw/*/skins/*.png")):
            digest = hashlib.sha1(Path(path).read_bytes()).hexdigest()[:16]
            _STEMS.setdefault(digest, set()).add(Path(path).stem.lower())
    return _STEMS.get(entry["hash"], set())


def skin_models(entry: dict) -> list[str]:
    """The installed source models (assets_source/worlds/mm9/models/mm9_deco_*.glb) holding an image of this skin."""
    global _IMAGES
    if _IMAGES is None:
        _IMAGES = {}
        for path in sorted(glob.glob(str(ROOT / "assets_source/worlds/mm9/models/mm9_deco_*.glb"))):
            data = Path(path).read_bytes()
            gltf = json.loads(data[20:20 + int.from_bytes(data[12:16], "little")])
            for image in gltf.get("images", []):
                _IMAGES.setdefault(image.get("name", "").removesuffix("_basecolor").lower(), set()).add(
                    Path(path).name)
    return sorted({model for stem in skin_stems(entry) for model in _IMAGES.get(stem, set())})


def opaque_skin(name: str, entry: dict) -> bool:
    """Whether every material drawing this skin (its images in the source models) is OPAQUE: its alpha is
    then no cut-out but MM9's shine mask (the gold suit of armour's plates, capstone, machine parts), which the game
    ignores. Such a skin is fully opaque here: the reference showed its low-alpha plates as magenta holes and the
    redraw kept them (Thjorgard City's gold suit, 2026-11-04)."""
    names = skin_stems(entry)
    modes = set()
    for model in skin_models(entry):
        path = ROOT / "assets_source/engine/models" / model
        data = path.read_bytes()
        gltf = json.loads(data[20:20 + int.from_bytes(data[12:16], "little")])
        for material in gltf.get("materials", []):
            texture = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            if texture is None:
                continue
            image = gltf["images"][gltf["textures"][texture["index"]]["source"]].get("name", "")
            if image.removesuffix("_basecolor") in names:
                modes.add(material.get("alphaMode", "OPAQUE"))
    return modes == {"OPAQUE"}


def native_rgba(name: str, entry: dict) -> Image.Image:
    image = Image.open(ROOT / entry["source"]).convert("RGBA")
    pixels = np.array(image)
    if opaque_skin(name, entry):
        pixels[..., 3] = 255
        return Image.fromarray(pixels)
    # The skin's own alpha (cut-outs, and the partial alpha of glass, ghosts and lamp glow), with chroma-key magenta
    # texels transparent too.
    chroma = (np.abs(pixels[..., :3].astype(int) - MAGENTA).sum(-1) < 60)
    pixels[..., 3] = np.where(chroma, 0, pixels[..., 3])
    return Image.fromarray(pixels)


def cmd_inventory(args) -> None:
    """Every distinct native skin (by content), with the props and projects that use it. Names already in
    work/inventory.json stay (a new project that sorts first would otherwise rename an accepted skin: 2026-11-04,
    the regions' portalbroken took portalwhole's name)."""
    entries, by_hash = {}, {}
    for name, entry in load(WORK / "inventory.json", {}).items():
        entries[name] = dict(entry, props=[])
        by_hash[entry["hash"]] = name
    for path in sorted(glob.glob(str(ROOT / "level_generation/props/mm9_*_claude/work/raw/*/skins/*.png"))):
        path = Path(path)
        digest = hashlib.sha1(path.read_bytes()).hexdigest()[:16]
        name = path.stem.lower()
        if digest in by_hash:
            entries[by_hash[digest]]["props"].append(f"{path.parents[4].name}:{path.parents[1].name}")
            continue
        if name in entries:
            name = f"{name}_{digest[:6]}"
        by_hash[digest] = name
        w, h = Image.open(path).size
        entries[name] = {"source": str(path.relative_to(ROOT)), "size": [w, h], "hash": digest,
                         "props": [f"{path.parents[4].name}:{path.parents[1].name}"]}
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "inventory.json").write_text(json.dumps(entries, indent=1) + "\n")
    print(f"{len(entries)} distinct skins")


def reference_image(name: str, entry: dict) -> Path:
    """The native at 4x (nearest, then a light blur so the model sees shapes, not texels) on a square canvas."""
    native = native_rgba(name, entry)
    rgba = np.array(native)
    # Only true cut-outs show as magenta: partly transparent texels (lantern glass, stained glass, glow) keep their
    # colour, which the redraw must keep (`finish` puts their alpha back). Before 2026-11-04 every texel under half
    # alpha was magenta here and the redraws lost the glass (lamppost1's frosted panes, lantern2's blue and yellow).
    flat = rgba[..., 3] < 16
    rgb = rgba[..., :3].copy()
    rgb[flat] = MAGENTA
    big = Image.fromarray(rgb).resize((native.width * SCALE, native.height * SCALE), Image.LANCZOS)
    side = max(big.size)
    canvas = Image.new("RGB", (side, side), (255, 0, 255))
    canvas.paste(big, (0, 0))
    path = WORK / "refs" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return path


def subject_of(entry: dict) -> str:
    prop = entry["props"][0].split(":")[1]
    return prop.replace("_", " ")


def run_worker(name: str, entry: dict, version: int, note: str) -> tuple[str, bool, int]:
    reference = reference_image(name, entry)
    target = WORK / "raw" / f"{name}_v{version}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    prompt = PROMPT.format(subject=subject_of(entry), note=("\n- " + note) if note else "")
    (WORK / "prompts").mkdir(exist_ok=True)
    (WORK / "prompts" / f"{name}_v{version}.txt").write_text(prompt + "\n")
    worker = WORKER_PROMPT.format(prompt=prompt, target=target)
    started = time.time()
    with open(WORK / "raw" / f"{name}_v{version}.log", "w") as stream:
        try:
            process = subprocess.run(["codex", "exec", "--json", "-s", "workspace-write", "-C", str(WORK),
                                      "--skip-git-repo-check", "-i", str(reference)],
                                     input=worker, text=True, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
            code = process.returncode
        except subprocess.TimeoutExpired:
            stream.write("\nskins.py: worker timed out after 900 s\n")
            code = -1
    return name, target.exists() and code == 0, round(time.time() - started)


def cmd_gen(args) -> None:
    inventory = load(WORK / "inventory.json")
    notes = load(WORK / "notes.json", {})
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.parallel, 16)) as pool:
        futures = [pool.submit(run_worker, name, inventory[name], args.version, notes.get(name, ""))
                   for name in args.names]
        for future in concurrent.futures.as_completed(futures):
            name, ok, seconds = future.result()
            print(f"{name} v{args.version}: {'ok' if ok else 'FAILED'} {seconds}s", flush=True)


def finish(name: str, entry: dict, version: int, scale: int = SCALE) -> dict:
    """Crop the native's area, resize to 4x, put the native's alpha back, and measure the layout against the native."""
    native = native_rgba(name, entry)
    w, h = native.size
    raw = Image.open(WORK / "raw" / f"{name}_v{version}.png").convert("RGB")
    side = max(w, h)
    # The reference was the native at the top-left of a square: crop the same share of the generated square.
    raw = raw.resize((side * scale, side * scale), Image.LANCZOS).crop((0, 0, w * scale, h * scale))
    # Hard cut-outs stay hard (nearest, lightly smoothed, then thresholded); partial alpha is enlarged smoothly.
    native_alpha = np.array(native.split()[3])
    hard = Image.fromarray(native_alpha).resize((w * scale, h * scale), Image.NEAREST).filter(ImageFilter.GaussianBlur(0.8))
    hard = np.where(np.array(hard) >= 128, 255, 0)
    smooth = np.array(Image.fromarray(native_alpha).resize((w * scale, h * scale), Image.BICUBIC))
    soft_native = (native_alpha > 16) & (native_alpha < 240)
    soft_area = np.array(Image.fromarray((soft_native * 255).astype(np.uint8)).resize((w * scale, h * scale),
                                                                                      Image.NEAREST)) > 0
    alpha = Image.fromarray(np.where(soft_area, smooth, hard).astype(np.uint8))
    # Chroma the model left inside opaque regions (specks of #FF00FF in purple glass) would show in game: those texels
    # take the native's colour, enlarged.
    pixels = np.array(raw).astype(int)
    speck = (np.abs(pixels - MAGENTA).sum(-1) < 90) & (np.array(alpha) > 0)
    if speck.any():
        enlarged = np.array(native.convert("RGB").resize((w * scale, h * scale), Image.LANCZOS)).astype(int)
        pixels[speck] = enlarged[speck]
        raw = Image.fromarray(pixels.astype(np.uint8))
    out = raw.copy()
    out.putalpha(alpha)
    # Colour under transparent texels from the nearest opaque one, so filtering and mips bring no magenta fringe
    # (the props' textures.py bleed).
    rgba = np.array(out)
    opaque = rgba[..., 3] > 127
    if opaque.any() and not opaque.all():
        _, (iy, ix) = ndimage.distance_transform_edt(~opaque, return_indices=True)
        rgba[..., :3] = rgba[..., :3][iy, ix]
        out = Image.fromarray(rgba)
    # Layout check: the result reduced to the native's size against the native, over opaque texels.
    small = np.array(raw.resize((w, h), Image.BOX)).astype(float)
    ref = np.array(native.convert("RGB")).astype(float)
    opaque = np.array(native.split()[3]) > 127
    diff = np.abs(small - ref).mean(-1)[opaque]
    blur_small = np.array(raw.resize((w // 4 or 1, h // 4 or 1), Image.BOX)).astype(float)
    blur_ref = np.array(native.convert("RGB").resize((w // 4 or 1, h // 4 or 1), Image.BOX)).astype(float)
    correlation = float(np.corrcoef(blur_small.mean(-1).ravel(), blur_ref.mean(-1).ravel())[0, 1])
    brightness = float(small.mean(-1)[opaque].mean() / max(ref.mean(-1)[opaque].mean(), 1.0))
    metrics = {"mean_abs_diff": round(float(diff.mean()), 1), "layout_correlation": round(correlation, 3),
               "brightness_ratio": round(brightness, 3)}
    (WORK / "x4").mkdir(exist_ok=True)
    out.save(WORK / "x4" / f"{name}.png")
    return metrics


def cmd_finish(args) -> None:
    inventory = load(WORK / "inventory.json")
    metrics = load(WORK / "metrics.json", {})
    for name in args.names:
        metrics[name] = {"version": args.version, "scale": args.scale,
                         **finish(name, inventory[name], args.version, args.scale)}
        print(name, metrics[name])
    (WORK / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")


def current_x4(entry: dict) -> Path | None:
    """The texture the models carry now (the prop project's textures/<prop>_basecolor.png)."""
    project, prop = entry["props"][0].split(":")
    path = ROOT / "level_generation/props" / project / "textures" / f"{prop}_basecolor.png"
    return path if path.exists() else None


def cmd_sheet(args) -> None:
    inventory = load(WORK / "inventory.json")
    metrics = load(WORK / "metrics.json", {})
    tile = 384
    sheet = Image.new("RGB", (tile * 3, len(args.names) * (tile + 20)), "white")
    draw = ImageDraw.Draw(sheet)
    for k, name in enumerate(args.names):
        entry, y = inventory[name], k * (tile + 20)
        images = [Image.open(ROOT / entry["source"]).convert("RGBA").resize((tile, tile), Image.NEAREST)]
        now = current_x4(entry)
        images.append(Image.open(now).convert("RGBA").resize((tile, tile), Image.LANCZOS) if now else None)
        images.append(Image.open(WORK / "x4" / f"{name}.png").convert("RGBA").resize((tile, tile), Image.LANCZOS))
        for column, image in enumerate(images):
            if image is not None:
                back = Image.new("RGBA", image.size, (255, 0, 255, 255))
                back.alpha_composite(image)
                sheet.paste(back.convert("RGB"), (column * tile, y + 20))
        m = metrics.get(name, {})
        draw.text((4, y + 3), f"{name}: native | now (x4 upscale) | Codex x4   diff {m.get('mean_abs_diff')} "
                  f"layout {m.get('layout_correlation')} brightness {m.get('brightness_ratio')}", fill="black")
    sheet.save(args.out)


def replace_images(glb: Path, replacements: dict, out: Path) -> int:
    """Copies a GLB with the named embedded images (image name -> PNG bytes) replaced; returns how many."""
    import struct
    data = glb.read_bytes()
    json_length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    offset = 20 + json_length
    binary = data[offset + 8:offset + 8 + struct.unpack_from("<I", data, offset)[0]]
    views = [bytes(binary[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]])
             for v in document["bufferViews"]]
    replaced = 0
    for image in document.get("images", []):
        new = replacements.get((image.get("name") or "").lower())
        if new is not None and "bufferView" in image:
            views[image["bufferView"]] = new
            replaced += 1
    chunks, position = [], 0
    for view, chunk in zip(document["bufferViews"], views):
        view["byteOffset"], view["byteLength"] = position, len(chunk)
        padded = chunk + b"\0" * (-len(chunk) % 4)
        chunks.append(padded)
        position += len(padded)
    document["buffers"][0]["byteLength"] = position
    body = json.dumps(document, separators=(",", ":")).encode()
    body += b" " * (-len(body) % 4)
    blob = b"".join(chunks)
    total = 12 + 8 + len(body) + 8 + len(blob)
    out.write_bytes(struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(body), 0x4E4F534A) + body
                    + struct.pack("<II", len(blob), 0x004E4942) + blob)
    return replaced


# Skins kept at their current upscale: mostly translucent (glass, a ghost, a crystal statue), where the redraw read the
# partial alpha as cut-outs and lost the material (review 2026-11-04).
KEEP_CURRENT = {"sorcererstatue", "icebanshee", "goblet", "jar", "beaker01"}


def cmd_install(args) -> None:
    """Swaps the finished x4 skins into copies of the source models and installs them (tools/install_model.py)."""
    import io
    inventory = load(WORK / "inventory.json")
    accepted = (set(args.names) if args.names else set(load(WORK / "metrics.json", {}))) - KEEP_CURRENT
    per_model = {}
    for skin in accepted:
        path = WORK / "x4" / f"{skin}.png"
        if not path.exists():
            continue
        buffer = io.BytesIO()
        Image.open(path).save(buffer, "PNG", optimize=True)
        for model in skin_models(inventory[skin]):
            per_model.setdefault(model, {}).update(
                {f"{stem}_basecolor": buffer.getvalue() for stem in skin_stems(inventory[skin])})
    staging = WORK / "glb"
    staging.mkdir(exist_ok=True)
    for model, replacements in sorted(per_model.items()):
        out = staging / model
        count = replace_images(ROOT / "assets_source/engine/models" / model, replacements, out)
        if args.dry_run:
            print(f"{model}: {count} image(s)")
            continue
        result = subprocess.run([sys.executable, str(ROOT / "tools/install_model.py"), str(out), "--world", "mm9"],
                                cwd=ROOT, capture_output=True, text=True)
        print(f"{model}: {count} image(s), install {'ok' if result.returncode == 0 else 'FAILED'}", flush=True)
        if result.returncode != 0:
            print(result.stdout[-800:], result.stderr[-800:])


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory")
    for cmd in ("gen", "finish"):
        p = sub.add_parser(cmd)
        p.add_argument("names", nargs="+")
        p.add_argument("--version", type=int, default=1)
        if cmd == "gen":
            p.add_argument("--parallel", type=int, default=8)
        else:
            # 8 for the big props (natives of 128 or less, about 150+ units: work/x8_names.json; user, 2026-11-04):
            # the generated 1254-pixel image holds the detail, and 4x left them at ~2 texels per unit.
            p.add_argument("--scale", type=int, default=SCALE)
    p = sub.add_parser("install")
    p.add_argument("names", nargs="*")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("sheet")
    p.add_argument("names", nargs="+")
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    {"inventory": cmd_inventory, "gen": cmd_gen, "finish": cmd_finish, "sheet": cmd_sheet,
     "install": cmd_install}[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
