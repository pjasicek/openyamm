#!/usr/bin/env python3
"""Door audit of the remade MM9 dungeons for the x4 texture pass.

For every mover (`initial_state.doors` in `<map>.scene.yml`) the leaf's broad faces (front/back) are read from the
BLV, and the texture mapping is fitted on the face plane: u and v as linear functions of a horizontal coordinate s
(along the face) and the height z. Leaves of one doorway are paired when their broad faces are coplanar and abut.
For each pair the script decides whether the two leaves show one picture split at the joint (`split`), the same
picture mirrored (`mirrored`), two different textures (`two-tex`) or independent copies (`copies`).

Writes `mm9_doors.json` (all leaves and pairs) and prints a markdown summary; `mm9_doors.md` is written from it.
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402

MAPS = ROOT / 'output/mm9_rework/assets_dev/worlds/mm9/maps'
INVENTORY = HERE.parent / 'inventory.json'


def fit_face(face, vertices):
    indices = face['vertex_indices']
    points = np.array([[vertices[i][k] for k in 'xyz'] for i in indices], float)
    normal = np.cross(points[1] - points[0], points[2] - points[0])
    for index in range(2, len(points) - 1):
        normal = normal + np.cross(points[index] - points[0], points[index + 1] - points[0])
    norm = np.linalg.norm(normal)
    if norm < 1e-6:
        return None
    normal /= norm
    if abs(normal[2]) > 0.7:
        return None  # top/bottom of a leaf or a trapdoor; handled as horizontal below
    horizontal = np.cross([0.0, 0.0, 1.0], normal)
    horizontal /= np.linalg.norm(horizontal)
    s = points @ horizontal
    z = points[:, 2]
    param = face.get('face_param') or {}
    us = np.array(face['texture_us'][:len(indices)], float) + param.get('texture_delta_u', 0)
    vs = np.array(face['texture_vs'][:len(indices)], float) + param.get('texture_delta_v', 0)
    design = np.stack([s, z, np.ones_like(s)], axis=1)
    cu = np.linalg.lstsq(design, us, rcond=None)[0]
    cv = np.linalg.lstsq(design, vs, rcond=None)[0]
    area = 0.5 * norm
    return {'normal': normal, 'h': horizontal, 'plane': float(points[0] @ normal), 's': (float(s.min()), float(s.max())),
            'z': (float(z.min()), float(z.max())), 'cu': cu, 'cv': cv, 'area': area, 'points': points,
            'u': (float(us.min()), float(us.max())), 'v': (float(vs.min()), float(vs.max()))}


def leaf_record(door, faces, vertices, sizes):
    broad = []
    for face_id in door['face_ids']:
        face = faces[face_id]
        name = (face.get('texture_name') or '').strip().lower()
        fit = fit_face(face, vertices)
        if fit is None or not name:
            continue
        fit['texture'] = name
        fit['face'] = face_id
        broad.append(fit)
    if not broad:
        return None
    broad.sort(key=lambda fit: -fit['area'])
    top = broad[0]['area']
    broad = [fit for fit in broad if fit['area'] > 0.5 * top]
    return broad


def describe_face(fit, size):
    width, height = size
    span_u = (fit['u'][1] - fit['u'][0]) / width
    span_v = (fit['v'][1] - fit['v'][0]) / height
    return span_u, span_v


def pair_leaves(leaves):
    """Leaves whose broad faces lie in one plane (either side) and abut along s."""
    pairs = []
    keys = list(leaves)
    for ia in range(len(keys)):
        for ib in range(ia + 1, len(keys)):
            a, b = leaves[keys[ia]], leaves[keys[ib]]
            best = None
            for fa in a:
                for fb in b:
                    if abs(float(fa['normal'] @ fb['normal'])) < 0.98:
                        continue
                    nb = fb['normal'] if float(fa['normal'] @ fb['normal']) > 0 else -fb['normal']
                    plane_b = float(fb['points'][0] @ fa['normal'])
                    if abs(plane_b - fa['plane']) > 2.0:
                        continue
                    sb = fb['points'] @ fa['h']
                    gap = max(sb.min() - fa['s'][1], fa['s'][0] - sb.max())
                    overlap_z = min(fa['z'][1], fb['z'][1]) - min(max(fa['z'][0], fb['z'][0]), 1e9)
                    if gap > 8 or gap < -2 or overlap_z < 0.5 * (fa['z'][1] - fa['z'][0]):
                        continue
                    if best is None or gap < best[0]:
                        best = (gap, fa, fb)
            if best:
                pairs.append((keys[ia], keys[ib], best[1], best[2]))
    return pairs


def classify_pair(fa, fb, sizes):
    """Compare the two coplanar faces in fa's (s, z) frame."""
    h = fa['h']
    sb = fb['points'] @ h
    # B's u as a function of fa's s: refit with fa's frame.
    zb = fb['points'][:, 2]
    us_b = fb['cu'][0] * (fb['points'] @ fb['h']) + fb['cu'][1] * zb + fb['cu'][2]
    design = np.stack([sb, zb, np.ones_like(sb)], axis=1)
    cub = np.linalg.lstsq(design, us_b, rcond=None)[0]
    vs_b = fb['cv'][0] * (fb['points'] @ fb['h']) + fb['cv'][1] * zb + fb['cv'][2]
    cvb = np.linalg.lstsq(design, vs_b, rcond=None)[0]
    # Which texture axis runs horizontally on each face.
    a_axis = 'u' if abs(fa['cu'][0]) >= abs(fa['cv'][0]) else 'v'
    b_axis = 'u' if abs(cub[0]) >= abs(cvb[0]) else 'v'
    ca = fa['cu'] if a_axis == 'u' else fa['cv']
    cb = cub if b_axis == 'u' else cvb
    if fa['s'][1] <= sb.min() + 1:
        joint = 0.5 * (fa['s'][1] + sb.min())
    else:
        joint = 0.5 * (fa['s'][0] + sb.max())
    zmid = 0.5 * (fa['z'][0] + fa['z'][1])
    value_a = ca[0] * joint + ca[1] * zmid + ca[2]
    value_b = cb[0] * joint + cb[1] * zmid + cb[2]
    same_sign = (ca[0] > 0) == (cb[0] > 0)
    if fa['texture'] != fb['texture']:
        kind = 'two-tex'
    elif not same_sign:
        kind = 'mirrored'
    else:
        width = sizes.get(fa['texture'], (128, 128))[0 if a_axis == 'u' else 1]
        diff = (value_a - value_b) % width
        kind = 'split' if min(diff, width - diff) < 2 else 'copies'
    return {'kind': kind, 'axis_a': a_axis, 'axis_b': b_axis, 'slope_a': float(ca[0]), 'slope_b': float(cb[0]),
            'joint_value_a': float(value_a), 'joint_value_b': float(value_b)}


