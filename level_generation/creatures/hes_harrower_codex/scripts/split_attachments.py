#!/usr/bin/env python3
"""hkr: split the rigid armour, props and the carbine out of the skinned Kreegan GLB into static attachment GLBs,
one per node (actors.yml `attachments`). A project-local generalisation of tools/split_attachment.py (that tool takes
one primitive per item and refuses variant materials that differ beyond their ramps); here an item is
  {name, joint, materials: [material name prefixes], optional lod_from: [source level per level]}
and its triangles are those of primitives whose material (or any of its variants) starts with one of the prefixes and
whose vertices are all weighted fully to the joint - so the crest on B_Head leaves the head skin (also fully on
B_Head) alone, and a plate plus its emissive glow strips form one attachment with two primitives. The triangles leave
every mesh of the creature (colour LODs and shadow meshes). The attachment holds the item in the joint's space (its
inverse bind matrix applied), one node whose mesh lists its coarser levels in `openyamm_lods`, and per primitive the
creature's material and its variants (same variant names, so a carrier's skin selects them, or an item `skin:`):
textures are cropped to the item's texture coordinates per material and the coordinates remapped into the crop.
Usage: split_attachments_hkr.py creature.glb --body body.glb --items items.json --outdir export/"""
import argparse, copy, io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from merge_head_material import (TEXTURE_SLOTS, TYPES, accessor_array, append_accessor, compact, image_of, read_glb,  # noqa
                                 slot, write_glb)
PADDING, GRID = 4, 64
MIN_TRIS = 8


def variant_materials(primitive, nvar):
    mats = [primitive['material']] * max(nvar, 1)
    for m in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        for v in m['variants']:
            mats[v] = m['material']
    return mats


def full_on(document, binary, primitive, joint_slot):
    mask = None
    for name in [n for n in primitive['attributes'] if n.startswith('JOINTS_')]:
        joints = accessor_array(document, binary, primitive['attributes'][name])
        wacc = primitive['attributes']['WEIGHTS_' + name[7:]]
        weights = accessor_array(document, binary, wacc).astype(np.float64)
        if document['accessors'][wacc].get('normalized'):
            weights /= np.iinfo(weights.dtype).max if weights.dtype.kind in 'ui' else 1.0
        full = ((joints == joint_slot) & (weights > 0.999)).any(axis=1)
        mask = full if mask is None else mask | full
    return mask


def compacted(document, binary, primitive, triangles, names):
    used, remapped = np.unique(triangles.ravel(), return_inverse=True)
    return {n: accessor_array(document, binary, primitive['attributes'][n])[used] for n in names}, remapped.astype(np.uint32)


def add_view(out, ob, data, target=None):
    ob.extend(b'\0' * (-len(ob) % 4))
    view = {'buffer': 0, 'byteOffset': len(ob), 'byteLength': len(data)}
    if target is not None: view['target'] = target
    out['bufferViews'].append(view); ob.extend(data)
    return len(out['bufferViews']) - 1


