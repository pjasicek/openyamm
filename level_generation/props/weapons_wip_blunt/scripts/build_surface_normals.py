"""Author shallow material heights and convert their slopes to glTF +Y tangent normals.

Heights describe material microstructure, independently of the painted albedo's lighting.
Append the atlas to the sixteen accepted component exports without rewriting their mesh data.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb
from normal_map_convention import measure


def normals(height):
    down, right = np.gradient(height)
    # PNG rows run down; glTF tangent +Y runs toward increasing texture V.
    vectors = np.stack((-right, down, np.ones_like(height)), axis=-1)
    vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
    return np.rint((vectors + 1) * 127.5).astype(np.uint8)


def heights():
    rng = np.random.default_rng(20261018)
    y, x = np.mgrid[:256, :256]
    edge = np.minimum.reduce([x, y, 255 - x, 255 - y])
    fade = np.clip((edge - 8) / 8, 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    atlas = np.zeros((1024, 1024))
    for cell in range(16):
        noise = rng.normal(size=(256, 256))
        fine = gaussian_filter(noise, .8)
        fine /= fine.std()
        broad = gaussian_filter(noise, 4)
        broad /= broad.std()
        if cell in (0, 8, 10, 15):  # Small forging depressions; oxidized steel is rougher.
            h = (.24 if cell == 0 else .13) * broad + .045 * fine
        elif cell in (1, 9, 12, 14):  # Fine tool marks; do not invent relief over painted ornaments.
            h = .04 * broad + .025 * fine
        elif cell in (2, 7, 11):
            phase = x + 1.5 * np.sin(y / 37) + .8 * broad
            grain = np.sin(phase * 1.3) + .45 * np.sin(phase * 2.9)
            h = (.21 if cell == 11 else .10 if cell == 2 else .055) * grain + .025 * fine
        elif cell in (3, 4):  # Leather pebble/wrinkle detail; existing diamonds remain in the colour map.
            h = .14 * gaussian_filter(fine, 1) + .09 * broad
        elif cell == 5:
            h = -.10 * np.maximum(fine - .7, 0) + .025 * broad
        elif cell == 13:
            h = .075 * (np.cos(x * 1.1) + np.cos(y * 1.1)) + .015 * fine
        else:  # Smooth enamel.
            h = .018 * broad + .008 * fine
        atlas[cell // 4 * 256:(cell // 4 + 1) * 256,
              cell % 4 * 256:(cell % 4 + 1) * 256] = h * fade
    return atlas


def main():
    y, x = np.mgrid[:16, :16]
    assert normals(x * .1)[8, 8, 0] < 128
    assert normals(-y * .1)[8, 8, 1] < 128
    assert tuple(normals(x * 0)[8, 8]) == (128, 128, 255)
    height = heights()
    assert np.abs(height).max() < 2
    rgb = normals(height)
    decoded = rgb / 127.5 - 1
    assert np.abs(np.linalg.norm(decoded, axis=-1) - 1).max() < .007
    correlation = measure(rgb)
    assert correlation > .7, correlation
    for cell in range(16):
        tile = rgb[cell // 4 * 256:(cell // 4 + 1) * 256,
                   cell % 4 * 256:(cell % 4 + 1) * 256]
        assert np.array_equal(tile[:7], np.broadcast_to([128, 128, 255], tile[:7].shape))
        assert np.std(tile[16:-16, 16:-16, :2]) > .5, cell
    Image.fromarray(np.rint((height + 2) / 4 * 65535).astype(np.uint16)).save(P / 'textures/material_height.png')
    normal_path = P / 'textures/material_normal.png'
    Image.fromarray(rgb).save(normal_path)
    png = normal_path.read_bytes()
    baseline = json.loads((P / 'review/normal_pass/before_hashes.json').read_text())
    assert len(baseline) == 16
    receipts = {}
    for icon, hashes in baseline.items():
        old = P / 'review/normal_pass/before' / f'{icon}_export.glb'
        assert hashlib.sha256(old.read_bytes()).hexdigest() == hashes['export']
        doc, binary = read_glb(old)
        material = doc['materials'][0]
        assert 'normalTexture' not in material
        old_views = list(doc['bufferViews'])
        padding = b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary) + len(padding), 'byteLength': len(png)})
        doc['images'].append({'name': 'material_normal', 'mimeType': 'image/png', 'bufferView': len(old_views)})
        sampler = doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler')
        texture = {'source': len(doc['images']) - 1}
        if sampler is not None:
            texture['sampler'] = sampler
        doc['textures'].append(texture)
        material['normalTexture'] = {'index': len(doc['textures']) - 1, 'scale': 1}
        export = P / 'work/blender' / f'{icon}_export.glb'
        write_glb(export, doc, binary + padding + png)
        new_doc, new_binary = read_glb(export)
        assert new_binary[:len(binary)] == binary
        assert new_doc['bufferViews'][:-1] == old_views
        assert read_glb(old)[0]['meshes'] == new_doc['meshes']
        receipts[icon] = {'sha256': hashlib.sha256(export.read_bytes()).hexdigest(),
                          'geometry_uv_albedo_mr_byte_identical': True}
    report = {'icons': receipts, 'map': 'textures/material_normal.png', 'height': 'textures/material_height.png',
              'height_encoding': '16-bit unsigned; decode /65535*4-2, height measured in texel units',
              'normal_convention': 'glTF/OpenGL +Y', 'mixed_derivative_correlation': correlation,
              'normal_sha256': hashlib.sha256(png).hexdigest(), 'strength': 1,
              'maximum_tangent_xy_length': float(np.linalg.norm(decoded[..., :2], axis=-1).max())}
    (P / 'review/normal_pass/generation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: 16 maps attached; mesh/UV/base/MR unchanged; +Y correlation {correlation:.3f}')


if __name__ == '__main__':
    main()
