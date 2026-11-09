#!/usr/bin/env python3
"""The Queen's body GLB: the approved reduced Glassback (work/hes_glassback_reduced_source.glb, a copy of
hes_glassback_reduce_claude/export/hes_glassback.glb) with ONE skin, hgb_q, whose region ramps are hers
(boss_glassback_queen.png, candidate 3): slate blue-grey scales with pale chalky mineral crust on the raised plates,
a pale ash belly. Geometry, rig, clips, LODs, textures and the region mask are unchanged.

The crust is a luminance-rank ramp on the hide region (R, and A, the family's rust streaks): each of the 16 stops of
the hide's luminance range takes the colour of the queen palette at that luminance's rank among the hide texels, so
the brightest ~45 % of the hide (the plate tops) turns pale and the darker scales and crevices stay slate.
Writes export/hes_glassback_queen.glb and textures/hgb_q_ramps.json. Args: none."""
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as R  # noqa: E402

SRC = ROOT / 'work/hes_glassback_reduced_source.glb'
OUT = ROOT / 'export/hes_glassback_queen.glb'
# (rank among the region's texels, sRGB colour)
# viewer review 1 (review/viewer_shots_v1.png): the first palette (pale from rank 0.55) read almost white; candidate 3
# is mostly slate blue-grey with pale crust on the brightest third
HIDE = [(0.0, (16, 18, 22)), (0.15, (32, 35, 41)), (0.35, (52, 56, 64)), (0.55, (72, 76, 85)),
        (0.68, (92, 92, 93)), (0.8, (118, 114, 107)), (0.92, (142, 136, 125)), (1.0, (165, 158, 146))]
BELLY = [(0.0, (70, 66, 60)), (0.5, (118, 112, 102)), (1.0, (155, 148, 136))]
# review 2 (review/viewer_shots_v2.png): still near-white in the viewer next to the family's viewer shots; lowered
# about 15 % (crust peak 218 -> 192); review 3: the hide's mean 94 against the family B's 60 still read white, lowered
# about 25 % more (hide mean ~70, crust peak 165)


def image_of(doc, binary, tex_index):
    img = doc['images'][doc['textures'][tex_index]['source']]
    v = doc['bufferViews'][img['bufferView']]
    off = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[off:off + v['byteLength']])))


def palette(stops, rank):
    r = np.array([s[0] for s in stops]); c = R.srgb_to_linear(np.array([s[1] for s in stops], float) / 255)
    return np.stack([np.interp(rank, r, c[:, k]) for k in range(3)], -1)


def rank_ramp(lum, weight, rng, stops):
    """16 linear colours over the luminance range rng: colour of the palette at each stop's rank among the texels."""
    sel = lum[weight > 0.5]
    srt = np.sort(sel)
    stop_lum = np.linspace(rng[0], rng[1], 16)
    rank = np.searchsorted(srt, stop_lum) / max(1, len(srt))
    return palette(stops, rank).round(5).tolist(), rank.round(3).tolist()


def main():
    doc, binary = R.read_glb(SRC)
    mats = doc['materials']
    base = mats[0]
    ex = base['extras']
    basecol = np.asarray(image_of(doc, binary, base['pbrMetallicRoughness']['baseColorTexture']['index'])
                         .convert('RGB'), np.float64) / 255
    mask = np.asarray(image_of(doc, binary, ex['openyamm_region_mask']['index']).convert('RGBA')
                      .resize(basecol.shape[1::-1], Image.BILINEAR), np.float64) / 255
    lum = R.luminance(basecol)
    ramps = [dict(r) for r in ex['openyamm_region_ramps']]
    report = {}
    for ch, stops in ((0, HIDE), (1, BELLY), (3, HIDE)):
        cols, rank = rank_ramp(lum, mask[..., ch], ramps[ch]['range'], stops)
        ramps[ch] = {'range': ramps[ch]['range'], 'colors': cols}
        report[ch] = {'stop_ranks': rank, 'texels': int((mask[..., ch] > 0.5).sum())}
    # keep only the A materials (body, LOD2, LOD3), recoloured as the queen; one variant hgb_q
    keep = [i for i, m in enumerate(mats) if m['name'].startswith('Glassback_A')]
    remap = {old: new for new, old in enumerate(keep)}
    new_mats = []
    for i in keep:
        m = json.loads(json.dumps(mats[i]))
        m['name'] = m['name'].replace('Glassback_A', 'Glassback_Q')
        m['extras']['openyamm_region_ramps'] = ramps
        new_mats.append(m)
    doc['materials'] = new_mats
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            maps = p['extensions']['KHR_materials_variants']['mappings']
            a = next(mp['material'] for mp in maps if mp['variants'] == [0])
            p['material'] = remap[a]
            p['extensions']['KHR_materials_variants'] = {'mappings': [{'material': remap[a], 'variants': [0]}]}
    doc['extensions']['KHR_materials_variants'] = {'variants': [{'name': 'hgb_q'}]}
    R.write_glb(OUT, doc, binary)
    json.dump({'variants': ['hgb_q'], 'ramps': ramps, 'report': report, 'hide_palette': HIDE, 'belly_palette': BELLY},
              open(ROOT / 'textures/hgb_q_ramps.json', 'w'), indent=1)
    print('BODY', OUT.name, 'materials', [m['name'] for m in new_mats], 'report', json.dumps(report)[:300])


if __name__ == '__main__':
    main()
