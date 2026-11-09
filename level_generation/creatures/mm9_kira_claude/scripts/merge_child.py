"""Njam: NJAM.abc names PeasantMale.abc as its child model, which holds the walk, run, hit, death and Njam_* attack clips (same 45 joints, same rest). Adapted from mm9_highwayman_claude/scripts/merge_child.py: joints compared by index (the two mesh nodes differ by name), the "----------" separator clip skipped.
"""
"""HIGHWAYMAN.abc holds only 9 of its clips; the rest (walk, run, die1, die2, taunt, wince1...) are in its LithTech child model FIGHTERBASE.abc
(the ChildModels section). Same 32 nodes, same rest pose. Appends FIGHTERBASE's clips to a converted highwayman GLB. Args: <in glb> <fighterbase glb> <out glb>"""
import sys
from pygltflib import GLTF2, Accessor, BufferView, AnimationChannel, AnimationChannelTarget, AnimationSampler, Animation
IN, FB, OUT = sys.argv[1:4]
g = GLTF2().load(IN); f = GLTF2().load(FB)
J = 45  # joints; the last two nodes are mesh nodes, named per file
assert [n.name for n in g.nodes][:J] == [n.name for n in f.nodes][:J]
import numpy as np
for i in range(J):
    a, b = g.nodes[i], f.nodes[i]
    for k in ("translation", "rotation", "scale"):
        x, y = getattr(a, k), getattr(b, k)
        if x is not None and y is not None and not np.allclose(x, y, atol=1e-4): print("rest differs", a.name, k)  # Spine/Thigh 4.5 mm, skirt hinges Bone22/14/10/02/18 up to 9 deg: re-rested onto our mesh anyway
blob = bytearray(g.binary_blob()); fblob = f.binary_blob()
def copy(i):
    global blob
    a = f.accessors[i]; bv = f.bufferViews[a.bufferView]
    data = fblob[(bv.byteOffset or 0):(bv.byteOffset or 0) + bv.byteLength]
    while len(blob) % 4: blob.append(0)
    off = len(blob); blob += data
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(data)))
    n = Accessor(bufferView=len(g.bufferViews) - 1, byteOffset=a.byteOffset, componentType=a.componentType, count=a.count, type=a.type, min=a.min, max=a.max)
    g.accessors.append(n); return len(g.accessors) - 1
for an in [x for x in f.animations if not x.name.startswith("---")]:
    cache = {}
    def c(i):
        if i not in cache: cache[i] = copy(i)
        return cache[i]
    sam = [AnimationSampler(input=c(s.input), output=c(s.output), interpolation=s.interpolation) for s in an.samplers]
    ch = [AnimationChannel(sampler=x.sampler, target=AnimationChannelTarget(node=x.target.node, path=x.target.path)) for x in an.channels]
    g.animations.append(Animation(name=an.name, samplers=sam, channels=ch))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('merged', OUT, [a.name for a in g.animations])
