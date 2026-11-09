"""HIGHWAYMAN.abc holds only 9 of its clips; the rest (walk, run, die1, die2, taunt, wince1...) are in its LithTech child model FIGHTERBASE.abc
(the ChildModels section). Same 32 nodes, same rest pose. Appends FIGHTERBASE's clips to a converted highwayman GLB. Args: <in glb> <fighterbase glb> <out glb>"""
import sys
from pygltflib import GLTF2, Accessor, BufferView, AnimationChannel, AnimationChannelTarget, AnimationSampler, Animation
IN, FB, OUT = sys.argv[1:4]
g = GLTF2().load(IN); f = GLTF2().load(FB)
assert [n.name for n in g.nodes] == [n.name for n in f.nodes]
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
for an in f.animations:
    cache = {}
    def c(i):
        if i not in cache: cache[i] = copy(i)
        return cache[i]
    sam = [AnimationSampler(input=c(s.input), output=c(s.output), interpolation=s.interpolation) for s in an.samplers]
    ch = [AnimationChannel(sampler=x.sampler, target=AnimationChannelTarget(node=x.target.node, path=x.target.path)) for x in an.channels]
    g.animations.append(Animation(name=an.name, samplers=sam, channels=ch))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('merged', OUT, [a.name for a in g.animations])
