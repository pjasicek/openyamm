#!/usr/bin/env python3
"""Tier colours of the four installed PeasantDF GLBs for mpqem_df.py's texture guard (the body and hand UVs are the same in
every design, so a collapse must look right in every design's paint). Writes work/tex_p<prim>_<design><tier>.png:
prim 0 (body set) = each tier's base colour with its region ramps (claude_shared/tier_textures.apply, the engine rule), plus
each design's region mask as tier M; prim 1 (head + hands set) = each tier's head colour with its head ramps, plus the head
region mask. Seven tiers: d1 A/B, d2 B, d3 A/B, d4 A/B."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
for n in '1234':
    doc, b = gb.read(HERE / 'before' / f'mm9_peasantdf{n}.glb')

    def image(i):
        im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        return Image.open(io.BytesIO(b[o:o + v['byteLength']]))
    mesh = doc['meshes'][next(nd for nd in doc['nodes'] if nd.get('name') == 'PeasantDF' and 'mesh' in nd)['mesh']]
    for pi, p in enumerate(mesh['primitives']):
        mats = [m['material'] for m in p['extensions']['KHR_materials_variants']['mappings']]
        for mi in mats:
            m = doc['materials'][mi]; ex = m['extras']
            tone = np.asarray(image(doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB'), np.float64) / 255
            mimg = image(ex['openyamm_region_mask']['index']).convert('RGBA'); size = (tone.shape[1], tone.shape[0])
            mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
            out = TT.apply(tone, mask, ex['openyamm_region_ramps'])
            tier = m['name'][-1]
            Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_p{pi}_d{n}{tier}.png')
            print('TEX', pi, n, tier, m['name'], tone.shape)
        Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_p{pi}_d{n}M.png')
