"""Conservative PC masks: separate stone guidance, solid oval interiors, preserved accessories.

This revision deliberately does not train a foreground/background competition.
It removes connected, positively identified backing and keeps the accepted RGB.
The v1 builder and review remain immutable provenance for comparisons.
"""

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull

import build as prior


HERE = Path(__file__).resolve().parent


def convex_mask(mask):
    ys, xs = np.nonzero(mask)
    points = np.column_stack((xs, ys))
    hull = ConvexHull(points)
    output = Image.new("L", (mask.shape[1], mask.shape[0]))
    ImageDraw.Draw(output).polygon([tuple(point) for point in points[hull.vertices]], fill=255)
    return np.asarray(output) > 0


def disk(radius):
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    return xx * xx + yy * yy <= radius * radius


def extract_alpha(rgb, guide, rounded, stone):
    pixels = rgb.astype(float)
    red, green, blue = pixels.transpose(2, 0, 1)
    distance = ndimage.distance_transform_edt(guide) - ndimage.distance_transform_edt(~guide)
    green_material = (green > red + 3) & (green > blue + 2)
    # Only known green exterior pixels teach the backing model. Pale accessories
    # never become background examples merely because they sit outside the guide.
    samples = pixels[(distance < -2) & green_material]
    if len(samples) < 32:
        raise ValueError("Not enough exterior backing samples; needs a saved manual mask")
    features = np.stack([red - green, blue - green, green * .3], axis=-1)
    sample_features = np.stack([samples[:, 0] - samples[:, 1], samples[:, 2] - samples[:, 1],
                                samples[:, 1] * .3], axis=-1)
    center = np.median(sample_features, axis=0)
    covariance = np.cov(sample_features.T) + np.diag([4, 4, 9])
    delta = features - center
    color_distance = np.sqrt(np.einsum("...i,ij,...j->...", delta, np.linalg.inv(covariance), delta))
    backing_ceiling = float(np.percentile(samples[:, 1], 99) + 8)
    removable = green_material & (color_distance < 4) & (green < backing_ceiling)
    # The accepted sheets also contain non-green border contamination. Treat the
    # far exterior as background; the eight-pixel refinement band retains nearby
    # accessories regardless of their color. Larger art/guide mismatches need a mask correction.
    removable |= distance < -8
    # A stone guide can contain palette-induced protrusions. Do not stretch a
    # convex core between those protrusions: protect its interior directly.
    if stone:
        core = distance > 6
    elif rounded:
        core = ndimage.binary_erosion(convex_mask(guide), iterations=2)
    else:
        core = distance > 2
    removable &= ~core
    edge = np.zeros(guide.shape, bool)
    edge[0] = edge[-1] = True
    edge[:, 0] = edge[:, -1] = True
    background = ndimage.binary_propagation(edge & removable, mask=removable)
    foreground = ndimage.binary_fill_holes(~background)
    labels, count = ndimage.label(foreground)
    if not count:
        raise ValueError("No foreground; needs a saved manual mask")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    main = labels == sizes.argmax()
    nearness = ndimage.distance_transform_edt(~main)
    kept = main.copy()
    retained_components, discarded_pixels = 0, 0
    for label in range(1, count + 1):
        if label == sizes.argmax():
            continue
        component = labels == label
        if np.any(component & core) or (sizes[label] >= 3 and np.any(component & (nearness < 4))
                                       and np.any(component & (distance > -8))):
            kept |= component
            retained_components += 1
        else:
            discarded_pixels += int(sizes[label])
    # For nearly convex portraits, bridge short bites into an otherwise full oval.
    # Padding keeps closing extensive at canvas edges; it cannot shrink a head.
    radius = 2 if stone else 4 if rounded else 1
    closed = ndimage.binary_closing(np.pad(kept, 8), structure=disk(radius))[8:-8, 8:-8]
    assert not np.any(kept & ~closed)
    kept = closed
    alpha = ndimage.gaussian_filter(kept.astype(float), .5)
    alpha[alpha < .02] = 0
    alpha[alpha > .98] = 1
    alpha = np.round(alpha * 255).astype(np.uint8)
    deep_core = ndimage.binary_erosion(core, iterations=2)
    return alpha, {
        "native_guide_area": int(guide.sum()), "candidate_area": int(kept.sum()),
        "transparent_pixels": int(np.count_nonzero(alpha == 0)),
        "soft_outline_pixels": int(np.count_nonzero((alpha > 0) & (alpha < 255))),
        "retained_accessory_components": retained_components, "discarded_detached_pixels": discarded_pixels,
        "protected_core_pixels": int(deep_core.sum()),
        "protected_core_lost_pixels": int(np.count_nonzero(alpha[deep_core] != 255)),
        "backing_green_ceiling": round(backing_ceiling, 3),
    }


