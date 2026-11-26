"""Xeen map rows: map_stats.txt, bolster_maps.txt and outdoor_travels.txt from source/maps.yml (the orchestrator's
registry: ids, stems, names, treasure levels, music, neighbours) and source/map_rows.yml (A2's: spawn slots, lock,
trap, perception, environment and the rest of each row).

The row shape is the one `oymap install` wrote for maps 9130-9140 (output/studio_play/xeen_root/engine/data_tables/
map_stats.txt). Spawn slots name a Xeen family (its descriptor family, "Xeen Goblin") or, on a built map not yet
rebased, the installed family it was built with.
"""

from __future__ import annotations

import re

import xeenlib
from xeenlib import BuildError

ROWS = 'map_rows.yml'
DIRECTIONS = {
    # direction: (column group in outdoor_travels: 0 Up, 1 Down, 2 Left, 3 Right; the side the party arrives by)
    'north': (0, 'down'),
    'south': (1, 'up'),
    'west': (2, 'left'),     # MMerge's "left" enters by the east edge (MapStats.cpp parseMergedOutdoorTravelSide)
    'east': (3, 'right'),
}


def leading_int(value, default=0):
    match = re.match(r'\s*(\d+)', str(value)) if value is not None else None
    return int(match.group(1)) if match else default


def included_maps(ctx, mode, per_map):
    """Maps built or installed in the world, and maps whose map_rows.yml entry sets `row_before_install` (a map lane
    tests the map from a scratch root before installing it; the game cannot load a map without its map_stats row)."""
    maps_dir = xeenlib.WORLD / 'maps'
    result = []
    for entry in ctx.maps:
        early = (per_map.get(entry['key']) or {}).get('row_before_install')
        if mode == 'all' or early or entry.get('built_as_mm7_stand_in') or (maps_dir / entry['stem']).exists():
            result.append(entry)
    return result


def slot_cells(slot, families, where):
    if 'family' in slot:
        family = families.get(slot['family'])
        if family is None:
            raise BuildError(f"{where}: no monster family {slot['family']!r} in monsters.yml")
        name = family['picture']
    elif 'monster' in slot:
        name = slot['monster']
    else:
        raise BuildError(f'{where}: a slot names a family or a monster')
    low, high = slot.get('count', [2, 3])
    return [name, name, slot.get('tier', 1), f' {low}-{high}'], slot.get('weight', 0)


