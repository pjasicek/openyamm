#!/usr/bin/env python3
"""Compare MM9 ABC meshes region by region, to find models that share a body.

Usage (any working directory):
    python3 level_generation/creatures/claude_shared/mm9_meshcmp.py a:b,c [d:e ...]

Names are ABC file stems, case-insensitive (peasantm4, foraddarre, wyrd_old). For each pair it prints, per region
(head, torso, arms, legs, from each vertex's dominant bone), the p90 and max distance in cm from A's LOD0 vertices to
B's LOD0 surface, both raw and after removing one rigid translation (the median offset; PeasantM2d was PeasantM2
shifted 2.6 cm), plus whether the skeletons match (same node names and bind matrices). 1 MM9 unit = 2.56 cm.
"""

import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "mm9_import_discovery"))
import convert_abc_model as abc  # noqa: E402

MODELS = REPO / "mm9" / "extracted" / "MODELS" / "MODELS"
CM = 2.56
REGIONS = ("head", "torso", "arms", "legs")


def find_model(stem):
    for path in MODELS.iterdir():
        if path.suffix.lower() == ".abc" and path.stem.lower() == stem.lower():
            return path
    raise SystemExit(f"no ABC named {stem} in {MODELS}")


def region_of(name):
    n = name.lower()
    if any(k in n for k in ("head", "neck", "ponytail", "jaw", "eye", "hair", "ear")):
        return "head"
    if any(k in n for k in ("clavicle", "arm", "hand", "finger", "elbow", "wrist")):
        return "arms"
    if any(k in n for k in ("thigh", "calf", "foot", "toe", "leg", "knee")):
        return "legs"
    return "torso"


def load(stem):
    model = abc.read_abc(find_model(stem))
    names = [node.name for node in model.nodes]
    points, regions, tris = [], [], []
    for piece in model.pieces:
        lod = piece.lods[0]
        base = len(points)
        for vertex in lod.vertices:
            points.append(vertex.position)
            if vertex.weights:
                best = max(vertex.weights, key=lambda w: w.bias)
                regions.append(region_of(names[best.node_index]) if best.node_index < len(names) else "torso")
            else:
                regions.append("torso")
        for face in lod.faces:
            if len(face.vertices) == 3:
                tris.append([base + fv.vertex_index for fv in face.vertices])
    return model, np.asarray(points, float) * CM, np.asarray(regions), np.asarray(tris, int)


MAX_SAMPLES = 400_000  # memory bound: a few tens of MB at most


def surface_samples(points, tris, step_cm=1.0):
    """Vertices plus a barycentric grid on each triangle (one grid per triangle, bounded in total)."""
    samples = [points]
    if len(tris) == 0:
        return points
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    size = np.maximum(np.linalg.norm(b - a, axis=1), np.linalg.norm(c - a, axis=1))
    n_per = np.clip(np.ceil(size / step_cm), 2, 8).astype(int)
    budget = MAX_SAMPLES - len(points)
    for n in range(2, 9):
        sel = n_per == n
        if not sel.any():
            continue
        grid = [(i / n, j / n) for i in range(0, n + 1) for j in range(0, n + 1 - i) if 0 < i + j]
        if budget < sel.sum() * len(grid):
            break
        budget -= sel.sum() * len(grid)
        aa, ab, ac = a[sel], b[sel] - a[sel], c[sel] - a[sel]
        for u, v in grid:
            samples.append(aa + u * ab + v * ac)
    return np.concatenate(samples)


def skeleton_match(ma, mb):
    na = [n.name for n in ma.nodes]
    nb = [n.name for n in mb.nodes]
    if na != nb:
        return f"skeleton differs ({len(na)} vs {len(nb)} nodes)"
    diff = max(float(np.abs(x.bind_matrix - y.bind_matrix).max()) for x, y in zip(ma.nodes, mb.nodes))
    return f"same skeleton ({len(na)} nodes), bind max diff {diff * CM:.2f} cm"


def report(stem_a, stem_b):
    ma, pa, ra, _ = load(stem_a)
    mb, pb, _, tb = load(stem_b)
    tree = cKDTree(surface_samples(pb, tb))
    raw, _ = tree.query(pa)
    offset = np.zeros(3)
    for _ in range(30):  # translation-only ICP
        _, idx = tree.query(pa + offset)
        step = np.mean(tree.data[idx] - (pa + offset), axis=0)
        offset += step
        if np.linalg.norm(step) < 0.01:
            break
    shifted, _ = tree.query(pa + offset)
    parts = []
    for label, dist in (("raw", raw), ("shifted", shifted)):
        cells = []
        for region in REGIONS:
            d = dist[ra == region]
            if len(d):
                cells.append(f"{region} p90 {np.percentile(d, 90):4.1f} max {d.max():4.1f}")
        parts.append(f"  {label:7s} " + " | ".join(cells))
    print(f"{stem_a} vs {stem_b}: {skeleton_match(ma, mb)}; rigid offset {np.linalg.norm(offset):.1f} cm")
    print("\n".join(parts))
    if len(pa) == len(pb):  # same vertex layout: compare vertex to vertex as well
        delta = pb - pa
        shift = np.median(delta, axis=0)
        cells = []
        for label, d in (("same-vertex", np.linalg.norm(delta, axis=1)),
                         ("same-vertex shifted", np.linalg.norm(delta - shift, axis=1))):
            row = " | ".join(f"{r} p90 {np.percentile(d[ra == r], 90):4.1f}" for r in REGIONS if (ra == r).any())
            cells.append(f"  {label}: {row}")
        print("\n".join(cells) + f"  (shift {np.round(shift, 2).tolist()} cm)")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for arg in sys.argv[1:]:
        stem_a, others = arg.split(":")
        for stem_b in others.split(","):
            report(stem_a, stem_b)


if __name__ == "__main__":
    main()