def add_accessor(out, ob, values, ctype, kind, target):
    values = np.ascontiguousarray(values)
    acc = {'bufferView': add_view(out, ob, values.tobytes(), target), 'componentType': ctype, 'count': int(len(values)), 'type': kind}
    if kind == 'VEC3':
        acc['min'] = values.min(axis=0).tolist(); acc['max'] = values.max(axis=0).tolist()
    out['accessors'].append(acc)
    return len(out['accessors']) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('creature', type=Path); ap.add_argument('--body', type=Path, required=True)
    ap.add_argument('--items', type=Path, required=True); ap.add_argument('--outdir', type=Path, required=True)
    a = ap.parse_args()
    doc, binary = read_glb(a.creature); binary = bytearray(binary)
    items = json.loads(a.items.read_text())
    names = [n.get('name') for n in doc['nodes']]
    skin = doc['skins'][0]
    variants = doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])
    nvar = len(variants)
    mname = lambda i: doc['materials'][i].get('name', '')
    base = next(i for i, m in enumerate(doc['meshes']) if 'openyamm_lods' in m.get('extras', {}))
    chain = [base] + doc['meshes'][base]['extras']['openyamm_lods']
    report = {}
    pending = {}                                   # mesh index -> list of (primitive index, triangles to remove)
    results = []
    for it in items:
        joint_slot = skin['joints'].index(names.index(it['joint']))
        inv_bind = accessor_array(doc, binary, skin['inverseBindMatrices'])[joint_slot].reshape(4, 4).T
        levels = []                                # per colour level: [(primitive, triangles)]
        for mi, mesh in enumerate(doc['meshes']):
            per = []
            for pi, prim in enumerate(mesh['primitives']):
                mats = variant_materials(prim, nvar)
                if not any(mname(m).startswith(p) for m in mats for p in it['materials']):
                    continue
                idx = accessor_array(doc, binary, prim['indices']).reshape(-1, 3)
                full = full_on(doc, binary, prim, joint_slot)
                tri = full[idx].all(axis=1)
                if tri.any():
                    pending.setdefault(mi, []).append((pi, tri))
                    if mi in chain:
                        per.append((prim, idx[tri]))
            if mi in chain and per:
                levels.append((mi, per))
        if [l[0] for l in levels] != chain:
            raise ValueError(f"{it['name']}: found in levels {[l[0] for l in levels]}, expected {chain}")
        # a far level that collapsed below MIN_TRIS (the creature-wide decimation left a small plate 1 triangle at
        # LOD3: a sliver instead of the plate at distance) keeps the previous level's triangles
        for k in range(1, len(levels)):
            if sum(len(t) for _, t in levels[k][1]) < MIN_TRIS:
                levels[k] = (levels[k][0], levels[k - 1][1])
        # an item's `lod_from` [l0, l1, ...]: level k takes level lod_from[k]'s triangles (a decimated level that
        # sampled across UV islands, scripts/lod_atlas_check.py)
        for k, src in enumerate(it.get('lod_from', [])):
            if 0 < k < len(levels) and src != k:
                levels[k] = (levels[k][0], levels[src][1])
        results.append((it, inv_bind, levels))
    # remove the items' triangles from the creature
    for mi, lst in pending.items():
        mesh = doc['meshes'][mi]; newp = []
        for pi, prim in enumerate(mesh['primitives']):
            idx = accessor_array(doc, binary, prim['indices']).reshape(-1, 3)
            keep = np.ones(len(idx), bool)
            for pj, tri in lst:
                if pj == pi: keep &= ~tri
            if keep.all():
                newp.append(prim); continue
            if not keep.any():
                continue
            attr_names = sorted(prim['attributes'])
            values, ind = compacted(doc, binary, prim, idx[keep], attr_names)
            reb = copy.deepcopy(prim)
            reb['attributes'] = {n: append_accessor(doc, binary, values[n], doc['accessors'][prim['attributes'][n]], 34962) for n in attr_names}
            it_ = 5123 if ind.max() < 65536 else 5125
            reb['indices'] = append_accessor(doc, binary, ind.astype(TYPES[it_]), {'componentType': it_, 'type': 'SCALAR'}, 34963)
            newp.append(reb)
        mesh['primitives'] = newp
    for it, inv_bind, levels in results:
        out, ob = build(doc, binary, it, inv_bind, levels, variants, nvar, mname)
        path = a.outdir / f"{it['name']}.glb"
        write_glb(path, out, bytes(ob))
        report[it['name']] = {'joint': it['joint'], 'tris_per_level': [sum(len(t) for _, t in per) for _, per in levels],
                              'primitives': len(levels[0][1]), 'kb': round(path.stat().st_size / 1024, 1)}
        print('SPLIT', it['name'], json.dumps(report[it['name']]))
    write_glb(a.body, *compact(doc, bytes(binary)))
    (a.outdir / 'attachments.json').write_text(json.dumps(report, indent=1))


