"""Remove the stray gold neck ring in front of the Warlock's throat from every LOD and shadow mesh (2026-11-12).

    python3 remove_chin_ring.py <in.glb> <out.glb> [--dry-run]

The ring is a loose loop of the Smart Topology export (LOD0 133 triangles) at y 1.337-1.375, z 0.088-0.116, below the
chin and above the cape clasp. Every connected component (vertices welded by position) whose vertices all lie in that
box is dropped; the index accessor is rewritten in place with a smaller count. Vertices stay (unreferenced).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "claude_shared" / "floor"))
from glb_pose import Glb, COMPONENTS  # noqa: E402

BOX_LO = np.array([-0.06, 1.32, 0.07])
BOX_HI = np.array([0.06, 1.39, 0.13])


def ring_triangles(positions, triangles):
    welded = np.unique(np.round(positions, 5), axis=0, return_inverse=True)[1].ravel()
    corners = welded[triangles]
    count = welded.max() + 1
    rows = np.concatenate([corners[:, 0], corners[:, 1], corners[:, 2]])
    cols = np.concatenate([corners[:, 1], corners[:, 2], corners[:, 0]])
    labels = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(count, count)),
                                  directed=False)[1]
    triangle_labels = labels[corners[:, 0]]
    drop = np.zeros(len(triangles), bool)
    for label in np.unique(triangle_labels):
        selected = triangle_labels == label
        points = positions[np.unique(triangles[selected])]
        if (points.min(0) >= BOX_LO).all() and (points.max(0) <= BOX_HI).all():
            drop |= selected
    return drop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("out")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    glb = Glb(args.source)
    done = set()
    for mesh in glb.json["meshes"]:
        for primitive in mesh["primitives"]:
            index = primitive["indices"]
            if index in done:
                raise SystemExit(f"{mesh['name']}: index accessor {index} is shared")
            done.add(index)
            accessor = glb.json["accessors"][index]
            positions = glb.accessor(primitive["attributes"]["POSITION"])
            triangles = glb.accessor(index).astype(np.int64).reshape(-1, 3)
            drop = ring_triangles(positions, triangles)
            print(f"{mesh['name']}: {len(triangles)} -> {len(triangles) - drop.sum()} (ring {drop.sum()})")
            kept = triangles[~drop].ravel().astype(COMPONENTS[accessor["componentType"]])
            view = glb.json["bufferViews"][accessor["bufferView"]]
            if view.get("byteStride"):
                raise SystemExit("strided index view")
            start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            glb.bin[start:start + kept.nbytes] = kept.tobytes()
            accessor["count"] = int(kept.size)
            if "min" in accessor:
                accessor["min"], accessor["max"] = [int(kept.min())], [int(kept.max())]
    if not args.dry_run:
        glb.write(args.out)


if __name__ == "__main__":
    main()