def build(ctx):
    rows_source = ctx.load_source(ROWS)
    defaults = rows_source.get('defaults') or {}
    per_map = rows_source.get('maps') or {}
    families = ctx.shared.get('families') or {}
    sources = ['source/maps.yml', f'source/{ROWS}']

    known_keys = {entry['key'] for entry in ctx.maps}
    for key in per_map:
        if key not in known_keys:
            raise BuildError(f'{ROWS}: map {key} is not in maps.yml')

    # Engine award rows reworded while the party is in Xeen (award_texts, mode override; the Warzone's 46-49, D-39).
    award_texts = ctx.table('english/award_texts.txt', sources=[f'source/{ROWS}'], contribution='award_texts',
                            engine='english/awards.txt', header_rows=1, rewords=True)
    for entry in rows_source.get('award_texts') or []:
        if not isinstance(entry.get('id'), int) or not entry.get('text'):
            raise BuildError(f'{ROWS} award_texts: a row needs id and text ({entry!r})')
        award_texts.add([entry['id'], entry['text'], entry.get('sort'), entry.get('note')],
                        origin=f"award_texts {entry['id']}")

    stats = ctx.table('map_stats.txt', sources=sources, domain='maps', engine='map_stats.txt', header_rows=3)
    bolster = ctx.table('bolster_maps.txt', sources=sources, domain='maps', engine='bolster_maps.txt', header_rows=1)
    travels = ctx.table('outdoor_travels.txt', sources=sources, engine='outdoor_travels.txt', header_rows=1,
                        numeric_key=False)

    maps = included_maps(ctx, rows_source.get('include', 'built'), per_map)
    by_key = {entry['key']: entry for entry in maps}
    lock_trap = {int(key): value for key, value in (defaults.get('lock_trap_by_treasure') or {}).items()}

    for entry in maps:
        key = entry['key']
        where = f"maps.yml {key}"
        extra = per_map.get(key) or {}
        treasure = leading_int(entry.get('treasure'))
        lock, trap = lock_trap.get(treasure, [0, 0])
        lock = extra.get('lock', lock)
        trap = extra.get('trap', trap)
        perception = extra.get('perception', lock)
        music = entry.get('music') if entry.get('music') is not None else extra.get('music')
        if music is None:
            ctx.warn(f'{key}: no music (maps.yml music is null and map_rows.yml has no fallback)')
        kind = entry.get('kind', 'blv')
        environment = extra.get('environment') or (defaults.get('environment') or {}).get(kind, 'STONEROOM')

        slots = extra.get('slots') or []
        if len(slots) > 3:
            raise BuildError(f'{ROWS} {key}: at most three spawn slots')
        slot_rows = []
        weights = []
        for index, slot in enumerate(slots):
            cells, weight = slot_cells(slot, families, f'{ROWS} {key} slot {index + 1}')
            slot_rows.append(cells)
            weights.append(weight)
        if weights and sum(weights) != 100:
            ctx.warn(f'{key}: slot weights add to {sum(weights)}, not 100')
        while len(slot_rows) < 3:
            slot_rows.append([0, 0, 0, 0])
            weights.append(0)
        if not slots and kind != 'open_air_blv' and leading_int(entry.get('monsters')) > 0:
            ctx.warn(f'{key}: no spawn slots in map_rows.yml')

        row = [entry['map_id'], entry['name'], entry['stem'], 0, 0, perception,
               extra.get('refill_days', defaults.get('refill_days', 672)),
               extra.get('alert_days', defaults.get('alert_days', 0)),
               extra.get('steal_perm', defaults.get('steal_perm', 0)),
               lock, trap, treasure, extra.get('encounter_chance', defaults.get('encounter_chance', 10))]
        row += weights
        for cells in slot_rows:
            row += cells
        # world_id (column 34) stays empty: the loader fills it with the contributing world (TABLES.md).
        row += [music if music is not None else 0, environment, 'map_studio', 0, 0, '-', '']
        stats.add(row, origin=key)

        settings = dict(defaults.get('bolster') or {})
        settings.update(extra.get('bolster') or {})
        outdoors = kind == 'odm'
        face = (str(entry.get('face', '')).split() or [''])[0]
        continent = (defaults.get('continents') or {}).get(face)
        if continent is None:
            raise BuildError(f"map_rows.yml defaults.continents: no continent for face {entry.get('face')!r} "
                             f"({entry.get('key')})")
        # The engine reads the Rain column as "rain unless `-`" (MergedBaseTables.cpp), so `rain: false` writes `-`;
        # an empty cell (or `rain: true`'s `x`) lets it rain. A snow-and-ice map never rains (D-184, X5 p14).
        rain = settings.get('rain')
        if settings.get('snow') and rain is not False:
            raise BuildError(f'{ROWS} {key}: bolster `snow: true` needs `rain: false` (D-184: a snow map never rains)')
        bolster.add([entry['map_id'], entry['name'], continent, settings.get('kind', 'LowerToEqual'),
                     bool(settings.get('spells', True)), bool(settings.get('summons', False)),
                     bool(settings.get('weather', outdoors)), settings.get('extra', 0),
                     settings.get('profs_max_rarity', 0), settings.get('sky', ''),
                     '-' if rain is False else ('x' if rain else ''), 'x' if settings.get('snow') else ''],
                    origin=key)

    days_default = (defaults.get('travel_days') or {}).get('default', 5)
    days_wild = (defaults.get('travel_days') or {}).get('wilderness', 7)
    exceptions = {}
    for item in rows_source.get('travel_days') or []:
        left, right = item['between']
        exceptions[frozenset((left, right))] = item['days']

    # A travel row joins two maps installed in the world only: an edge toward an unbuilt neighbour gets none (the map
    # lane seals that edge with a sign).
    maps_dir = xeenlib.WORLD / 'maps'
    for entry in maps:
        if entry.get('kind') != 'odm' or not (maps_dir / entry['stem']).exists():
            continue
        groups = [['', '', ''] for _ in range(4)]
        linked = False
        # `no_travel` (map_rows.yml): edges the map leaves by its own device instead (X3's north: a step plate and a
        # barrier, D-11.6).
        closed = set((per_map.get(entry['key']) or {}).get('no_travel') or [])
        for direction, target_key in (entry.get('neighbours') or {}).items():
            if direction not in DIRECTIONS or direction in closed:
                continue
            target = by_key.get(target_key)
            if target is None or target.get('kind') != 'odm' or not (maps_dir / target['stem']).exists():
                continue
            column, side = DIRECTIONS[direction]
            days = exceptions.get(frozenset((entry['key'], target_key)))
            if days is None:
                wild = 'wilderness' in str(entry.get('role')) or 'wilderness' in str(target.get('role'))
                days = days_wild if wild else days_default
            groups[column] = [target['stem'], side, days]
            linked = True
        if not linked:
            continue
        row = [entry['stem']]
        for group in groups:
            row += group
        row += ['', entry['name'], '', '', '', '']
        travels.add(row, origin=entry['key'])

    edge_spans(ctx, maps, exceptions, days_default, days_wild, per_map)
    dimension_doors(ctx)


