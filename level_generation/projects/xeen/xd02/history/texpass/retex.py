#!/usr/bin/env python3
"""XD-02 texture pass (2026-11-13): one-off edit of rooms.yml and objects.yml.

Families: the workings, caves and camp from MM6 Snergle's Caverns (6d05); the Red Dwarves' worked rooms (chapel,
tally room and steps, strongroom) from MM6 Snergle's Iron Mines (6d09); three mine things the Snergle maps lack from
MM7's own Red Dwarf Mines (7d34): the gold seam c1gold, the iron ch004i, the bedding t2bedsht. Chests take the
shipped chest set ch1* (6d09's own chests). Text substitution line by line; run once on the pass-1 files.
"""
import re
import sys

L4 = sys.argv[1]

THEMES = '''themes:
  - id: theme:camp
    wall: {texture: t3ll5, size: [256, 256]}
    floor: {texture: t3oor1, size: [128, 128]}
    ceiling: {texture: d2ceil2, size: [256, 256]}
    reveal: {texture: t3d2abs, size: [32, 256]}
    door: {texture: t3dr1, size: [256, 256], fit: true}
    notes: "The clan's camp in old workings (Snergle's Caverns 6d05, its barrack rooms): red rock, red earth floor, plank ceiling on beams, timber jambs, 6d05's own plank door."
  - id: theme:cave
    wall: {texture: crstont, size: [256, 256]}
    floor: {texture: d2ceil4, size: [256, 256]}
    ceiling: {texture: crdrf1, size: [128, 128]}
    reveal: {texture: crstont, size: [256, 256]}
    notes: "Natural rock the miners broke into (6d05's caverns): blue-grey cave stone, dark rock floor, gravel roof. The chasm, the spider galleries, the grottoes, the burrow."
  - id: theme:drowned_cave
    wall: {texture: crstont, size: [256, 256]}
    floor: {texture: 6wtrtyl, size: [128, 128]}
    ceiling: {texture: crdrf1, size: [128, 128]}
    reveal: {texture: crstont, size: [256, 256]}
    notes: "The flooded working: cave stone over standing water (6d05's own water, marked water in objects.yml)."
  - id: theme:drowned_line
    wall: {texture: t3ll6, size: [256, 256]}
    floor: {texture: 6wtrtyl, size: [128, 128]}
    ceiling: {texture: t3ll6, size: [256, 256]}
    reveal: {texture: t3d2abs, size: [32, 256]}
    notes: "The drowned east line: 6d05's tunnel rock over 6d05's water."
  - id: theme:dwarf_chapel
    wall: {texture: d7wl1ctr, size: [256, 256]}
    floor: {texture: d7flor4, size: [128, 128]}
    ceiling: {texture: d7ceil2, size: [128, 128]}
    reveal: {texture: d7trim8, size: [64, 64]}
    door: {texture: d7dor1, size: [256, 256], fit: true}
    notes: "The Red Dwarves' chapel (Snergle's Iron Mines 6d09): dwarf block walls under a carved frieze, rune-tiled floor, carved ceiling, dressed stone jambs, kerb and pillars."
  - id: theme:dwarf_hall
    wall: {texture: d7wl2ctr, size: [256, 256]}
    floor: {texture: d7flor4, size: [128, 128]}
    ceiling: {texture: d7ceil2, size: [128, 128]}
    reveal: {texture: d7trim8, size: [64, 64]}
    door: {texture: d7dor2, size: [256, 256], fit: true}
    notes: "The Red Dwarves' worked rooms (6d09): rough-dressed stone under a dressed course, rune tiles, carved ceiling, iron-studded double door."
  - id: theme:dwarf_vault
    wall: {texture: d7trim8, size: [64, 64]}
    floor: {texture: d7flor4, size: [128, 128]}
    ceiling: {texture: mnwl2, size: [256, 256]}
    reveal: {texture: d7trim8, size: [64, 64]}
    notes: "The Red Dwarves' vault (6d09): dressed blocks, rune tiles, smooth rock roof; no timber (its secret wall shows no frame)."
  - id: theme:pit
    wall: {texture: t3ll6, size: [256, 256]}
    floor: {texture: d2ceil4, size: [256, 256]}
    ceiling: {texture: crdrf1, size: [128, 128]}
    reveal: {texture: t3ll6, size: [256, 256]}
    notes: "The Open Stope's raw pit faces (6d05's tunnel rock), dark rock floor, gravel roof; its benches are cut red rock (t3ll5) with earth tops."
  - id: theme:red_workings
    wall: {texture: t3ll5, size: [256, 256]}
    floor: {texture: t3oor1, size: [128, 128]}
    ceiling: {texture: t3ll6, size: [256, 256]}
    reveal: {texture: t3d2abs, size: [32, 256]}
    notes: "Worked chambers without lagging (6d05): red worked face, red earth floor, dark rock roof; gold seams are switches in c1gold."
  - id: theme:rock_tunnel
    wall: {texture: t3ll6, size: [256, 256]}
    floor: {texture: d2ceil4, size: [256, 256]}
    ceiling: {texture: t3ll6, size: [256, 256]}
    reveal: {texture: t3d2abs, size: [32, 256]}
    notes: "Untimbered tunnels and the deep line (6d05's tunnels): dark grained rock on walls and roof, dark rock floor."
  - id: theme:timbered_room
    wall: {texture: t3ll5, size: [256, 256]}
    floor: {texture: t3oor1, size: [128, 128]}
    ceiling: {texture: d2ceil1, size: [256, 256]}
    reveal: {texture: t3d2abs, size: [32, 256]}
    door: {texture: t3dr1, size: [256, 256], fit: true}
    notes: "Timbered chambers (6d05's rooms): red worked face, red earth floor, plank lagging on beams, timber jambs, plank door."
  - id: theme:timbered_tunnel
    wall: {texture: t3ll6, size: [256, 256]}
    floor: {texture: t3oor1, size: [128, 128]}
    ceiling: {texture: d2ceil1, size: [256, 256]}
    reveal: {texture: t3d2abs, size: [32, 256]}
    door: {texture: t3dr1, size: [256, 256], fit: true}
    notes: "Timbered drifts (6d05's tunnels): dark grained rock, red earth floor, plank lagging over the timber sets."
'''

