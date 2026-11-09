#!/usr/bin/env python3
"""Merge a creature's head material into its body material: one draw per creature instead of two.

Runtime post-process for skinned actor GLBs built with a separate head texture set (CLAUDE_CREATURE_TEXTURES.md,
"Head detail"). In every mesh with exactly one body and one head primitive (the head material's name contains
"Head"), the two primitives become one, using one atlas per map: the body images on the left, a 32-pixel gutter
(edge texels repeated, so mips do not blend the halves) and the head images on the right, each at its original
resolution, so texel density and pixels are unchanged. Texture coordinates are remapped into the halves; region
masks are merged the same way (the head half is empty where the head has no mask). Each colour variant gets one
merged material, copied from the body's variant material; the head's ramps must equal the body's when it has its own
mask. Metallic, roughness and specular factors that differ between body and head are baked into the halves of the
metallic-roughness atlas (blue, green, and red with "openyamm_specular_mask"), so a matte head and glossy armour keep
their look; any other material property that differs is refused rather than dropped.
Meshes without a head primitive are left alone, so the tool is a no-op for creatures without a head set.
Usage: merge_head_material.py in.glb out.glb"""
import copy
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
TYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
GUTTER = 32
# Scalars that may differ between body and head: material path, glTF default, metallic-roughness channel.
SCALARS = ((('pbrMetallicRoughness', 'metallicFactor'), 1.0, 2), (('pbrMetallicRoughness', 'roughnessFactor'), 1.0, 1),
           (('extras', 'openyamm_specular'), 1.0, 0))
METALLIC_ROUGHNESS = ('pbrMetallicRoughness', 'metallicRoughnessTexture')
# Material keys that are allowed to differ between body and head (they are re-pointed to the atlas).
TEXTURE_SLOTS = (('pbrMetallicRoughness', 'baseColorTexture'), ('pbrMetallicRoughness', 'metallicRoughnessTexture'),
                 ('normalTexture',), ('extras', 'openyamm_region_mask'))


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + size]), bytearray(raw[28 + size:])


def write_glb(path, document, binary):
    binary += b'\0' * (-len(binary) % 4)
    document['buffers'][0]['byteLength'] = len(binary)
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(binary))
                     + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                     + struct.pack('<II', len(binary), 0x004e4942) + binary)


def accessor_array(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype(TYPES[accessor['componentType']])
    components = COMPONENTS[accessor['type']]
    stride = view.get('byteStride', dtype.itemsize * components)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    rows = np.frombuffer(bytes(binary[offset:offset + stride * (accessor['count'] - 1) + dtype.itemsize * components]),
                         np.uint8) if accessor['count'] else np.zeros(0, np.uint8)
    if stride == dtype.itemsize * components:
        return rows.view(dtype).reshape(accessor['count'], components).copy()
    out = np.empty((accessor['count'], components), dtype)
    for row in range(accessor['count']):
        out[row] = np.frombuffer(bytes(rows[row * stride:row * stride + dtype.itemsize * components]), dtype)
    return out


def append_accessor(document, binary, values, template, target):
    binary.extend(b'\0' * (-len(binary) % 4))
    packed = np.ascontiguousarray(values).tobytes()
    document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(packed),
                                    'target': target})
    binary.extend(packed)
    accessor = {key: value for key, value in template.items() if key in ('componentType', 'type', 'normalized')}
    accessor.update({'bufferView': len(document['bufferViews']) - 1, 'count': int(len(values))})
    if template.get('type') == 'VEC3' and template.get('componentType') == 5126:
        accessor['min'] = np.asarray(values).min(axis=0).tolist()
        accessor['max'] = np.asarray(values).max(axis=0).tolist()
    document['accessors'].append(accessor)
    return len(document['accessors']) - 1


def image_of(document, binary, texture_index):
    image = document['images'][document['textures'][texture_index]['source']]
    view = document['bufferViews'][image['bufferView']]
    data = bytes(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])
    return Image.open(io.BytesIO(data)), image.get('name', 'image')


