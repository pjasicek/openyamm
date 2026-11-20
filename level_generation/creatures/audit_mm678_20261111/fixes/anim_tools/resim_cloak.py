#!/usr/bin/env python3
"""Re-simulate the cloak or robe chains of an EXISTING looping clip with a gait package's cloak.py (anim fixes,
2026-11-11). Run from a fix project holding a copy of the package's scripts/ (compose_gait.py, cloak.py, gaitlib.py).

    resim_cloak.py <in.glb> <out.glb> <clip> '<cloak spec as in a job: {"chains": ..., "preset": ..., ...}>' [--rate 60]
    resim_cloak.py <in.glb> <out.glb> <clip> '<a job's "cloth" list for cloth_sim.py (h08 lineage): [{...}, ...]>'

A JSON object is a cloak.py spec (h01/h03 lineage); a JSON list is a cloth_sim.py config list (h08/h11 lineage).

The body (every other channel) stays as it is; only the chain joints' channels of that clip are replaced, keyed at
N = rate x length samples plus the loop key. New accessors are appended; the rest of the GLB stays byte for byte.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path.cwd() / 'scripts'))
import compose_gait  # noqa: E402
import gaitlib  # noqa: E402
from gaitlib import glb_pose  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('clip')
    p.add_argument('spec')
    p.add_argument('--rate', type=float, default=60.0)
    args = p.parse_args()
    body = compose_gait.Body(args.input)
    T = body.clip_length(args.clip)
    N = int(round(T * args.rate))
    times = np.arange(N) / N * T
    _, worlds = body.clip_world(args.clip, times)
    spec = json.loads(args.spec)
    if isinstance(spec, list):
        import cloth_sim
        report = {}
        worlds, names = cloth_sim.apply(body, worlds, T, spec, report)
        nodes = sorted({body.idx[n] for n in names})
        hem = report.get('hem_floor', report.get('cloth'))
    else:
        import cloak
        sim = cloak.Cloak(body, spec, spec.get('floor'), spec.get('leg_pad', 0.0))
        pts = sim.simulate(worlds, T)
        worlds = sim.pose(worlds, pts)
        nodes = sorted(sim.nodes())
        hem = round(float(pts[:, :, -1, 1].min()), 3)
    g = body.glb
    animation = g.json['animations'][body.model.clips[args.clip]]
    keep = [c for c in animation['channels'] if c['target']['node'] not in set(nodes)]
    samplers = animation['samplers']
    channels = [dict(c) for c in keep]
    t_acc = g.append_accessor((np.arange(N + 1) / N * T).reshape(-1, 1), 'SCALAR')
    for node in nodes:
        parent = body.parent[node]
        rest = body.model.rest[node]
        q, t = [], []
        for i in range(N + 1):
            W = worlds[i % N]
            local = np.linalg.inv(W[parent]) @ W[node]
            t.append(local[:3, 3])
            q.append(glb_pose.matrix_quaternion(local[:3, :3]))
        q = np.array(q)
        for i in range(1, len(q)):
            if np.dot(q[i], q[i - 1]) < 0:
                q[i] = -q[i]
        for path, values, kind in (('translation', np.array(t), 'VEC3'), ('rotation', q, 'VEC4'),
                                   ('scale', np.tile(rest[2], (N + 1, 1)), 'VEC3')):
            samplers.append({'input': t_acc, 'output': g.append_accessor(values, kind), 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': int(node), 'path': path}})
    used = sorted({c['sampler'] for c in channels})
    remap = {old: new for new, old in enumerate(used)}
    animation['samplers'] = [samplers[i] for i in used]
    for c in channels:
        c['sampler'] = remap[c['sampler']]
    animation['channels'] = channels
    gaitlib.restore_nodes(g, body.aliases)
    g.write(args.output)
    print(f'RESIM {args.clip}: {len(nodes)} chain joints over {N} samples; {hem}')


if __name__ == '__main__':
    main()
