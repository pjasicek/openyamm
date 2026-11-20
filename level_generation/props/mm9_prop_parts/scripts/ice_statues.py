#!/usr/bin/env python3
"""Dark Passageway's ice statues (DarkP_RaisingSwitch.scr, DarkP_BridgeReset.scr, DarkP_CanyonSwitch.scr) drawn by
the installed MM9 creature models, in ice: each statue decoration's `animated` copy
(assets_source/worlds/mm9/models/mm9_deco_<statue>_anim.glb, devdocs/ANIMATED_DECORATIONS.md) becomes its creature's
model (assets_source/worlds/mm9/models/mm9_<creature>.glb) instead of MM9's low-poly mesh (prop_skins.py):

  1. the creature at rest in its `Standing` pose's first frame (MM9's statues stand in `stand`), fitted onto the
     statue decoration (the MM9 mesh posed in `stand`, which stays the binding's model for picking): the same height
     and base, turned about the vertical to the facing whose silhouette matches best;
  2. the fit as a new root node over the creature's own (its skeleton, LODs, clips untouched otherwise);
  3. ice in place of the creature's colour tiers: one material per default material, its colour the creature
     texture's light and shade mapped onto the statue skin's (MM9's spells/icebolt.dtx x4) colours with a little of
     that skin's crystal detail over it, translucent by that skin's alpha (blended, as MM9's statues), glossy, no glow (the region ramps, material variants, specular and pulse
     extras and emissive maps are left out);
  4. clips under the names the map's script plays (MM9's, lower case: fidget1, hattack2, rattack1 ...): each MM9
     clip of the statue's old copy takes the creature clip of its kind with the same length (the creature models
     carry MM9's own animations; AttackMelee and AttackMelee2 swap between models, so the length decides).

Usage: ice_statues.py [statue ...] [--install]   (install: tools/install_model.py --world mm9 over the old copy; the
map's converter reads the clip lengths, so convert Dark Passageway again afterwards)."""
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import prop_parts as pp  # noqa: E402

MODELS = pp.SOURCE
# statue decoration -> creature model
STATUES = {'iceskeleton': 'skeleton', 'icezombie': 'zombie', 'icelich': 'lich', 'icebanshee': 'banshee',
           'iceterror': 'terror', 'iceskeletonwarrior': 'skelwar'}
REST_CLIP = 'Standing'
# MM9 clip (lower case, air variants folded) -> the creature clips of its kind
KINDS = {'stand': ['Standing'], 'walk': ['Walking'], 'fly': ['Walking'], 'run': ['Running'],
         'fidget1': ['Fidget'], 'fidget2': ['Fidget2'], 'fidget3': ['Fidget3'], 'taunt': ['Taunt'],
         'hattack1': ['AttackMelee', 'AttackMelee2'], 'hattack2': ['AttackMelee', 'AttackMelee2'],
         'rattack1': ['AttackRanged', 'AttackRanged2'], 'rattack2': ['AttackRanged', 'AttackRanged2'],
         'wince1': ['Hit', 'Hit2'], 'wince2': ['Hit', 'Hit2'], 'wince3': ['Hit', 'Hit2'],
         'die1': ['Death', 'Death2'], 'die2': ['Death', 'Death2'], 'resurrect': ['Resurrect'],
         'resurrectspell': ['ResurrectSpell'], 'search': ['Search'], 'backpedal': ['Backpedal'],
         'backpedalrun': ['BackpedalRun'], 'transition': ['Transition'], 'wakeup2': ['Wakeup2'],
         'coffin2': ['Coffin2']}
LENGTH_TOLERANCE = 0.04          # seconds: MM9's clip length against the creature clip's
ROUGHNESS = 0.3
DETAIL = 0.3                     # share of the ice skin's own crystal pattern over the mapped colours


def durations(doc, binary):
    return {a['name']: max(float(pp.array(doc, binary, s['input']).max()) for s in a['samplers'])
            for a in doc.get('animations', [])}


def kind(name):
    key = name.lower().replace('air', '')
    return {'stand': 'stand', 'walk': 'walk'}.get(key, key)


def clip_map(old, creature):
    """{MM9 name: creature clip} for every MM9 clip of the old copy that has one of its kind and length."""
    out, taken = {}, set()
    for name, length in sorted(old.items()):
        candidates = [c for c in KINDS.get(kind(name), []) if c in creature]
        best = min(candidates, key=lambda c: (abs(creature[c] - length), c in taken), default=None)
        if best is not None and abs(creature[best] - length) <= LENGTH_TOLERANCE:
            out[name] = best
            taken.add(best)
    return out


