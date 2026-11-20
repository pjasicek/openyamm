#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard and texture_drift.py: work/tex_<base>_<tier>.png (bytes
as installed). Thrall material names: Thrall_A/B/C (limbs, one shared image + region ramps in the engine), ThrallTorso,
ThrallTorso_B/C, ThrallHead, ThrallHead_B/C (tier A has no suffix): written as tex_Thrall_A, tex_ThrallTorso_A, ... ."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_thrall.glb')
for m in doc['materials']:
    name = m['name'] if m['name'][-2:] in ('_A', '_B', '_C') else m['name'] + '_A'
    ti = m['pbrMetallicRoughness']['baseColorTexture']['index']
    src = doc['textures'][ti]['source']; im = doc['images'][src]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); (HERE / 'work' / f"tex_{name}.png").write_bytes(b[o:o + v['byteLength']]); print('TEX', name, 'image', src)