def add_image(document, binary, image, name, sampler):
    buffer = io.BytesIO()
    image.save(buffer, 'PNG', optimize=True)
    data = buffer.getvalue()
    binary.extend(b'\0' * (-len(binary) % 4))
    document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    document['images'].append({'bufferView': len(document['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    texture = {'source': len(document['images']) - 1}
    if sampler is not None:
        texture['sampler'] = sampler
    document['textures'].append(texture)
    return len(document['textures']) - 1


def slot(material, path):
    value = material
    for key in path:
        value = value.get(key) if isinstance(value, dict) else None
        if value is None:
            return None
    return value


def strip_textures(material):
    stripped = copy.deepcopy(material)
    for path in TEXTURE_SLOTS:
        parent = stripped
        for key in path[:-1]:
            parent = parent.get(key, {})
        parent.pop(path[-1], None)
    stripped.get('extras', {}).pop('openyamm_region_ramps', None)
    for path, _, _ in SCALARS:
        stripped.get(path[0], {}).pop(path[1], None)
    stripped.pop('name', None)
    return stripped


def adjust(image, changes):
    if image is None or not changes:
        return image
    pixels = np.asarray(image).astype(np.float32)
    for channel, operation, value in changes:
        pixels[..., channel] = pixels[..., channel] * value if operation == 'scale' else value * 255.0
    return Image.fromarray(np.clip(np.rint(pixels), 0, 255).astype(np.uint8), image.mode)


def set_slot(material, path, value):
    for key in path[:-1]:
        material = material.setdefault(key, {})
    material[path[-1]] = value


class Atlas:
    """Body | gutter | head, at the body height; the head image keeps its own size."""

    def __init__(self, body_size, head_size):
        self.body_width, self.height = body_size
        self.head_width, self.head_height = head_size
        if self.head_height > self.height:
            raise ValueError('head images taller than the body images are not supported')
        self.width = self.body_width + GUTTER + self.head_width

    def compose(self, body, head, adjustments=((), ())):
        """adjustments: per half, (channel, 'scale' | 'set', value) applied before packing."""
        body, head = (adjust(image, changes) for image, changes in zip((body, head), adjustments))
        mode = body.mode if body is not None else head.mode
        atlas = Image.new(mode, (self.width, self.height))
        if body is not None:
            atlas.paste(body, (0, 0))
            atlas.paste(body.crop((self.body_width - 1, 0, self.body_width, self.height))
                        .resize((GUTTER // 2, self.height)), (self.body_width, 0))
        if head is not None:
            head_x = self.body_width + GUTTER
            atlas.paste(head, (head_x, 0))
            atlas.paste(head.crop((0, 0, 1, self.head_height)).resize((GUTTER // 2, self.head_height)),
                        (head_x - GUTTER // 2, 0))
        return atlas

    def remap(self, uv, head):
        uv = uv.astype(np.float64).copy()
        if uv.size and ((uv < -1e-4).any() or (uv > 1 + 1e-4).any()):
            raise ValueError('texture coordinates outside [0, 1] cannot be packed into an atlas')
        if head:
            uv[:, 0] = (self.body_width + GUTTER + uv[:, 0] * self.head_width) / self.width
            uv[:, 1] = uv[:, 1] * self.head_height / self.height
        else:
            uv[:, 0] = uv[:, 0] * self.body_width / self.width
        return uv.astype(np.float32)


def main():
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    document, binary = read_glb(source)
    materials = document['materials']
    variants = document.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])

    def variant_materials(primitive):
        mappings = primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
        chosen = [primitive.get('material')] * max(len(variants), 1)
        for mapping in mappings:
            for variant in mapping['variants']:
                chosen[variant] = mapping['material']
        return chosen

    merged_materials = {}      # (body material, head material) -> merged material index
    atlas_textures = {}        # (body texture, head texture or None) -> atlas texture index
    merged_meshes = 0
    for mesh in document['meshes']:
        # Shared maps retain one atlas layout and cached materials across distance LODs.
        primitives = mesh['primitives']
        heads = [p for p in primitives if 'Head' in materials[p.get('material', 0)].get('name', '')]
        if len(primitives) != 2 or len(heads) != 1:
            continue
        head = heads[0]
        body = primitives[0] if primitives[1] is head else primitives[1]
        if body.get('mode', 4) != head.get('mode', 4) or body.get('targets') or head.get('targets'):
            raise ValueError(f"{mesh.get('name')}: body and head primitives differ in mode or have morph targets")
        for name in set(body['attributes']) ^ set(head['attributes']):
            # A second set of joint influences on one side only: the other side gets zero weights.
            if not name.startswith(('JOINTS_', 'WEIGHTS_')):
                raise ValueError(f"{mesh.get('name')}: only one of body and head has {name}")
        body_variants, head_variants = variant_materials(body), variant_materials(head)
        merged_variant_materials = []
        for body_index, head_index in zip(body_variants, head_variants):
            key = (body_index, head_index)
            if key not in merged_materials:
                body_material, head_material = materials[body_index], materials[head_index]
                if strip_textures(body_material) != strip_textures(head_material):
                    raise ValueError(f"{body_material['name']} and {head_material['name']} differ beyond textures")
                head_ramps = slot(head_material, ('extras', 'openyamm_region_ramps'))
                if head_ramps is not None and head_ramps != slot(body_material, ('extras', 'openyamm_region_ramps')):
                    raise ValueError(f"{head_material['name']}: head ramps differ from the body's")
                merged = copy.deepcopy(body_material)
                adjustments = ([], [])
                for path, default, channel in SCALARS:
                    values = [material_slot if material_slot is not None else default
                              for material_slot in (slot(body_material, path), slot(head_material, path))]
                    if values[0] == values[1]:
                        continue
                    if slot(body_material, METALLIC_ROUGHNESS) is None or slot(head_material, METALLIC_ROUGHNESS) is None:
                        raise ValueError(f"{head_material['name']}: {path[-1]} differs without a metallic-roughness map")
                    if slot(body_material, ('extras', 'openyamm_specular_mask')):
                        raise ValueError(f"{body_material['name']} already has a specular mask")
                    top = max(values)
                    set_slot(merged, path, top)
                    for half, value in zip(adjustments, values):
                        # The red channel is unused by glTF; as a specular mask it is written, not scaled.
                        half.append((channel, 'set' if channel == 0 else 'scale', value / top))
                    if channel == 0:
                        set_slot(merged, ('extras', 'openyamm_specular_mask'), True)
                for path in TEXTURE_SLOTS:
                    body_slot, head_slot = slot(body_material, path), slot(head_material, path)
                    if body_slot is None and head_slot is None:
                        continue
                    if body_slot is None:
                        raise ValueError(f"{body_material['name']} lacks {'.'.join(path)} that the head has")
                    changes = tuple(map(tuple, adjustments)) if path == METALLIC_ROUGHNESS else ((), ())
                    texture_key = (body_slot['index'], head_slot['index'] if head_slot else None, changes)
                    if texture_key not in atlas_textures:
                        body_image, name = image_of(document, binary, body_slot['index'])
                        head_image = image_of(document, binary, head_slot['index'])[0] if head_slot else None
                        atlas = Atlas(body_image.size, head_image.size if head_image else body_image.size)
                        if head_image is not None and head_image.mode != body_image.mode:
                            head_image = head_image.convert(body_image.mode)
                        sampler = document['textures'][body_slot['index']].get('sampler')
                        atlas_textures[texture_key] = (add_image(document, binary, atlas.compose(body_image, head_image, changes),
                                                                 name + '_head_atlas', sampler), atlas)
                    set_slot(merged, path, dict(body_slot, index=atlas_textures[texture_key][0]))
                materials.append(merged)
                merged_materials[key] = len(materials) - 1
            merged_variant_materials.append(merged_materials[key])
        # One atlas layout per creature: every map pairs a body image with a head image of the same sizes.
        atlases = {(a.body_width, a.height, a.head_width, a.head_height) for _, a in atlas_textures.values()}
        if len(atlases) != 1:
            raise ValueError('body and head maps of different sizes would need different texture coordinate layouts')
        atlas = next(iter(atlas_textures.values()))[1]
        attributes = {}
        count_body = document['accessors'][body['attributes']['POSITION']]['count']
        for name in sorted(set(body['attributes']) | set(head['attributes'])):
            template = document['accessors'][(body['attributes'].get(name) or head['attributes'][name])]
            values = []
            for primitive in (body, head):
                if name in primitive['attributes']:
                    values.append(accessor_array(document, binary, primitive['attributes'][name]))
                else:
                    count = document['accessors'][primitive['attributes']['POSITION']]['count']
                    values.append(np.zeros((count, COMPONENTS[template['type']]), TYPES[template['componentType']]))
            body_values, head_values = values
            if body_values.dtype != head_values.dtype:
                if not name.startswith('JOINTS_'):
                    raise ValueError(f"{mesh.get('name')}: body and head store {name} differently")
                wider = np.promote_types(body_values.dtype, head_values.dtype)
                body_values, head_values = body_values.astype(wider), head_values.astype(wider)
                template = dict(template, componentType=next(k for k, v in TYPES.items() if np.dtype(v) == wider))
            if name.startswith('TEXCOORD'):
                body_values, head_values = atlas.remap(body_values, False), atlas.remap(head_values, True)
            attributes[name] = append_accessor(document, binary, np.concatenate([body_values, head_values]),
                                               template, 34962)
        indices = np.concatenate([accessor_array(document, binary, body['indices']).ravel(),
                                  accessor_array(document, binary, head['indices']).ravel() + count_body])
        index_type = 5123 if indices.max() < 65536 else 5125
        index_accessor = append_accessor(document, binary, indices.astype(TYPES[index_type]),
                                         {'componentType': index_type, 'type': 'SCALAR'}, 34963)
        merged_primitive = {'attributes': attributes, 'indices': index_accessor, 'material': merged_variant_materials[0]}
        if 'mode' in body:
            merged_primitive['mode'] = body['mode']
        if variants:
            merged_primitive['extensions'] = {'KHR_materials_variants': {'mappings': [
                {'material': material, 'variants': [variant]}
                for variant, material in enumerate(merged_variant_materials)]}}
        mesh['primitives'] = [merged_primitive]
        merged_meshes += 1
    # Body-only primitives (the shadow meshes) move to the merged materials too, with their coordinates in the body
    # half, so the separate body textures can be dropped.
    by_body = {}
    for (body_index, _), merged_index in merged_materials.items():
        if by_body.setdefault(body_index, merged_index) != merged_index:
            raise ValueError(f"{materials[body_index]['name']} pairs with more than one head material")
    remapped_accessors = {}
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            mappings = primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
            used = [primitive.get('material')] + [mapping['material'] for mapping in mappings]
            if not any(index in by_body for index in used):
                continue
            if not all(index in by_body or index in by_body.values() for index in used):
                raise ValueError(f"{mesh.get('name')}: mixes merged and unmerged materials")
            if primitive.get('material') in by_body.values():
                continue
            primitive['material'] = by_body[primitive['material']]
            for mapping in mappings:
                mapping['material'] = by_body[mapping['material']]
            for name, index in primitive['attributes'].items():
                if name.startswith('TEXCOORD'):
                    if index not in remapped_accessors:
                        remapped_accessors[index] = append_accessor(
                            document, binary, atlas.remap(accessor_array(document, binary, index), False),
                            document['accessors'][index], 34962)
                    primitive['attributes'][name] = remapped_accessors[index]
    if merged_meshes == 0:
        write_glb(destination, document, binary)
        print('MERGE no head primitives; unchanged')
        return
    write_glb(destination, *compact(document, binary))
    print(f'MERGE {merged_meshes} meshes, {len(merged_materials)} merged materials, {len(atlas_textures)} atlases '
          f'({atlas.width}x{atlas.height})')


def compact(document, binary):
    """Drop materials, textures, images and buffer views nothing references any more."""
    used_materials = set()
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            used_materials.add(primitive.get('material'))
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                used_materials.add(mapping['material'])
    material_map, materials = {}, []
    for index, material in enumerate(document['materials']):
        if index in used_materials:
            material_map[index] = len(materials)
            materials.append(material)
    document['materials'] = materials
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            if 'material' in primitive:
                primitive['material'] = material_map[primitive['material']]
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                mapping['material'] = material_map[mapping['material']]
    used_textures = set()
    for material in materials:
        for path in TEXTURE_SLOTS:
            value = slot(material, path)
            if value is not None:
                used_textures.add(value['index'])
    texture_map, textures = {}, []
    for index, texture in enumerate(document['textures']):
        if index in used_textures:
            texture_map[index] = len(textures)
            textures.append(texture)
    document['textures'] = textures
    for material in materials:
        for path in TEXTURE_SLOTS:
            value = slot(material, path)
            if value is not None:
                value['index'] = texture_map[value['index']]
    image_map, images = {}, []
    for texture in textures:
        if texture['source'] not in image_map:
            image_map[texture['source']] = len(images)
            images.append(document['images'][texture['source']])
        texture['source'] = image_map[texture['source']]
    document['images'] = images
    used_views = {a['bufferView'] for a in document['accessors'] if 'bufferView' in a}
    used_views |= {image['bufferView'] for image in images}
    used_accessors = set()
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            used_accessors |= set(primitive['attributes'].values()) | {primitive['indices']}
            for target in primitive.get('targets', []):
                used_accessors |= set(target.values())
    for skin in document.get('skins', []):
        if 'inverseBindMatrices' in skin:
            used_accessors.add(skin['inverseBindMatrices'])
    for animation in document.get('animations', []):
        for sampler in animation['samplers']:
            used_accessors |= {sampler['input'], sampler['output']}
    accessor_map, accessors = {}, []
    for index, accessor in enumerate(document['accessors']):
        if index in used_accessors:
            accessor_map[index] = len(accessors)
            accessors.append(accessor)
    document['accessors'] = accessors
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {k: accessor_map[v] for k, v in primitive['attributes'].items()}
            primitive['indices'] = accessor_map[primitive['indices']]
            primitive['targets'] = [{k: accessor_map[v] for k, v in t.items()} for t in primitive.get('targets', [])]
            if not primitive['targets']:
                del primitive['targets']
    for skin in document.get('skins', []):
        if 'inverseBindMatrices' in skin:
            skin['inverseBindMatrices'] = accessor_map[skin['inverseBindMatrices']]
    for animation in document.get('animations', []):
        for sampler in animation['samplers']:
            sampler['input'], sampler['output'] = accessor_map[sampler['input']], accessor_map[sampler['output']]
    used_views = {a['bufferView'] for a in accessors if 'bufferView' in a} | {i['bufferView'] for i in images}
    view_map, views, packed = {}, [], bytearray()
    for index, view in enumerate(document['bufferViews']):
        if index not in used_views:
            continue
        packed.extend(b'\0' * (-len(packed) % 4))
        start = view.get('byteOffset', 0)
        data = binary[start:start + view['byteLength']]
        view_map[index] = len(views)
        views.append(dict(view, byteOffset=len(packed)))
        packed.extend(data)
    for accessor in accessors:
        if 'bufferView' in accessor:
            accessor['bufferView'] = view_map[accessor['bufferView']]
    for image in images:
        image['bufferView'] = view_map[image['bufferView']]
    document['bufferViews'] = views
    return document, packed


if __name__ == '__main__':
    main()
