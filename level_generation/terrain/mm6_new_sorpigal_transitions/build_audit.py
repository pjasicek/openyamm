"""Inventory native land masks and assemble repeatable, water-free flat review cases."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
CATALOGUE = PROJECT.parent / 'mm6_new_sorpigal'
STUDY = PROJECT.parent / 'mm6_new_sorpigal_master_study'
# Visually reviewed source topology. Clockwise corners: NW, NE, SE, SW; 1 = foreground.
CORNERS = {'n': '0011', 'e': '1001', 's': '1100', 'w': '0110',
           'ne': '0001', 'nw': '0010', 'se': '1000', 'sw': '0100',
           'xne': '1011', 'xnw': '0111', 'xse': '1101', 'xsw': '1110'}
PORTS = {'6drsrecap': 'W', '6drsrwcap': 'E', '6drsrew': 'EW', '6drsrns': 'NS',
         '6drsrn_e': 'NE', '6drsrn_w': 'NW', '6drsrs_e': 'SE', '6drsrs_w': 'SW',
         '6drsrew_s': 'ESW'}
BASES = {'6grastyl': 'grass', '6dirttyl': 'dirt', '6voltyl': 'volcano'}
SIDES = {'N': (0, 1), 'E': (1, 2), 'S': (3, 2), 'W': (0, 3)}


def save_json(name, data):
    (PROJECT / name).write_text(json.dumps(data, indent=2) + '\n')


def main():
    catalogue = json.loads((CATALOGUE / 'catalogue.json').read_text())
    tiles = {t['name']: t for t in catalogue['tiles']
             if t['family'] in ('grass_dirt', 'rock_dirt', 'roads') or t['name'] in BASES}
    cells = list(csv.DictReader((CATALOGUE / 'map_cells.csv').open()))
    grid = {(int(c['column']), int(c['row'])): c['texture'] for c in cells}
    masks, signatures, profiles = [], {}, {}
    prompts = PROJECT / 'imagegen_briefs'
    prompts.mkdir(exist_ok=True)
    for name, tile in tiles.items():
        family = tile['family']
        if name in BASES:
            signatures[name] = [BASES[name]] * 4
        elif family == 'roads':
            signatures[name] = ['dirt'] * 4
        else:
            prefix, foreground = ('6grdrt', 'grass') if family == 'grass_dirt' else ('voldrt', 'volcano')
            signatures[name] = [foreground if bit == '1' else 'dirt' for bit in CORNERS[name[len(prefix):]]]
        profiles[name] = {}
        for side, (i, j) in SIDES.items():
            ends = [signatures[name][i], signatures[name][j]]
            profiles[name][side] = ('road_opening' if side in PORTS.get(name, '') else '/'.join(ends))
        if family == 'bases':
            continue
        foreground = {'grass_dirt': 'grass', 'rock_dirt': 'volcano', 'roads': 'cobbles'}[family]
        record = {'tile': name, 'family': family, 'shape': tile['kind'], 'suffix': tile['native_suffix'],
                  'white': foreground, 'black': 'dirt', 'mask': f'masks/v1/{name}.png',
                  'authoring_size': [512, 512], 'runtime_composite_size': [256, 256],
                  'source': '../mm6_new_sorpigal/' + tile['source_rgb'],
                  'source_bmp_sha256': tile['source_sha256'], 'used_cells': tile['rendered_cells'],
                  'corners_NW_NE_SE_SW': signatures[name], 'edge_topology': profiles[name],
                  'road_openings': list(PORTS.get(name, '')), 'status': 'needs_imagegen_extraction_and_review'}
        if (PROJECT / 'masks/connected_v4' / (name + '.png')).exists():
            record['status'] = 'generated_connected_v4; see reports for validation'
            record['connected_mask'] = f'masks/connected_v4/{name}.png'
        masks.append(record)
        brief = f'''Use case: background-extraction (material coverage, opaque grayscale output)
Asset: MM6 New Sorpigal {name}; {tile['kind']}; {family}.
All reference paths below are relative to mm6_new_sorpigal_transitions/, not this prompt folder.
Input 1, edit target: {record['source']} (original 128px tile, unrotated).
Input 2, supporting image reference: contexts/{name}.png; target is the central tile.
Gray blank cells in the context are excluded water, not a material to extract.
Input 3, supporting reference: reviewed shared edge profiles when available; extraction cannot be finalized without them.
Extract material coverage only: white=all {foreground} coverage, black=all underlying dirt.
Return one square opaque grayscale mask. No material texture, colour, labels, perspective, shadows, border or padding.
Preserve the native silhouette, area, orientation, meaningful islands and indentations. Do not turn internal
material shading or cobble grout into dirt holes. Gray is only narrow coverage/antialiasing at the boundary,
not broad soft gray regions. Do not invent a cleaner geometric layout or widen the road.
Corner materials clockwise NW/NE/SE/SW: {', '.join(signatures[name])}.
Edge topology (N/S read left-to-right, E/W top-to-bottom): {json.dumps(profiles[name])}.
Road openings: {PORTS.get(name, 'not a road')}. Preserve source widths and termination shape.
Native outline is authoritative in the interior. Reviewed shared edge profiles are authoritative at joins.
Keep corner samples and edge crossings fixed in later revisions; modify only the specifically failed area.
Work at sufficient resolution for a 512px authoring mask. Retain raw output; normalize size mechanically once.
This is a candidate extraction, not an exact recovered alpha. Review with neighboring candidates before acceptance.
'''
        (prompts / f'{name}.txt').write_text(brief)
    pairs, conflicts = [], []
    cases = []
    for name in [*BASES, 'cobbles_material']:
        cases.append({'id': f'repeat:{name}', 'group': 'Master repeats', 'label': f'{name} — 5×5 repeat',
                      'tiles': [[name] * 5 for _ in range(5)]})
    for raw in json.loads((CATALOGUE / 'adjacency.json').read_text()):
        a, b, direction = raw['a'], raw['b'], raw['direction_from_a']
        if a not in tiles or b not in tiles:
            continue
        side_a, side_b, dx, dy = ('E', 'W', 1, 0) if direction == 'east' else ('S', 'N', 0, 1)
        locations = [{'column': x, 'row': y, 'world_x': -32768 + 512*x, 'world_y': 32768 - 512*y}
                     for (x, y), n in grid.items() if n == a and grid.get((x+dx, y+dy)) == b]
        assert len(locations) == raw['count']
        conflict = profiles[a][side_a] != profiles[b][side_b]
        record = {**raw, 'id': f'{a}:{side_a}--{b}:{side_b}', 'side_a': side_a, 'side_b': side_b,
                  'profile_a': profiles[a][side_a], 'profile_b': profiles[b][side_b],
                  'topology_conflict': conflict, 'locations': locations}
        pairs.append(record)
        cases.append({'id': record['id'], 'group': 'Observed pairs',
                      'label': f'{a} {direction} {b} ({raw["count"]})' + (' — SOURCE CONFLICT' if conflict else ''),
                      'tiles': [[a, b]] if dx else [[a], [b]], 'conflict': conflict})
        if conflict:
            conflicts.append(record)
            for location in locations:
                x, y = location['column'], location['row']
                patch = [[grid.get((xx, yy)) if grid.get((xx, yy)) in tiles else None
                          for xx in range(x-1, x+3)] for yy in range(y-1, y+3)]
                cases.append({'id': f'conflict:{x},{y}:{direction}', 'group': 'Source conflicts',
                              'label': f'({x},{y}) {a} {direction} {b}', 'tiles': patch,
                              'origin': [x-1, y-1], 'conflict': True})
    junctions = {}
    for (x, y), a in grid.items():
        patch = (a, grid.get((x+1, y)), grid.get((x, y+1)), grid.get((x+1, y+1)))
        if all(n in tiles for n in patch):
            junctions.setdefault(patch, []).append([x, y])
    for i, (patch, locations) in enumerate(sorted(junctions.items())):
        conflict = any(profiles[patch[a]][sa] != profiles[patch[b]][sb]
                       for a, sa, b, sb in [(0, 'E', 1, 'W'), (2, 'E', 3, 'W'),
                                             (0, 'S', 2, 'N'), (1, 'S', 3, 'N')])
        cases.append({'id': f'junction:{i}', 'group': 'Observed 2×2 corners',
                      'label': f'{i+1}: ' + ' / '.join(patch) + f' ({len(locations)})',
                      'tiles': [list(patch[:2]), list(patch[2:])], 'locations': locations, 'conflict': conflict})
    for mask in masks:
        name = mask['tile']
        positions = [(x, y) for (x, y), n in grid.items() if n == name]
        # Prefer a wholly land context; otherwise leave water cells blank, never substitute land.
        x, y = max(positions, key=lambda pos: sum(grid.get((pos[0]+dx, pos[1]+dy)) in tiles
                                                for dy in range(-1, 2) for dx in range(-1, 2)))
        patch = [[grid.get((xx, yy)) if grid.get((xx, yy)) in tiles else None
                  for xx in range(x-1, x+2)] for yy in range(y-1, y+2)]
        cases.append({'id': f'context:{name}', 'group': 'Tile contexts', 'label': f'{name} at ({x},{y})',
                      'tiles': patch, 'origin': [x-1, y-1]})
        (PROJECT / 'contexts').mkdir(exist_ok=True)
        context = Image.new('RGB', (384, 384), '#36414a')
        for row, names in enumerate(patch):
            for column, native in enumerate(names):
                if native:
                    with Image.open(CATALOGUE / tiles[native]['source_rgb']) as image:
                        context.paste(image, (column*128, row*128))
        context.save(PROJECT / 'contexts' / f'{name}.png')
    # Group edge endpoints connected by compatible observed joins. Contradictions are separate review cases.
    parents = {f'{name}:{side}': f'{name}:{side}' for name in tiles for side in SIDES}
    def root(key):
        while parents[key] != key:
            key = parents[key]
        return key
    for pair in pairs:
        if not pair['topology_conflict']:
            a, b = f'{pair["a"]}:{pair["side_a"]}', f'{pair["b"]}:{pair["side_b"]}'
            parents[root(a)] = root(b)
    groups = {}
    for key in parents:
        groups.setdefault(root(key), []).append(key)
    edge_groups = [{'id': i, 'members': members, 'topology': profiles[members[0].split(':')[0]][members[0][-1]],
                    'status': 'shared_pixel_profile_not_yet_authored'}
                   for i, members in enumerate(sorted(groups.values()))]
    metrics = []
    for name, material in {**BASES, 'cobbles_material': 'cobbles'}.items():
        path = STUDY / 'runtime_x2/materials' / f'{material}.png'
        pixels = np.asarray(Image.open(path).convert('RGB'), dtype=float)
        for axis in ('x', 'y'):
            edge = pixels[:, -1] - pixels[:, 0] if axis == 'x' else pixels[-1] - pixels[0]
            inside = np.diff(pixels, axis=1 if axis == 'x' else 0)
            metrics.append({'tile': name, 'material': material, 'axis': axis, 'size': 256,
                            'boundary_mean_abs_rgb': float(np.abs(edge).mean()),
                            'internal_mean_abs_rgb': float(np.abs(inside).mean()),
                            'ratio': float(np.abs(edge).mean()/np.abs(inside).mean()),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'status': 'diagnostic_only_not_a_visual_seam_pass'})
    save_json('mask_inventory.json', {'mask_count': len(masks), 'polarity': 'white=foreground; black=dirt',
              'orientation': 'north up, no rotation/mirroring; edge profiles read N/S left-to-right, E/W top-to-bottom',
              'masks': masks})
    save_json('adjacency_constraints.json', {'pairs': pairs, 'edge_groups': edge_groups,
              'note': 'Observed compatible joins constrain shared profiles; isolated sides still need synthetic tests.'})
    save_json('source_conflicts.json', conflicts)
    save_json('master_edge_diagnostics.json', metrics)
    if (PROJECT / 'extra_cases.json').exists():
        cases.extend(json.loads((PROJECT / 'extra_cases.json').read_text()))
    save_json('test_cases.json', cases)
    images = {name: {'original': '../mm6_new_sorpigal/' + tile['source_rgb']} for name, tile in tiles.items()}
    for name, material in {**BASES, 'cobbles_material': 'cobbles'}.items():
        images.setdefault(name, {})['master'] = f'../mm6_new_sorpigal_master_study/runtime_x2/materials/{material}.png'
    for name, record in images.items():
        candidate = f'runtime_x2/worlds/mm6/terrain_x2/{name}.png'
        if name == 'cobbles_material':
            candidate = 'material_seams/connected_v2/cobbles_256.png'
        if (PROJECT / candidate).exists():
            record['candidate'] = candidate
        mask = f'masks/connected_v4/{name}.png'
        if (PROJECT / mask).exists():
            record['mask'] = mask
    data = {'cases': cases, 'images': images, 'masks': masks}
    template = (PROJECT / 'review_template.html').read_text()
    (PROJECT / 'index.html').write_text(template.replace('__DATA__', json.dumps(data)))
    summary = {'masks': dict(Counter(m['family'] for m in masks)), 'unique_pairs': len(pairs),
               'placed_joins': sum(p['count'] for p in pairs), 'source_conflicting_pairs': len(conflicts),
               'unique_2x2': len(junctions), 'edge_groups': len(edge_groups), 'review_cases': len(cases),
               'status': 'source audit; current generation and acceptance are recorded in README.md and reports/review_v5.json'}
    save_json('audit_summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
