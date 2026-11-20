#!/usr/bin/env python3
"""Read-only MM5 source survey; writes derived evidence beside this script."""

from collections import Counter, defaultdict
import csv
import hashlib
import html
import json
from pathlib import Path
import re
import struct

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'reference/mm4_5_world_of_xeen/unpacked'
OUTPUT = Path(__file__).resolve().parent

REGIONS = [
    ('nw', 'Alamar and Necropolis', ['A1', 'A2', 'B1', 'B2']),
    ('sw', 'Castleview and Kalindra', ['A3', 'A4', 'B3', 'B4']),
    ('nc', 'Desert of Doom and Northern Highlands', ['C1', 'C2', 'D1', 'D2']),
    ('sc', 'Sprite Forest and Southern Tower', ['C3', 'C4', 'D3', 'D4']),
    ('ne', 'Blackfang and Lakeside', ['E1', 'E2', 'F1', 'F2']),
    ('se', 'Sandcaster and Eastern Forest', ['E3', 'E4', 'F3', 'F4']),
]

SERVICES = ['Bank', 'Blacksmith', 'Guild', 'Tavern', 'Temple', 'Training']
# Explicit map-dependent service transitions verified in ScummVM locations.cpp.
# Values are destination map, arrival x/y, required legacy quest item. These are evidence, not runtime overrides.
SPECIAL = {
    (3, 8): (57, 11, 8, 40), (13, 8): (69, 7, 4, 43), (16, 8): (61, 7, 12, 41),
    (23, 8): (65, 3, 8, 42), (29, 8): (53, 11, 8, 44),
    (12, 9): (73, 0, 7, 47), (22, 9): (78, 8, 14, 48),
    (4, 13): (29, 15, 31, 35), (6, 13): (35, 15, 8, 38),
    (19, 13): (31, 31, 16, 36), (22, 13): (33, 0, 3, 37), (98, 13): (37, 7, 0, 39),
}


def load(path):
    return json.loads(path.read_text())


