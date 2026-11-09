#!/usr/bin/env python3
"""MM9 PC paperdolls: graft a generated MM9 head onto an existing MM6-MM8 doll body.

The donor body, its hand layers, offsets and doll type stay as they are, so every equipment variant fits exactly as
on the donor. Only the head and the top of the neck above `seam_y` are replaced by a Codex repaint of the donor's
head region in the identity of the character's new portrait family (../mm9_pc_portraits/).

  python3 dolls.py prepare PC03     # crop, references, brief, run.sh
  python3 dolls.py extract PC03     # register the Codex result to the donor, composite, previews
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ICONS = ROOT / "assets_dev/engine/icons_x2"
PORTRAITS = HERE.parent / "mm9_pc_portraits"
sys.path.insert(0, str(PORTRAITS))
from portraits import RUNNER, TRANSIENT  # noqa: E402

UPSCALE = 4
IDENTITY_SLOTS = (1, 19, 26, 28)
RENDERER = ROOT / "tools/mm9_import_discovery/render_paperdoll_equipment_preview.py"


def plan(cid):
    table = json.loads((HERE / "dolls.json").read_text())["characters"]
    if cid not in table:
        raise SystemExit(f"Unknown character {cid}; see dolls.json")
    return table[cid]


def workspace(cid):
    folder = HERE / cid.lower()
    folder.mkdir(exist_ok=True)
    return folder


def donor_crop(info):
    body = Image.open(ICONS / f"{info['donor_body']}.png").convert("RGBA")
    box = tuple(body.width if v is None else v for v in info["head_box"])
    return body, box, body.crop(box)


BRIEF = """# Codex brief: MM9 {cid} head on an existing paperdoll body

Scope: image generation only, with your built-in image generation tool. Write only into `{folder}`. No builds, no
other edits, no scripts that alter pixels.

## Inputs (attached in this order)

1. `donor.png`: TARGET. The head, neck and shoulders of an existing game paperdoll (a full-body figure in a fixed
   pose), on a transparent background, enlarged 4x from the game asset.
2. `identity.png`: the NEW character's face from its game portrait set, at several head angles: {description}.

## What to produce

One square image with exactly the framing of input 1: the same figure, but with the head of input 2's character.

- Replace the head: face, hair, ears, beard, horns and any headdress, hood or crown, and the neck above the collar.
  The new head has the same size, position, turn, tilt and gaze as the head in input 1, and joins the same neck at
  the same place, so it sits naturally on the unchanged body. Where input 1's hair, beard or hood falls onto the
  shoulders or chest, the new character's own hair, beard or hood takes that place, as long as it naturally is.
- Everything else (torso, clothing, arms) stays exactly as in input 1: same pose, colours, shading and edges. It is
  replaced by the original afterwards, so do not restyle it.
- Lighting and rendering of the head match input 1's body: the same pre-rendered game look, light from the same side,
  the same skin tone where the neck meets the body. Identity (hair shape and colour, face shape, eyes, brows, nose,
  mouth, skin tone) comes from input 2. Calm neutral expression, mouth closed.
- Hair stays close to the head: no larger silhouette than input 1's head plus the new character's hair needs.
- Genuinely transparent RGBA background (alpha 0) outside the figure; no backdrop, shadow or halo. Square output
  around 1024x1024. No text or marks.

## Records

- Copy the exact generated file, unmodified, to `raw.png`. If the result changed the body framing or has no real
  transparency, do ONE corrective regeneration and keep the first as `raw_rejected.png`.
- Write `generation.json`: exact prompt, input paths with sha256, output path, sha256, size, mode, and a short
  self-check against this brief.
