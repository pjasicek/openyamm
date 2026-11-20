import sys
import struct
from collections import Counter
import yaml

A = yaml.safe_load(open(sys.argv[1]))
B = yaml.safe_load(open(sys.argv[2]))


def pos(p):
    return (p['x'], p['y'], p['z'])


def ms(title, la, lb, key, show):
    ca, cb = Counter(map(key, la)), Counter(map(key, lb))
    rem, add = ca - cb, cb - ca
    if not rem and not add and len(la) == len(lb):
        return
    print('## %s: base %d, other %d; removed %d, added %d' % (title, len(la), len(lb), sum(rem.values()),
                                                              sum(add.values())))
    for sign, src, d in (('-', la, rem), ('+', lb, add)):
        seen = set()
        for x in src:
            k = key(x)
            if d.get(k) and k not in seen:
                seen.add(k)
                print('  %s %s%s' % (sign, show(x), '' if d[k] == 1 else ' x%d' % d[k]))


for sec in ('environment',):
    if A.get(sec) != B.get(sec):
        for k in set(A[sec]) | set(B[sec]):
            if A[sec].get(k) != B[sec].get(k):
                print('## %s.%s: %s -> %s' % (sec, k, str(A[sec].get(k))[:200], str(B[sec].get(k))[:200]))
if A.get('terrain') != B.get('terrain'):
    print('## terrain section differs')
SA, SB = A['initial_state'], B['initial_state']
for k in ('location',):
    if SA.get(k) != SB.get(k):
        print('## %s: %s -> %s' % (k, SA.get(k), SB.get(k)))
if SA.get('visible_outlines') != SB.get('visible_outlines'):
    print('## visible_outlines differ')
for k in ('face_attribute_overrides', 'decoration_flags'):
    if SA.get(k) != SB.get(k):
        la, lb = SA.get(k) or [], SB.get(k) or []
        print('## %s: base %d entries, other %d' % (k, len(la), len(lb)))
        ms(k, la, lb, lambda x: str(x), lambda x: str(x)[:200])


def actor_key(a):
    return (a['name'], a['monster_id'], a['monster_info_id'], pos(a['position']), a['group'], a['npc_id'],
            a['attributes'], a['hp'], a['radius'], a['move_speed'], a['carried_item_id'], a['ally'], a['unique_name_index'])


def actor_show(a):
    return ('name=%r monster_id=%d info=%d pos=%s group=%d npc=%d attr=0x%X host=%d item=%d ally=%d uniq=%d hp=%d' %
            (a['name'], a['monster_id'], a['monster_info_id'], pos(a['position']), a['group'], a['npc_id'],
             a['attributes'], a['hostility_type'], a['carried_item_id'], a['ally'], a['unique_name_index'], a['hp']) +
            ' radius=%d speed=%d sprites=%s' % (a['radius'], a['move_speed'], a['sprite_ids']))


ms('actors', SA.get('actors') or [], SB.get('actors') or [], actor_key, actor_show)


def item_id(hexs):
    raw = bytes.fromhex(hexs[:8]) if hexs else b'\0\0\0\0'
    return struct.unpack('<i', raw)[0]


def so_key(o):
    return (o['object_description_id'], o['sprite_id'], pos(o['position']), item_id(o.get('raw_containing_item_hex', '')),
            o['attributes'])


def so_show(o):
    return 'object=%d sprite=%d pos=%s item=%d attr=0x%X' % (o['object_description_id'], o['sprite_id'],
                                                             pos(o['position']),
                                                             item_id(o.get('raw_containing_item_hex', '')),
                                                             o['attributes'])


ms('sprite_objects', SA.get('sprite_objects') or [], SB.get('sprite_objects') or [], so_key, so_show)


