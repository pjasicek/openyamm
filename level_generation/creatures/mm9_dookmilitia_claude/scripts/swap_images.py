"""Replace embedded images of a GLB by name from PNG files (preview, run 2): swap_images.py <in> <out> name=png ..."""
import sys
from pygltflib import GLTF2, BufferView
src, dst, *pairs = sys.argv[1:]
g = GLTF2().load(src); blob = bytearray(g.binary_blob())
for pr in pairs:
    name, png = pr.split('=')
    im = next(i for i in g.images if i.name == name)
    while len(blob) % 4: blob.append(0)
    d = open(png, 'rb').read(); o = len(blob); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d))); im.bufferView = len(g.bufferViews) - 1
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst); print('SWAPPED', len(pairs))
