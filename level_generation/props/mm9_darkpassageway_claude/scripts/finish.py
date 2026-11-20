#!/usr/bin/env python3
"""Finish Dark Passageway props with the isle props project's finish step (its scripts/finish.py, paths pointed at
this project), as Yanmir's Fort's finish.py: alpha modes, double-sided pieces, the flame cards' material (the isle's
FIRE: unlit, BLEND, `openyamm_billboard: card`, the 16x4 flipbook), LOD linking, checks (one mesh node, decreasing
LODs, COLOR_0, base on the ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install
hands each to tools/install_model.py --world mm9. Cut-outs: the bushes' leaf cards and the trees' branch cards (their
second skin, material <prop>_1). The claw torch's ice orb (`clawtorch_orb`, build.py) glows blue with a slow flicker
(Yanmir's ORB). The six ice statuettes are blended (MM9 draws Icebolt translucent; looked at in game on
2026-10-31, review/propfix_game/); the stone banshees and the crystal stay opaque.
Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
# material name (without the _2s double-sided suffix) -> alpha mode
# The ice statuettes in Icebolt.dtx's own soft alpha (0.38-0.83): no depth write, each body's faces in index order;
# in game (review/propfix_game/blend) the far limbs and the cloak's inside read as ice, not as sorting faults.
BLEND = {'iceskeleton', 'icezombie', 'icelich', 'icebanshee', 'iceterror', 'iceskeletonwarrior'}
CUTOUT = {'bush03', 'bush05', 'tree01b_1', 'tree02_1', 'tree05_1', 'tree06_1'}
ORB = {'emissive': [0.12, 0.28, 0.62], 'extras': {'openyamm_flicker': [0.15, 3.0]}}


def settings(prop, name):
    if name == 'Fire' or name.startswith('Fire_'):     # Fire_<k>: the lit claw torch's orb flames (build.py)
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
