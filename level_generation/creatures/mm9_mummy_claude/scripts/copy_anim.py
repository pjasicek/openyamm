#!/usr/bin/env python3
"""Copy animations from one GLB to another with the same node order. Args: <anim source> <target> <out>"""
import sys
from pygltflib import GLTF2, BufferView, Accessor
A, B, O = sys.argv[1:4]
a = GLTF2().load(A); b = GLTF2().load(B)
assert [n.name for n in a.nodes][:-1] == [n.name for n in b.nodes][:-1]
ab = a.binary_blob(); bb = bytearray(b.binary_blob()); amap = {}
def acc(i):
    if i in amap: return amap[i]
    x = a.accessors[i]; v = a.bufferViews[x.bufferView]
    data = ab[v.byteOffset or 0:(v.byteOffset or 0) + v.byteLength]
    while len(bb) % 4: bb.append(0)
    o = len(bb); bb.extend(data)
    b.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(data)))
    y = Accessor(bufferView=len(b.bufferViews) - 1, byteOffset=x.byteOffset, componentType=x.componentType, count=x.count, type=x.type, min=x.min, max=x.max)
    b.accessors.append(y); amap[i] = len(b.accessors) - 1; return amap[i]
b.animations = a.animations
for an in b.animations:
    for s in an.samplers:
        s.input = acc(s.input); s.output = acc(s.output)
b.buffers[0].byteLength = len(bb); b.set_binary_blob(bytes(bb)); b.save(O)
