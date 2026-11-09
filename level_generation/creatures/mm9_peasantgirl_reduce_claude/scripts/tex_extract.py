#!/usr/bin/env python3
"""Tier base colours of BOTH installed peasant-girl GLBs for mpqem.py's texture guard (one cut serves both GLBs, so every
tier of the family guards it): work/tex_<prim material of the elf GLB>_<tier>.png.
Body (PeasantGirl_G1E prim; the same shared tone image in both GLBs): tiers g2, g3 (human GLB materials PeasantGirl_G2 / _G3)
and g1e (elf GLB PeasantGirl_G1E), each the tone with its region ramps applied by the engine rule (claude_shared/tier_textures.
apply, ramps and mask read from the GLBs), plus the region mask as tier M. Head (PeasantGirlHead): each girl's head image."""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import bglbio as gb  # noqa: E402
import tier_textures as TT  # noqa: E402
GL = {k: gb.read(HERE / 'before' / f) for k, f in (('h', 'mm9_peasantgirl.glb'), ('e', 'mm9_peasantgirl1e.glb'))}


def image(k, i):
    doc, b = GL[k]; im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


def mat(k, name):
    doc, _ = GL[k]; m = next(m for m in doc['materials'] if m['name'] == name)
    return m, doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']


mh, th = mat('h', 'PeasantGirl_G2'); me, te = mat('e', 'PeasantGirl_G1E')
tone = np.asarray(image('h', th).convert('RGB'), np.float64) / 255
assert np.array_equal(np.asarray(image('h', th)), np.asarray(image('e', te))), 'body tone differs between the GLBs'
mimg = image('h', mh['extras']['openyamm_region_mask']['index']).convert('RGBA')
size = (tone.shape[1], tone.shape[0])
mask = np.stack([np.asarray(ch.resize(size, Image.BILINEAR), np.float64) / 255 for ch in mimg.split()], -1)
for tier, k, name in (('g2', 'h', 'PeasantGirl_G2'), ('g3', 'h', 'PeasantGirl_G3'), ('g1e', 'e', 'PeasantGirl_G1E')):
    m, _ = mat(k, name)
    out = TT.apply(tone, mask, m['extras']['openyamm_region_ramps'])
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / f'tex_PeasantGirl_G1E_{tier}.png')
    print('TEX body', tier, name)
Image.fromarray((mask[..., :3] * 255 + 0.5).astype(np.uint8)).save(HERE / 'work' / 'tex_PeasantGirl_G1E_M.png')
for tier, k, name in (('g2', 'h', 'PeasantGirlHead_pg_g2'), ('g3', 'h', 'PeasantGirlHead_pg_g3'), ('g1e', 'e', 'PeasantGirlHead')):
    _, t = mat(k, name); image(k, t).convert('RGB').save(HERE / 'work' / f'tex_PeasantGirlHead_{tier}.png'); print('TEX head', tier, name)
