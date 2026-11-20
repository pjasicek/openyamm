"""Derive a model's dark state from its baked export: the same GLB with the glowing texels of its base colour map
(bright, saturated, in a hue band) dimmed, for a decoration that swaps to an unlit model (the Scour's collar node).

    python3 -I scripts/derive_dark_variant.py <export.glb> <out.glb> [hue_low hue_high]

Hues are degrees (default 290-20, through 0: the collar node's violet-red lenses). Every image the base colour
textures use is changed; the mesh, UVs and the other maps are copied unchanged."""
import io
import json
import struct
import sys

import numpy as np
from PIL import Image


def read_glb(path):
    data = open(path, 'rb').read()
    magic, version, _ = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF' and version == 2, path
    offset, chunks = 12, {}
    while offset < len(data):
        length, kind = struct.unpack_from('<I4s', data, offset)
        chunks[kind] = data[offset + 8:offset + 8 + length]
        offset += 8 + length
    return json.loads(chunks[b'JSON']), chunks[b'BIN\x00']


def write_glb(path, gltf, binary):
    text = json.dumps(gltf, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    binary += b'\x00' * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<4sII', b'glTF', 2, total))
        handle.write(struct.pack('<I4s', len(text), b'JSON') + text)
        handle.write(struct.pack('<I4s', len(binary), b'BIN\x00') + binary)


def dim(png, hue_low, hue_high):
    image = Image.open(io.BytesIO(png)).convert('RGBA')
    rgba = np.asarray(image).astype(np.float32) / 255.0
    hsv = np.asarray(image.convert('RGB').convert('HSV')).astype(np.float32) / 255.0
    hue = hsv[..., 0] * 360.0
    in_band = (hue >= hue_low) | (hue <= hue_high) if hue_low > hue_high else (hue >= hue_low) & (hue <= hue_high)
    glow = in_band & (hsv[..., 1] > 0.45) & (hsv[..., 2] > 0.45)
    # A soft edge: how far past the thresholds a texel is, so the lens rims fade instead of stepping.
    strength = np.clip((hsv[..., 2] - 0.45) / 0.25, 0, 1) * np.clip((hsv[..., 1] - 0.45) / 0.2, 0, 1) * glow
    dark = rgba[..., :3] * np.array([0.22, 0.16, 0.24])          # dull violet-black glass
    rgba[..., :3] = rgba[..., :3] * (1 - strength[..., None]) + dark * strength[..., None]
    out = io.BytesIO()
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA').save(out, 'PNG', optimize=True)
    return out.getvalue(), int(glow.sum())


def main():
    source, target = sys.argv[1], sys.argv[2]
    hue_low, hue_high = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (290.0, 20.0)
    gltf, binary = read_glb(source)
    images = {gltf['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
              for m in gltf['materials'] if 'baseColorTexture' in m.get('pbrMetallicRoughness', {})}
    replaced = {}
    for index in images:
        view = gltf['bufferViews'][gltf['images'][index]['bufferView']]
        start = view.get('byteOffset', 0)
        replaced[gltf['images'][index]['bufferView']], count = dim(binary[start:start + view['byteLength']],
                                                                   hue_low, hue_high)
        gltf['images'][index]['mimeType'] = 'image/png'
        print(f'image {index}: {count} glowing texels dimmed')
    # Rebuild the binary chunk view by view, in order, each 4-byte aligned.
    out = b''
    for number, view in enumerate(gltf['bufferViews']):
        start = view.get('byteOffset', 0)
        payload = replaced.get(number, binary[start:start + view['byteLength']])
        out += b'\x00' * (-len(out) % 4)
        view['byteOffset'] = len(out)
        view['byteLength'] = len(payload)
        out += payload
    gltf['buffers'][0]['byteLength'] = len(out)
    write_glb(target, gltf, out)
    print(target)


main()
