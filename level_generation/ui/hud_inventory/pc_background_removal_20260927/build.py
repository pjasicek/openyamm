"""Deterministic PC alpha investigation; writes review candidates only.

Uses current accepted RGB, archived native silhouettes, and a seeded binary
graph cut. No image generation, RGB edits, registration, crop, or installation.
Requires the pipeline's existing Pillow, NumPy and SciPy dependencies.
"""

import argparse
import hashlib
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import PIL
import scipy
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.cluster.vq import kmeans2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import breadth_first_order, maximum_flow
from scipy.special import logsumexp


HERE = Path(__file__).resolve().parent
HUD = HERE.parent
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from native_sources import native_source

SAMPLE_FRAMES = [1, 12, 35, 36, 38, 39, 55, 56]
PLATE_FRAMES = [1, 4, 5, 6, 8, 11, 12, 18, 19, 25, 26, 34, 35, 36, 37, 38, 39, 45, 47, 53, 55, 56]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def largest(mask):
    labels, count = ndimage.label(mask)
    if not count:
        raise ValueError("No foreground component; inspect this frame separately")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    selected = sizes.argmax()
    return labels == selected, int(sizes.sum() - sizes[selected])


def inputs():
    accepted = json.loads((HUD / "accepted_icons.json").read_text())["records"]
    families = json.loads((HUD / "review/second_pass/portrait_families/manifest.json").read_text())["families"]
    present, missing = [], []
    for family in families:
        frames = []
        for number in range(1, 57):
            target = f"engine--icons--{family['prefix']}{number:02d}.bmp"
            if target not in accepted:
                continue
            record = accepted[target]
            native = native_source(record["source"])
            if sha(native) != record["source_sha256"] or sha(record["artifact"]) != record["sha256"]:
                raise ValueError(f"Source/acceptance hash changed: {target}")
            frames.append(dict(record, number=number, native=str(native), target=target))
        if frames and len(frames) != 56:
            raise ValueError(f"Incomplete accepted family: {family['path']}")
        if frames:
            present.append({"id": family["path"], "frames": frames})
        else:
            missing.append(family["path"])
    return present, missing


def native_rgb(frame):
    with Image.open(frame["native"]) as image:
        if image.size != (59, 79):
            raise ValueError(f"Unexpected native size: {frame['native']}")
        return np.asarray(image.convert("RGB"))


def backing_estimate(families):
    """The originals share a textured backing, with palette quantization differences.

    Frame 36 exposes much of it. Estimate its RGB at each native coordinate from
    all identities, then refine from other poses. Low-support pixels are marked
    unknown, never treated as reliable background. This is a geometric guide,
    not the alpha for the restored artwork.
    """
    def green_samples(images):
        red, green, blue = images.transpose(3, 0, 1, 2)
        return (green - red > 4) & (green - blue > 2) & (green > 45) & (green < 110)

    initial = np.array([native_rgb(family["frames"][35]) for family in families], dtype=float)
    eligible = green_samples(initial)
    if not eligible.any(axis=0).all():
        raise ValueError("Backing estimate has unsupported coordinates; inspect the reference set")
    rough = np.nanmedian(np.where(eligible[..., None], initial, np.nan), axis=0)
    samples = np.array([native_rgb(frame) for family in families for frame in family["frames"]
                        if frame["number"] in PLATE_FRAMES], dtype=float)
    eligible = green_samples(samples) & (np.max(np.abs(samples - rough), axis=-1) < 12)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered")
        estimate = np.nanmedian(np.where(eligible[..., None], samples, np.nan), axis=0)
    support = eligible.sum(axis=0)
    estimate[support == 0] = 0  # Explicitly unknown and excluded in native_guide().
    return estimate, support


def native_guide(native, backing, support):
    similar = (np.max(np.abs(native.astype(float) - backing), axis=-1) < 17) & (support >= 3)
    edge = np.zeros(similar.shape, bool)
    edge[0] = edge[-1] = True
    edge[:, 0] = edge[:, -1] = True
    background = ndimage.binary_propagation(edge & similar, mask=similar)
    foreground, _ = largest(ndimage.binary_fill_holes(~background))
    return np.repeat(np.repeat(foreground, 2, axis=0), 2, axis=1)


def color_cost(data, samples):
    # Fixed seed makes clustering reproducible; this learns colors, not new art.
    _, labels = kmeans2(samples, 5, iter=15, minit="++", seed=0)
    components = []
    for number in range(5):
        points = samples[labels == number]
        if len(points) < 4:
            continue
        covariance = np.cov(points.T) + np.eye(3) * .4
        delta = data - points.mean(axis=0)
        score = -.5 * np.einsum("...i,ij,...j->...", delta, np.linalg.inv(covariance), delta)
        score -= .5 * np.linalg.slogdet(covariance)[1]
        score += np.log(len(points) / len(samples))
        components.append(score)
    if not components:
        raise ValueError("Insufficient color samples; inspect this frame separately")
    return -logsumexp(components, axis=0)


