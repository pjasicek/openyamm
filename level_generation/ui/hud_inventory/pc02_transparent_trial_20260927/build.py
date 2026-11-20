"""Extract the two pc02 imagegen masters onto fixed native x2 canvases.

No segmentation, color key, oval stencil, repainting, or runtime installation.
Generated alpha is resampled with RGB in premultiplied form. The archived native
silhouettes are measurement guides only; they never replace generated alpha.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SIZE = (118, 158)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def box_for(alpha, threshold):
    ys, xs = np.where(alpha >= threshold)
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def resample(cell, scale, offset):
    """Subpixel placement and downsampling in one premultiplied Lanczos pass."""
    # Pillow resize supports a floating source window and Lanczos, whereas its
    # affine transform only supports bicubic. Padding makes outside samples zero.
    border = max(cell.size)
    padded = Image.new("RGBA", (cell.width + 2 * border, cell.height + 2 * border))
    padded.paste(cell, (border, border))
    x, y = offset
    sx, sy = scale
    window = (border - x / sx, border - y / sy,
              border + (SIZE[0] - x) / sx, border + (SIZE[1] - y) / sy)
    return padded.convert("RGBa").resize(SIZE, Image.Resampling.LANCZOS, box=window).convert("RGBA")


def context(portrait, hud, ring=True):
    result = hud["basebar"].crop((39, 55, 163, 219))
    result.alpha_composite(portrait.resize((112, 152), Image.Resampling.LANCZOS), (6, 6))
    result.alpha_composite(hud["facemask"].resize((120, 160), Image.Resampling.LANCZOS), (2, 2))
    if ring:
        result.alpha_composite(hud["selring"].resize((120, 160), Image.Resampling.LANCZOS), (0, 2))
    return result


def composite(image, color):
    result = Image.new("RGBA", image.size, color)
    result.alpha_composite(image)
    return result.convert("RGB")


def build():
    sources = json.loads((HERE / "sources.json").read_text())
    geometry = json.loads((HERE / "geometry.json").read_text())
    masters = json.loads((HERE / "masters.json").read_text())
    outputs = ["frames", "uncorrected", "native", "alpha", "context"]
    for folder in outputs:
        (HERE / folder).mkdir(exist_ok=True)
    raw = {}
    for letter in "AB":
        path = HERE / letter / "attempt_01/raw.png"
        assert digest(path) == masters[letter]["sha256"], "Changed master"
        raw[letter] = Image.open(path).convert("RGBA")
    hud = {name: Image.open(ROOT / f"assets_dev/engine/icons_x2/{name}.png").convert("RGBA")
           for name in ["basebar", "facemask", "selring"]}
    accepted = json.loads((HERE.parent / "accepted_icons.json").read_text())["records"]
    records = []
    for source, measure in zip(sources["frames"], geometry["frames"]):
        number = source["frame"]
        assert measure["frame"] == number
        source_path = ROOT / source["source"]
        assert digest(source_path) == source["source_sha256"], "Changed original"
        name = f"pc02-{number:02}.png"
        record = accepted[f"engine--icons--pc02-{number:02}.bmp"]
        assert digest(Path(record["artifact"])) == record["sha256"], "Changed accepted art"
        runtime_path = ROOT / f"assets_dev/engine/icons_x2/{name}"
        assert digest(runtime_path) == record["sha256"], "Runtime differs from acceptance receipt"
        letter = source["sheet"]
        rect = measure["source_rect"]
        cell = raw[letter].crop(rect)
        cell_alpha = np.asarray(cell.getchannel("A"))
        outline = box_for(cell_alpha, 128)
        fringe = box_for(cell_alpha, 8)
        core = box_for(cell_alpha, 250)
        native = measure["native_box"]
        center = (outline[0] + outline[2]) / 2
        # A fixed x=59 pivot for every output; the silhouette's center follows
        # that pivot, while gaze, tilt and internal facial motion stay intact.
        # Bottom uses the nearly opaque core, so a fuzzy generated neck cannot
        # leave a floating transparent strip underneath the portrait.
        width = outline[2] - outline[0]
        height = core[3] - outline[1]
        native_width = native[2] - native[0]
        native_height = native[3] - native[1]
        scale_height = native_height / height
        scale_width = native_width / width
        scale_fringe = 59 / max(center - fringe[0], fringe[2] - center)
        # Width containment must never lower the crown. Match native height
        # independently while retaining the existing horizontal fit.
        scale = min(scale_height, scale_width, scale_fringe)
        offset = (59 - scale * center, native[3] - scale_height * core[3])
        candidate = resample(cell, (scale, scale_height), offset)
        candidate.save(HERE / "frames" / name)
        candidate.getchannel("A").save(HERE / "alpha" / name)

        # Nominal reference-window extraction, before any per-frame correction.
        slot = source["slot"]
        reference_scale = raw[letter].width / 1092
        nominal_scale = 1 / reference_scale
        left = (slot % 7 * 156 + 19) * reference_scale
        top = (slot // 7 * 182 + 12) * reference_scale
        nominal = resample(cell, (nominal_scale, nominal_scale),
                           ((rect[0] - left) * nominal_scale, (rect[1] - top) * nominal_scale))
        nominal.save(HERE / "uncorrected" / name)
        original = Image.open(source_path).convert("RGB").resize(SIZE, Image.Resampling.NEAREST)
        original.save(HERE / "native" / name)
        context(candidate, hud).save(HERE / "context" / name)
        a = np.asarray(candidate.getchannel("A"))
        corrected_box = box_for(a, 128)
        assert abs(corrected_box[1] - native[1]) <= 1, f"Crown height changed: {name}"
        assert corrected_box[3] == native[3], f"Bottom anchor changed: {name}"
        sample_x = width / (native_width / 2)
        sample_y = (outline[3] - outline[1]) / (native_height / 2)
        assert min(sample_x, sample_y) > 2, f"Insufficient actual master sampling: {name}"
        assert np.count_nonzero(a == 0) > 500, f"Missing transparency: {name}"
        notes = []
        if number in [35, 36]:
            notes.append("Lowered pose: matched to the native visible fragment; not enlarged into a full head.")
        if number == 12:
            notes.append("Stone material uses the generated alpha, with no color-based removal.")
        if number == 37:
            notes.append("Native tilted pose has an off-center bottom contact; inspect its motion against neighbors.")
        mismatch = (width / (outline[3] - outline[1])) / (native_width / native_height) - 1
        if abs(mismatch) > .10:
            notes.append("Generated silhouette proportions differ from the native by more than 10%; review this pose.")
        edge = np.concatenate([a[:, 0], a[:, -1], a[0]])
        records.append({
            "number": number, "name": name, "sheet": letter, "slot": slot,
            "candidate": f"frames/{name}", "uncorrected": f"uncorrected/{name}",
            "native": f"native/{name}", "alpha": f"alpha/{name}", "context": f"context/{name}",
            "source_rect": rect, "native_box": native, "master_box": outline,
            "core_box": core, "output_box": corrected_box,
            "scale": round(scale, 8), "scale_y": round(scale_height, 8),
            "offset": [round(v, 6) for v in offset],
            "sampling": [round(sample_x, 4), round(sample_y, 4)],
            "scale_adjustment_percent": round((scale / nominal_scale - 1) * 100, 2),
            "silhouette_aspect_difference_percent": round(mismatch * 100, 2),
            "transparent_pixels": int(np.count_nonzero(a == 0)),
            "bottom_center_alpha": int(a[-1, 59]), "outline_boundary_peak_alpha": int(edge.max()),
            "sha256": digest(HERE / "frames" / name), "source_sha256": source["source_sha256"],
            "runtime_sha256": digest(runtime_path), "notes": notes,
        })

    # Flat review sheets have no influence on the RGBA exports.
    for letter in "AB":
        contact = Image.new("RGB", (7 * 132, 4 * 190), (30, 33, 39))
        draw = ImageDraw.Draw(contact)
        for record in [r for r in records if r["sheet"] == letter]:
            slot = record["slot"]
            x, y = (slot % 7) * 132 + 7, (slot // 7) * 190 + 22
            draw.text((x, y - 16), record["name"][:-4], fill=(225, 229, 237))
            contact.paste(composite(Image.open(HERE / record["candidate"]), (65, 70, 81, 255)), (x, y))
        contact.save(HERE / letter / "contact.png")
    sample_numbers = [1, 12, 18, 25, 29, 35, 36, 37, 38, 39, 53, 56]
    contact = Image.new("RGB", (6 * 270, 2 * 378), (28, 31, 37))
    draw = ImageDraw.Draw(contact)
    for i, number in enumerate(sample_numbers):
        record = records[number - 1]
        x, y = (i % 6) * 270, (i // 6) * 378
        draw.text((x + 8, y + 6), f"pc02-{number:02}: original / aligned", fill=(230, 230, 230))
        contact.paste(Image.open(HERE / record["native"]), (x + 8, y + 26))
        candidate = Image.open(HERE / record["candidate"])
        contact.paste(composite(candidate, (240, 240, 240, 255)), (x + 140, y + 26))
        contact.paste(composite(candidate, (5, 5, 5, 255)), (x + 8, y + 203))
        contact.paste(context(candidate, hud).convert("RGB"), (x + 137, y + 199))
    contact.save(HERE / "comparison.png")
    data = {"family": "pc02", "status": "trial_for_visual_review", "size": list(SIZE),
            "masters": masters, "frames": records,
            "sampling_min": min(min(r["sampling"]) for r in records),
            "verification": {"count": len(records), "rgba_size": list(SIZE),
                             "original_hashes_unchanged": 56, "runtime_hashes_unchanged": 56,
                             "raw_alpha_preserved": True, "color_key_or_native_mask_applied": False}}
    write_json(HERE / "manifest.json", data)
    (HERE / "manifest.js").write_text("window.PC02_TRIAL = " + json.dumps(data) + ";\n")
    print(json.dumps({"count": len(records), "minimum_actual_sampling": data["sampling_min"],
                      "scale_adjustment_range_percent": [min(r["scale_adjustment_percent"] for r in records),
                                                         max(r["scale_adjustment_percent"] for r in records)],
                      "bottom_center_alpha_range": [min(r["bottom_center_alpha"] for r in records),
                                                    max(r["bottom_center_alpha"] for r in records)],
                      "shape_review_frames": [r["number"] for r in records
                                              if abs(r["silhouette_aspect_difference_percent"]) > 10]}, indent=2))


if __name__ == "__main__":
    build()