ROOM_THEME = {
    'adit_mouth': 'timbered_room', 'top_station': 'timbered_room', 'lamp_room': 'timbered_room',
    'east_landing': 'timbered_room', 'west_line_landing': 'timbered_room', 'repair_niche': 'timbered_room',
    'main_drift': 'timbered_tunnel', 'foot_drift': 'timbered_tunnel', 'foot_incline': 'timbered_tunnel',
    'foot_bend': 'timbered_tunnel', 'west_line': 'timbered_tunnel', 'west_line_upper': 'timbered_tunnel',
    'collapsed_adit': 'timbered_tunnel',
    'sorting_floor': 'red_workings', 'chute_1': 'red_workings', 'chute_2': 'red_workings', 'chute_3': 'red_workings',
    'turntable': 'red_workings', 'stope_rim': 'red_workings',
    'stope_gallery': 'rock_tunnel', 'crawl': 'rock_tunnel', 'deep_ramp': 'rock_tunnel', 'deep_mouth': 'rock_tunnel',
    'deep_station': 'rock_tunnel',
    'east_line': 'drowned_line', 'flooded_working': 'drowned_cave',
    'mess_hall': 'camp', 'bunk_cut': 'camp', 'bunk_niche_1': 'camp', 'bunk_niche_2': 'camp', 'bunk_niche_3': 'camp',
    'stope_floor': 'pit', 'chasm': 'cave',
    'spider_galleries': 'cave', 'blue_grotto': 'cave', 'red_pool_grotto': 'cave', 'gold_hump': 'cave',
    'mole_pocket': 'cave',
    'dwarf_shrine': 'dwarf_chapel', 'chapel_steps': 'dwarf_chapel',
    'tally_room': 'dwarf_hall', 'tally_steps': 'dwarf_hall', 'forgotten_strongroom': 'dwarf_vault',
}
WORKED = {'dwarf_shrine', 'chapel_steps', 'tally_room', 'tally_steps', 'forgotten_strongroom'}

