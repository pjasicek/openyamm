#!/usr/bin/env python3
"""The flat letter: Anskram Keep's finished `scroll` (scroll-open.ABC, its Static_Model pose: the sheet upright) turned
into MM9's `down` pose, which BookLetter.scr plays when its third parameter (bDown) is 1 (`:Init` LoopAnim Down): 40
letters in 17 MM9 maps lie flat on their table or floor. Both poses centre the sheet on the object's origin; MM9's
MoveToFloor sets either's box bottom on the surface, so the flat letter stands where the upright one does, base on the
surface: the finished GLB's vertices are turned by the pose's exact rotation (the ABC's down root against its
Static_Model root, fitted rigidly: a quarter turn about the sheet's x axis) in the GLB's frame (its axis signs found by
matching the static pose), then based and centred again. Same mesh, UVs, skin and LODs.

    python3 level_generation/props/mm9_outdoor_regions_claude/scripts/scrollflat.py [--install]

The converter's shared rule (dungeon/content.py `flat_letter`) puts every bDown BookLetter.scr letter on it.
"""
import itertools
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
SOURCE = REPO / "assets_source/worlds/mm9/models/mm9_deco_scroll.glb"
OUT = HERE / "work/mm9_deco_scrollflat.glb"
sys.path.insert(0, str(REPO / "tools/mm9_import_discovery"))
from convert_abc_model import read_abc, source_animation_pose  # noqa: E402


def abc_pose(model, name):
    animation = next(a for a in model.animations if a.name.lower() == name.lower())
    pose = source_animation_pose(model, animation, 0.0)
    parents = {c: i for i, n in enumerate(model.nodes) for c in n.children}
    world = []
    for i in range(len(model.nodes)):
        x, y, z, w = pose[i].rotation
        m = np.eye(4)
        m[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
        m[:3, 3] = pose[i].translation
        world.append(m if i not in parents else world[parents[i]] @ m)
    skin = [w @ np.linalg.inv(n.bind_matrix) for w, n in zip(world, model.nodes)]
    return np.array([sum(wt.bias * (skin[wt.node_index] @ np.append(v.position, 1.0)) for wt in v.weights)[:3]
                     for piece in model.pieces for v in piece.lods[0].vertices])


def rigid(a, b):
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1] *= -1
        r = vt.T @ u.T
    return r


def main() -> int:
    model = read_abc(REPO / "mm9/extracted/MODELS/MODELS/PROPS/SCROLL-OPEN.abc")
    static, down = abc_pose(model, "Static_Model"), abc_pose(model, "down")
    turn = rigid(static, down)                           # LT: static -> down
    data = SOURCE.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    doc = json.loads(data[20:20 + length])
    offset = 20 + length
    blob = bytearray(data[offset + 8:offset + 8 + struct.unpack_from("<I", data, offset)[0]])

    def accessor(index):
        a = doc["accessors"][index]
        v = doc["bufferViews"][a["bufferView"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return start, np.frombuffer(bytes(blob[start:start + a["count"] * 12]), np.float32).reshape(-1, 3).copy()
    node = next(n for n in doc["nodes"] if "mesh" in n)
    chain = [node["mesh"]] + doc["meshes"][node["mesh"]].get("extras", {}).get("openyamm_lods", [])
    lod0 = np.concatenate([accessor(p["attributes"]["POSITION"])[1] for p in doc["meshes"][chain[0]]["primitives"]])
    # the GLB frame against the ABC's: a scale and axis signs (the upright GLB is the static pose, based and centred)
    centre = (lod0.min(0) + lod0.max(0)) / 2
    scale = (lod0[:, 1].max() - lod0[:, 1].min()) / (static[:, 1].max() - static[:, 1].min())
    reference = (static - (static.min(0) + static.max(0)) / 2) * scale
    tree = cKDTree(lod0 - centre)
    signs = min(itertools.product((1, -1), repeat=3), key=lambda s: np.median(tree.query(reference * s)[0]))
    fit = float(np.median(tree.query(reference * np.array(signs))[0]) / scale)
    frame = np.diag(signs).astype(float)
    turn_glb = frame @ turn @ frame
    # every LOD turned about the upright box centre, then based (min y 0) and centred on the LOD0 footprint
    turned = {}
    for mesh in chain:
        for p in doc["meshes"][mesh]["primitives"]:
            start, pos = accessor(p["attributes"]["POSITION"])
            turned[(mesh, id(p))] = (start, (pos - centre) @ turn_glb.T)
    base = np.concatenate([v for (mesh, _), (_, v) in turned.items() if mesh == chain[0]])
    shift = np.array([-(base[:, 0].min() + base[:, 0].max()) / 2, -base[:, 1].min(),
                      -(base[:, 2].min() + base[:, 2].max()) / 2])
    for mesh in chain:
        for p in doc["meshes"][mesh]["primitives"]:
            start, pos = turned[(mesh, id(p))]
            pos = (pos + shift).astype(np.float32)
            blob[start:start + pos.nbytes] = pos.tobytes()
            a = doc["accessors"][p["attributes"]["POSITION"]]
            a["min"], a["max"] = pos.min(0).tolist(), pos.max(0).tolist()
            if "NORMAL" in p["attributes"]:
                nstart, normals = accessor(p["attributes"]["NORMAL"])
                normals = (normals @ turn_glb.T).astype(np.float32)
                blob[nstart:nstart + normals.nbytes] = normals.tobytes()
    for item in doc.get("meshes", []) + doc.get("nodes", []):
        if item.get("name", "").startswith("scroll"):
            item["name"] = "scrollflat" + item["name"][len("scroll"):]
    body = json.dumps(doc, separators=(",", ":")).encode()
    body += b" " * (-len(body) % 4)
    total = 12 + 8 + len(body) + 8 + len(blob)
    OUT.write_bytes(struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(body), 0x4E4F534A) + body
                    + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))
    height = float((base + shift)[:, 1].max())
    meta = {"prop": "scrollflat", "source": "mm9_deco_scroll.glb (Anskram Keep)", "glb_axis_signs": list(signs),
            "static_fit_lt": round(fit, 3), "height_m": round(height, 4), "height_units": round(height * 81.7, 2),
            "turn_lt": np.round(turn, 4).tolist()}
    (HERE / "work/scrollflat_meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    winding = subprocess.run([sys.executable, str(REPO / "level_generation/decorations/mm8_3d/animated/scripts/"
                                                  "check_winding.py"), str(OUT)], capture_output=True, text=True)
    print(json.dumps(meta), winding.stdout.strip()[-60:])
    if "--install" in sys.argv:
        target = REPO / "assets_source/worlds/mm9/models/mm9_deco_scrollflat.glb"
        if target.exists() and "--replace" not in sys.argv:
            sys.exit(f"{target} exists (--replace)")
        result = subprocess.run([sys.executable, str(REPO / "tools/install_model.py"), str(OUT), "--world", "mm9"], cwd=REPO,
                                capture_output=True, text=True)
        print("install", "ok" if result.returncode == 0 else "FAILED " + result.stderr[-300:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
