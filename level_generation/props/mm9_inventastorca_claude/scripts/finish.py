#!/usr/bin/env python3
"""Finish Inventa Storca props with the isle props project's finish step (its scripts/finish.py, paths pointed at this
project): alpha modes, double-sided pieces, LOD linking, checks (one mesh node, decreasing LODs, COLOR_0, base on the
ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install hands each to
tools/install_model.py --world mm9. Glass skins (jars, beaker, the shelf's bottles) blend; skins with holes (cages, rack,
wheels, pillory, the herbs) are cut-outs. Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
# material name (without the _2s double-sided suffix) -> alpha mode
BLEND = {'jar', 'jarbroken', 'beaker01', 'shelfitem05'}
CUTOUT = {'bagherbs_1', 'torturecage01', 'torturerack01', 'torturewheel01', 'torturewheel02', 'pillory',
          'skeletoncage', 'shelfitem02'}


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