def posed_points(raw, doc, binary, clip, time):
    """LOD0 (the first mesh) vertices skinned at the clip's time, in the creature's space."""
    node_index = next(i for i, n in enumerate(doc['nodes']) if n.get('mesh') == 0)
    skin = doc['skins'][doc['nodes'][node_index]['skin']]
    ibm = pp.mat4s(doc, binary, skin['inverseBindMatrices'])
    joints = np.array([raw.world(j, clip, time) @ ibm[k] for k, j in enumerate(skin['joints'])])
    out = []
    for prim in doc['meshes'][0]['primitives']:
        p = pp.array(doc, binary, prim['attributes']['POSITION']).astype(float)
        ph = np.c_[p, np.ones(len(p))]
        posed = np.zeros((len(p), 3))
        for set_index in range(4):
            if f'JOINTS_{set_index}' not in prim['attributes']:
                break
            j = pp.array(doc, binary, prim['attributes'][f'JOINTS_{set_index}']).astype(int)
            w = pp.array(doc, binary, prim['attributes'][f'WEIGHTS_{set_index}']).astype(float)
            if w.max() > 1.0:          # normalized integer weights
                w = w / 255.0 if w.max() <= 255 else w / 65535.0
            posed += np.einsum('nk,nkij,nj->ni', w, joints[j], ph)[:, :3]
        out.append(posed)
    return np.concatenate(out)


def fit(creature, statue):
    """(scale, yaw, translation): statue ~ R_y(yaw) scale creature + translation. Scale from the heights, the base and
    the footprint's centre aligned, the yaw (1 degree steps) whose turned creature lies nearest the statue."""
    scale = np.ptp(statue[:, 1]) / np.ptp(creature[:, 1])
    c = creature * scale
    sample = c[np.random.default_rng(0).choice(len(c), min(len(c), 3000), replace=False)]
    best = None
    for degrees in range(0, 360):
        r = pp.axis_rotation(1, np.radians(degrees))
        turned = sample @ r.T
        t = np.array([(statue[:, 0].min() + statue[:, 0].max()) / 2 - (turned[:, 0].min() + turned[:, 0].max()) / 2,
                      statue[:, 1].min() - turned[:, 1].min(),
                      (statue[:, 2].min() + statue[:, 2].max()) / 2 - (turned[:, 2].min() + turned[:, 2].max()) / 2])
        d1 = np.median(pp.nearest(turned + t, statue)[0])
        d2 = np.median(pp.nearest(statue, turned + t)[0])
        error = d1 + d2
        if best is None or error < best[0]:
            best = (error, degrees, t)
    print(f'  fit: scale {scale:.4f}, yaw {best[1]} deg, chamfer {best[0]:.4f} (height {np.ptp(statue[:, 1]):.3f})')
    return scale, np.radians(best[1]), best[2]


def png(image):
    out = io.BytesIO()
    image.save(out, 'PNG', optimize=True)
    return out.getvalue()


def ice_palette(skin):
    """A 256-entry colour ramp: the ice skin's colours ordered by their lightness (its quantiles)."""
    rgb = np.asarray(skin.convert('RGB'), float).reshape(-1, 3)
    lum = rgb @ [0.299, 0.587, 0.114]
    order = np.argsort(lum)
    quantiles = np.linspace(0.02, 0.98, 256)
    picks = order[(quantiles * (len(order) - 1)).astype(int)]
    # each entry the mean of its neighbourhood in lightness, so the ramp is smooth
    ramp = np.array([rgb[order[max(0, k - 200):k + 200]].mean(0) for k in (quantiles * (len(order) - 1)).astype(int)])
    del picks
    return ramp


def ice_texture(source, skin, ramp):
    """The creature texture's light and shade on the ice ramp, with the ice skin's own pattern over it."""
    src = source.convert('RGBA')
    rgb = np.asarray(src, float)[..., :3]
    alpha = np.asarray(src)[..., 3]
    lum = rgb @ [0.299, 0.587, 0.114]
    lo, hi = np.percentile(lum, 2), np.percentile(lum, 98)
    index = np.clip((lum - lo) / max(hi - lo, 1.0), 0, 1) * 255
    mapped = ramp[index.astype(int)]
    tile = skin.convert('RGBA').resize(src.size, Image.LANCZOS)
    detail = np.asarray(tile, float)[..., :3]
    out = (1 - DETAIL) * mapped + DETAIL * detail * (mapped.mean() / max(detail.mean(), 1.0))
    out = np.clip(out, 0, 255).astype(np.uint8)
    # MM9's statues are translucent ice: the skin's alpha (its crystals), times the creature's cut-outs
    ice_alpha = np.asarray(tile, float)[..., 3] / 255.0
    alpha = np.clip(alpha * ice_alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([out, alpha]), 'RGBA')


def image_of(doc, binary, index):
    view = doc['bufferViews'][doc['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']])))