"""


def prepare(cid):
    info, folder = plan(cid), workspace(cid)
    body, box, crop = donor_crop(info)
    crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.Resampling.LANCZOS).save(folder / "donor.png")
    frames = [Image.open(PORTRAITS / info["portrait_dir"] / "frames" / f"{info['portrait_prefix']}{n:02d}.png")
              .convert("RGBA") for n in IDENTITY_SLOTS]
    strip = Image.new("RGBA", (len(frames) * 236, 316))
    for k, frame in enumerate(frames):
        strip.alpha_composite(frame.resize((236, 316), Image.Resampling.LANCZOS), (k * 236, 0))
    strip.save(folder / "identity.png")
    relative = folder.relative_to(ROOT)
    (folder / "brief.md").write_text(BRIEF.format(cid=cid, folder=relative, description=info["description"]))
    command = (f'codex exec "Follow the brief in {relative}/brief.md exactly. The attached images are its inputs in '
               f'order. Produce the image with your built-in image generation tool and save it as specified." '
               f'-c model_reasoning_effort=medium -C {ROOT} -s workspace-write --add-dir ~/.codex/generated_images '
               f'-o {relative}/codex_last_message.md -i {relative}/donor.png {relative}/identity.png '
               f'< /dev/null > {relative}/codex_run.log 2>&1')
    run = folder / "run.sh"
    run.write_text(RUNNER.format(root=ROOT, command=command, output=relative / "raw.png",
                                 log=relative / "codex_run.log", transient=TRANSIENT))
    run.chmod(0o755)
    print(f"Prepared. From the repository root run: {run.relative_to(ROOT)}")


def register(raw, crop, seam_y):
    """Find the scale and shift that put the generated figure on the donor: Codex returns a square image and may
    reframe a tall crop, so search the scale widely and template-match the donor's body below the seam (OpenCV)."""
    import cv2
    target = np.asarray(crop).astype(np.float32)
    top = min(seam_y + 8, crop.height - 16)
    template = np.ascontiguousarray(target[top:, :, :3])
    mask = np.ascontiguousarray(np.repeat((target[top:, :, 3:4] > 200).astype(np.float32), 3, axis=2))
    source = np.asarray(raw).astype(np.float32)
    pad = max(crop.width, crop.height)

    def match(scale):
        size = (max(1, round(raw.width * scale)), max(1, round(raw.height * scale)))
        resized = np.asarray(Image.fromarray(source.astype(np.uint8), "RGBA").resize(size, Image.Resampling.LANCZOS))
        resized = resized.astype(np.float32)
        padded = np.zeros((size[1] + 2 * pad, size[0] + 2 * pad, 4), np.float32)
        padded[pad:pad + size[1], pad:pad + size[0]] = resized
        # Transparent pixels count as black, so the body must land on opaque generated pixels.
        rgb = np.ascontiguousarray(padded[:, :, :3] * (padded[:, :, 3:4] / 255))
        if rgb.shape[0] < template.shape[0] or rgb.shape[1] < template.shape[1]:
            return None
        scores = cv2.matchTemplate(rgb, template, cv2.TM_SQDIFF, mask=mask)
        _, _, location, _ = cv2.minMaxLoc(scores)
        error = scores[location[1], location[0]] / max(mask.sum(), 1)
        return float(error), location, padded

    fit = crop.height / raw.height
    best = None
    for scale in np.concatenate([np.linspace(fit * 0.55, fit * 1.15, 49)]):
        result = match(scale)
        if result and (best is None or result[0] < best[0]):
            best = (result[0], scale, result[1], result[2])
    for scale in np.linspace(best[1] * 0.985, best[1] * 1.015, 13):
        result = match(scale)
        if result and result[0] < best[0]:
            best = (result[0], scale, result[1], result[2])
    error, scale, (lx, ly), padded = best
    # Template top-left (0, top) in the donor sits at (lx, ly) in the padded generated image.
    ox, oy = lx, ly - top
    canvas = padded[oy:oy + crop.height, ox:ox + crop.width]
    full = np.zeros(target.shape, np.float32)
    full[:canvas.shape[0], :canvas.shape[1]] = canvas
    return np.sqrt(error), scale / fit, ox - pad, oy - pad, full.astype(float)


def srgb_to_lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_srgb(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > 0.2069, f ** 3, (f - 16 / 116) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    c = xyz @ np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]]).T
    c = np.where(c > 0.0031308, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055, 12.92 * c)
    return np.clip(c * 255, 0, 255)


def skin_mask(pixels):
    """Opaque skin-coloured pixels: warm hue, moderate saturation, not too dark."""
    rgb = pixels[..., :3] / 255.0
    high, low = rgb.max(-1), rgb.min(-1)
    saturation = np.where(high > 0, (high - low) / np.maximum(high, 1e-6), 0)
    warm = (rgb[..., 0] >= rgb[..., 1]) & (rgb[..., 1] >= rgb[..., 2] * 0.85)
    return (pixels[..., 3] > 220) & warm & (saturation > 0.15) & (saturation < 0.75) & (high > 0.2)