def main():
    inventory = json.loads(INVENTORY.read_text())
    entries = {entry['name']: entry for entry in inventory['textures'] if entry['world'] == 'mm9'}
    sizes = {name: tuple(entry['size']) for name, entry in entries.items() if 'size' in entry}
    report = {'maps': {}, 'textures': defaultdict(lambda: {'maps': set(), 'leaves': 0, 'pairs': defaultdict(int),
                                                            'spans': set(), 'partners': set(), 'movers': set()})}
    scope = {name.lower() for name in (inventory.get('map_scope') or {}).get('mm9', [])}
    for blv in sorted(MAPS.glob('*.blv')):
        if blv.name.lower() not in scope:
            continue  # only the maps in the x4 inventory's mm9 scope (24 dungeons and 7 cities)
        scene_path = blv.with_suffix('').with_suffix('.scene.yml')
        if not scene_path.exists():
            continue
        scene = yaml.safe_load(scene_path.read_text())
        doors = (scene.get('initial_state') or {}).get('doors') or []
        payload = parse_blv_file(blv)['payload']
        faces, vertices = payload['faces'], payload['vertices']
        leaves = {}
        movers = {}
        for door in doors:
            record = leaf_record(door, faces, vertices, sizes)
            if not record:
                continue
            leaves[door['door_id']] = record
            mover = door.get('mover') or {}
            movers[door['door_id']] = ('hinged' if 'rotation' in mover else
                                       'slide-v' if abs(door['direction'][2]) > 32768 else 'slide-h')
        pairs = pair_leaves(leaves)
        paired = set()
        map_pairs = []
        for ida, idb, fa, fb in pairs:
            info = classify_pair(fa, fb, sizes)
            info.update(a=ida, b=idb, tex_a=fa['texture'], tex_b=fb['texture'],
                        mover_a=movers[ida], mover_b=movers[idb],
                        width_a=fa['s'][1] - fa['s'][0], height_a=fa['z'][1] - fa['z'][0])
            info['span_a'] = describe_face(fa, sizes.get(fa['texture'], (128, 128)))
            info['span_b'] = describe_face(fb, sizes.get(fb['texture'], (128, 128)))
            map_pairs.append(info)
            paired.update((ida, idb))
            for tex, other in ((fa['texture'], fb['texture']), (fb['texture'], fa['texture'])):
                t = report['textures'][tex]
                t['pairs'][info['kind']] += 1
                if other != tex:
                    t['partners'].add(other)
        singles = []
        for door_id, record in leaves.items():
            for fit in record[:2]:
                tex = fit['texture']
                t = report['textures'][tex]
                t['maps'].add(blv.stem)
                t['leaves'] += 1
                t['movers'].add(movers[door_id])
                span = describe_face(fit, sizes.get(tex, (128, 128)))
                t['spans'].add((round(span[0], 2), round(span[1], 2)))
            if door_id not in paired:
                fit = record[0]
                singles.append({'door': door_id, 'texture': fit['texture'], 'mover': movers[door_id],
                                'span': describe_face(fit, sizes.get(fit['texture'], (128, 128))),
                                'width': fit['s'][1] - fit['s'][0], 'height': fit['z'][1] - fit['z'][0]})
        report['maps'][blv.stem] = {'doors': len(doors), 'leaves': len(leaves), 'pairs': map_pairs,
                                    'singles': singles}
    textures = {}
    for tex, t in report['textures'].items():
        entry = entries.get(tex, {})
        textures[tex] = {'maps': sorted(t['maps']), 'leaves': t['leaves'], 'pairs': dict(t['pairs']),
                         'spans': sorted(t['spans']), 'partners': sorted(t['partners']), 'movers': sorted(t['movers']),
                         'size': entry.get('size'), 'source': entry.get('source_texture'),
                         'assembly': entry.get('assembly'), 'relatives': [r['id'] for r in entry.get('relatives', [])],
                         'exclude': entry.get('exclude'), 'faces_total': entry.get('faces'),
                         'area_total': entry.get('area')}
    report['textures'] = textures
    (HERE / 'mm9_doors.json').write_text(json.dumps(report, indent=1, default=lambda o: list(o) if isinstance(o, (set, tuple)) else float(o)))
    write_markdown(json.loads((HERE / 'mm9_doors.json').read_text()), entries)
    print(len(textures), 'mover textures')