def build(statue):
    creature_name = STATUES[statue]
    doc, binary = pp.read_glb(MODELS / f'mm9_{creature_name}.glb')
    statue_doc, statue_bin = pp.read_glb(MODELS / f'mm9_deco_{statue}.glb')
    old_doc, old_bin = pp.read_glb(pp.HERE / 'work' / statue / f'mm9_deco_{statue}_anim.glb') \
        if (pp.HERE / 'work' / statue / f'mm9_deco_{statue}_anim.glb').exists() \
        else pp.read_glb(MODELS / f'mm9_deco_{statue}_anim.glb')
    raw = pp.Raw.__new__(pp.Raw)
    raw.doc, raw.bin, raw.pose = doc, binary, (None, 0.0)
    raw.parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
    raw.tracks = {}
    for animation in doc.get('animations', []):
        tracks = {}
        for channel in animation['channels']:
            sampler = animation['samplers'][channel['sampler']]
            tracks[(channel['target']['node'], channel['target']['path'])] = (
                pp.array(doc, binary, sampler['input']).ravel(), pp.array(doc, binary, sampler['output']))
        raw.tracks[animation['name']] = tracks
    print(f'{statue} <- mm9_{creature_name}.glb')

    creature_points = posed_points(raw, doc, binary, REST_CLIP, 0.0)
    statue_points = np.concatenate([pp.array(statue_doc, statue_bin, p['attributes']['POSITION'])
                                    for p in statue_doc['meshes'][0]['primitives']]).astype(float)
    scale, yaw, translation = fit(creature_points, statue_points)

    # Rest in the Standing pose: every animated node's local transform at the clip's first frame.
    for (node, path), (times, values) in raw.tracks[REST_CLIP].items():
        if path in ('translation', 'rotation', 'scale'):
            doc['nodes'][node][path] = [float(v) for v in values[0]]
            doc['nodes'][node].pop('matrix', None)

    # The fit as a new root over the scene's roots.
    roots = doc['scenes'][doc.get('scene', 0)]['nodes']
    doc['nodes'].append({'name': 'Statue', 'children': list(roots), 'scale': [float(scale)] * 3,
                         'rotation': [0.0, float(np.sin(yaw / 2)), 0.0, float(np.cos(yaw / 2))],
                         'translation': [float(v) for v in translation]})
    doc['scenes'][doc.get('scene', 0)]['nodes'] = [len(doc['nodes']) - 1]

    # Clips under MM9's names.
    mapping = clip_map(durations(old_doc, old_bin), durations(doc, binary))
    by_name = {a['name']: a for a in doc['animations']}
    doc['animations'] = [dict(by_name[c], name=n) for n, c in sorted(mapping.items())]
    missing = sorted(set(durations(old_doc, old_bin)) - set(mapping))
    print(f'  clips: {mapping}; no creature clip for {missing}')

    # Ice materials: each primitive's default material, iced once.
    skin_image = image_of(statue_doc, statue_bin, statue_doc['materials'][0]['pbrMetallicRoughness']
                          ['baseColorTexture']['index'] if 'index' in statue_doc['materials'][0]['pbrMetallicRoughness']
                          ['baseColorTexture'] else 0)
    ramp = ice_palette(skin_image)
    new_images, new_materials, material_of = [], [], {}
    texture_image = {i: t['source'] for i, t in enumerate(doc.get('textures', []))}
    iced_image = {}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            prim.pop('extensions', None)
            m = prim.get('material')
            if m is None:
                continue
            if m not in material_of:
                source = doc['materials'][m]
                pbr = source.get('pbrMetallicRoughness', {})
                material = {'name': source.get('name', f'm{m}') + '_ice',
                            'pbrMetallicRoughness': {'metallicFactor': 0.0, 'roughnessFactor': ROUGHNESS}}
                # translucent ice, as MM9's statue skin (its alpha): blended like the old statue's
                material['alphaMode'] = 'BLEND'
                if 'doubleSided' in source:
                    material['doubleSided'] = source['doubleSided']
                if 'baseColorTexture' in pbr:
                    image = texture_image[pbr['baseColorTexture']['index']]
                    if image not in iced_image:
                        iced = ice_texture(image_of(doc, binary, image), skin_image, ramp)
                        new_images.append(png(iced))
                        iced_image[image] = len(new_images) - 1
                    material['pbrMetallicRoughness']['baseColorTexture'] = {'index': ('ice', iced_image[image])}
                if 'normalTexture' in source:
                    material['normalTexture'] = dict(source['normalTexture'],
                                                     index=('keep', texture_image[source['normalTexture']['index']]))
                new_materials.append(material)
                material_of[m] = len(new_materials) - 1
            prim['material'] = material_of[m]
    doc['materials'] = new_materials
    # Blended ice casts no dedicated shadow (the loader allows shadow LODs only under opaque geometry): their meshes
    # go, the others renumbered.
    shadow = set()
    for mesh in doc['meshes']:
        shadow |= set((mesh.get('extras') or {}).pop('openyamm_shadow_lods', []))
    if shadow:
        kept = [i for i in range(len(doc['meshes'])) if i not in shadow]
        renumber = {old: new for new, old in enumerate(kept)}
        if any(n.get('mesh') in shadow for n in doc['nodes']):
            raise SystemExit(f'{statue}: a node draws a shadow LOD mesh')
        doc['meshes'] = [doc['meshes'][i] for i in kept]
        for node in doc['nodes']:
            if 'mesh' in node:
                node['mesh'] = renumber[node['mesh']]
        for mesh in doc['meshes']:
            extras = mesh.get('extras') or {}
            if 'openyamm_lods' in extras:
                extras['openyamm_lods'] = [renumber[i] for i in extras['openyamm_lods']]
    for key in ('extensionsUsed', 'extensionsRequired'):
        if key in doc:
            doc[key] = [e for e in doc[key] if e != 'KHR_materials_variants']
            if not doc[key]:
                doc.pop(key)
    doc.pop('extensions', None)
    return compact(doc, binary, new_images)