def match_skin(generated, donor, seam, strength_other):
    """Move the new head's skin colour (Lab mean and spread) onto the donor head's, which was rendered under the same
    light as the body below the seam. Non-skin pixels (hair, eyes) get part of the shift so the head keeps one light."""
    region = np.zeros(generated.shape[:2], bool)
    region[:seam] = True
    # Target: the donor's skin just below the seam (neck, shoulders, chest), where the colours must meet; donors whose
    # face differs from their own body (pc18) would otherwise leave a step. Few skin pixels there (beards, robes,
    # skulls): the donor's own head skin, rendered under the same light.
    join = np.zeros(generated.shape[:2], bool)
    join[seam:seam + 60] = True
    target = skin_mask(donor) & join
    if target.sum() < 150:
        target = skin_mask(donor) & region
    source = skin_mask(generated) & region
    lab = srgb_to_lab(generated[..., :3])
    donor_lab = srgb_to_lab(donor[..., :3])
    mean_s, std_s = lab[source].mean(0), lab[source].std(0) + 1e-6
    mean_t, std_t = donor_lab[target].mean(0), donor_lab[target].std(0)
    moved = (lab - mean_s) / std_s * std_t + mean_t
    weight = np.where(source, 1.0, strength_other)[..., None]
    out = generated.copy()
    out[..., :3] = lab_to_srgb(lab + weight * (moved - lab))
    return out, {"skin_source_rgb": [round(v) for v in generated[source][:, :3].mean(0)],
                 "skin_target_rgb": [round(v) for v in donor[target][:, :3].mean(0)]}


def head_weight(generated, donor, threshold):
    """Where the new head differs from the donor: the generated pixels there replace the donor's. Codex copies the
    body around the head closely, so shoulders, arms and clothes keep the donor's own pixels (no tone step), while
    the new face, hair, beard or hood comes through, also below the donor's hair line. Holes are filled so a face
    is never patched with the donor's, and the edge is feathered."""
    from scipy import ndimage
    gen_p = generated[:, :, :3] * generated[:, :, 3:4] / 255
    don_p = donor[:, :, :3] * donor[:, :, 3:4] / 255
    difference = np.maximum(np.abs(gen_p - don_p).max(2), np.abs(generated[:, :, 3] - donor[:, :, 3]))
    mask = difference > threshold
    mask = ndimage.binary_opening(mask, iterations=1)
    mask = ndimage.binary_closing(mask, structure=np.ones((3, 3)), iterations=4)
    mask = ndimage.binary_fill_holes(mask)
    labels, count = ndimage.label(mask)
    if count:
        # Keep the head: components touching the top third, or large ones (long hair, beards, hoods).
        sizes = ndimage.sum(mask, labels, range(1, count + 1))
        tops = ndimage.minimum(np.indices(mask.shape)[0], labels, range(1, count + 1))
        keep = [i + 1 for i in range(count) if tops[i] < mask.shape[0] / 3 or sizes[i] > 400]
        mask = np.isin(labels, keep)
    mask = ndimage.binary_dilation(mask, iterations=2)
    return np.clip(ndimage.gaussian_filter(mask.astype(float), 1.2) * 1.4, 0, 1)


