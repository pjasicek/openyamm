"""Appends FIGHTERBASE clips (the LithTech child model of DOOKMILITIA.abc) to a converted body GLB. First 32 nodes must match; from mm9_dookmilitia_claude. Args: <in glb> <fighterbase glb> <out glb>"""
import sys
from pygltflib import GLTF2, Accessor, BufferView, AnimationChannel, AnimationChannelTarget, AnimationSampler, Animation
IN, FB, OUT = sys.argv[1:4]
g = GLTF2().load(IN); f = GLTF2().load(FB)
gn = [n.name for n in g.nodes]; fn = [n.name for n in f.nodes]; assert gn[:32] == fn[:32]
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
import numpy as np
# LithTech applies a child model's rotations to the parent's bones. FIGHTERBASE is about 7 % smaller than this body with narrower clavicles, so every
# translation key takes this body's rest offset; only the Pelvis keeps its motion, scaled by the Spine1 ratio. Same bone frames in both models (0 deg).
ratio = {}
ref = float(np.linalg.norm(g.nodes[gn.index('Bip01 Spine1')].translation) / np.linalg.norm(f.nodes[fn.index('Bip01 Spine1')].translation))
for i in range(32):
    ratio[i] = None if 'Pelvis' not in gn[i] else ref
print('ref', round(ref, 4))
fb = f.binary_blob()
def read(i):
    a = f.accessors[i]; bv = f.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(fb, 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def add(arr, ty):
    global blob
    while len(blob) % 4: blob.append(0)
    off = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=ty, min=[float(x) for x in arr.min(0)], max=[float(x) for x in arr.max(0)]))
    return len(g.accessors) - 1
for an in f.animations:
    cache = {}
    trans = {x.sampler: x.target.node for x in an.channels if x.target.path == 'translation' and x.target.node < 32}
    def fixtrans(a, n):
        if ratio[n] is not None: return a * ratio[n]
        return np.tile(np.array(g.nodes[n].translation or [0, 0, 0], float), (len(a), 1))
    def c(i):
        if i not in cache: cache[i] = copy(i)
        return cache[i]
    sam = [AnimationSampler(input=c(s.input), output=add(fixtrans(read(s.output), trans[j]), 'VEC3') if j in trans else c(s.output), interpolation=s.interpolation) for j, s in enumerate(an.samplers)]
    ch = [AnimationChannel(sampler=x.sampler, target=AnimationChannelTarget(node=x.target.node, path=x.target.path)) for x in an.channels]
    g.animations.append(Animation(name=an.name, samplers=sam, channels=ch))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('merged', OUT, [a.name for a in g.animations])