def compact(doc, binary, new_images):
    """A GLB of what the document still uses: its meshes', skins' and clips' accessors, the kept images (normal maps)
    and the new ones, packed into a fresh buffer."""
    blob = bytearray()
    views, accessors, images, textures = [], [], [], []

    def add_view(data, target=None):
        blob.extend(b'\0' * (-len(blob) % 4))
        entry = {'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}
        if target:
            entry['target'] = target
        views.append(entry)
        blob.extend(data)
        return len(views) - 1

    accessor_map = {}

    def accessor(index):
        if index in accessor_map:
            return accessor_map[index]
        source = dict(doc['accessors'][index])
        view = doc['bufferViews'][source['bufferView']]
        start = view.get('byteOffset', 0)
        data = bytes(binary[start:start + view['byteLength']])
        source['bufferView'] = add_view(data, view.get('target'))
        if 'byteStride' in view:
            views[-1]['byteStride'] = view['byteStride']
        accessors.append(source)
        accessor_map[index] = len(accessors) - 1
        return accessor_map[index]

    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            prim['attributes'] = {k: accessor(v) for k, v in prim['attributes'].items()}
            if 'indices' in prim:
                prim['indices'] = accessor(prim['indices'])
            if 'targets' in prim:
                prim['targets'] = [{k: accessor(v) for k, v in t.items()} for t in prim['targets']]
    for skin in doc.get('skins', []):
        skin['inverseBindMatrices'] = accessor(skin['inverseBindMatrices'])
    for animation in doc.get('animations', []):
        animation['samplers'] = [dict(s, input=accessor(s['input']), output=accessor(s['output']))
                                 for s in animation['samplers']]
    image_map = {}

    def texture(ref):
        kind, index = ref
        key = (kind, index)
        if key not in image_map:
            if kind == 'ice':
                data, mime = new_images[index], 'image/png'
            else:
                source = doc['images'][index]
                view = doc['bufferViews'][source['bufferView']]
                start = view.get('byteOffset', 0)
                data, mime = bytes(binary[start:start + view['byteLength']]), source.get('mimeType', 'image/png')
            images.append({'bufferView': add_view(data), 'mimeType': mime})
            textures.append({'source': len(images) - 1, 'sampler': 0})
            image_map[key] = len(textures) - 1
        return image_map[key]

    for material in doc['materials']:
        pbr = material['pbrMetallicRoughness']
        if 'baseColorTexture' in pbr:
            pbr['baseColorTexture'] = {'index': texture(pbr['baseColorTexture']['index'])}
        if 'normalTexture' in material:
            material['normalTexture']['index'] = texture(material['normalTexture']['index'])
    out = {k: v for k, v in doc.items() if k not in ('accessors', 'bufferViews', 'images', 'textures', 'samplers',
                                                      'buffers')}
    out.update({'accessors': accessors, 'bufferViews': views, 'images': images, 'textures': textures,
                'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}],
                'buffers': [{'byteLength': len(blob)}]})
    return out, bytes(blob)


def main():
    statues = [a for a in sys.argv[1:] if not a.startswith('--')] or list(STATUES)
    for statue in statues:
        out_doc, out_bin = build(statue)
        out_dir = pp.HERE / 'work' / f'{statue}_ice'
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f'mm9_deco_{statue}_anim.glb'
        pp.write_glb(path, out_doc, out_bin)
        print(f'  -> {path} ({path.stat().st_size // 1024} KB)')
        if '--install' in sys.argv:
            subprocess.run([sys.executable, str(pp.REPO / 'tools/install_model.py'), str(path), '--world', 'mm9',
                            '--name', path.name], check=True)


if __name__ == '__main__':
    main()