def extract(cid):
    info, folder = plan(cid), workspace(cid)
    body, box, crop = donor_crop(info)
    raw = Image.open(folder / "raw.png").convert("RGBA")
    seam, band = info["seam_y"], info.get("seam_band", 6)
    error, scale, dx, dy, generated = register(raw, crop, seam)
    donor = np.asarray(crop).astype(float)
    generated, skin = match_skin(generated, donor, seam, info.get("skin_match_other", 0.15))
    # Weight of the generated pixels: 1 above the band, 0 below, linear inside it.
    rows = np.clip((seam + band / 2 - np.arange(crop.height)) / band, 0, 1)[:, None]
    weight = (rows * head_weight(generated, donor, info.get("difference_threshold", 40)))[:, :, None]
    # Premultiplied blend so the head's own alpha (hair edges) survives.
    gen_p = generated[:, :, :3] * generated[:, :, 3:4] / 255
    don_p = donor[:, :, :3] * donor[:, :, 3:4] / 255
    alpha = weight[:, :, 0] * generated[:, :, 3] + (1 - weight[:, :, 0]) * donor[:, :, 3]
    colour = weight * gen_p + (1 - weight) * don_p
    out = np.zeros_like(donor)
    out[:, :, 3] = alpha
    nz = alpha > 0
    out[nz, :3] = colour[nz] * 255 / alpha[nz, None]
    head_pixels = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    # Below the blend band the weight is 0: copy the donor rows exactly rather than through the float blend.
    keep = seam + (band + 1) // 2
    head_pixels[keep:] = np.asarray(crop)[keep:]
    head = Image.fromarray(head_pixels, "RGBA")
    result = body.copy()
    result.paste(head, box[:2])
    name = info["body_asset"]
    result.save(folder / f"{name}.png")
    # Below the seam band the body is the donor's to the pixel.
    below = np.asarray(result)[box[1] + keep:]
    same = np.array_equal(below, np.asarray(body)[box[1] + keep:])
    report = {"registration_error": round(float(error), 2), "scale_vs_height_fit": round(float(scale), 3),
              "offset": [int(dx), int(dy)],
              "body_below_seam_identical": bool(same), "size": list(result.size), **skin}
    (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(report)
    preview(cid, info, folder, body, result)


def preview(cid, info, folder, donor_body, result):
    # Side by side: donor head, new head, portrait frame 01, enlarged.
    box = tuple(donor_body.width if v is None else v for v in info["head_box"])
    a = donor_body.crop(box)
    b = result.crop(box)
    portrait = Image.open(PORTRAITS / info["portrait_dir"] / "frames" / f"{info['portrait_prefix']}01.png")
    sheet = Image.new("RGBA", (3 * 3 * a.width, 3 * a.height), (62, 64, 72, 255))
    sheet.alpha_composite(a.resize((3 * a.width, 3 * a.height), Image.Resampling.LANCZOS), (0, 0))
    sheet.alpha_composite(b.resize((3 * a.width, 3 * a.height), Image.Resampling.LANCZOS), (3 * a.width, 0))
    p = portrait.convert("RGBA")
    p = p.resize((round(p.width * 3 * a.height / p.height), 3 * a.height), Image.Resampling.LANCZOS)
    sheet.alpha_composite(p, (6 * a.width + (3 * a.width - p.width) // 2, 0))
    sheet.save(folder / "head_compare.png")
    # Full dolls with equipment through the shared preview renderer, the new body under the donor body's name.
    override = folder / "override"
    override.mkdir(exist_ok=True)
    result.save(override / f"{info['donor_body']}.png")
    for label, extra in (("donor", None), ("new", override)):
        command = [sys.executable, str(RENDERER), "--character-ids", str(info["donor_row"]),
                   "--output", str(folder / f"equipment_{label}.png")]
        for item in info["preview_items"]:
            command += ["--item-id", str(item)]
        if extra is not None:
            command += ["--extra-icon-root", str(extra), "--extra-icon-scale", "2"]
        subprocess.run(command, check=True, cwd=ROOT)
    print(f"Wrote head_compare.png, equipment_donor.png, equipment_new.png in {folder}")


def seams(_cid=None):
    """Contact sheet of every planned donor box with its seam, for review before generation."""
    table = json.loads((HERE / "dolls.json").read_text())["characters"]
    tiles = []
    for cid, info in table.items():
        body, box, crop = donor_crop(info)
        tile = Image.new("RGBA", (272, 272), (52, 54, 62, 255))
        tile.alpha_composite(crop, (0, 0))
        draw = ImageDraw.Draw(tile)
        y = info["seam_y"]
        draw.line([(0, y), (272, y)], fill=(255, 60, 60, 255), width=1)
        draw.text((4, 4), f"{cid} {info['donor_body']} seam {y}", fill=(255, 220, 0, 255))
        tiles.append(tile.resize((408, 408), Image.Resampling.LANCZOS))
    sheet = Image.new("RGBA", (5 * 408, -(-len(tiles) // 5) * 408), (30, 30, 34, 255))
    for k, tile in enumerate(tiles):
        sheet.alpha_composite(tile, (k % 5 * 408, k // 5 * 408))
    sheet.save(HERE / "seams.png")
    print(f"Wrote {HERE / 'seams.png'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "extract"):
        sub.add_parser(name).add_argument("character")
    sub.add_parser("seams")
    arguments = parser.parse_args()
    if arguments.command == "seams":
        seams()
        return
    {"prepare": prepare, "extract": extract}[arguments.command](arguments.character)


if __name__ == "__main__":
    main()
