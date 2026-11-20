#!/usr/bin/env python3
"""Puts chosen joints' channels of chosen clips back at the node's rest value, in a copy of a GLB (anim fixes,
2026-11-11). Only the matched samplers' outputs change (new accessors appended); everything else stays byte for byte.

    channel_rest.py <in.glb> <out.glb> --clips Walking [Jog ...] --joints 'B_Skirt*' [--paths rotation,translation]
"""
import argparse
import fnmatch
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402

DEFAULTS = {'rotation': [0.0, 0.0, 0.0, 1.0], 'translation': [0.0, 0.0, 0.0], 'scale': [1.0, 1.0, 1.0]}
KINDS = {'rotation': 'VEC4', 'translation': 'VEC3', 'scale': 'VEC3'}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--clips', nargs='+', required=True)
    p.add_argument('--joints', required=True, help="comma-separated globs")
    p.add_argument('--paths', default='rotation')
    args = p.parse_args()
    glb = glb_pose.Glb(args.input)
    doc = glb.json
    nodes = doc['nodes']
    globs = args.joints.split(',')
    paths = args.paths.split(',')
    names = {a.get('name'): i for i, a in enumerate(doc['animations'])}
    for clip in args.clips:
        animation = doc['animations'][names[clip]]
        changed = 0
        for channel in animation['channels']:
            node = channel['target']['node']
            path = channel['target']['path']
            if path not in paths or not any(fnmatch.fnmatch(nodes[node].get('name', ''), g) for g in globs):
                continue
            sampler = animation['samplers'][channel['sampler']]
            count = doc['accessors'][sampler['output']]['count']
            rest = np.array(nodes[node].get(path, DEFAULTS[path]), dtype=np.float32)
            sampler['output'] = glb.append_accessor(np.tile(rest, (count, 1)), KINDS[path])
            changed += 1
        print(f'CHANNELREST {clip}: {changed} channels at rest')
    glb.write(args.output)


if __name__ == '__main__':
    main()
