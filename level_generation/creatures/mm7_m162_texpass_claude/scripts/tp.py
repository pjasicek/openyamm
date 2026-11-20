"""Shared helpers of the generic MM6-MM8 texture-pass toolkit (texpass-2, 2026-11-11), after the Troll's
mm8_m480_texpass_claude/scripts. The project's texpass.json names the target GLB(s), the meshes laid out together
(the LOD0 body first; extra LOD-less meshes such as wings that sample the same images), head bones and regions.
Every script here reads it; copy the scripts folder to the next project and write its texpass.json."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
CREATURES = HERE.parent
REPO = CREATURES.parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(CREATURES / 'claude_shared'))
CFG = json.loads((HERE / 'texpass.json').read_text())
from glb import Glb  # noqa: E402


def installed(i=0):
    world, stem = CFG['targets'][i]
    return REPO / 'assets_source' / 'worlds' / world / 'models' / f'{stem}.glb'


def before_glb(i=0):
    return HERE / 'work' / 'before_texpass' / f'{CFG["targets"][i][1]}.glb'


def mesh_index(doc, name):
    hits = [i for i, m in enumerate(doc['meshes']) if m.get('name') == name]
    assert len(hits) == 1, (name, hits)
    return hits[0]


def layout_prims(doc):
    """[(mesh index, primitive index)] of the layout meshes, in order; texpass.json layout_prims [[mesh, prim], ...]
    instead lays out only those primitives (ADragon m182: the head set only, body and wings sets kept)."""
    if CFG.get('layout_prims'):
        return [(mesh_index(doc, name), int(pi)) for name, pi in CFG['layout_prims']]
    out = []
    for name in CFG['layout_meshes']:
        mi = mesh_index(doc, name)
        for pi in range(len(doc['meshes'][mi]['primitives'])):
            out.append((mi, pi))
    return out


def material_images(doc, mat_index):
    """kind -> image index for a material (basecolor, metal_rough, normal, region_mask), present ones only."""
    m = doc['materials'][mat_index]
    tex = doc['textures']
    out = {}
    pbr = m.get('pbrMetallicRoughness', {})
    if 'baseColorTexture' in pbr:
        out['basecolor'] = tex[pbr['baseColorTexture']['index']]['source']
    if 'metallicRoughnessTexture' in pbr:
        out['metal_rough'] = tex[pbr['metallicRoughnessTexture']['index']]['source']
    if 'normalTexture' in m:
        out['normal'] = tex[m['normalTexture']['index']]['source']
    if 'emissiveTexture' in m:
        out['emissive'] = tex[m['emissiveTexture']['index']]['source']
    if 'occlusionTexture' in m:
        out['occlusion'] = tex[m['occlusionTexture']['index']]['source']
    if 'openyamm_burn_map' in m.get('extras', {}):
        out['burn'] = tex[m['extras']['openyamm_burn_map']['index']]['source']
    if 'openyamm_region_mask' in m.get('extras', {}):
        out['region_mask'] = tex[m['extras']['openyamm_region_mask']['index']]['source']
    return out


def prim_images(doc, pr):
    """Images of a primitive's material plus those only its variant materials have (Robot m386: tier A has no region
    mask, tiers B/C do; the mask is the same image)."""
    out = material_images(doc, pr['material'])
    for m in pr.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        for kind, image in material_images(doc, m['material']).items():
            out.setdefault(kind, image)
    return out


def part_images(doc):
    """Image set per layout primitive (installed GLB)."""
    return [prim_images(doc, doc['meshes'][mi]['primitives'][pi]) for mi, pi in layout_prims(doc)]


def body_images(doc):
    """Image set of the LOD0 body, checked to be shared by every layout primitive (base colour at least). With
    texpass.json merge_sets the layout primitives may have their own sets: the first one's images become the merged
    atlas and apply.py points the other materials at them."""
    prims = layout_prims(doc)
    first = prim_images(doc, doc['meshes'][prims[0][0]]['primitives'][prims[0][1]])
    if CFG.get('merge_sets'):
        return first
    for mi, pi in prims[1:]:
        other = prim_images(doc, doc['meshes'][mi]['primitives'][pi])
        assert other['basecolor'] == first['basecolor'], ('layout meshes must share the base colour image', mi)
    return first


def weights_float(w):
    w = np.asarray(w)
    if w.dtype == np.uint8:
        return w.astype(np.float64) / 255
    if w.dtype == np.uint16:
        return w.astype(np.float64) / 65535
    return w.astype(np.float64)


def tri_area3(xyz):
    return np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2


def tri_area2(uv):
    return np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
                  - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
