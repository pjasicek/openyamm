#!/usr/bin/env python3
"""Finish keep props with the isle props project's finish step (its scripts/finish.py, paths pointed at this project):
alpha modes, double-sided pieces, the unlit billboard flame flipbook, LOD linking, checks (one mesh node, decreasing
LODs, COLOR_0, base on the ground, check_winding.py: 0 inverted closed parts) -> work/mm9_deco_<prop>.glb; --install
hands each to tools/install_model.py --world mm9. Usage: finish.py [prop ...] [--install]"""
import sys

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
import finish as isle_finish  # noqa: E402

isle_finish.HERE = props_table.HERE
isle_finish.CUTOUT = {'chair'}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    props = args or sorted(set(props_table.MODELS.values()) | {'gatefire'})
    ok = all([isle_finish.finish(prop, '--install' in sys.argv) for prop in props])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
