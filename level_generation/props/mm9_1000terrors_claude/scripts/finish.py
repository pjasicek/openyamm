#!/usr/bin/env python3
"""Finish the Thousand Terrors props with the isle props project's finish step (its scripts/finish.py, paths pointed
at this project; Lindisfarne Monastery's finish): alpha modes, double-sided pieces, the flame cards' unlit 'card'
billboard flipbook (the isle's FIRE settings, the pipeline as fixed on 2026-10-30), LOD linking, checks (one mesh
node, decreasing LODs, COLOR_0, base on the ground, check_winding.py: 0 inverted closed parts) ->
work/mm9_deco_<prop>.glb; --install hands each to tools/install_model.py --world mm9.
Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
# material name (without the _2s double-sided suffix) -> alpha mode
BLEND = set()
CUTOUT = set()
# TerrorLight1's orb (build.py): MM9's blue flame sits at its centre; the orb glows blue (Yanmir's Fort's claw orbs,
# here nearer the paired MM9 lights' 0/39/196) with a slow flicker.
ORB = {'emissive': [0.08, 0.20, 0.62], 'extras': {'openyamm_flicker': [0.15, 3.0]}}
# The water orbs (build_waterorb.py): MM9's translucent WorldObjects (Alpha 0.4) over the blue candle lights:
# alpha-blended, base colour factor alpha 0.4 (x the opaque water123 frame), single-sided, a faint blue emission
# (MM9 lightmapped them from the blue light inside; a BLV light inside lights only their back faces here) and the
# TerrorLight orbs' slow flicker. Its texture is water123.spr's ten frames at 15 a second (waterorb_flipbook.py, a
# 5 x 2 flipbook; 2026-11-09: before, frame 0 only).
WATERORB = {'alpha': 'BLEND', 'opacity': 0.4, 'emissive': [0.02, 0.08, 0.35],
            'extras': {'openyamm_flicker': [0.15, 3.0], 'openyamm_specular': 0.0, 'openyamm_flipbook': [5, 2, 15]}}
OPACITY = {'waterorb': 0.4}
_write_glb = isle_finish.link.write_glb


def write_glb(path, document, binary):
    """The isle finish writes no base colour factor: set the alpha of OPACITY materials before the GLB is written."""
    for material in document.get('materials', []):
        if material.get('name') in OPACITY:
            pbr = material.setdefault('pbrMetallicRoughness', {})
            pbr['baseColorFactor'] = [1.0, 1.0, 1.0, OPACITY[material['name']]]
    return _write_glb(path, document, binary)


isle_finish.link.write_glb = write_glb


def settings(prop, name):
    if name == 'Fire':
        return isle_finish.FIRE
    if name == f'{prop}_orb':
        return ORB
    if name == 'waterorb':
        return WATERORB
    base = name[:-3] if name.endswith('_2s') else name
    out = {}
    if base in BLEND:
        out = {'alpha': 'BLEND'}
    elif base in CUTOUT:
        out = {'alpha': 'MASK', 'cutoff': 0.5}
    if name.endswith('_2s'):
        out = dict(out, double=True)
    return out


isle_finish.settings = settings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    props = args or props_table.built_props()
    ok = all([isle_finish.finish(prop, '--install' in sys.argv) for prop in props])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
