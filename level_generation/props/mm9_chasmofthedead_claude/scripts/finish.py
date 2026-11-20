#!/usr/bin/env python3
"""Finish the Chasm of the Dead props with the isle props project's finish step (its scripts/finish.py, paths pointed at
this project, as the Anskram Keep's finish.py): alpha modes (cut-out skins: the harp's strings, the hanging bowls'
chains), double-sided pieces, the unlit billboard flame flipbook, LOD linking, checks (one mesh node, decreasing
LODs, COLOR_0, base on the ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install
hands each to tools/install_model.py --world mm9. Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
isle_finish.CUTOUT = {'bluebowl'}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ok = all([isle_finish.finish(prop, '--install' in sys.argv) for prop in args or props_table.built_props()])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
