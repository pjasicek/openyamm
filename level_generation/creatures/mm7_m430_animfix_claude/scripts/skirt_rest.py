#!/usr/bin/env python3
"""Puts the skirt bones of chosen clips back at rest (following the pelvis), in a copy of the GLB (anim fix,
2026-11-11). The 2026-10-21 floor fix (`floor_fix.py --lift-joints`) bent the Wight's eight skirt bones up to 35 degrees
to keep the walking hem above the floor, which pulled the robe into long sheets (cloth 41.6 % bad against 7.5 % before
the fix). Only the rotation samplers of the matched joints in the named clips change; new accessors are appended.

    skirt_rest.py <in.glb> <out.glb> --clips Walking [--joints 'B_Skirt*']
"""
import argparse
import fnmatch
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--clips', nargs='+', required=True)
    p.add_argument('--joints', default='B_Skirt*')
    args = p.parse_args()
    glb = glb_pose.Glb(args.input)
    doc = glb.json
    nodes = doc['nodes']
    names = {a.get('name'): i for i, a in enumerate(doc['animations'])}
    for clip in args.clips:
        animation = doc['animations'][names[clip]]
        changed = 0
        for channel in animation['channels']:
            node = channel['target']['node']
            if channel['target']['path'] != 'rotation' or \
                    not fnmatch.fnmatch(nodes[node].get('name', ''), args.joints):
                continue
            sampler = animation['samplers'][channel['sampler']]
            count = doc['accessors'][sampler['output']]['count']
            rest = np.array(nodes[node].get('rotation', [0.0, 0.0, 0.0, 1.0]), dtype=np.float32)
            sampler['output'] = glb.append_accessor(np.tile(rest, (count, 1)), 'VEC4')
            changed += 1
        print(f'SKIRTREST {clip}: {changed} rotation channels at rest')
    glb.write(args.output)


if __name__ == '__main__':
    main()