def panel_contact(output, families, cases, name):
    by_id = {family["id"]: family for family in families}
    board = Image.new("RGB", (4 * 126, len(cases) * 184), "#242628")
    draw = ImageDraw.Draw(board)
    for row, (family_id, number) in enumerate(cases):
        frame = next(frame for frame in by_id[family_id]["frames"] if frame["number"] == number)
        images = [Image.open(output / frame[key]).convert("RGBA") for key in ["before", "prior", "candidate"]]
        panels = [images[0], Image.alpha_composite(Image.new("RGBA", (118, 158), "#eeeeee"), images[1]),
                  Image.alpha_composite(Image.new("RGBA", (118, 158), "#eeeeee"), images[2]),
                  Image.alpha_composite(Image.new("RGBA", (118, 158), "#151719"), images[2])]
        for column, image in enumerate(panels):
            x, y = column * 126, row * 184
            label = ["accepted", "v1", "v2 light", "v2 dark"][column]
            draw.text((x + 2, y + 2), f"{family_id} {number:02d} {label}", fill="white")
            board.paste(image, (x + 2, y + 22))
    board.save(output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "review_v2_04")
    args = parser.parse_args()
    output = args.output.resolve()
    if (output / "manifest.json").exists():
        raise SystemExit("Existing review is immutable; choose a fresh --output")
    started = time.monotonic()
    old_path = HERE / "review/manifest.json"
    old = json.loads(old_path.read_text())
    if prior.sha(HERE / "build.py") != old["code_sha256"]:
        raise ValueError("The v1 geometry helper changed; create an explicit reference revision")
    families, missing = prior.inputs()
    backing, support = prior.backing_estimate(families)
    by_id = {family["id"]: family for family in families}
    output.mkdir(parents=True, exist_ok=True)
    output_families = []
    verification = {"rgb_identical": 0, "dimensions_identical": 0, "repeat_masks_identical": 0,
                    "protected_core_lost_pixels": 0}
    for old_family in old["families"]:
        family_id = old_family["id"]
        family = by_id[family_id]
        neutral = prior.native_guide(prior.native_rgb(family["frames"][0]), backing, support)
        deficit = float(1 - neutral.sum() / convex_mask(neutral).sum())
        rounded = deficit < .085
        frames = []
        folder = output / family_id
        folder.mkdir(exist_ok=True)
        for old_frame in old_family["frames"]:
            number = old_frame["number"]
            frame = family["frames"][number - 1]
            if frame["sha256"] != old_frame["accepted_sha256"]:
                raise ValueError(f"Accepted input changed since v1: {frame['target']}")
            rgba = np.asarray(Image.open(frame["artifact"]).convert("RGBA"))
            guide = prior.native_guide(prior.native_rgb(frame), backing, support)
            if number == 12:
                guide |= neutral
            alpha, metrics = extract_alpha(rgba[:, :, :3], guide, rounded, number == 12)
            if number in [1, 12]:
                repeated, _ = extract_alpha(rgba[:, :, :3], guide, rounded, number == 12)
                assert np.array_equal(repeated, alpha)
                verification["repeat_masks_identical"] += 1
            result = rgba.copy()
            result[:, :, 3] = alpha
            path = folder / f"{number:02d}.png"
            Image.fromarray(result).save(path)
            Image.fromarray(alpha).save(folder / f"{number:02d}_alpha.png")
            reloaded = np.asarray(Image.open(path))
            assert reloaded.shape == rgba.shape == (158, 118, 4)
            assert np.array_equal(reloaded[:, :, :3], rgba[:, :, :3])
            verification["rgb_identical"] += 1
            verification["dimensions_identical"] += 1
            verification["protected_core_lost_pixels"] += metrics["protected_core_lost_pixels"]
            previous = np.asarray(Image.open(HERE / "review" / old_frame["candidate"]))[:, :, 3]
            pale = rgba[:, :, :3].min(axis=2) > 100
            metrics.update(pale_pixels_removed_v1=int(np.count_nonzero(pale & (previous < 128))),
                           pale_pixels_removed_v2=int(np.count_nonzero(pale & (alpha < 128))))
            def relative_old(key):
                return os.path.relpath(HERE / "review" / old_frame[key], output)
            frames.append({
                "number": number, "target": frame["target"], "accepted_source": frame["artifact"],
                "accepted_sha256": frame["sha256"], "native_source": frame["native"],
                "native_sha256": frame["source_sha256"], "neutral_native_sha256": family["frames"][0]["source_sha256"],
                "before": relative_old("before"), "prior": relative_old("candidate"),
                "native_preview": relative_old("native_preview"), "candidate": f"{family_id}/{number:02d}.png",
                "alpha": f"{family_id}/{number:02d}_alpha.png", "candidate_sha256": prior.sha(path),
                "stone_guide": number == 12, "rounded_profile": rounded, "metrics": metrics,
            })
        output_families.append({"id": family_id, "frames": frames, "rounded_profile": rounded,
                                "neutral_convexity_deficit": round(deficit, 6)})
    manifest = {
        "revision": 2, "status": "candidate_revision_requires_review", "families": output_families,
        "candidate_count": verification["rgb_identical"], "verification": verification,
        "prior_manifest_sha256": prior.sha(old_path), "code_sha256": prior.sha(__file__),
        "geometry_helper_sha256": prior.sha(HERE / "build.py"), "seconds": round(time.monotonic() - started, 2),
        "missing_native_families": missing, "versions": old["versions"],
        "policy": "positive_backing_removal_stone_neutral_union_solid_oval_accessory_retention",
    }
    prior.save_json(output / "manifest.json", manifest)
    (output / "data.js").write_text("window.PC_ALPHA = " + json.dumps(manifest).replace("<", "\\u003c") + ";\n")
    cases = [(name, 12) for name in ["7pc01", "7pc02", "7pc04", "7pc05", "7pc08", "7pc19", "malea", "wets_"]]
    panel_contact(output, output_families, cases, "stone_comparison.png")
    cases = [("7pc05", 1), ("7pc05", 55), ("7pc08", 1), ("7pc19", 1), ("malea", 1), ("malea", 55)]
    panel_contact(output, output_families, cases, "accessories_comparison.png")
    print(json.dumps({key: manifest[key] for key in ["candidate_count", "verification", "seconds"]}))


if __name__ == "__main__":
    main()
