#!/usr/bin/env python3
"""Put a painted texture set (albedo, normal, metallic-roughness PNGs) on every material of a GLB.

    paint_glb.py <in.glb> <albedo.png> <normal.png> <mr.png> <out.glb>
"""
import sys

import pygltflib


def main():
    src, albedo, normal, mr, out = sys.argv[1:6]
    g = pygltflib.GLTF2().load(src)
    blob = bytearray(g.binary_blob())

    def add(path, name):
        with open(path, 'rb') as stream:
            data = stream.read()
        while len(blob) % 4:
            blob.append(0)
        g.bufferViews.append(pygltflib.BufferView(buffer=0, byteOffset=len(blob), byteLength=len(data)))
        blob.extend(data)
        g.images.append(pygltflib.Image(bufferView=len(g.bufferViews) - 1, mimeType='image/png', name=name))
        g.textures.append(pygltflib.Texture(source=len(g.images) - 1))
        return len(g.textures) - 1

    a, n, m = add(albedo, 'albedo'), add(normal, 'normal'), add(mr, 'mr')
    for material in g.materials:
        pbr = material.pbrMetallicRoughness
        pbr.baseColorTexture = pygltflib.TextureInfo(index=a)
        pbr.baseColorFactor = [1, 1, 1, 1]
        pbr.metallicRoughnessTexture = pygltflib.TextureInfo(index=m)
        pbr.metallicFactor = pbr.roughnessFactor = 1
        material.normalTexture = pygltflib.NormalMaterialTexture(index=n)
    g.buffers[0].byteLength = len(blob)
    g.set_binary_blob(bytes(blob))
    g.save_binary(out)
    print('painted', out)


if __name__ == '__main__':
    main()
