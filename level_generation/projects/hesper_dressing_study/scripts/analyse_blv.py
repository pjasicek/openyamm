#!/usr/bin/env python3
"""Per-map and per-sector dressing statistics for every MM6/MM7/MM8 BLV.

Read-only. Writes data/sectors.json (per sector), data/maps.csv (per map) and data/worlds.json (per world).
Floor = face with Newell normal z > 0.7. "Detail" faces are non-portal faces whose texture is not one of the
sector's three largest textures by area, or whose area is below 0.3 M units^2 (proxy for BLV-built furniture).
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / 'data'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402

SMALL_FACE = 300_000.0


def load_catalog():
    table = ROOT / 'assets_dev/engine/data_tables/decoration_data.txt'
    catalog, names, aliases = {}, {}, {}
    for row in csv.reader(table.open(), delimiter='\t'):
        if not row or not row[0].isdigit():
            continue
        entry = dict(id=int(row[0]) - 1, name=row[1].lower(), hint=row[2], light_radius=int(row[6]),
                     flags=row[11], sprite_id=int(row[12]))
        catalog[entry['id']] = entry
        names[entry['name']] = entry
        for alias in (row[14].split(',') if len(row) > 14 else []):
            aliases[alias.strip().lower()] = entry
    return catalog, names, aliases


def resolve(entity, catalog, names, aliases):
    # Same order as level_generation/scripts/inspect_decoration_references.py: name, alias, raw list id.
    name = entity['name'].strip().lower()
    raw = catalog.get(entity['decoration_list_id'])
    entry = names.get(name) if name else catalog[0]
    if entry is None:
        entry = aliases.get(name) if raw is None or raw['name'] == 'pending' else None
        entry = entry or raw
    return entry


def visible(entry, entity):
    flags = entry['flags']
    return bool(entry['sprite_id']) and 'DontDraw' not in flags and not (entity['ai_attributes'] & 32)


def newell(points):
    n = np.zeros(3)
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
    return n


def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def analyse(world, path, cat):
    p = parse_blv_file(path)['payload']
    V = np.array([[v['x'], v['y'], v['z']] for v in p['vertices']], float)
    sectors = defaultdict(lambda: dict(floor_area=0.0, faces=0, tex_area=Counter(), tex_faces=Counter(),
                                       face_list=[], floors=[], event_faces=0, xy=[], zs=[], verticals=[],
                                       fluid_area=0.0, clickable=[]))
    for f in p['faces']:
        if f['is_portal'] or len(f['vertex_indices']) < 3:
            continue
        P = V[f['vertex_indices']]
        n = newell(P)
        area = float(np.linalg.norm(n) / 2)
        if area <= 0:
            continue
        nz = n[2] / (2 * area)
        s = sectors[f['room_number']]
        tex = f['texture_name'].lower()
        s['faces'] += 1
        s['tex_area'][tex] += area
        s['tex_faces'][tex] += 1
        s['face_list'].append((tex, area))
        s['xy'].append(P[:, :2])
        s['zs'].append(P[:, 2])
        event = (f['face_param'] or {}).get('cog_triggered', 0)
        if event:
            s['event_faces'] += 1
            if f['attributes'] & 0x02000000:
                s['clickable'].append(dict(face=f['index'], event=event, texture=tex, area=round(area),
                                           centre=P.mean(axis=0).round().tolist()))
        if abs(nz) < 0.3:
            s['verticals'].append((P.mean(axis=0), area, tex))
        if nz > 0.7:
            if f['attributes'] & 0x10:
                s['fluid_area'] += area
            s['floor_area'] += area
            s['floors'].append((P[:, :2], float(P[:, 2].mean()), area))
    decos = defaultdict(list)
    for e in p['entities']:
        entry = resolve(e, *cat)
        if entry is None or not visible(entry, e):
            continue
        x, y, z = (e['position'][a] for a in 'xyz')
        best = None
        for sid, s in sectors.items():
            for poly, fz, _ in s['floors']:
                if fz <= z + 96 and point_in_poly(x, y, poly):
                    if best is None or fz > best[1]:
                        best = (sid, fz)
        decos[best[0] if best else -1].append(dict(name=entry['name'], hint=entry['hint'], pos=[x, y, z],
                                                   light=entry['light_radius'] > 0))
    rows = []
    for sid, s in sorted(sectors.items()):
        top3 = {t for t, _ in s['tex_area'].most_common(3)}
        detail = [(t, a) for t, a in s['face_list'] if t not in top3 or a < SMALL_FACE]
        detail_tex = Counter()
        for t, a in detail:
            detail_tex[t] += 1
        xy = np.vstack(s['xy'])
        zs = np.concatenate(s['zs'])
        if s['floors']:
            main = max(s['floors'], key=lambda q: q[2])
            floor_z = main[1]
            fxy = np.vstack([q[0] for q in s['floors']])
            centre = fxy.mean(axis=0)
        else:
            floor_z = float(zs.min())
            centre = xy.mean(axis=0)
        if s['floors']:
            lo, hi = fxy.min(axis=0), fxy.max(axis=0)
            levels = Counter()
            for _, fz, a in s['floors']:
                levels[int(round(fz / 32))] += a
            floor_levels = sum(a > 0.05 * s['floor_area'] for a in levels.values())
            inner = [v for v in s['verticals'] if lo[0] + 384 < v[0][0] < hi[0] - 384 and lo[1] + 384 < v[0][1] < hi[1] - 384]
            width, depth = float(hi[0] - lo[0]), float(hi[1] - lo[1])
        else:
            floor_levels, inner, width, depth = 0, [], 0.0, 0.0
        long_side = max(width, depth, 1.0)
        rows.append(dict(world=world, map=path.name, sector=sid, floor_area=round(s['floor_area']),
                         faces=s['faces'], textures=len(s['tex_area']), detail_faces=len(detail),
                         detail_small=sum(a < SMALL_FACE for _, a in detail),
                         detail_offtex=sum(t not in top3 for t, _ in detail),
                         event_faces=s['event_faces'],
                         top_textures=[t for t, _ in s['tex_area'].most_common(3)],
                         detail_textures=detail_tex.most_common(8),
                         bbox=[*xy.min(axis=0).round().tolist(), *xy.max(axis=0).round().tolist()],
                         z_range=[float(zs.min()), float(zs.max())], floor_z=round(floor_z),
                         centre=centre.round().tolist(), width=round(width), depth=round(depth),
                         mean_width=round(s['floor_area'] / long_side), floor_levels=floor_levels,
                         fluid_share=round(s['fluid_area'] / max(s['floor_area'], 1), 2),
                         height=round(float(zs.max()) - floor_z), inner_vertical_faces=len(inner),
                         inner_textures=Counter(v[2] for v in inner).most_common(5),
                         clickable=s['clickable'],
                         decorations=Counter(d['name'] for d in decos.get(sid, [])).most_common(),
                         decoration_count=len(decos.get(sid, [])),
                         decoration_positions=[(d['name'], d['pos']) for d in decos.get(sid, [])]))
    lights = len(p['lights'])
    return rows, dict(unassigned_decorations=len(decos.get(-1, [])), lights=lights)


def main():
    cat = load_catalog()
    all_rows, maps = [], []
    for world in ('mm6', 'mm7', 'mm8'):
        for path in sorted((ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.blv')):
            try:
                rows, extra = analyse(world, path, cat)
            except Exception as exc:  # report and continue: one broken file should not stop the census
                print('skip', world, path.name, exc, file=sys.stderr)
                continue
            all_rows += rows
            floor = sum(r['floor_area'] for r in rows)
            decos = sum(r['decoration_count'] for r in rows)
            faces = sum(r['faces'] for r in rows)
            dfaces = sum(r['detail_faces'] for r in rows)
            big = [r for r in rows if r['floor_area'] > 0]
            maps.append(dict(world=world, map=path.name, sectors=len(big), floor_area_m=round(floor / 1e6, 2),
                             decorations=decos + extra['unassigned_decorations'],
                             decos_per_m=round((decos + extra['unassigned_decorations']) / max(floor / 1e6, 1e-9), 2),
                             empty_sector_share=round(sum(r['decoration_count'] == 0 for r in big) / max(len(big), 1), 2),
                             faces=faces, faces_per_m=round(faces / max(floor / 1e6, 1e-9)),
                             detail_share=round(dfaces / max(faces, 1), 2),
                             event_faces=sum(r['event_faces'] for r in rows), lights=extra['lights']))
            print(world, path.name, maps[-1]['decorations'], 'decos', flush=True)
    OUT.mkdir(exist_ok=True)
    (OUT / 'sectors.json').write_text(json.dumps(all_rows))
    with (OUT / 'maps.csv').open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(maps[0]))
        w.writeheader()
        w.writerows(maps)
    worlds = {}
    for world in ('mm6', 'mm7', 'mm8'):
        ms = [m for m in maps if m['world'] == world]
        rs = [r for r in all_rows if r['world'] == world and r['floor_area'] > 0]
        names = Counter()
        hints = {}
        for r in rs:
            for n, c in r['decorations']:
                names[n] += c
        floor = sum(m['floor_area_m'] for m in ms)
        deco = sum(m['decorations'] for m in ms)
        worlds[world] = dict(maps=len(ms), sectors=len(rs), floor_area_m=round(floor, 1), decorations=deco,
                             decos_per_m=round(deco / floor, 2),
                             empty_sector_share=round(sum(r['decoration_count'] == 0 for r in rs) / len(rs), 2),
                             median_map_decos_per_m=float(np.median([m['decos_per_m'] for m in ms])),
                             detail_share=round(sum(r['detail_faces'] for r in rs) / sum(r['faces'] for r in rs), 2),
                             faces_per_m=round(sum(r['faces'] for r in rs) / floor),
                             top_decorations=names.most_common(25))
    (OUT / 'worlds.json').write_text(json.dumps(worlds, indent=1))


if __name__ == '__main__':
    main()
