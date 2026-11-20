#!/usr/bin/env python3
"""Scale chosen joints' rotations in one clip toward a reference pose, in a copy of a GLB (anim fixes, 2026-11-11).

    scale_keys.py <in.glb> <out.glb> --clip Hit --joints 'B_Spine*,B_Neck,B_Head' --factor 0.5 \
        [--ref Standing] [--ref-time 0] [--translation-joints B_Pelvis --translation-factor 0.5]

Per key: rotation = slerp(reference local rotation, key rotation, factor); the reference is the joint's local rotation
in --ref at --ref-time (default: Standing frame 0, which one-shot clips blend from and to), so the clip's start and end
stay where they were when they already equal it. --translation-joints scale their translation keys the same way.
Only the matched samplers' outputs change (new accessors appended).
"""
import argparse
import fnmatch
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--clip', required=True)
    p.add_argument('--joints', required=True)
    p.add_argument('--factor', type=float, required=True)
    p.add_argument('--ref', default='Standing')
    p.add_argument('--ref-time', type=float, default=0.0)
    p.add_argument('--translation-joints', default='')
    p.add_argument('--translation-factor', type=float, default=1.0)
    args = p.parse_args()
    g = glb_pose.Glb(args.input)
    m = glb_pose.Model(g)
    doc = g.json
    names = [x.get('name', '') for x in doc['nodes']]
    ref = m.sample(args.ref, args.ref_time)
    rot_globs = args.joints.split(',')
    tr_globs = [x for x in args.translation_joints.split(',') if x]
    anim = doc['animations'][m.clips[args.clip]]
    changed = []
    for ch in anim['channels']:
        node = ch['target']['node']
        path = ch['target']['path']
        name = names[node]
        if path == 'rotation' and any(fnmatch.fnmatch(name, x) for x in rot_globs):
            f = args.factor
        elif path == 'translation' and any(fnmatch.fnmatch(name, x) for x in tr_globs):
            f = args.translation_factor
        else:
            continue
        sampler = anim['samplers'][ch['sampler']]
        vals = g.accessor(sampler['output']).astype(np.float64)
        r = ref.get(node, m.rest[node])[0 if path == 'translation' else 1]
        if path == 'rotation':
            out = np.array([glb_pose.slerp(np.asarray(r), v / np.linalg.norm(v), f) for v in vals])
            out /= np.linalg.norm(out, axis=1, keepdims=True)
            for i in range(1, len(out)):
                if np.dot(out[i], out[i - 1]) < 0:
                    out[i] = -out[i]
            kind = 'VEC4'
        else:
            out = np.asarray(r) + f * (vals - np.asarray(r))
            kind = 'VEC3'
        sampler['output'] = g.append_accessor(out, kind)
        changed.append(f'{name}.{path}')
    print(f'SCALEKEYS {args.clip}: {len(changed)} channels x{args.factor}')
    g.write(args.output)


if __name__ == '__main__':
    main()