def cut_mask(rgb, guide):
    """Refine only a band around the native guide; no image coordinates change."""
    distance = ndimage.distance_transform_edt(guide) - ndimage.distance_transform_edt(~guide)
    height, width = guide.shape
    count = height * width
    source, sink = count, count + 1
    indices = np.arange(count).reshape(height, width)
    data = rgb.astype(float) / 8
    neighbors = []
    for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        ya, yb = slice(0, height - dy), slice(dy, height)
        xa = slice(max(0, -dx), min(width, width - dx))
        xb = slice(max(0, dx), min(width, width + dx))
        first, second = indices[ya, xa].ravel(), indices[yb, xb].ravel()
        delta = np.sum((rgb[ya, xa].astype(float) - rgb[yb, xb].astype(float)) ** 2, axis=-1)
        cost = (2 * np.exp(-delta / (2 * 18 ** 2)) + .08) / (np.sqrt(2) if dy and dx else 1)
        neighbors.append((first, second, cost.ravel()))
    foreground = guide.copy()
    for _ in range(3):
        background_cost = color_cost(data, data[~foreground])
        foreground_cost = color_cost(data, data[foreground])
        base = np.minimum(background_cost, foreground_cost)
        background_cost -= base
        foreground_cost -= base
        foreground_cost += np.maximum(-distance, 0) * .16
        background_cost += np.maximum(distance, 0) * .16
        background_cost[distance > 6] = 100000
        foreground_cost[distance < -8] = 100000
        rows, columns = [np.full(count, source), np.arange(count)], [np.arange(count), np.full(count, sink)]
        weights = [background_cost.ravel(), foreground_cost.ravel()]
        for first, second, cost in neighbors:
            rows.extend([first, second])
            columns.extend([second, first])
            weights.extend([cost, cost])
        graph = coo_matrix((np.maximum(1, np.round(np.concatenate(weights) * 100)).astype(np.int64),
                            (np.concatenate(rows), np.concatenate(columns))), shape=(count + 2, count + 2)).tocsr()
        flow = maximum_flow(graph, source, sink)
        residual = graph - flow.flow
        residual.data[residual.data <= 0] = 0
        residual.eliminate_zeros()
        reachable = breadth_first_order(residual, source, directed=True, return_predecessors=False)
        result = np.zeros(count + 2, bool)
        result[reachable] = True
        result = result[:count].reshape(height, width)
        if np.array_equal(foreground, result):
            break
        foreground = result
    # Closing enclosed holes protects similarly colored eyes/skin. True enclosed
    # background holes and detached fine features require explicit mask review.
    foreground, detached = largest(ndimage.binary_fill_holes(foreground))
    alpha = ndimage.gaussian_filter(foreground.astype(float), .55)
    alpha[alpha < .02] = 0
    alpha[alpha > .98] = 1
    return np.round(alpha * 255).astype(np.uint8), {
        "native_guide_area": int(guide.sum()), "candidate_area": int(foreground.sum()),
        "guide_disagreement_pixels": int(np.count_nonzero(foreground != guide)),
        "discarded_detached_pixels": detached,
        "transparent_pixels": int(np.count_nonzero(alpha == 0)),
        "soft_outline_pixels": int(np.count_nonzero((alpha > 0) & (alpha < 1))),
    }


