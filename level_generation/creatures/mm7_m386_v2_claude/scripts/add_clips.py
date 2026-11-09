#!/usr/bin/env python3
"""Add clips from a donor GLB (a Blender export of the same rig) to an existing export, matching nodes by name.

    add_clips.py <target.glb> <donor.glb> <out.glb> --clips Walk2 Run2

The target keeps every node, mesh, LOD, material variant and clip; each named donor clip is appended under its own
name (a clip of that name already in the target is an error). Key times and values are copied unchanged: the donor
comes from the same armature, so its node-local transforms are valid on the target's skeleton. Every donor channel
must target a node whose name exists exactly once in the target, and the joints' rest transforms are compared first.
"""
import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target', type=Path)
    parser.add_argument('donor', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--clips', nargs='+', required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.target.resolve(), args.donor.resolve()):
        raise SystemExit('write to a new file')
    target, donor = Glb(args.target), Glb(args.donor)
    names = [node.get('name') for node in target.json['nodes']]
    existing = {animation.get('name') for animation in target.json.get('animations', [])}

    # Same rig: every donor joint must exist in the target with the same rest transform.
    for skin in donor.json.get('skins', []):
        for joint in skin['joints']:
            node = donor.json['nodes'][joint]
            if names.count(node['name']) != 1:
                raise SystemExit(f"joint {node['name']} is not one node in the target")
            other = target.json['nodes'][names.index(node['name'])]
            for key, default in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])):
                a = np.array(node.get(key, default)); b = np.array(other.get(key, default))
                if key == 'rotation' and np.dot(a, b) < 0:
                    b = -b
                if np.abs(a - b).max() > 2e-4:
                    raise SystemExit(f"rest {key} of {node['name']} differs: {a} vs {b}")

    animations = {animation.get('name'): animation for animation in donor.json.get('animations', [])}
    for clip in args.clips:
        if clip in existing:
            raise SystemExit(f'{clip} is already in the target')
        source = animations[clip]
        copied = {}
        samplers = []
        for sampler in source['samplers']:
            entry = dict(sampler)
            for key in ('input', 'output'):
                index = sampler[key]
                if index not in copied:
                    accessor = donor.json['accessors'][index]
                    copied[index] = target.append_accessor(donor.accessor(index), accessor['type'])
                entry[key] = copied[index]
            samplers.append(entry)
        channels = []
        for channel in source['channels']:
            name = donor.json['nodes'][channel['target']['node']]['name']
            if names.count(name) != 1:
                raise SystemExit(f'{clip}: channel node {name} is not one node in the target')
            channels.append({'sampler': channel['sampler'],
                             'target': {'node': names.index(name), 'path': channel['target']['path']}})
        target.json['animations'].append({'name': clip, 'channels': channels, 'samplers': samplers})
        times = donor.accessor(source['samplers'][0]['input'])
        print(f'{clip}: {len(channels)} channels, {len(times)} keys, {float(times[-1, 0]):.4f} s')
    target.write(args.output)
    print('wrote', args.output)


if __name__ == '__main__':
    main()