FINDINGS = """## Findings (2026-10-31)

- **Cities (2026-11-01):** the seven city BLVs (Arslegard, Drangheim, Frosgard, Guberland, Sturmford, Thjorgard,
  Thronheim) add 106 door pairs (52 mirrored, 49 split, 5 copies) and none of them uses two textures either.
- **No double door in the 24 dungeons is made of two textures.** Every paired door uses one texture, so no door needs
  an `assembly_overrides.json` entry, and no door texture is a mirrored copy of another (`--copy-from --mirror` does
  not apply). The two `two-tex` pairs are a Dungeon of Secrets wall (`dungcmvp15`) beside an invisible helper face.
- **split @ centre** (Yanmir's Fort, Drangheim Prison, Ta'Sar Academy, The Thousand Terrors, Dook's Castle, Arena,
  Training Hall, Lindisfarne, Anskram `anskramdoor2`): the texture is the whole double door and each leaf shows one
  half; the leaves meet at the texture's centre column. One master is one canvas, so the leaves continue by
  construction; what matters is registration (the centre gap stays on the centre column) and the layout check.
- **mirrored @ centre** (Anskram Keep, Klusos House, Temple of Honk, Inventa Storca, Verhoffin `verdoor5`, Ta'Sar
  `door_dungeon2`): both leaves show the same half, one flipped by its UVs; the joint is the centre column against
  its own mirror image, continuous by construction. The other half of the texture is never seen on these doors.
- **mirrored @ edge** (Beethoven `door13`, Verhoffin `verdoor2-rust`, Bathhouse `karh-door-03`, Anskram
  `thjordoor2`): the joint is the texture's left edge against its mirror: the edge column must not carry a rim or
  line (edge/rim/line checks; never accept those flags on a door).
- **split @ edge** (`dungeonsecretdoor1` in Dungeon of Secrets and Yanmir's Fort, one `dungeondoor` pair): each leaf
  shows the whole picture and leaf A's right edge meets leaf B's left edge, so the texture's u wrap must be seamless
  (wrap splice and seam check; judged in game at the joint). The Inventa Storca `dungeondoor` pair shows the halves
  swapped (right half on the left leaf), so its joint is the texture's u edge although the texture is not marked as
  wrapping; MM9's own UVs, left as they are.
- **Single leaves** showing half of a two-leaf picture (Lich Lab `verdoor8-panel`, 71 leaves: the lit-window half;
  some leaves sample a few texels past u = 0, so the u wrap matters there too) or the whole picture (Chasm
  `koenugtombdoor`, Dungeon of Secrets `dungeonsecretdoor2`, Lindisfarne `Lindisfarne_Door2`, Ruined Temple
  `ruindoor`, Thjorad Mine `refineryslidingdoor128`, `darkdoor`).
- **Native offsets** (table below): a few pairs do not continue in MM9's own UVs (Drangheim Prison doors 69/70 and
  76/77 by 7 texels, Bathhouse 9/10 by 19, Ta'Sar joints at u = 67-75 instead of 64). The rework keeps MM9's UVs, so
  these look the same with the 1x art; they are map data, not texture problems, and are left alone here.
- Pilot set (common types first, every mapping kind): `verdrahook`, `yanmh7oyef`, `pris68v3ri`, `koenkzg05g`,
  `tasa2sautz`, `dung4y77qh`, `verd9vx2h2`, `doornnw65b`, `doorpjfvqy`, `honkvup7f3`, `thjozz6y06`, `dungm4uan3` and its
  frame relative `dung2bwia7`. Already accepted in the Anskram pilot: `ansk8hz857`, `anskjrfvb9`, `thjogdrt3q`.

""".split('\n')


