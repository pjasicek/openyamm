"""Splits the installed Bedraggled Human's one body | head atlas set into two texture sets, so each can take a full
2048 square (the cook caps every creature texture at 2048, so the installed 4128x2048 atlas drew at 2048x1024).

LOD0 and LOD1 (the meshes that sample the LOD0 atlas) get two primitives each: primitive 0 = body faces (old UV
centroid u < 0.5), primitive 1 = head faces (u > 0.5, the separately modelled head, neck and hair). Faces keep their
order inside each primitive; vertices are copied per primitive with every attribute. The head primitive takes a new
material `Bedraggled_Head`: Bedraggled_A without region mask and ramps (the head half of the installed mask is zero in
every channel, so the tiers never recoloured it), mapped for every variant. Shadow meshes, far LODs, nodes, skin,
clips and the body materials are unchanged. At this stage both materials still sample the installed atlas images, so
the split GLB renders exactly as the installed one.

Usage: m620_split.py <in glb> <out glb>
"""
import copy
import json
import sys

import numpy as np

from glb import Glb

SPLIT_U = 0.5


def split_mesh(g, mesh_index, head_mat):
    doc = g.doc
    mesh = doc['meshes'][mesh_index]
    assert len(mesh['primitives']) == 1, mesh['name']
    pr = mesh['primitives'][0]
    faces = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
    uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
    head = uv[faces][:, :, 0].mean(1) > SPLIT_U
    parts = []
    for sel in (~head, head):
        f = faces[sel]
        verts, inverse = np.unique(f.ravel(), return_inverse=True)
        parts.append((verts, inverse.reshape(-1, 3)))
    original = {name: g.accessor(acc) for name, acc in pr['attributes'].items()}
    head_pr = copy.deepcopy(pr)
    head_pr['material'] = head_mat
    variants = len(doc['extensions']['KHR_materials_variants']['variants'])
    head_pr['extensions'] = {'KHR_materials_variants': {'mappings': [
        {'material': head_mat, 'variants': list(range(variants))}]}}
    for target, (verts, f) in zip((pr, head_pr), parts):
        for name, acc in list(target['attributes'].items()):
            data = original[name]
            if target is head_pr:
                doc['accessors'].append(copy.deepcopy(doc['accessors'][acc]))
                acc = len(doc['accessors']) - 1
                target['attributes'][name] = acc
            g.set_accessor(acc, data[verts])
        ia = pr['indices']
        if target is head_pr:
            doc['accessors'].append(copy.deepcopy(doc['accessors'][ia]))
            ia = len(doc['accessors']) - 1
            target['indices'] = ia
        g.set_accessor(ia, f.reshape(-1))
    mesh['primitives'].append(head_pr)
    return int((~head).sum()), int(head.sum())


def main():
    src, dst = sys.argv[1:3]
    g = Glb(src)
    doc = g.doc
    lod0 = next(n['mesh'] for n in doc['nodes'] if n.get('name') == 'Bedraggled' and 'mesh' in n)
    lod1 = doc['meshes'][lod0]['extras']['openyamm_lods'][0]
    body_mat = doc['meshes'][lod0]['primitives'][0]['material']
    head = copy.deepcopy(doc['materials'][body_mat])
    head['name'] = 'Bedraggled_Head'
    extras = head.get('extras', {})
    extras.pop('openyamm_region_mask', None)
    extras.pop('openyamm_region_ramps', None)
    if not extras:
        head.pop('extras', None)
    doc['materials'].append(head)
    head_mat = len(doc['materials']) - 1
    report = {}
    for level, mi in ((0, lod0), (1, lod1)):
        report[f'LOD{level}'] = split_mesh(g, mi, head_mat)
    g.save(dst)
    print('SPLIT', json.dumps(report), 'head material', head_mat)


if __name__ == '__main__':
    main()
