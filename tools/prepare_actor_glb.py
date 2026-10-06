#!/usr/bin/env python3
"""Prepare runtime PNG maps, optionally omitting mesh effects implemented by the particle system."""
import argparse
import io
import json
import struct
from pathlib import Path

from PIL import Image


def omit_mesh_nodes(document, original, names):
    for name in names:
        matches = [node for node in document['nodes'] if node.get('name') == name]
        if len(matches) != 1 or 'mesh' not in matches[0]:
            raise ValueError(f'Expected one mesh node to omit: {name}')
        node = matches[0]
        index = document['nodes'].index(node)
        del node['mesh']
        node.pop('weights', None)
        for animation in document.get('animations', []):
            animation['channels'] = [channel for channel in animation['channels']
                                     if not (channel['target']['node'] == index
                                             and channel['target']['path'] == 'weights')]

    used_meshes = sorted({node['mesh'] for node in document['nodes'] if 'mesh' in node})
    mesh_indices = {old: new for new, old in enumerate(used_meshes)}
    document['meshes'] = [document['meshes'][index] for index in used_meshes]
    for node in document['nodes']:
        if 'mesh' in node:
            node['mesh'] = mesh_indices[node['mesh']]

    references = []
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            references.extend((primitive['attributes'], key) for key in primitive['attributes'])
            if 'indices' in primitive:
                references.append((primitive, 'indices'))
            for target in primitive.get('targets', []):
                references.extend((target, key) for key in target)
    for skin in document.get('skins', []):
        if 'inverseBindMatrices' in skin:
            references.append((skin, 'inverseBindMatrices'))
    for animation in document.get('animations', []):
        used = sorted({channel['sampler'] for channel in animation['channels']})
        indices = {old: new for new, old in enumerate(used)}
        animation['samplers'] = [animation['samplers'][index] for index in used]
        for channel in animation['channels']:
            channel['sampler'] = indices[channel['sampler']]
        for sampler in animation['samplers']:
            references.extend([(sampler, 'input'), (sampler, 'output')])
    used_accessors = sorted({obj[key] for obj, key in references})
    indices = {old: new for new, old in enumerate(used_accessors)}
    document['accessors'] = [document['accessors'][index] for index in used_accessors]
    for obj, key in references:
        obj[key] = indices[obj[key]]

    references = [(accessor, 'bufferView') for accessor in document['accessors'] if 'bufferView' in accessor]
    for accessor in document['accessors']:
        for sparse in accessor.get('sparse', {}).values():
            if isinstance(sparse, dict) and 'bufferView' in sparse:
                references.append((sparse, 'bufferView'))
    references.extend((image, 'bufferView') for image in document.get('images', []) if 'bufferView' in image)
    used_views = sorted({obj[key] for obj, key in references})
    indices = {old: new for new, old in enumerate(used_views)}
    views = [document['bufferViews'][index] for index in used_views]
    payload = bytearray()
    for view in views:
        offset = view.get('byteOffset', 0)
        payload.extend(b'\0' * (-len(payload) % 4))
        view['byteOffset'] = len(payload)
        payload.extend(original[offset:offset + view['byteLength']])
    document['bufferViews'] = views
    for obj, key in references:
        obj[key] = indices[obj[key]]
    return bytes(payload)


def prepare(source: Path, destination: Path, omitted_mesh_nodes=()):
    data = source.read_bytes()
    magic, version, length = struct.unpack_from("<III", data)
    if magic != 0x46546C67 or version != 2 or length != len(data):
        raise ValueError("Expected a complete glTF 2 GLB")
    json_length, json_kind = struct.unpack_from("<II", data, 12)
    if json_kind != 0x4E4F534A:
        raise ValueError("Expected a JSON chunk")
    document = json.loads(data[20:20 + json_length])
    bin_length, bin_kind = struct.unpack_from("<II", data, 20 + json_length)
    if bin_kind != 0x004E4942 or 28 + json_length + bin_length != len(data):
        raise ValueError("Expected one embedded BIN chunk")
    original = data[28 + json_length:]
    if omitted_mesh_nodes:
        original = omit_mesh_nodes(document, original, omitted_mesh_nodes)
    payload = bytearray(original)
    for image in document.get("images", []):
        if image.get("mimeType") != "image/jpeg":
            continue
        view = document["bufferViews"][image["bufferView"]]
        offset = view.get("byteOffset", 0)
        with Image.open(io.BytesIO(original[offset:offset + view["byteLength"]])) as pixels:
            encoded = io.BytesIO()
            pixels.save(encoded, format="PNG")
        png = encoded.getvalue()
        payload.extend(b"\0" * (-len(payload) % 4))
        image["bufferView"] = len(document["bufferViews"])
        image["mimeType"] = "image/png"
        document["bufferViews"].append({"buffer": 0, "byteOffset": len(payload), "byteLength": len(png)})
        payload.extend(png)
    document["buffers"][0]["byteLength"] = len(payload)
    payload.extend(b"\0" * (-len(payload) % 4))
    encoded = json.dumps(document, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    result = (struct.pack("<III", magic, version, 28 + len(encoded) + len(payload))
              + struct.pack("<II", len(encoded), json_kind) + encoded
              + struct.pack("<II", len(payload), bin_kind) + payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(result)
    print(f"{destination}: {len(result)} bytes; retained geometry, UVs, skin and animation samples unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--omit-mesh-node", action="append", default=[],
                        help="Replace this authored mesh effect with runtime particles; compact unused data")
    arguments = parser.parse_args()
    prepare(arguments.source, arguments.destination, arguments.omit_mesh_node)
