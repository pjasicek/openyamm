"""Shared helpers of the MM6-MM8 texture-pass kit (audit 2026-11-11, stream texpass-1).

The kit generalises the Troll's scripts (mm8_m480_texpass_claude/scripts) to any installed creature GLB: several
LOD0 primitives may join one new atlas (a claws set merged into the body), burn maps are carried, LOD2/LOD3 maps are
refilled per primitive. Every script reads <project>/texpass.json:

  world, stem          installed file assets_source/worlds/<world>/models/<stem>.glb (backed up in
                       work/before_texpass/<stem>.glb, which every script reads; never the live file)
  node                 LOD0 node name (its mesh carries extras.openyamm_lods / openyamm_shadow_lods)
  atlas_prims          LOD0 primitive indices laid into the new atlas; the first one's material is the main material,
                       whose images are replaced; the others' materials are pointed at the main material's textures
  head_bones           joint-name regexes; a triangle is head when its corners' head weight averages over 0.5
  head_factor          texel density factor of head islands (1.8)
  group_factors        {name: [regex, factor]} vertex-weight groups denser (hands 1.3)
  uv_options           extra uv_atlas.unwrap keyword arguments
  size                 atlas size (2048)
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

KIT = Path(__file__).resolve().parent
PROJECT = KIT.parent
CREATURES = PROJECT.parent
REPO = CREATURES.parents[1]
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(CREATURES / 'claude_shared'))
try:
    from glb import Glb  # noqa: E402  (not inside Blender, which has no PIL)
except ImportError:
    Glb = None


def config():
    """texpass.json, or the file named by TP_CONFIG (a second world's copy of a shared layout)."""
    import os
    return json.loads((PROJECT / os.environ.get('TP_CONFIG', 'texpass.json')).read_text())


def lod0_path(cfg=None):
    """work/lod0_before<tag>.npz: a model with two atlases (TP_CONFIG per atlas) gives each config a 'tag'."""
    cfg = cfg or config()
    return PROJECT / 'work' / f"lod0_before{cfg.get('tag', '')}.npz"


def before_glb(cfg=None):
    cfg = cfg or config()
    return PROJECT / 'work' / 'before_texpass' / f"{cfg['stem']}.glb"


def lod0_mesh_index(doc, node_name):
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    return node['mesh']


def joint_names(doc):
    return [doc['nodes'][j].get('name', '') for j in doc['skins'][0]['joints']]


def bone_weight(joints, weights, names, patterns):
    """Per-vertex summed weight of joints whose name matches any regex."""
    hit = np.array([any(re.search(p, n) for p in patterns) for n in names], bool)
    return (np.where(hit[joints], weights, 0)).sum(1)


def tri_area3(xyz):
    return np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2


def tri_area2(uv):
    return np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
                  - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2


def material_maps(material):
    """{kind: texture index} of a material: basecolor, metal_rough, normal, region_mask, burn_map, emissive."""
    pbr = material.get('pbrMetallicRoughness', {})
    extras = material.get('extras', {})
    found = {'basecolor': pbr.get('baseColorTexture'), 'metal_rough': pbr.get('metallicRoughnessTexture'),
             'normal': material.get('normalTexture'), 'region_mask': extras.get('openyamm_region_mask'),
             'burn_map': extras.get('openyamm_burn_map'), 'emissive': material.get('emissiveTexture')}
    return {k: v['index'] for k, v in found.items() if isinstance(v, dict) and 'index' in v}


def primitive_materials(primitive):
    """Default material and every variant material of a primitive."""
    out = [primitive['material']]
    for m in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        if m['material'] not in out:
            out.append(m['material'])
    return out
