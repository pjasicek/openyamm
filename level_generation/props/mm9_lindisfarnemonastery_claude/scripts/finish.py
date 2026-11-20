#!/usr/bin/env python3
"""Finish Lindisfarne Monastery props with the isle props project's finish step (its scripts/finish.py, paths
pointed at this project): alpha modes, double-sided pieces, LOD linking, checks (one mesh node, decreasing LODs,
COLOR_0, base on the ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install hands
each to tools/install_model.py --world mm9. Skins with transparent texels are cut-outs: the tree's branch cards
(TreeBranch3) and the wash tub's drain (two triangles of the tub sample the skin's transparent spot).
Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
# material name (without the _2s double-sided suffix) -> alpha mode
BLEND = set()
CUTOUT = {'tree04_1', 'washtubtable'}


def settings(prop, name):
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
