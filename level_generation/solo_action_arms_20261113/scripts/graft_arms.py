#!/usr/bin/env python3
"""First-person arms from one of our own humanoid creature models (route B): cut its forearms and hands, re-pose them
onto the first-person skeleton's bind pose and bind them to that skeleton, so the first-person clips drive them.

    graft_arms.py <our_model.glb> <first_person_arms.glb> <out.glb> [--scale-mode forearm|hand] [--keep-elbow 0.5]

Our rigs use biped bone names (B_L_Forearm, B_L_Finger01 ...), the first-person skeleton the same names with the
'Bip01 L ' prefix, so every joint maps one to one. Per joint, a frame is built from the bone's direction (to its child
joint) and the hand's index-to-little-finger line; vertices bound to a joint are carried rigidly (times one global
scale) from our joint's frame to the first-person joint's frame, blended by their skin weights. Faces mostly weighted
to the upper arm and above are cut. The output is a copy of the first-person GLB whose arm meshes are replaced by ours,
with our materials and textures; skeleton, nodes and clips stay byte-identical.

The first-person GLB used for now is the private Oblivion stand-in (reference/oblivion_poc/), so the output belongs
there too; nothing derived from it may be committed. Run with the gltf_venv python (pygltflib, numpy).
"""
import argparse
import re

import numpy as np
import pygltflib

COMPONENT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(g, blob, index):
    acc = g.accessors[index]
    view = g.bufferViews[acc.bufferView]
    dtype = np.dtype(COMPONENT[acc.componentType])
    width = WIDTH[acc.type]
    stride = view.byteStride or dtype.itemsize * width
    start = (view.byteOffset or 0) + (acc.byteOffset or 0)
    raw = np.frombuffer(blob, dtype=np.uint8, count=stride * (acc.count - 1) + dtype.itemsize * width, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, shape=(acc.count, dtype.itemsize * width), strides=(stride, 1))
    data = np.ascontiguousarray(rows).view(dtype).reshape(acc.count, width)
    if acc.normalized and dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(dtype).max
    return data


class Writer:
    def __init__(self, g, blob):
        self.g = g
        self.blob = bytearray(blob)

    def add_bytes(self, data, target=None):
        while len(self.blob) % 4:
            self.blob.append(0)
        view = pygltflib.BufferView(buffer=0, byteOffset=len(self.blob), byteLength=len(data))
        if target is not None:
            view.target = target
        self.blob.extend(data)
        self.g.bufferViews.append(view)
        return len(self.g.bufferViews) - 1

    def add_accessor(self, array, component, kind, target, minmax=False):
        array = np.ascontiguousarray(array)
        acc = pygltflib.Accessor(bufferView=self.add_bytes(array.tobytes(), target), componentType=component,
                                 count=len(array), type=kind)
        if minmax:
            acc.min = array.min(axis=0).tolist()
            acc.max = array.max(axis=0).tolist()
        self.g.accessors.append(acc)
        return len(self.g.accessors) - 1


def bind_frames(g, blob, skin_index):
    skin = g.skins[skin_index]
    ibm = read(g, blob, skin.inverseBindMatrices).reshape(-1, 4, 4).transpose(0, 2, 1)
    names = [g.nodes[j].name for j in skin.joints]
    world = np.linalg.inv(ibm)
    return names, world


def first_person_name(name):
    if name.startswith('Bip01 '):
        return name                                    # already bound to the first-person skeleton (re-bind)
    match = re.fullmatch(r'B_([LR])_(.+)', name)
    return f'Bip01 {match.group(1)} {match.group(2)}' if match else None


def source_prefix(names, side):
    return f'Bip01 {side} ' if any(n.startswith('Bip01 ') for n in names) else f'B_{side}_'


AIM = {'Forearm': 'Hand', 'ForearmTwist': 'Hand', 'Hand': 'Finger2', 'Finger0': 'Finger01', 'Finger01': 'Finger02'}
for finger in '1234':
    AIM['Finger' + finger] = 'Finger' + finger + '1'
    AIM['Finger' + finger + '1'] = 'Finger' + finger + '2'
PARENT = {'Finger02': 'Finger01', 'Finger12': 'Finger11', 'Finger22': 'Finger21', 'Finger32': 'Finger31',
          'Finger42': 'Finger41'}