EDGE_SIDES = {direction: side for direction, (_, side) in DIRECTIONS.items()}
EDGE_HALF = 32768   # an ODM edge runs from -32768 to 32768 along x (north and south) or y (west and east)


def named_arrival(entry, name):
    """[x, y, z] and facing of a named arrival (`entrance:<id>`) of an installed map, from the `arrivals` list
    `oymap install` writes into its <stem>.studio.yml (D-4)."""
    path = xeenlib.WORLD / 'maps' / (entry['stem'].rsplit('.', 1)[0] + '.studio.yml')
    data = xeenlib.load_yaml(path) if path.exists() else None
    for arrival in (data or {}).get('arrivals') or []:
        if arrival.get('name') == name:
            return arrival.get('at'), arrival.get('facing')
    raise BuildError(f"{ROWS} {entry['key']} arrivals: {name} is not a named arrival of {path.name}")


def edge_spans(ctx, maps, exceptions, days_default, days_wild, per_map):
    """data_tables/edge_spans.yml (A1's world table for split edges, D-11.6): one entry per stretch of a map's edge
    with its own destination. From maps.yml: a map's `edge_spans` ({edge: [{from, to, map, at, facing}]}, `from`/`to`
    in map units along the edge) and its `arrivals` ({neighbour: {at, facing}}: the neighbour's whole edge toward this
    map lands there); from map_rows.yml a map's `arrivals` ({neighbour: entrance:<id>}, a named arrival of the
    installed map, or {at, facing}). Written only between two maps installed in the world, as the travel rows are."""
    maps_dir = xeenlib.WORLD / 'maps'
    by_key = {entry['key']: entry for entry in maps}

    def installed(entry):
        return entry is not None and entry.get('kind') == 'odm' and (maps_dir / entry['stem']).exists()

    def days_between(left, right):
        days = exceptions.get(frozenset((left['key'], right['key'])))
        if days is None:
            wild = 'wilderness' in str(left.get('role')) or 'wilderness' in str(right.get('role'))
            days = days_wild if wild else days_default
        return days

    def span(entry, edge, low, high, target, at=None, facing=None):
        if edge not in DIRECTIONS:
            raise BuildError(f"maps.yml {entry['key']}: edge {edge!r} is not north, south, west or east")
        if not -EDGE_HALF <= low < high <= EDGE_HALF:
            raise BuildError(f"maps.yml {entry['key']} {edge}: span {low}..{high} is not inside the edge")
        item = {'map': entry['stem'], 'edge': edge, 'from': low, 'to': high, 'to_map': target['stem'],
                'side': EDGE_SIDES[edge], 'days': days_between(entry, target)}
        if at is not None:
            if len(at) != 3:
                raise BuildError(f"maps.yml {entry['key']} {edge}: `at` is [x, y, z]")
            item['at'] = [int(value) for value in at]
            item['facing'] = int(facing or 0)
        return item

    result = []
    for entry in maps:
        if not installed(entry):
            continue
        for edge, spans in (entry.get('edge_spans') or {}).items():
            for item in spans:
                target = by_key.get(item['map'])
                if installed(target):
                    result.append(span(entry, edge, item['from'], item['to'], target, item.get('at'),
                                       item.get('facing')))
        arrivals = dict(entry.get('arrivals') or {})
        for neighbour_key, arrival in ((per_map.get(entry['key']) or {}).get('arrivals') or {}).items():
            if neighbour_key in arrivals:
                raise BuildError(f"{ROWS} {entry['key']} arrivals: {neighbour_key} is in maps.yml's arrivals too")
            arrivals[neighbour_key] = arrival
        for neighbour_key, arrival in arrivals.items():
            neighbour = by_key.get(neighbour_key)
            if not installed(neighbour):
                continue
            if isinstance(arrival, str):
                at, facing = named_arrival(entry, arrival)
                arrival = {'at': at, 'facing': facing}
            edges = [edge for edge, key in (neighbour.get('neighbours') or {}).items() if key == entry['key']]
            if len(edges) != 1:
                raise BuildError(f"maps.yml {entry['key']} arrivals: {neighbour_key} has {len(edges)} edges toward it")
            result.append(span(neighbour, edges[0], -EDGE_HALF, EDGE_HALF, entry, arrival.get('at'),
                               arrival.get('facing')))
    if not result:
        return
    result.sort(key=lambda item: (item['map'], list(DIRECTIONS).index(item['edge']), item['from']))
    lines = ['# One map edge, several destinations (DECISIONS D-11.6; A1\'s table, lanes/A1.md): a span runs from `from`',
             '# to `to` in map units along the edge (x for north and south, y for west and east); `side` and `days` as',
             "# outdoor_travels; `at` and `facing` the arrival on `to_map` (else the side's default).",
             'edge_spans:']
    for item in result:
        cells = [f"{key}: [{', '.join(str(number) for number in value)}]" if isinstance(value, list)
                 else f'{key}: {value}' for key, value in item.items()]
        lines.append('  - {' + ', '.join(cells) + '}')
    ctx.text('data_tables/edge_spans.yml', '\n'.join(lines) + '\n', sources=['source/maps.yml'])


DOORS = 'dimension_doors.yml'
DOORS_MARKER = '# --- generated content below ---\n'


def dimension_doors(ctx):
    """data_tables/dimension_doors.yml (the world's `dimension_doors` contribution, TABLES.md "Dimension Door"): the
    part of source/dimension_doors.yml below its marker line, as written; each landing map must be in maps.yml."""
    path = xeenlib.SOURCE / DOORS
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if DOORS_MARKER not in text:
        raise BuildError(f'source/{DOORS}: no line {DOORS_MARKER.strip()!r}')
    content = text.split(DOORS_MARKER, 1)[1]
    data = xeenlib.load_yaml(path) or {}
    stems = {entry['stem'].lower() for entry in ctx.maps}
    for door in data.get('doors') or []:
        for landing in door.get('landings') or []:
            if str(landing.get('map', '')).lower() not in stems:
                raise BuildError(f"source/{DOORS}: door {door.get('key')}: landing map {landing.get('map')} is not in "
                                 'maps.yml')
    ctx.text(f'data_tables/{DOORS}', content, sources=[f'source/{DOORS}'])