def save(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n')


def clean(value):
    value = re.sub(r'[\t\v\f]\d{2,3}', '', value)
    value = re.sub(r'[\x01-\x08][a-z]?', '', value)
    return ' '.join(value.split())


def stem(number):
    return f'maze{"x" if number >= 100 else "0"}{number:03}'


def square(number):
    number = number - 88 if number >= 89 else number
    return chr(65 + (number - 1) // 4) + str((number - 1) % 4 + 1)


def numberForSquare(label):
    return (ord(label[0]) - 65) * 4 + int(label[1])


def writeCsv(name, rows):
    with (OUTPUT / name).open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def logicalMap(root, blocks):
    offsets = {root: (0, 0)}
    pending = [root]
    while pending:
        current = pending.pop()
        x, y = offsets[current]
        for direction, dx, dy in [('north', 0, 16), ('east', 16, 0), ('south', 0, -16), ('west', -16, 0)]:
            neighbor = blocks[current]['neighbors'][direction]
            if neighbor <= 129:
                continue
            offset = (x + dx, y + dy)
            if neighbor in offsets:
                assert offsets[neighbor] == offset
            else:
                offsets[neighbor] = offset
                pending.append(neighbor)
    width = max(x for x, y in offsets.values()) + 16
    height = max(y for x, y in offsets.values()) + 16
    assert min(x for x, y in offsets.values()) == min(y for x, y in offsets.values()) == 0
    return offsets, width, height


def sourceEvents(number, width, height):
    events = load(SOURCE / 'events/dark_initial_state' / (stem(number) + '.evt.json'))
    text = load(SOURCE / 'text/dark' / ('a' + stem(number)[1:] + '.txt.json'))
    groups = defaultdict(list)
    for event in events:
        groups[(event['x'], event['y'])].append(event)
    sites, transfers = [], []
    for (x, y), records in sorted(groups.items()):
        spatial = 0 <= x < width and 0 <= y < height
        titles, labels, services, messages = set(), set(), set(), set()
        travel = []
        for event in records:
            opcode, parameters = event['opcode'], event['parameters']
            if opcode == 5 and len(parameters) >= 2:
                titles.add(clean(text[parameters[0]]))
                messages.add(parameters[1])
            elif opcode in (1, 2, 3, 4, 0x27, 0x29, 0x31, 0x32, 0x35) and parameters:
                if parameters[0] < len(text):
                    labels.add(clean(text[parameters[0]]))
            if opcode == 17 and parameters:
                action = parameters[0]
                if action < 6:
                    services.add(SERVICES[action])
                if (number, action) in SPECIAL:
                    destination, destX, destY, questItem = SPECIAL[number, action]
                    travel.append(dict(destination=destination, arrival=[destX, destY],
                                       kind='keyed service entrance', questItem=questItem,
                                       eventOffset=event['offset'], line=event['line']))
                elif action >= 6:
                    labels.add({12: 'Cross-world pyramid (MM4 boundary)', 8: 'Keyed tower entrance',
                                9: 'Keyed dungeon entrance', 13: 'Town gate'}.get(action, f'Location action {action}'))
            if opcode in (7, 31, 52) and len(parameters) >= 3:
                destination = parameters[0]
                arrival = [value if value < 128 else value - 256 for value in parameters[1:3]]
                travel.append(dict(destination=destination, arrival=arrival,
                                   kind={7: 'teleport/exit', 31: 'teleport/continue', 52: 'fall'}[opcode],
                                   eventOffset=event['offset'], line=event['line']))
        titles.discard('')
        labels = {value for value in labels if value and value != 'Nothing here.'}
        site = dict(map=number, x=x, y=y, spatial=spatial, npcTitles=sorted(titles),
                    services=sorted(services), labels=sorted(labels), dialogueTextIndices=sorted(messages),
                    eventRecords=len(records), transfers=travel)
        sites.append(site)
        for transfer in travel:
            transfers.append(dict(source=number, x=x, y=y, spatial=spatial, **transfer))
    return sites, transfers, len(events)


def mapImage(number, blocks, offsets, width, height, sites):
    scale = 12
    image = Image.new('RGB', (width * scale + 1, height * scale + 33), '#272a30')
    draw = ImageDraw.Draw(image)
    draw.text((4, 5), f'{number}: {blocks[number].get("name", "")} ({width} x {height})', fill='white')
    for block, (dx, dy) in offsets.items():
        for y, row in enumerate(blocks[block]['cells']):
            for x, cell in enumerate(row):
                px, py = (dx + x) * scale, (height - 1 - dy - y) * scale + 32
                if blocks[number]['outdoors']:
                    terrain = blocks[block]['surfaceTypes'][cell['layers'][0]] & 15
                    colors = ['#356184', '#98866a', '#567b45', '#d2dade', '#56654b', '#b64021', '#d4b976',
                              '#988063', '#243b65', '#a29b8a', '#263247', '#bea783', '#414b43', '#f3f1e8',
                              '#554333', '#10141e']
                    color = colors[terrain]
                    wall = blocks[block]['wallTypes'][cell['layers'][1]]
                    if wall in (2, 3, 8, 13, 14, 15):
                        color = '#315e3a' if wall == 3 else '#56794b'
                    elif wall in (1, 7, 9, 10, 12):
                        color = '#bbc3c9' if wall == 7 else '#69463b' if wall == 10 else '#686761'
                    elif wall in (5, 6):
                        color = '#839990'
                else:
                    color = '#454b54'
                draw.rectangle((px, py, px + scale - 1, py + scale - 1), fill=color, outline='#343b43')
                if not blocks[number]['outdoors']:
                    lines = [(px, py, px + scale, py), (px + scale, py, px + scale, py + scale),
                             (px, py + scale, px + scale, py + scale), (px, py, px, py + scale)]
                    walls = [(cell['word'] >> shift) & 15 for shift in (12, 8, 4, 0)]
                    for value, line in zip(walls, lines):
                        if value:
                            draw.line(line, fill='#deded6' if value == 1 else '#d0ad55')
    for site in sites:
        if not site['spatial']:
            continue
        px, py = site['x'] * scale + scale // 2, (height - 1 - site['y']) * scale + scale // 2 + 32
        color = '#64ffff' if site['services'] else '#ffff70' if site['npcTitles'] else '#ff7cd4'
        if site['services'] or site['npcTitles'] or site['transfers']:
            draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=color)
    folder = OUTPUT / 'plans'
    folder.mkdir(exist_ok=True)
    image.save(folder / f'{number:03}.png')


def main():
    blocks = {m['mazeNumber']: m for path in (SOURCE / 'maps/dark_initial_state').glob('*.dat.json')
              for m in [load(path)]}
    maps, allSites, allTravel, chunkRows = [], [], [], []
    owner = {}
    for number in range(1, 130):
        offsets, width, height = logicalMap(number, blocks)
        for block, (x, y) in offsets.items():
            assert block not in owner
            owner[block] = number
            chunkRows.append(dict(block=block, logicalMap=number, name=blocks[number]['name'], x=x, y=y))
        sites, travel, records = sourceEvents(number, width, height)
        for site in sites:
            site['mapName'] = blocks[number]['name']
        allSites.extend(sites)
        allTravel.extend(travel)
        physicalSites = [site for site in sites if site['spatial']]
        category = ('surface' if number <= 24 else 'plane' if number <= 28 else
                    'sky' if 89 <= number <= 112 else 'town' if number in (29, 31, 33, 35, 37) else 'interior')
        terrain = Counter()
        if blocks[number]['outdoors']:
            for row in blocks[number]['cells']:
                terrain.update(blocks[number]['surfaceTypes'][cell['layers'][0]] for cell in row)
        maps.append(dict(id=number, name=blocks[number]['name'], scope='MM5' if number <= 112 else 'WoX bonus',
                         category=category, width=width, height=height, blocks=sorted(offsets),
                         neighbors=blocks[number]['neighbors'], terrainCounts=dict(terrain),
                         npcSites=sum(bool(s['npcTitles']) for s in physicalSites),
                         serviceSites=sum(bool(s['services']) for s in physicalSites),
                         npcOrServiceSites=sum(bool(s['npcTitles'] or s['services']) for s in physicalSites),
                         eventSites=len(physicalSites), helperScriptSites=len(sites) - len(physicalSites),
                         eventRecords=records, square=square(number) if category in ('surface', 'sky') else '',
                         plan=f'plans/{number:03}.png'))
        mapImage(number, blocks, offsets, width, height, sites)
    assert set(owner) == set(blocks) == set(range(1, 184))
    byId = {m['id']: m for m in maps}
    for travel in allTravel:
        travel['sourceName'] = byId[travel['source']]['name']
        travel['destinationName'] = byId.get(travel['destination'], {}).get('name', 'dynamic/mirror/fall destination')
        travel['scope'] = byId[travel['source']]['scope']
    regions = []
    for key, name, squares in REGIONS:
        numbers = [numberForSquare(s) for s in squares]
        sites = [s for s in allSites if s['map'] in numbers and s['spatial']]
        entrances = [t for t in allTravel if t['source'] in numbers and t['spatial']
                     and t['destination'] not in numbers and t['destination'] != 0]
        towns = {'sw': [29], 'se': [31], 'ne': [33], 'nw': [35]}.get(key, [])
        regions.append(dict(id=key, name=name, squares=squares, sourceMaps=numbers, skyMaps=[n + 88 for n in numbers],
                            townMaps=towns, npcSites=sum(bool(s['npcTitles']) for s in sites),
                            eventSites=len(sites),
                            destinationMaps=sorted({t['destination'] for t in entrances}),
                            directEntranceSites=len({(t['source'], t['x'], t['y']) for t in entrances})))
    mirrors = []
    data = (SOURCE / 'raw/dark/darkmirr.txt').read_bytes()
    assert len(data) % 32 == 0
    for pos in range(0, len(data), 32):
        record = data[pos:pos + 32]
        mirrors.append(dict(word=record[:28].split(b'\0')[0].decode('cp437'),
                            destination=record[28], x=struct.unpack('b', record[29:30])[0],
                            y=struct.unpack('b', record[30:31])[0], direction=struct.unpack('b', record[31:32])[0]))
    regionBySquare = {square: key for key, _, squares in REGIONS for square in squares}
    seams = []
    for number in range(1, 25):
        maze = blocks[number]
        for direction in ('east', 'south'):
            neighbor = maze['neighbors'][direction]
            if not neighbor or regionBySquare[square(number)] == regionBySquare[square(neighbor)]:
                continue
            roadCells = []
            for cell in range(16):
                coordinates = ((15, cell), (0, cell)) if direction == 'east' else ((cell, 0), (cell, 15))
                surfaces = [blocks[n]['surfaceTypes'][blocks[n]['cells'][y][x]['layers'][0]]
                            for n, (x, y) in zip((number, neighbor), coordinates)]
                if all(surface in (7, 11) for surface in surfaces):
                    roadCells.append(cell)
            seams.append(dict(source=number, sourceSquare=square(number), destination=neighbor,
                              destinationSquare=square(neighbor), direction=direction,
                              sourceRegion=regionBySquare[square(number)],
                              destinationRegion=regionBySquare[square(neighbor)],
                              roadCrossings=roadCells,
                              note='Terrain road codes on both sides only; not a complete passability test'))
    summary = dict(logicalMaps=129, mm5LogicalMaps=112, woxBonusLogicalMaps=17, gridBlocks=len(blocks),
                   continuationBlocks=len(blocks) - len(maps),
                   mm5GridBlocks=sum(len(m['blocks']) for m in maps if m['scope'] == 'MM5'),
                   mm5Categories=dict(Counter(m['category'] for m in maps if m['scope'] == 'MM5')),
                   townMetrics=[m for m in maps if m['category'] == 'town'],
                   bounds='MM5 only; WoX bonus records inventoried separately; no MM4 survey',
                   caveat='Static records: conditional branches are not simulated. NPC sites are not physical house counts.')
    save('inventory.json', dict(summary=summary, maps=maps, regions=regions, sites=allSites,
                                transfers=allTravel, mirrorDestinations=mirrors, chunkOwnership=chunkRows,
                                regionalSeams=seams))
    writeCsv('maps.csv', [{k: '|'.join(map(str, v)) if k == 'blocks' else v for k, v in m.items()
                           if k not in ('neighbors', 'terrainCounts')} for m in maps])
    writeCsv('chunks.csv', chunkRows)
    writeCsv('region_boundaries.csv', seams)
    writeCsv('travel.csv', [{k: v for k, v in t.items() if k != 'questItem'} for t in allTravel])
    writeCsv('sites.csv', [dict(map=s['map'], mapName=s['mapName'], x=s['x'], y=s['y'], spatial=s['spatial'],
                               npc=' | '.join(s['npcTitles']), services=' | '.join(s['services']),
                               labels=' | '.join(v[:160] for v in s['labels'])) for s in allSites])
    files = [SOURCE / 'extraction_manifest.json'] + list((SOURCE / 'raw/dark_initial_state').glob('*'))
    save('provenance.json', dict(sources=[dict(path=str(f.relative_to(ROOT)),
                                            sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files],
                                  basis='Local GOG game data; ScummVM scripts/locations/map behavior for interpretation'))
    lines = ['# MM5 logical map inventory', '',
             'Reconstructed from original DAT neighbor links and original map-name records. '
             'Cells are source-grid cells, not OpenYAMM units. All 183 DAT blocks have exactly one logical owner.', '',
             '| Map | Original name | Dimensions | Storage blocks | Proposed treatment |',
             '| ---: | --- | --- | --- | --- |']
    for m in maps:
        category = m['category']
        treatment = ('Excluded: WoX bonus' if m['scope'] != 'MM5' else
                     'Merge into surface region ' + regionBySquare[m['square']].upper() if category == 'surface' else
                     'Separate sky layer, region ' + regionBySquare[m['square']].upper() if category == 'sky' else
                     'Standalone elemental plane' if category == 'plane' else
                     'Town district / gated location; see assessment' if category == 'town' else
                     'Interior complex; see assessment')
        lines.append(f'| {m["id"]} | [{m["name"]}]({m["plan"]}) | {m["width"]}×{m["height"]} | '
                     f'{", ".join(map(str, m["blocks"]))} | {treatment} |')
    (OUTPUT / 'MAP_INVENTORY.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