S = {  # texture: size
    't3ll5': (256, 256), 't3ll6': (256, 256), 'crstont': (256, 256), 'd2ceil4': (256, 256), 'd2ceil3': (256, 256),
    'crdrf1': (128, 128), 't3oor1': (128, 128), 'd2ceil1': (256, 256), 'd2ceil2': (256, 256), 't3d2abs': (32, 256),
    'bemh32c': (256, 32), 't3dr1': (256, 256), 'ch004i': (64, 64), 'c1gold': (256, 256), 't2bedsht': (128, 256),
    'ch1side': (64, 64), 'ch1frntb': (64, 64), 'ch1topb': (64, 64), 'd7wl1ctr': (256, 256), 'd7wl2ctr': (256, 256),
    'd7trim8': (64, 64), 'd7flor4': (128, 128), 'd7ceil2': (128, 128), 'd7dor1': (256, 256), 'd7dor2': (256, 256),
    'cbedsqr': (128, 128), 'mnwl2': (256, 256), '6wtrtyl': (128, 128),
}

SURF = re.compile(r'(\b[a-z_]+): \{texture: ([\w-]+), size: \[(\d+), (\d+)\]((?:, (?:fit|scale): [\w.]+)*)\}')


def surf(key, tex, fit=False):
    w, h = S[tex]
    return f'{key}: {{texture: {tex}, size: [{w}, {h}]{", fit: true" if fit else ""}}}'


def room_map(room, feature, line, key, tex, extra):
    """New surface text for one surface of rooms.yml, or None to keep it."""
    notes = line.lower()
    cart = ('cart' in notes and 'cable' not in notes) or 'ore cart' in notes
    worked = room in WORKED
    if tex in ('warnsign', 'runeeyvlij', 'sign22', 'sign128', 'orertlga', 'lavatyl', '7slimywtr'):
        return None
    if tex in ('beamplnv', 'd6ebeam', '7trim9_32'):
        return surf(key, 't3d2abs')
    if tex == 'beamplnh':
        return surf(key, 'bemh32c')
    if tex == 'ironn7dmbs':
        return surf(key, 'ch004i')
    if tex == '7trimd':
        if cart:
            return surf(key, 'ch1topb', fit=True)
        if worked:
            return surf(key, 'cbedsqr')
        if key == 'top_surface':
            return surf(key, 'd2ceil2')
        return surf(key, 'bemh32c')
    if tex == '7trimda':
        if worked:
            return surf(key, 'cbedsqr')
        if 'trestle' in notes and 'deck' in notes:
            return surf(key, 'd2ceil1')
        return surf(key, 'd2ceil2')
    if tex == 'cfb1':
        if 'hearth' in notes:
            return surf(key, 'd2ceil3')
        if cart or 'ore' in notes:
            return surf(key, 'crdrf1')
        return surf(key, 'd2ceil4')
    if tex == 'dirt':
        if 'spoil' in notes:
            return surf(key, 'crdrf1')
        return surf(key, 't3oor1')
    if tex == 'cwb1':
        if 'spilled ore' in notes:
            return surf(key, 'crdrf1')
        if room in ('flooded_working', 'gold_hump'):
            return surf(key, 'crstont')
        if room == 'stope_gallery':
            return surf(key, 't3ll6')
        return surf(key, 't3ll5')  # stope benches, mess hall pillars
    if tex == 'c2b':
        return surf(key, 'crstont')
    if tex == '7cdb':
        return surf(key, 'd7trim8')
    if tex == 'cwb':
        if feature == 'ceiling_levels' and key == 'surface':
            return surf(key, 'd7ceil2')
        return surf(key, 'd7trim8')
    if tex in ('7tfb11', '7tfb1'):
        return surf(key, 'd7flor4')
    if tex == '7wtrtyl':
        return surf(key, '6wtrtyl')
    if tex == 'bembllg':
        return surf(key, 't2bedsht')
    raise SystemExit(f'rooms.yml: no rule for {tex} ({key}) in {room}: {line.strip()[:120]}')