def chest_items(c):
    raw = bytes.fromhex(c['raw_items_hex'])
    out = []
    for i in range(len(raw) // 36):
        v = struct.unpack_from('<i', raw, i * 36)[0]
        if v:
            out.append(v)
    return out


ca, cb = SA.get('chests') or [], SB.get('chests') or []
if len(ca) != len(cb):
    print('## chests count %d -> %d' % (len(ca), len(cb)))
for i in range(max(len(ca), len(cb))):
    x = ca[i] if i < len(ca) else None
    y = cb[i] if i < len(cb) else None
    if x == y:
        continue
    if x is None or y is None:
        print('  chest %d: %s -> %s' % (i, x and (x['chest_type_id'], chest_items(x)),
                                        y and (y['chest_type_id'], chest_items(y))))
        continue
    parts = []
    for k in ('chest_type_id', 'flags'):
        if x[k] != y[k]:
            parts.append('%s %s->%s' % (k, x[k], y[k]))
    ia, ib = chest_items(x), chest_items(y)
    if ia != ib:
        parts.append('items %s -> %s' % (ia, ib))
    other = [k for k in x if k not in ('chest_type_id', 'flags', 'raw_items_hex') and x[k] != y.get(k)]
    if other:
        parts.append('other fields differ: %s' % other)
    if parts:
        print('  chest %d: %s' % (i, '; '.join(parts)))

da, db = SA.get('doors') or [], SB.get('doors') or []
if da != db:
    ia = {d['door_id']: d for d in da}
    ib = {d['door_id']: d for d in db}
    out = []
    for did in sorted(set(ia) | set(ib)):
        x, y = ia.get(did), ib.get(did)
        if x is None or y is None:
            out.append('  door id %d only in %s' % (did, 'base' if x else 'other'))
            continue
        diffs = []
        for k in ('legacy_attributes', 'direction', 'move_length', 'open_speed', 'close_speed', 'state'):
            if x[k] != y[k]:
                diffs.append('%s %s->%s' % (k, x[k], y[k]))
        if len(set(x['face_ids'])) != len(set(y['face_ids'])):
            diffs.append('distinct faces %d->%d' % (len(set(x['face_ids'])), len(set(y['face_ids']))))
        if len(set(x['vertex_ids'])) != len(set(y['vertex_ids'])):
            diffs.append('distinct vertices %d->%d' % (len(set(x['vertex_ids'])), len(set(y['vertex_ids']))))
        if diffs:
            out.append('  door id %d: %s' % (did, ', '.join(diffs)))
    print('## doors (matched by door_id): base %d, other %d, slot order changed: %s' % (
        len(da), len(db), [d['door_id'] for d in da] != [d['door_id'] for d in db]))
    print('\n'.join(out))

va, vb = SA.get('variables') or {}, SB.get('variables') or {}
for k in set(va) | set(vb):
    if va.get(k) != vb.get(k):
        x, y = va.get(k) or [], vb.get(k) or []
        idx = [(i, x[i] if i < len(x) else None, y[i] if i < len(y) else None) for i in range(max(len(x), len(y)))
               if (x[i] if i < len(x) else None) != (y[i] if i < len(y) else None)]
        print('## variables.%s changed: %s' % (k, idx[:30]))
other_keys = set(SA) | set(SB)
for k in sorted(other_keys - {'location', 'visible_outlines', 'face_attribute_overrides', 'decoration_flags', 'actors',
                              'sprite_objects', 'chests', 'doors', 'variables'}):
    if SA.get(k) != SB.get(k):
        print('## initial_state.%s differs: %s -> %s' % (k, str(SA.get(k))[:300], str(SB.get(k))[:300]))
# outdoor entity initial flags
if 'entities' in A:
    fa = Counter((e['name'], pos(e['position']), e.get('initial_decoration_flag')) for e in A['entities'])
    fb = Counter((e['name'], pos(e['position']), e.get('initial_decoration_flag')) for e in B['entities'])
    if fa != fb:
        print('## entity initial_decoration_flag/entity set differs: -%s +%s' % (list((fa - fb).items())[:10],
                                                                              list((fb - fa).items())[:10]))
