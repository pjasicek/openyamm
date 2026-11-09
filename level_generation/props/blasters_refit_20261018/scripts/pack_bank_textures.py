"""Reserve the bottom 128 rows for the shotgun's seven authored emitters; keep one material draw."""
import io
from pathlib import Path
import sys

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb


def main():
    doc, binary = read_glb(P / 'work/meshy/blastsg_raw.glb')
    mat = doc['materials'][0]
    pbr = mat['pbrMetallicRoughness']
    slots = {'base': pbr['baseColorTexture']['index'], 'mr': pbr['metallicRoughnessTexture']['index'],
             'normal': mat['normalTexture']['index']}
    swatches = Image.open(P / 'textures/shotgun_swatches_raw.png').convert('RGB').resize((1024, 128))
    for role, texture in slots.items():
        image = doc['images'][doc['textures'][texture]['source']]
        view = doc['bufferViews'][image['bufferView']]
        offset = view.get('byteOffset', 0)
        body = Image.open(io.BytesIO(binary[offset:offset+view['byteLength']])).convert('RGB')
        atlas = Image.new('RGB', (1024, 1024))
        atlas.paste(body.resize((1024, 896), Image.Resampling.LANCZOS), (0, 0))
        if role == 'base':
            strip = swatches
        elif role == 'normal':
            strip = Image.new('RGB', (1024, 128), (128, 128, 255))
        else:
            strip = Image.fromarray(np.tile(np.array([255, 145, 255], np.uint8), (128, 1024, 1)))
            strip.paste(Image.new('RGB', (342, 128), (255, 95, 0)), (682, 0))
        atlas.paste(strip, (0, 896))
        assert atlas.size == (1024, 1024)
        atlas.save(P / 'textures' / f'shotgun_{role}.png')


if __name__ == '__main__':
    main()
