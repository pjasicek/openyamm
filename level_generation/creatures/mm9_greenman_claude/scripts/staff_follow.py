"""Hold the staff bone rigidly in the hand in every clip of a runtime GLB.

The MM9 clips key the staff bone (Bone01, a child of the scene root) in world space for MM9's own hand; our joints are
fitted to a different body, so the staff is re-keyed from OUR hand: Bone01_world(t) = Hand_world(t) * rel, with rel the
staff-in-hand transform (glTF space; default from scripts/retarget_pmale.json 'follow', optionally offset by
--offset x,y,z in hand space and --rot-deg ax,ay,az about the hand's axes).
Usage: staff_follow.py in.glb out.glb [--offset x,y,z] [--rot-deg a,b,c]"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from retarget_mm9 import read, sample, rest, parents, qmul, qinv, qrot
from pygltflib import GLTF2, AnimationSampler, AnimationChannel, AnimationChannelTarget, Accessor, BufferView

ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--offset', default='0,0,0'); ap.add_argument('--rot-deg', default='0,0,0')
ap.add_argument('--config', default=os.path.join(os.path.dirname(__file__), 'retarget_pmale.json'))
a = ap.parse_args()
fnode, (hnode, rt, rq) = next(iter(json.load(open(a.config))['follow'].items()))
rt = np.array(rt) + np.array([float(x) for x in a.offset.split(',')]); rq = np.array(rq)
for ax, deg in zip(np.eye(3), [float(x) for x in a.rot_deg.split(',')]):
    if deg:
        h = np.radians(deg) / 2
        rq = qmul(rq[None], np.array([*(ax * np.sin(h)), np.cos(h)])[None])[0]
G = GLTF2().load(a.inp)
names = {n.name: i for i, n in enumerate(G.nodes)}; par = parents(G)
fi, hi = names[fnode], names[hnode]
blob = bytearray(G.binary_blob())
def add(arr, typ):
    arr = np.ascontiguousarray(arr, np.float32)
    while len(blob) % 4:
        blob.append(0)
    G.bufferViews.append(BufferView(buffer=0, byteOffset=len(blob), byteLength=arr.nbytes)); blob.extend(arr.tobytes())
    G.accessors.append(Accessor(bufferView=len(G.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(G.accessors) - 1
for an in G.animations:
    tin = None
    for c in an.channels:
        if c.target.node == hi and c.target.path == 'rotation':
            tin = an.samplers[c.sampler].input
    if tin is None:
        tin = an.samplers[an.channels[0].sampler].input
    times = read(G, tin)[:, 0]; F = len(times)
    def wfk(i):
        q = sample(G, an, i, 'rotation', times); t = sample(G, an, i, 'translation', times)
        q = q if q is not None else np.repeat(rest(G.nodes[i], 'rotation')[None], F, 0)
        t = t if t is not None else np.repeat(rest(G.nodes[i], 'translation')[None], F, 0)
        if i not in par:
            return t, q
        pt, pq = wfk(par[i])
        return pt + qrot(pq, t), qmul(pq, q)
    ht, hq = wfk(hi)
    wq = qmul(hq, rq[None]); wt = ht + qrot(hq, np.repeat(rt[None], F, 0))
    if fi in par:
        pt, pq = wfk(par[fi]); lq = qmul(qinv(pq), wq); lt = qrot(qinv(pq), wt - pt)
    else:
        lq, lt = wq, wt
    for f in range(1, F):
        if np.dot(lq[f], lq[f - 1]) < 0:
            lq[f] = -lq[f]
    keep = [c for c in an.channels if c.target.node != fi]
    an.channels = keep
    tacc = add(times[:, None], 'SCALAR'); G.accessors[tacc].min = [float(times.min())]; G.accessors[tacc].max = [float(times.max())]
    an.samplers.append(AnimationSampler(input=tacc, output=add(lq, 'VEC4'), interpolation='LINEAR'))
    an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=fi, path='rotation')))
    an.samplers.append(AnimationSampler(input=tacc, output=add(lt, 'VEC3'), interpolation='LINEAR'))
    an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=fi, path='translation')))
    print('STAFF', an.name, F, 'keys; staff low (y)', round(float(wt[:, 1].min()), 3))
G.buffers[0].byteLength = len(blob); G.set_binary_blob(bytes(blob)); G.save(a.out)