def frames(names, world, prefix):
    """Per joint (short name) the 4x4 world frame: x along the bone, z across the hand, origin at the joint."""
    position = {n[len(prefix):]: world[i][:3, 3] for i, n in enumerate(names) if n.startswith(prefix)}
    lateral = position['Finger1'] - position['Finger4']
    result = {}
    for short in position:
        aim_short = AIM.get(short)
        source = short
        while aim_short is None and source in PARENT:
            source = PARENT[source]
            aim_short = AIM.get(source)
        if aim_short is None or aim_short not in position:
            continue
        x = position[aim_short] - position[source]
        x /= np.linalg.norm(x)
        z = np.cross(x, lateral)
        z /= np.linalg.norm(z)
        y = np.cross(z, x)
        frame = np.eye(4)
        frame[:3, 0], frame[:3, 1], frame[:3, 2] = x, y, z
        frame[:3, 3] = position[short]
        result[short] = frame
    return result, position


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ours')
    parser.add_argument('first_person')
    parser.add_argument('out')
    parser.add_argument('--keep', type=float, default=0.5, help='share of a face\'s weight on kept joints to keep it')
    parser.add_argument('--scale', type=float, default=0.0, help='override the global scale')
    parser.add_argument('--hand-scale', type=float, default=1.0, help='extra scale of hands and fingers (races)')
    parser.add_argument('--upper', action='store_true',
                        help='keep the upper arm, carried rigidly with the forearm and bound to it, so the arm runs on '
                             'past the elbow towards the eye as the first-person meshes do')
    parser.add_argument('--girth', type=float, default=1.0,
                        help='scale of the forearm and upper arm across their axis (our arms are slimmer)')
    args = parser.parse_args()

    src = pygltflib.GLTF2().load(args.ours)
    src_blob = src.binary_blob()
    dst = pygltflib.GLTF2().load(args.first_person)
    dst_blob = dst.binary_blob()

    hand_node = next(i for i, n in enumerate(dst.nodes) if n.mesh is not None and dst.meshes[n.mesh].name == 'Hand')
    dst_skin = dst.nodes[hand_node].skin
    dst_names, dst_world = bind_frames(dst, dst_blob, dst_skin)
    dst_index = {n: i for i, n in enumerate(dst_names)}

    src_node = next(i for i, n in enumerate(src.nodes) if n.skin is not None and n.mesh is not None)
    src_skin = src.nodes[src_node].skin
    src_names, src_world = bind_frames(src, src_blob, src_skin)

    transforms = {}
    upper_alias = {}
    scale = args.scale
    for side in 'LR':
        s_prefix = source_prefix(src_names, side)
        s_frames, s_pos = frames(src_names, src_world, s_prefix)
        d_frames, d_pos = frames(dst_names, dst_world, f'Bip01 {side} ')
        if not scale:
            scale = float(np.linalg.norm(d_pos['Hand'] - d_pos['Forearm']) /
                          np.linalg.norm(s_pos['Hand'] - s_pos['Forearm']))
        for short, s_frame in s_frames.items():
            if short not in d_frames:
                continue
            local_scale = scale * (args.hand_scale if short.startswith(('Hand', 'Finger')) else 1.0)
            across = local_scale * (args.girth if short.startswith('Forearm') else 1.0)
            scaling = np.diag([local_scale, across, across, 1.0])
            transforms[s_prefix + short] = d_frames[short] @ scaling @ np.linalg.inv(s_frame)
        # Oblivion's ForearmTwist sits at the elbow, ours along the forearm: twist-weighted geometry rides the forearm's
        # mapping, so it keeps its place along the arm instead of being pulled to the elbow.
        if s_prefix + 'ForearmTwist' in transforms and s_prefix + 'Forearm' in transforms:
            transforms[s_prefix + 'ForearmTwist'] = transforms[s_prefix + 'Forearm']
        if args.upper and s_prefix + 'Forearm' in transforms:
            transforms[s_prefix + 'UpperArm'] = transforms[s_prefix + 'Forearm']
            upper_alias[s_prefix + 'UpperArm'] = s_prefix + 'Forearm'
    print('global scale', scale, 'mapped joints', len(transforms))

    w = Writer(dst, dst_blob)
    # Our materials and their textures, copied over by image.
    image_map, texture_map, material_map = {}, {}, {}

    def copy_texture(info):
        if info is None:
            return None
        tex = src.textures[info.index]
        if tex.source not in image_map:
            img = src.images[tex.source]
            view = src.bufferViews[img.bufferView]
            data = src_blob[view.byteOffset:view.byteOffset + view.byteLength]
            dst.images.append(pygltflib.Image(bufferView=w.add_bytes(data), mimeType=img.mimeType, name=img.name))
            image_map[tex.source] = len(dst.images) - 1
        if info.index not in texture_map:
            dst.textures.append(pygltflib.Texture(source=image_map[tex.source], sampler=0 if dst.samplers else None))
            texture_map[info.index] = len(dst.textures) - 1
        return texture_map[info.index]

    def copy_material(index):
        if index in material_map:
            return material_map[index]
        m = src.materials[index]
        pbr = m.pbrMetallicRoughness
        base = copy_texture(pbr.baseColorTexture)
        mr = copy_texture(pbr.metallicRoughnessTexture)
        normal = copy_texture(m.normalTexture)
        new = pygltflib.Material(
            name='own_' + (m.name or str(index)),
            pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                baseColorFactor=pbr.baseColorFactor,
                baseColorTexture=pygltflib.TextureInfo(index=base) if base is not None else None,
                metallicRoughnessTexture=pygltflib.TextureInfo(index=mr) if mr is not None else None,
                metallicFactor=pbr.metallicFactor, roughnessFactor=pbr.roughnessFactor),
            normalTexture=pygltflib.NormalMaterialTexture(index=normal) if normal is not None else None,
            alphaMode=m.alphaMode, alphaCutoff=m.alphaCutoff, doubleSided=m.doubleSided)
        dst.materials.append(new)
        material_map[index] = len(dst.materials) - 1
        return material_map[index]

    primitives = []
    kept_faces = 0
    for mesh_index in {n.mesh for n in src.nodes if n.skin == src_skin and n.mesh is not None}:
        for prim in src.meshes[mesh_index].primitives:
            a = prim.attributes
            pos = read(src, src_blob, a.POSITION).astype(np.float64)
            nrm = read(src, src_blob, a.NORMAL).astype(np.float64)
            uv = read(src, src_blob, a.TEXCOORD_0)
            joints = read(src, src_blob, a.JOINTS_0).astype(int)
            weights = read(src, src_blob, a.WEIGHTS_0).astype(np.float64)
            tri = read(src, src_blob, prim.indices).reshape(-1, 3).astype(np.int64)
            names = np.array(src_names)[joints]
            mapped = np.vectorize(lambda n: n in transforms)(names)
            share = (weights * mapped).sum(1)
            keep_face = share[tri].mean(1) >= args.keep
            if not keep_face.any():
                continue
            tri = tri[keep_face]
            used = np.unique(tri)
            remap = -np.ones(len(pos), dtype=np.int64)
            remap[used] = np.arange(len(used))
            new_pos = np.zeros((len(used), 3))
            new_nrm = np.zeros((len(used), 3))
            new_joints = np.zeros((len(used), 4), dtype=np.uint16)
            new_weights = np.zeros((len(used), 4), dtype=np.float32)
            for out_i, v in enumerate(used):
                acc_p = np.zeros(3)
                acc_n = np.zeros(3)
                total = 0.0
                slots = []
                for k in range(4):
                    name = names[v, k]
                    wk = weights[v, k]
                    if wk <= 0 or name not in transforms:
                        continue
                    m = transforms[name]
                    acc_p += wk * (m @ np.append(pos[v], 1.0))[:3]
                    acc_n += wk * (m[:3, :3] @ nrm[v])
                    total += wk
                    slots.append((dst_index[first_person_name(upper_alias.get(name, name))], wk))
                if total == 0:
                    # Only unmapped joints (upper arm): follow the forearm of its side.
                    side = 'L' if pos[v][0] > 0 else 'R'
                    name = source_prefix(src_names, side) + 'Forearm'
                    m = transforms[name]
                    acc_p, acc_n, total = (m @ np.append(pos[v], 1.0))[:3], m[:3, :3] @ nrm[v], 1.0
                    slots = [(dst_index[first_person_name(name)], 1.0)]
                new_pos[out_i] = acc_p / total
                new_nrm[out_i] = acc_n / max(np.linalg.norm(acc_n), 1e-9)
                merged = {}
                for j, wk in slots:
                    merged[j] = merged.get(j, 0.0) + wk
                slots = sorted(merged.items(), key=lambda s: -s[1])
                for k, (j, wk) in enumerate(slots[:4]):
                    new_joints[out_i, k] = j
                    new_weights[out_i, k] = wk / total
            kept_faces += len(tri)
            attrs = pygltflib.Attributes(
                POSITION=w.add_accessor(new_pos.astype(np.float32), 5126, 'VEC3', 34962, minmax=True),
                NORMAL=w.add_accessor(new_nrm.astype(np.float32), 5126, 'VEC3', 34962),
                TEXCOORD_0=w.add_accessor(uv[used].astype(np.float32), 5126, 'VEC2', 34962),
                JOINTS_0=w.add_accessor(new_joints, 5123, 'VEC4', 34962),
                WEIGHTS_0=w.add_accessor(new_weights, 5126, 'VEC4', 34962))
            indices = w.add_accessor(remap[tri].reshape(-1, 1).astype(np.uint32), 5125, 'SCALAR', 34963)
            primitives.append(pygltflib.Primitive(attributes=attrs, indices=indices,
                                                  material=copy_material(prim.material)))
    dst.meshes[dst.nodes[hand_node].mesh].primitives = primitives
    for node in dst.nodes:
        if node.mesh is not None and dst.meshes[node.mesh].name == 'Arms':
            node.mesh = None
            node.skin = None
    dst.buffers[0].byteLength = len(w.blob)
    dst.set_binary_blob(bytes(w.blob))
    dst.save_binary(args.out)
    print('kept faces', kept_faces, 'primitives', len(primitives), 'wrote', args.out)


if __name__ == '__main__':
    main()