def contact(output, families, names, filename, frame_number=1):
    board = Image.new("RGB", (5 * 126, len(names) * 183), "#242628")
    draw = ImageDraw.Draw(board)
    for row, name in enumerate(names):
        family = next(family for family in families if family["id"] == name)
        record = next(frame for frame in family["frames"] if frame["number"] == frame_number)
        source = Image.open(output / record["before"]).convert("RGBA")
        candidate = Image.open(output / record["candidate"]).convert("RGBA")
        panels = [source.convert("RGB")]
        for color in ["#eeeeee", "#181818"]:
            panels.append(Image.alpha_composite(Image.new("RGBA", candidate.size, color), candidate).convert("RGB"))
        panels.append(candidate.getchannel("A").convert("RGB"))
        panels.append(Image.open(output / record["native_preview"]).convert("RGB"))
        for column, panel in enumerate(panels):
            x, y = column * 126, row * 183
            label = ["accepted", "light", "dark", "alpha", "native"][column]
            draw.text((x + 2, y + 2), f"{name} {frame_number:02d} {label}", fill="white")
            board.paste(panel, (x + 2, y + 22))
    board.save(output / filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "review")
    parser.add_argument("--frames", default=",".join(map(str, SAMPLE_FRAMES)), help="Comma-separated frames or all")
    parser.add_argument("--families", help="Comma-separated family IDs; default all available families")
    parser.add_argument("--full-family", action="append", default=[], help="Also include all 56 poses for this family")
    args = parser.parse_args()
    if (args.output / "manifest.json").exists():
        raise SystemExit("Review already exists; choose a new --output to preserve the previous investigation")
    started = time.monotonic()
    families, missing = inputs()
    backing, support = backing_estimate(families)
    selected_frames = set(range(1, 57)) if args.frames == "all" else set(map(int, args.frames.split(",")))
    if not selected_frames or not selected_frames <= set(range(1, 57)):
        raise SystemExit("Frame numbers must be within 1..56")
    selected_families = set(args.families.split(",")) if args.families else {family["id"] for family in families}
    available = {family["id"] for family in families}
    if not (selected_families | set(args.full_family)) <= available:
        raise SystemExit("Requested family is unavailable")
    args.output.mkdir(parents=True, exist_ok=True)
    Image.fromarray(backing.round().astype(np.uint8)).save(args.output / "native_backing_estimate.png")
    output_families = []
    verification = {"rgb_identical": 0, "dimensions_identical": 0, "repeat_masks_identical": 0}
    for family in families:
        if family["id"] not in selected_families:
            continue
        folder = args.output / family["id"]
        folder.mkdir(exist_ok=True)
        output_frames = []
        for frame in family["frames"]:
            if frame["number"] not in selected_frames and family["id"] not in args.full_family:
                continue
            with Image.open(frame["artifact"]) as image:
                before = np.array(image.convert("RGBA"))
            if before.shape != (158, 118, 4) or np.any(before[:, :, 3] != 255):
                raise ValueError(f"Expected the accepted opaque 118x158 portrait: {frame['target']}")
            native = native_rgb(frame)
            guide = native_guide(native, backing, support)
            alpha, metrics = cut_mask(before[:, :, :3], guide)
            if not output_frames:
                repeated, _ = cut_mask(before[:, :, :3], guide)
                assert np.array_equal(alpha, repeated), frame["target"]
                verification["repeat_masks_identical"] += 1
            candidate = before.copy()
            candidate[:, :, 3] = alpha
            stem = f"{frame['number']:02d}"
            Image.fromarray(before).save(folder / f"{stem}_before.png")
            Image.fromarray(candidate).save(folder / f"{stem}.png")
            Image.fromarray(alpha).save(folder / f"{stem}_alpha.png")
            Image.fromarray(native).resize((118, 158), Image.Resampling.NEAREST).save(folder / f"{stem}_native.png")
            reloaded = np.asarray(Image.open(folder / f"{stem}.png"))
            assert reloaded.shape == before.shape, frame["target"]
            assert np.array_equal(reloaded[:, :, :3], before[:, :, :3]), frame["target"]
            verification["rgb_identical"] += 1
            verification["dimensions_identical"] += 1
            output_frames.append({
                "number": frame["number"], "target": frame["target"],
                "accepted_source": frame["artifact"], "accepted_sha256": frame["sha256"],
                "native_source": frame["native"], "native_sha256": frame["source_sha256"],
                "before": f"{family['id']}/{stem}_before.png", "candidate": f"{family['id']}/{stem}.png",
                "alpha": f"{family['id']}/{stem}_alpha.png", "native_preview": f"{family['id']}/{stem}_native.png",
                "candidate_sha256": sha(folder / f"{stem}.png"), "metrics": metrics,
            })
        output_families.append({"id": family["id"], "frames": output_frames})
        if len(output_families) % 12 == 0:
            print(f"Prepared {len(output_families)} families / {verification['rgb_identical']} frames", flush=True)
    manifest = {
        "status": "investigation_only_all_candidates_require_visual_review", "families": output_families,
        "available_family_count": len(families), "available_frame_count": sum(len(f["frames"]) for f in families),
        "missing_native_families": missing, "candidate_count": verification["rgb_identical"],
        "verification": verification, "seconds": round(time.monotonic() - started, 2),
        "accepted_index_sha256": sha(HUD / "accepted_icons.json"), "code_sha256": sha(__file__),
        "backing_reference_frames": PLATE_FRAMES, "backing_low_support_pixels": int(np.count_nonzero(support < 3)),
        "backing_sources": [{"path": frame["native"], "sha256": frame["source_sha256"]}
                            for family in families for frame in family["frames"] if frame["number"] in PLATE_FRAMES],
        "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "pillow": PIL.__version__},
        "notes": ["RGB and canvas are unchanged, including RGB under transparent pixels.",
                  "A seed of zero makes color clustering deterministic in this recorded environment.",
                  "Partial alpha is confined to a narrow smoothed silhouette edge.",
                  "Guide errors, similar-color edges, detached features and enclosed holes need review.",
                  "No accepted art, ledger, runtime asset or game code was modified."],
    }
    save_json(args.output / "manifest.json", manifest)
    viewer = {key: manifest[key] for key in ["status", "families", "candidate_count", "verification", "seconds"]}
    (args.output / "data.js").write_text("window.PC_ALPHA = " + json.dumps(viewer).replace("<", "\\u003c") + ";\n")
    available = {family["id"] for family in output_families}
    if 1 in selected_frames and {"pc01", "7pc19", "pc23", "pc41"} <= available:
        contact(args.output, output_families, ["pc01", "7pc19", "pc23", "pc41"], "examples.png")
    if 1 in selected_frames and {"wets_", "pc21", "pc24", "pc25", "pc37", "7pc24"} <= available:
        contact(args.output, output_families, ["wets_", "pc21", "pc24", "pc25", "pc37", "7pc24"], "edge_cases.png")
    print(json.dumps({key: manifest[key] for key in ["candidate_count", "verification", "seconds"]}))


if __name__ == "__main__":
    main()