def build(doc, binary, it, inv_bind, levels, variants, nvar, mname):
    out = {'asset': {'version': '2.0', 'generator': 'hkr split_attachments_hkr.py'}, 'buffers': [{'byteLength': 0}],
           'bufferViews': [], 'accessors': [], 'images': [], 'textures': [], 'samplers': [
               {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071}],
           'materials': [], 'meshes': [], 'nodes': [{'name': it['joint'], 'mesh': 0}], 'scenes': [{'nodes': [0]}], 'scene': 0}
    ob = bytearray()
    # material groups by the level-0 primitives' default material base name (same order in every level)
    groups = []
    gkey = lambda prim: mname(prim['material']).rsplit('_', 1)[0] if nvar else mname(prim['material'])
    for prim, _ in levels[0][1]:
        groups.append(variant_materials(prim, nvar))
    keys = [gkey(prim) for prim, _ in levels[0][1]]
    # crop boxes per group over all levels
    mat_out = []
    for g, mats in enumerate(groups):
        tcs = []
        for _, per in levels:
            hit = [(p_, t_) for p_, t_ in per if gkey(p_) == keys[g]]
            if not hit: continue
            prim, tri = hit[0]
            if 'TEXCOORD_0' in prim['attributes']:
                tc = accessor_array(doc, binary, prim['attributes']['TEXCOORD_0'])[np.unique(tri.ravel())]
                tcs.append(tc)
        m0 = doc['materials'][mats[0]]
        slots = [p for p in TEXTURE_SLOTS if slot(m0, p) is not None]
        box = (0.0, 0.0, 1.0, 1.0); tex_index = {}
        if slots and tcs:
            tc = np.concatenate(tcs)
            images = {p: image_of(doc, binary, slot(m0, p)['index']) for p in slots}
            largest = max(im.size for im, _ in images.values()); grid = (max(1, largest[0] // GRID), max(1, largest[1] // GRID))
            c0 = [max(int(np.floor((tc[:, k].min() * largest[k] - PADDING) / largest[k] * grid[k])), 0) for k in (0, 1)]
            c1 = [min(int(np.ceil((tc[:, k].max() * largest[k] + PADDING) / largest[k] * grid[k])), grid[k]) for k in (0, 1)]
            box = (c0[0] / grid[0], c0[1] / grid[1], c1[0] / grid[0], c1[1] / grid[1])
            for p, (im, iname) in images.items():
                w, h = im.size
                crop = (round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h))
                buf = io.BytesIO(); im.crop(crop).save(buf, 'PNG', optimize=True)
                out['images'].append({'bufferView': add_view(out, ob, buf.getvalue()), 'mimeType': 'image/png', 'name': f"{iname}_{it['name']}"})
                out['textures'].append({'source': len(out['images']) - 1, 'sampler': 0})
                tex_index[p] = len(out['textures']) - 1
        idxs = []
        for m in mats:
            mat = copy.deepcopy(doc['materials'][m])
            for p, ti in tex_index.items():
                slot(mat, p)['index'] = ti
            out['materials'].append(mat); idxs.append(len(out['materials']) - 1)
        mat_out.append((idxs, box))
    for level, (_, per) in enumerate(levels):
        prims = []
        for prim, tri in per:
            g = keys.index(gkey(prim))
            nm = [n for n in ('POSITION', 'NORMAL', 'TEXCOORD_0') if n in prim['attributes']]
            values, ind = compacted(doc, binary, prim, tri, nm)
            pos = np.c_[values['POSITION'].astype(np.float64), np.ones(len(values['POSITION']))]
            values['POSITION'] = (pos @ inv_bind.T)[:, :3].astype(np.float32)
            if 'NORMAL' in values:
                n_ = values['NORMAL'].astype(np.float64) @ inv_bind[:3, :3].T
                values['NORMAL'] = (n_ / np.linalg.norm(n_, axis=1, keepdims=True)).astype(np.float32)
            idxs, box = mat_out[g]
            if 'TEXCOORD_0' in values:
                uv = values['TEXCOORD_0'].astype(np.float64)
                uv[:, 0] = (uv[:, 0] - box[0]) / (box[2] - box[0]); uv[:, 1] = (uv[:, 1] - box[1]) / (box[3] - box[1])
                values['TEXCOORD_0'] = uv.astype(np.float32)
            attrs = {k: add_accessor(out, ob, v, 5126, 'VEC3' if v.shape[1] == 3 else 'VEC2', 34962) for k, v in values.items()}
            ia = add_accessor(out, ob, ind.astype(np.uint16 if ind.max() < 65536 else np.uint32).reshape(-1, 1),
                              5123 if ind.max() < 65536 else 5125, 'SCALAR', 34963)
            p_ = {'attributes': attrs, 'indices': ia, 'material': idxs[0]}
            if nvar:
                p_['extensions'] = {'KHR_materials_variants': {'mappings': [{'material': idxs[v], 'variants': [v]} for v in range(nvar)]}}
            prims.append(p_)
        out['meshes'].append({'name': it['name'] if level == 0 else f"{it['name']}_LOD{level}", 'primitives': prims})
    if len(levels) > 1:
        out['meshes'][0]['extras'] = {'openyamm_lods': list(range(1, len(levels)))}
    if nvar:
        out['extensionsUsed'] = ['KHR_materials_variants']
        out['extensions'] = {'KHR_materials_variants': {'variants': copy.deepcopy(variants)}}
    out['buffers'][0]['byteLength'] = len(ob)
    return out, ob


if __name__ == '__main__':
    main()
