#!/usr/bin/env python3
"""MM7 torches with coloured flames: torch07 (red), torch05 (purple) and torch06 (green) are the native torch01 sprite
with another flame colour (the bracket pixels match within a few levels), so their models are the MM6 torch01 models
(mm6_deco_torch01, _free) with the flame flipbook image swapped for the shared coloured flame of the same layout
(../../shared_flames/). Everything else, geometry included, stays byte for byte. Writes work/mm7_deco_torch01_<colour>
[_free].glb; install each with tools/install_model.py <glb> --engine.
Usage: make_torch_variants.py"""
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCES = REPO / 'assets_source/engine/models'
FLAMES = HERE.parents[1] / 'shared_flames'
COLOURS = ('red', 'purple', 'green')
FLAME_IMAGE = 'flame02_basecolor'


def read_glb(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + length])
    offset = 20 + length
    size = struct.unpack_from('<I', data, offset)[0]
    return document, data[offset + 8:offset + 8 + size]


def write_glb(path, document, binary):
    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    binary += b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    path.write_bytes(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(text), 0x4E4F534A) + text
                     + struct.pack('<II', len(binary), 0x004E4942) + binary)


def with_flame(document, binary, flame_bytes, colour):
    """A copy of the model whose flame image is flame_bytes; the binary chunk is rebuilt view by view."""
    document = json.loads(json.dumps(document))
    image = next(image for image in document['images'] if image.get('name') == FLAME_IMAGE)
    image['name'] = f'flame02_{colour}_basecolor'
    replaced = image['bufferView']
    out = bytearray()
    for index, view in enumerate(document['bufferViews']):
        start = view.get('byteOffset', 0)
        chunk = flame_bytes if index == replaced else binary[start:start + view['byteLength']]
        out += b'\0' * (-len(out) % 4)
        view['byteOffset'] = len(out)
        view['byteLength'] = len(chunk)
        out += chunk
    document['buffers'][0]['byteLength'] = len(out) + (-len(out) % 4)
    return document, bytes(out)


def main():
    (HERE / 'work').mkdir(exist_ok=True)
    for variant in ('', '_free'):
        document, binary = read_glb(SOURCES / f'mm6_deco_torch01{variant}.glb')
        for colour in COLOURS:
            flame = (FLAMES / f'flame02_{colour}_basecolor.png').read_bytes()
            out = HERE / 'work' / f'mm7_deco_torch01_{colour}{variant}.glb'
            write_glb(out, *with_flame(document, binary, flame, colour))
            print(out.relative_to(REPO), out.stat().st_size)


if __name__ == '__main__':
    main()
