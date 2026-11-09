#!/usr/bin/env python3
"""MM9's posed figures (Prop objects carrying a character model; PropAnim.scr loops one animation, no AI) as static
decorations of our 3D creature models (user, 2026-11-05: "do as you recommend"): each model's mesh and LODs skinned at
one frame of one clip, in its MM9 tier (KHR_materials_variants), its skin, clips, shadow LODs and the other tiers'
textures dropped. The glTF origin stays the actor's (between its feet), so a figure at its DAT position lies or stands
where MM9's does; the base is lifted onto y = 0. Heights: the actor's (actors.yml scale: units per model metre) at
MM9 scale 1.

    python3 level_generation/props/mm9_outdoor_regions_claude/scripts/pose_bake.py [prop ...] [--install]

Writes work/mm9_deco_<prop>.glb and work/<prop>_meta.json (height_units, triangles) for placements.py.
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
MODELS = REPO / "assets_source/worlds/mm9/models"

# prop -> (our model, tier variant or None, clip, "start" | "end", actors.yml scale)
POSED = {
    # Yorwick's and Afterworld's battlefield: PropAnim static_die1 / static_die2
    "clansoldierdeadb": ("mm9_clansoldier", "clan_b", "DeadStatic", "start", 100.0),     # Clanshield1: Clan Soldier
    "clansoldierdead2b": ("mm9_clansoldier", "clan_b", "Dead2", "end", 100.0),
    "clansoldierdeada": ("mm9_clansoldier", "clan_a", "DeadStatic", "start", 100.0),     # BeldShield1: no tier of its own
    "kiradead": ("mm9_kira", None, "StaticDie", "start", 100.0),
    "bjarnidead": ("mm9_bjarni", None, "Dead", "end", 100.0),
    "sigmunddead": ("mm9_sigmund", None, "StaticDie", "start", 100.0),
    "tryggvadead": ("mm9_tryggva", None, "DeadStatic", "start", 100.0),
    # Afterworld's seated heroes (the cities' bjarnisitting, sigmundsit, tryggvasit were MM9's own meshes)
    "bjarniseated": ("mm9_bjarni", None, "Sit", "start", 100.0),
    "sigmundseated": ("mm9_sigmund", None, "Sit", "start", 100.0),
    "tryggvaseated": ("mm9_tryggva", None, "Sit", "start", 100.0),
    # Boot Camp's museum of creatures (no script: MM9 shows the model's first pose); tiers by MM9 skin
    "dragonflyfigure": ("mm9_dfly", "dfly_b", "Standing", "start", 100.0),           # DRAGONFLY2
    "eyefigure": ("mm9_eye", "eye_b", "Standing", "start", 100.0),                   # ORBUS2
    "gezzamptfigure": ("mm9_gezzampt", "gezz_b", "Standing", "start", 100.0),        # GEZZAMPT2
    "jellysporefigure": ("mm9_jelly", "jelly_b", "Standing", "start", 100.0),        # JELLYSPORE4: nearest tier
    "lizardorcfigure": ("mm9_lizardorc", "liz_a", "Standing", "start", 100.0),       # LIZORCCUTLASS
    "nosferatufigure": ("mm9_nosferatu", "nos_b", "Standing", "start", 100.0),       # NOSFERATU2
    "skeletonfigure": ("mm9_skeleton", "skel_a", "Standing", "start", 100.0),        # SKELETONDAGGER
    "skeletonwarriorfigure": ("mm9_skelwar", "skelwar_b", "Standing", "start", 100.0),   # SKELETONSCIMITAR
    "troglodytefigure": ("mm9_troglodyte", "trog_b", "Standing", "start", 100.0),    # TROGLODYTE2
    # the whack-a-honky geese (Thjorgard, Guberland) at rest in their holes: the game itself is not carried
    "goosefigure": ("mm9_goose", "goose_a", "Standing", "start", 100.0),             # GOOSE (white)
}
UNITS_PER_METRE = 100.0      # actors.yml scale 100 (every figure here)
COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
DTYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NORMALISED = {5121: 255.0, 5123: 65535.0}


class Glb:
    def __init__(self, path: Path):
        data = path.read_bytes()
        length = struct.unpack_from("<I", data, 12)[0]
        self.doc = json.loads(data[20:20 + length])
        offset = 20 + length
        self.bin = data[offset + 8:offset + 8 + struct.unpack_from("<I", data, offset)[0]]

    def view(self, index: int) -> bytes:
        v = self.doc["bufferViews"][index]
        return self.bin[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]

    def accessor(self, index: int) -> np.ndarray:
        a = self.doc["accessors"][index]
        n = COMPONENTS[a["type"]]
        dtype = DTYPES[a["componentType"]]
        v = self.doc["bufferViews"][a["bufferView"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 0) or n * np.dtype(dtype).itemsize
        raw = np.frombuffer(self.bin, dtype=np.uint8, count=stride * (a["count"] - 1) + n * np.dtype(dtype).itemsize,
                            offset=start)
        out = np.lib.stride_tricks.as_strided(raw, (a["count"], n * np.dtype(dtype).itemsize), (stride, 1)).copy()
        out = out.view(dtype).reshape(a["count"], n)
        if a.get("normalized") and a["componentType"] in NORMALISED:
            out = out.astype(np.float32) / NORMALISED[a["componentType"]]
        return out


def quat_matrix(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(t, r, s) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = quat_matrix(r) * np.asarray(s)[None, :]
    m[:3, 3] = t
    return m


def sample(g: Glb, sampler: dict, time: float) -> np.ndarray:
    times = g.accessor(sampler["input"])[:, 0]
    values = g.accessor(sampler["output"]).astype(float)
    if sampler.get("interpolation") == "CUBICSPLINE":
        values = values[1::3]
    k = int(np.searchsorted(times, time, side="right")) - 1
    if k < 0:
        return values[0]
    if k >= len(times) - 1 or sampler.get("interpolation") == "STEP":
        return values[min(k, len(times) - 1)]
    f = (time - times[k]) / max(times[k + 1] - times[k], 1e-9)
    a, b = values[k], values[k + 1]
    if len(a) == 4:                                   # rotation: nlerp along the short way
        b = b if np.dot(a, b) >= 0 else -b
        q = a * (1 - f) + b * f
        return q / np.linalg.norm(q)
    return a * (1 - f) + b * f


def pose_matrices(g: Glb, clip: str, when: str) -> list:
    doc = g.doc
    animation = next((a for a in doc["animations"] if a["name"] == clip), None)
    if animation is None:
        raise SystemExit(f"no clip {clip}")
    inputs = [g.accessor(s["input"])[:, 0] for s in animation["samplers"]]
    time = 0.0 if when == "start" else max(float(t.max()) for t in inputs)
    local = []
    for node in doc["nodes"]:
        if "matrix" in node:
            local.append([np.array(node["matrix"], float).reshape(4, 4).T, None])
        else:
            local.append([None, [np.array(node.get("translation", [0, 0, 0]), float),
                                 np.array(node.get("rotation", [0, 0, 0, 1]), float),
                                 np.array(node.get("scale", [1, 1, 1]), float)]])
    for channel in animation["channels"]:
        target = channel["target"]
        if "node" not in target or local[target["node"]][1] is None:
            continue
        slot = {"translation": 0, "rotation": 1, "scale": 2}.get(target["path"])
        if slot is not None:
            local[target["node"]][1][slot] = sample(g, animation["samplers"][channel["sampler"]], time)
    matrices = [m if m is not None else trs(*parts) for m, parts in local]
    parent = {c: i for i, n in enumerate(doc["nodes"]) for c in n.get("children", [])}
    world = [None] * len(doc["nodes"])

    def resolve(i):
        if world[i] is None:
            world[i] = matrices[i] if i not in parent else resolve(parent[i]) @ matrices[i]
        return world[i]
    return [resolve(i) for i in range(len(doc["nodes"]))]


def bake(prop: str) -> dict:
    model, tier, clip, when, scale = POSED[prop]
    g = Glb(MODELS / f"{model}.glb")
    doc = g.doc
    node = next(n for n in doc["nodes"] if "mesh" in n)
    skin = doc["skins"][node["skin"]]
    world = pose_matrices(g, clip, when)
    ibm = g.accessor(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    joint = np.array([world[j] @ ibm[k] for k, j in enumerate(skin["joints"])])
    base = doc["meshes"][node["mesh"]]
    chain = [node["mesh"]] + base.get("extras", {}).get("openyamm_lods", [])
    variants = [v["name"] for v in doc.get("extensions", {}).get("KHR_materials_variants", {}).get("variants", [])]
    variant = variants.index(tier) if tier else None
    out = {"accessors": [], "bufferViews": [], "meshes": [], "materials": [], "textures": [], "images": [],
           "samplers": doc.get("samplers", [])}
    blob = bytearray()

    def add(array: np.ndarray, kind: str, component: int, target=None, bounds=False) -> int:
        nonlocal blob
        data = array.tobytes()
        view = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}
        if target:
            view["target"] = target
        out["bufferViews"].append(view)
        blob += data + b"\0" * (-len(data) % 4)
        accessor = {"bufferView": len(out["bufferViews"]) - 1, "componentType": component, "count": len(array),
                    "type": kind}
        if bounds:
            accessor["min"] = array.min(0).tolist()
            accessor["max"] = array.max(0).tolist()
        out["accessors"].append(accessor)
        return len(out["accessors"]) - 1

    material_map, texture_map, image_map = {}, {}, {}

    def material(index: int) -> int:
        if index in material_map:
            return material_map[index]
        m = json.loads(json.dumps(doc["materials"][index]))

        def texture(info):
            t = info["index"]
            if t not in texture_map:
                tex = dict(doc["textures"][t])
                src = tex["source"]
                if src not in image_map:
                    image = dict(doc["images"][src])
                    data = g.view(image["bufferView"])
                    out["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)})
                    blob.extend(data + b"\0" * (-len(data) % 4))
                    image["bufferView"] = len(out["bufferViews"]) - 1
                    out["images"].append(image)
                    image_map[src] = len(out["images"]) - 1
                tex["source"] = image_map[src]
                out["textures"].append(tex)
                texture_map[t] = len(out["textures"]) - 1
            info["index"] = texture_map[t]
        pbr = m.get("pbrMetallicRoughness", {})
        for key in ("baseColorTexture", "metallicRoughnessTexture"):
            if key in pbr:
                texture(pbr[key])
        for key in ("normalTexture", "occlusionTexture", "emissiveTexture"):
            if key in m:
                texture(m[key])
        # the tier's colour regions (openyamm_region_mask: a texture the model shader reads, as the actor's do)
        for value in m.get("extras", {}).values():
            if isinstance(value, dict) and isinstance(value.get("index"), int):
                texture(value)
        out["materials"].append(m)
        material_map[index] = len(out["materials"]) - 1
        return material_map[index]

    meshes, lowest = [], None
    for mesh_index in chain:
        primitives = []
        for p in doc["meshes"][mesh_index]["primitives"]:
            a = p["attributes"]
            pos = g.accessor(a["POSITION"]).astype(float)
            nrm = g.accessor(a["NORMAL"]).astype(float) if "NORMAL" in a else None
            joints = g.accessor(a["JOINTS_0"]).astype(int)
            weights = g.accessor(a["WEIGHTS_0"]).astype(float)
            weights /= np.maximum(weights.sum(1, keepdims=True), 1e-9)
            skinning = np.einsum("vk,vkij->vij", weights, joint[joints])
            p4 = np.concatenate([pos, np.ones((len(pos), 1))], 1)
            posed = np.einsum("vij,vj->vi", skinning, p4)[:, :3]
            indices = g.accessor(p["indices"]).reshape(-1, 3).astype(np.uint32)
            # a part on a mirrored bone (the skeleton's dagger) comes out wound the other way: flip it back
            mirrored = np.linalg.det(skinning[:, :3, :3]) < 0
            flip = mirrored[indices].all(1)
            indices[flip] = indices[flip][:, [0, 2, 1]]
            entry = {"positions": posed, "normals": None, "uv": g.accessor(a["TEXCOORD_0"]).astype(np.float32),
                     "indices": indices.reshape(-1)}
            if nrm is not None:
                n = np.einsum("vij,vj->vi", skinning[:, :3, :3], nrm)
                entry["normals"] = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
            chosen = p.get("material", 0)
            if variant is not None:
                for mapping in p.get("extensions", {}).get("KHR_materials_variants", {}).get("mappings", []):
                    if variant in mapping["variants"]:
                        chosen = mapping["material"]
            entry["material"] = chosen
            primitives.append(entry)
            if mesh_index == chain[0]:
                low = posed[:, 1].min()
                lowest = low if lowest is None else min(lowest, low)
        meshes.append(primitives)
    for level, primitives in enumerate(meshes):
        gltf_primitives = []
        for e in primitives:
            positions = (e["positions"] - [0, lowest, 0]).astype(np.float32)
            attributes = {"POSITION": add(positions, "VEC3", 5126, 34962, bounds=True),
                          "TEXCOORD_0": add(e["uv"], "VEC2", 5126, 34962),
                          "COLOR_0": add(np.ones((len(positions), 4), np.float32), "VEC4", 5126, 34962)}
            if e["normals"] is not None:
                attributes["NORMAL"] = add(e["normals"].astype(np.float32), "VEC3", 5126, 34962)
            gltf_primitives.append({"attributes": attributes, "indices": add(e["indices"], "SCALAR", 5125, 34963),
                                    "material": material(e["material"])})
        out["meshes"].append({"name": prop if level == 0 else f"{prop}_LOD{level}", "primitives": gltf_primitives})
    if len(out["meshes"]) > 1:
        out["meshes"][0]["extras"] = {"openyamm_lods": list(range(1, len(out["meshes"])))}
    document = {"asset": {"version": "2.0", "generator": "pose_bake.py"}, "scene": 0,
                "scenes": [{"nodes": [0]}], "nodes": [{"name": prop, "mesh": 0}],
                "buffers": [{"byteLength": len(blob)}], **{k: v for k, v in out.items() if v}}
    path = HERE / f"work/mm9_deco_{prop}.glb"
    body = json.dumps(document, separators=(",", ":")).encode()
    body += b" " * (-len(body) % 4)
    data = bytes(blob)
    total = 12 + 8 + len(body) + 8 + len(data)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(body), 0x4E4F534A) + body
                     + struct.pack("<II", len(data), 0x004E4942) + data)
    lod0 = np.concatenate([e["positions"] for e in meshes[0]])
    height_m = float(lod0[:, 1].max() - lowest)
    triangles = [sum(len(e["indices"]) // 3 for e in level) for level in meshes]
    meta = {"prop": prop, "model": model, "tier": tier, "clip": clip, "frame": when, "height_units":
            round(height_m * scale, 2), "origin_local_units": [0.0, 0.0, 0.0], "triangles": triangles,
            "extent_m": (lod0.max(0) - lod0.min(0)).round(3).tolist(), "bytes": path.stat().st_size}
    (HERE / f"work/{prop}_meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


def main() -> int:
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted(POSED)
    failed = False
    for prop in wanted:
        meta = bake(prop)
        path = HERE / f"work/mm9_deco_{prop}.glb"
        winding = subprocess.run([sys.executable, str(REPO / "level_generation/decorations/mm8_3d/animated/scripts/"
                                                      "check_winding.py"), str(path)], capture_output=True, text=True)
        decreasing = all(b < a for a, b in zip(meta["triangles"], meta["triangles"][1:]))
        print(prop, meta["clip"], meta["tier"], "height", meta["height_units"], "tris", meta["triangles"],
              f"{meta['bytes'] // 1024} KB", winding.stdout.strip().split(":")[-1].strip(),
              "" if decreasing else "LODS NOT DECREASING")
        failed |= not decreasing
        if "--install" in sys.argv and decreasing:
            if (REPO / f"assets_source/worlds/mm9/models/mm9_deco_{prop}.glb").exists() and "--replace" not in sys.argv:
                print("  exists, not replaced (--replace)")
                continue
            result = subprocess.run([sys.executable, str(REPO / "tools/install_model.py"), str(path), "--world", "mm9"],
                                    cwd=REPO, capture_output=True, text=True)
            print("  install", "ok" if result.returncode == 0 else "FAILED " + result.stderr[-300:])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
