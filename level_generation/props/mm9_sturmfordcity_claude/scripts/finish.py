#!/usr/bin/env python3
"""Finish Sturmford City props with the isle props project's finish step (its scripts/finish.py, paths pointed at
this project), as Hall of the Gods' finish.py: alpha modes, double-sided pieces, the flame cards' material (the isle's
FIRE: unlit, BLEND, `openyamm_billboard: card`, the 16x4 flipbook), LOD linking, checks (one mesh node, decreasing
LODs, COLOR_0, base on the ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install
hands each to tools/install_model.py --world mm9. Cut-outs: the skins with transparent texels.
Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
# material name (without the _2s double-sided suffix) -> alpha mode
BLEND = set()
# Skins with transparent texels (the beet rack's slats, the lanterns' panes): cut-outs.
CUTOUT = {'beetrack', 'lamppost4', 'lanternwall1'}
ORB = {}


def settings(prop, name):
    if name == 'Fire':
        return isle_finish.FIRE
    if name == f'{prop}_orb':
        return ORB
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
