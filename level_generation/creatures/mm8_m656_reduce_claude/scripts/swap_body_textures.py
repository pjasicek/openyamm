"""Put a recomposed Mercenary body texture set into an exported GLB without touching geometry, skins or clips.
The runtime atlases (tools/merge_head_material.py) hold the 1024-pixel body maps on the left, a 32-pixel gutter
(16 columns repeating the body's last column, 16 the head's first) and the head maps on the right. The body half and
its gutter columns are replaced; the head half is kept. The normal map's green channel is inverted, as
tools/prepare_actor_glb.py did for the installed body half (verified: the installed half equals
../mm8_m656_claude/textures/body_* with only G inverted). The variant ramps come from the same composition, since
compose_mercenary.py measures them over the body and head together.
With --head the head half (its maps from the same folder) and its gutter columns are replaced as well.
Usage: swap_body_textures.py in.glb <textures dir> out.glb [--head]"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from merge_head_material import read_glb, write_glb, add_image, compact

src, tex, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); HEAD = '--head' in sys.argv[4:]
doc, binary = read_glb(src)
SLOTS = {('pbrMetallicRoughness', 'baseColorTexture'): 'body_basecolor', ('pbrMetallicRoughness', 'metallicRoughnessTexture'): 'body_orm',
         ('normalTexture',): 'body_normal', ('extras', 'openyamm_region_mask'): 'body_region_mask'}
ramps = json.loads((tex / 'mercenary_ramps.json').read_text())['materials'][0]['ramps']
def get(m, path):
    for k in path:
        m = m[k]
    return m
replaced = {}
for path, name in SLOTS.items():
    texture = get(doc['materials'][0], path)['index']
    image = doc['images'][doc['textures'][texture]['source']]
    view = doc['bufferViews'][image['bufferView']]
    atlas = Image.open(io.BytesIO(bytes(binary[view.get('byteOffset', 0):][:view['byteLength']])))
    body = Image.open(tex / f'{name}.png').convert(atlas.mode)
    assert body.size == (1024, 1024) and atlas.size == (2080, 1024), (body.size, atlas.size)
    if name == 'body_normal':
        a = np.asarray(body).copy(); a[..., 1] = 255 - a[..., 1]; body = Image.fromarray(a, body.mode)
    atlas = atlas.copy(); atlas.paste(body, (0, 0)); atlas.paste(body.crop((1023, 0, 1024, 1024)).resize((16, 1024)), (1024, 0))
    if HEAD:
        head = Image.open(tex / f"{name.replace('body_', 'head_')}.png").convert(atlas.mode)
        assert head.size == (1024, 1024), head.size
        if name == 'body_normal':
            a = np.asarray(head).copy(); a[..., 1] = 255 - a[..., 1]; head = Image.fromarray(a, head.mode)
        atlas.paste(head, (1056, 0)); atlas.paste(head.crop((0, 0, 1, 1024)).resize((16, 1024)), (1040, 0))
    replaced[texture] = add_image(doc, binary, atlas, image.get('name', name), doc['textures'][texture].get('sampler'))
for material in doc['materials']:
    for path in SLOTS:
        slot = get(material, path); slot['index'] = replaced[slot['index']]
    material['extras']['openyamm_region_ramps'] = ramps['mercenary_' + material['name'][-1].lower()]
write_glb(dst, *compact(doc, binary))
print('SWAP', dst, {k: v for k, v in replaced.items()}, 'images', len(doc['images']))