def joint_class(value, width):
    position = value % width
    if min(position, width - position) <= 3:
        return 'edge'
    if abs(position - width / 2) <= 3:
        return 'centre'
    return f'u={position:.0f}'


def write_markdown(report, entries):
    lines = ['# MM9 dungeon doors: texture audit (generated by `mm9_doors.py`)', '',
             'Every mover of the 24 remade dungeons (`initial_state.doors`), its broad faces from the BLV and how they',
             'map their texture (span = share of the texture width/height one leaf shows). Leaves are paired when',
             'their broad faces are coplanar and abut. Pair kinds: **split** = one texture continues across the',
             'joint (each leaf shows its part of one picture); **mirrored** = both leaves show the same part, one',
             'flipped by its UVs; **copies** = same texture, not continuous (offset given); **two-tex** = different',
             'textures. Joint = where the joint falls in the texture (centre column, texture edge, or offset).', '']
    lines += FINDINGS
    door_art, other = [], []
    for name, t in sorted(report['textures'].items(), key=lambda kv: -kv[1]['leaves']):
        if t.get('exclude'):
            continue
        source = (t.get('source') or '').replace('\\', '/').lower()
        (door_art if '/doors/' in source else other).append((name, t))
    joints = defaultdict(lambda: defaultdict(int))
    mismatches = []
    for map_name, m in report['maps'].items():
        for pair in m['pairs']:
            if pair['tex_a'] != pair['tex_b']:
                continue
            width = (entries.get(pair['tex_a'], {}).get('size') or [128, 128])[0 if pair['axis_a'] == 'u' else 1]
            ja, jb = joint_class(pair['joint_value_a'], width), joint_class(pair['joint_value_b'], width)
            joints[pair['tex_a']][f"{pair['kind']} @ {ja if ja == jb else ja + '/' + jb}"] += 1
            if pair['kind'] == 'copies':
                diff = (pair['joint_value_a'] - pair['joint_value_b']) % width
                mismatches.append((map_name, pair['a'], pair['b'], pair['tex_a'], min(diff, width - diff)))
    lines += ['## Door art (MM9 `doors` folders)', '',
              '| Texture | DTX | Size | Wrap | Maps | Leaf faces | Movers | Leaf span (u, v) | Pairs | Assembly needed |',
              '|---|---|---|---|---|---|---|---|---|---|']
    for name, t in door_art:
        entry = entries.get(name, {})
        spans = sorted({(round(s[0], 1), round(s[1], 1)) for s in t['spans']})
        pairs = ', '.join(f'{k}: {v}' for k, v in sorted(joints[name].items())) or 'single leaves'
        lines.append(f"| `{name}` | {Path((t.get('source') or '').replace(chr(92), '/')).name} | "
                     f"{'x'.join(map(str, t['size']))} | {entry.get('wrap') or '-'} | {', '.join(t['maps'])} | "
                     f"{t['leaves']} | {', '.join(t['movers'])} | {'; '.join(f'{a}, {b}' for a, b in spans[:4])} | "
                     f"{pairs} | no (one texture) |")
    lines += ['', '## Other textures on movers (secret walls, lifts, platforms, bars)', '',
              'Tiled materials that happen to sit on a mover; they follow the normal tiling rules.', '',
              '| Texture | DTX | Leaf faces | Pairs |', '|---|---|---|---|']
    for name, t in other:
        pairs = ', '.join(f'{k}: {v}' for k, v in sorted(joints[name].items())) or '-'
        lines.append(f"| `{name}` | {Path((t.get('source') or '').replace(chr(92), '/')).name} | {t['leaves']} | {pairs} |")
    lines += ['', '## Pairs whose leaves do not continue (native UVs, not a texture problem)', '',
              '| Map | Doors | Texture | Offset at the joint (texels) |', '|---|---|---|---|']
    for map_name, a, b, tex, diff in sorted(mismatches):
        lines.append(f'| {map_name} | {a}, {b} | `{tex}` | {diff:.1f} |')
    lines += ['', '## Per map', '', '| Map | Movers | Paired leaves (split / mirrored / copies / two-tex) | Single leaves |',
              '|---|---|---|---|']
    for map_name, m in report['maps'].items():
        kinds = defaultdict(int)
        for pair in m['pairs']:
            kinds[pair['kind']] += 1
        lines.append(f"| {map_name} | {m['doors']} | {kinds['split']} / {kinds['mirrored']} / {kinds['copies']} / "
                     f"{kinds['two-tex']} | {len(m['singles'])} |")
    (HERE / 'mm9_doors.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