def do_rooms():
    path = f'{L4}/rooms.yml'
    lines = open(path).read().split('\n')
    out, room, feature, skip = [], None, None, False
    for line in lines:
        if line == 'themes:':
            out.extend(THEMES.rstrip('\n').split('\n'))
            skip = True
            continue
        if skip:
            if line.startswith('defaults:'):
                skip = False
                out.append('defaults: {theme: theme:red_workings, ambient: 20}')
            continue
        m = re.match(r'  - id: room:(\w+)', line)
        if m:
            room, feature = m.group(1), None
        if line.startswith('openings:'):
            room = None
        m = re.match(r'    (\w+):', line)
        if m:
            feature = m.group(1)
        if room and re.match(r'    theme: theme:', line):
            line = f'    theme: theme:{ROOM_THEME[room]}'
        if room == 'stope_floor' and feature == 'bands':
            continue  # the pit's walls are one raw face; the band of deep rock is gone
        if room:
            line = SURF.sub(lambda mm: room_map(room, feature, line, mm.group(1), mm.group(2), mm.group(5))
                            or mm.group(0), line)
        out.append(line)
    open(path, 'w').write('\n'.join(out))


VEIN_ON = {'vein_flooded': 'crstont', 'vein_rich': 't3ll6', 'vein_rim': 't3ll5', 'vein_se': 't3ll6',
           'vein_sorting': 't3ll5', 'vein_sw': 't3ll6'}


def obj_map(item, line, key, tex, part=False):
    if item.startswith('door:gate_') or item == 'door:hoist_gate':
        return surf(key, 'd2ceil1', fit=True)
    if item.startswith('door:vent_'):
        return surf(key, 't3dr1', fit=True)
    if item == 'door:mole_rock':
        return surf(key, 't3ll6')
    if item == 'door:strongroom':
        return surf(key, 'd7trim8')
    if item in ('door:web_wall', 'chest:cocoon', 'exit:x1', 'exit:x4'):
        return None
    if item == 'exit:deep':
        return surf(key, 't3ll6')
    if item.startswith('chest:'):
        if key == 'top_surface':
            return surf(key, 'ch1topb', fit=True)
        return surf(key, 'ch1frntb', fit=True)
    if item.startswith('switch:vein_'):
        return surf(key, 'c1gold')
    if item.startswith('switch:'):
        return surf(key, 'ch004i' if tex == 'ironn7dmbs' else 't3d2abs')
    if item.startswith('mover:'):
        if tex == 'ironn7dmbs':
            return surf(key, 'ch004i')
        if tex in ('d6ebeam', 'beamplnv'):
            return surf(key, 't3d2abs')
        if tex == 'beamplnh':
            return surf(key, 'bemh32c')
        if tex == 'cwb1':
            return surf(key, 't3ll6')
        if tex == 'cfb1':
            return surf(key, 'crdrf1')
        if tex == '7trimda':
            return surf(key, 'd2ceil2')
        if tex == '7trimd':
            if part:  # the carts' side boards
                return surf(key, 'bemh32c' if key == 'top_surface' else 'ch1topb', fit=key != 'top_surface')
            return surf(key, 'bemh32c')  # the deck block's edges
    raise SystemExit(f'objects.yml: no rule for {tex} ({key}) in {item}: {line.strip()[:120]}')


def do_objects():
    path = f'{L4}/objects.yml'
    lines = open(path).read().split('\n')
    out, item, part = [], None, False
    for line in lines:
        m = re.match(r'  - id: ([\w:]+)', line)
        if m:
            item, part = m.group(1), False
        if line == '    parts:':
            part = True
        if re.match(r'^[a-z_]+:', line):
            item = None
        if item == 'door:chapel' and 'pictures:' in line:
            out.append(line)
            continue
        if item == 'door:chapel' and line.startswith('      - [{texture: t5d1'):
            out.append('      - [{texture: d7dor1, size: [256, 256]}]')
            continue
        if item and item.startswith('switch:vein_') and re.match(r'    on: ', line):
            out.append(f'    on: {VEIN_ON[item[7:]]}')
            continue
        new = SURF.sub(lambda mm: obj_map(item, line, mm.group(1), mm.group(2), part) or mm.group(0), line) if item else line
        out.append(new)
        if item in ('door:mole_rock', 'door:strongroom') and line.startswith('    surface:'):
            out.append('    tile: true')
        if item and item.startswith('chest:') and item != 'chest:cocoon' and line.startswith('    surface:'):
            out.append('    end_surface: {texture: ch1side, size: [64, 64], fit: true}')
    open(path, 'w').write('\n'.join(out))


do_rooms()
do_objects()
