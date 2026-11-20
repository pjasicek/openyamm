import sys
from collections import Counter, defaultdict
sys.path.insert(0, sys.argv[1])
import geo

a_path, b_path = sys.argv[2], sys.argv[3]  # a = base, b = other (maw or ours)
A = geo.parse_odm(a_path) if a_path.endswith('.odm') else geo.parse_blv(a_path)
B = geo.parse_odm(b_path) if b_path.endswith('.odm') else geo.parse_blv(b_path)


def bbox_of(points):
    pts = [p for p in points if p is not None]
    if not pts:
        return None
    xs, ys, zs = zip(*pts)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def fmt_bb(bb):
    return 'x %d..%d y %d..%d z %d..%d' % (bb[0], bb[3], bb[1], bb[4], bb[2], bb[5]) if bb else '-'


def multiset_diff(title, la, lb, key, show):
    ca = Counter(key(x) for x in la)
    cb = Counter(key(x) for x in lb)
    removed = ca - cb
    added = cb - ca
    print('## %s: base %d, other %d; removed %d, added %d' % (title, len(la), len(lb), sum(removed.values()),
                                                              sum(added.values())))
    seen = set()
    for x in la:
        k = key(x)
        if removed.get(k) and k not in seen:
            seen.add(k)
            print('  - ' + show(x) + ('' if removed[k] == 1 else ' x%d' % removed[k]))
    seen = set()
    for x in lb:
        k = key(x)
        if added.get(k) and k not in seen:
            seen.add(k)
            print('  + ' + show(x) + ('' if added[k] == 1 else ' x%d' % added[k]))


def face_key(f):
    return (tuple(sorted(v for v in f['verts'] if v is not None)), f['tex'])


def face_full(f):
    return face_key(f) + (f['attr'], f['event'])


def show_face(f, extra=''):
    return 'tex=%s attr=0x%X event=%d cog=%d nverts=%d %s %s' % (
        f['tex'], f['attr'], f['event'], f['cog'], len(f['verts']), fmt_bb(bbox_of(f['verts'])), extra)


def ent_show(e):
    return '%s desc=%d pos=%s yaw=%d event=%d trig=%d evar=%d cog=%d flags=0x%X' % (
        e['name'], e['desc'], e['pos'], e['yaw'], e['event'], e['trig'], e['evar'], e['cog'], e['flags'])


def ent_key(e):
    return (e['name'], e['pos'], e['yaw'], e['event'], e['trig'], e['evar'], e['cog'], e['flags'])


def spawn_show(sp):
    return 'pos=%s radius=%d type=%d index=%d attr=0x%X group=%d' % (sp['pos'], sp['radius'], sp['type'],
                                                                     sp['index'], sp['attr'], sp['group'])


def spawn_key(sp):
    return (sp['pos'], sp['radius'], sp['type'], sp['index'], sp['attr'], sp['group'])


COSMETIC = 0x80000000 | 0x8000 | 0x20000 | 0x10000 | 0x1000 | 0x8 | 0x80
cosmetic = Counter()


def face_changes(fa, fb, label):
    """Faces matched by geometry+texture; report geometry adds/removes and attribute/event changes."""
    ka = defaultdict(list)
    kb = defaultdict(list)
    for f in fa:
        ka[face_key(f)].append(f)
    for f in fb:
        kb[face_key(f)].append(f)
    removed = []
    added = []
    changed = []
    for k in set(ka) | set(kb):
        la, lb = ka.get(k, []), kb.get(k, [])
        n = min(len(la), len(lb))
        for i in range(n):
            x, y = la[i], lb[i]
            if ((x['attr'] ^ y['attr']) & ~COSMETIC) or x['event'] != y['event']:
                changed.append((x, y))
            elif x['attr'] != y['attr']:
                cosmetic[x['attr'] ^ y['attr']] += 1
        removed += la[n:]
        added += lb[n:]
    return removed, added, changed


if A['kind'] == 'odm':
    for key in ('name', 'sky', 'tileset', 'tile_lookup'):
        if A[key] != B[key]:
            print('header %s: %r -> %r' % (key, A[key], B[key]))
    for layer in ('height', 'tile', 'attr'):
        diffs = [i for i in range(128 * 128) if A[layer][i] != B[layer][i]]
        if diffs:
            cx = [i % 128 for i in diffs]
            cy = [i // 128 for i in diffs]
            print('## terrain %s: %d cells changed, cells x %d..%d y %d..%d (world x %d..%d, y %d..%d)' % (
                layer, len(diffs), min(cx), max(cx), min(cy), max(cy), (min(cx) - 64) * 512, (max(cx) - 63) * 512,
                (64 - max(cy) - 1) * 512, (64 - min(cy)) * 512))
            for i in diffs[:12]:
                print('   cell (%d,%d) %d -> %d' % (i % 128, i // 128, A[layer][i], B[layer][i]))
    # bmodels
    def bm_key(b):
        return (b['pos'], len(b['faces']))
    amap = defaultdict(list)
    for b in A['bmodels']:
        amap[bm_key(b)].append(b)
    used = set()
    renames = []
    print('## bmodels: base %d, other %d' % (len(A['bmodels']), len(B['bmodels'])))
    for b in B['bmodels']:
        cands = [x for x in amap.get(bm_key(b), []) if x['i'] not in used]
        if not cands:
            # try same name only
            cands = [x for x in A['bmodels'] if x['name'] == b['name'] and x['i'] not in used and
                     len(x['faces']) == len(b['faces'])]
        if not cands:
            evs = sorted(set(f['event'] for f in b['faces'] if f['event']))
            texs = Counter(f['tex'] for f in b['faces']).most_common(6)
            print('  + bmodel[%d] %s / %s pos=%s bbox=%s faces=%d events=%s tex=%s' % (
                b['i'], b['name'], b['name2'], b['pos'], fmt_bb((b['bbox'][0], b['bbox'][1], b['bbox'][2],
                                                                b['bbox'][3], b['bbox'][4], b['bbox'][5])),
                len(b['faces']), evs, texs))
            grp = defaultdict(list)
            for f in b['faces']:
                grp[(f['event'], f['attr'])].append(f)
            for (ev, at), fl in sorted(grp.items()):
                print('      event=%d attr=0x%X faces=%d %s tex=%s' % (ev, at, len(fl),
                      fmt_bb(bbox_of([v for f in fl for v in f['verts']])), Counter(f['tex'] for f in fl).most_common(3)))
            continue
        a = cands[0]
        used.add(a['i'])
        rem, add, chg = face_changes(a['faces'], b['faces'], b['name'])
        hdr = []
        if a['name'] != b['name']:
            renames.append((a['name'], b['name']))
        if a['pos'] != b['pos']:
            hdr.append('pos %s->%s' % (a['pos'], b['pos']))
        if a['name2'] != b['name2']:
            hdr.append('name2 %s->%s' % (a['name2'], b['name2']))
        if a['bbox'] != b['bbox']:
            hdr.append('bbox %s->%s' % (a['bbox'], b['bbox']))
        if rem or add or chg:
            print('  ~ bmodel %s [%d->%d] %s: faces -%d +%d, changed %d' % (b['name'], a['i'], b['i'], ' '.join(hdr),
                                                                          len(rem), len(add), len(chg)))
            for sign, lst in (('-', rem), ('+', add)):
                grp = defaultdict(list)
                for f in lst:
                    grp[(f['event'], f['attr'])].append(f)
                for (ev, at), fl in sorted(grp.items()):
                    print('      %s event=%d attr=0x%X faces=%d %s tex=%s' % (sign, ev, at, len(fl),
                          fmt_bb(bbox_of([v for f in fl for v in f['verts']])), Counter(f['tex'] for f in fl).most_common(4)))
            for x, y in chg[:40]:
                print('      ~ tex=%s %s: attr 0x%X->0x%X event %d->%d' % (x['tex'], fmt_bb(bbox_of(x['verts'])),
                                                                          x['attr'], y['attr'], x['event'],
                                                                          y['event']))
    if renames:
        print('  (renamed only, editor suffixes: %d bmodels, e.g. %s)' % (len(renames), renames[:3]))
    for a in A['bmodels']:
        if a['i'] not in used:
            evs = sorted(set(f['event'] for f in a['faces'] if f['event']))
            print('  - bmodel[%d] %s / %s pos=%s faces=%d events=%s' % (a['i'], a['name'], a['name2'], a['pos'],
                                                                      len(a['faces']), evs))
else:
    print('## counts: verts %d->%d faces %d->%d extras %d->%d sectors %d->%d doors(header) %d->%d outlines %d->%d '
          'bsp %d->%d' % (len(A['verts']), len(B['verts']), len(A['faces']), len(B['faces']), len(A['extras']),
                          len(B['extras']), A['sector_count'], B['sector_count'], A['door_count'], B['door_count'],
                          A['outline_count'], B['outline_count'], A['bsp_nodes'], B['bsp_nodes']))
    rem, add, chg = face_changes(A['faces'], B['faces'], 'blv')
    print('## faces: removed %d, added %d, attr/event changed %d' % (len(rem), len(add), len(chg)))
    by_sec = defaultdict(list)
    for f in rem:
        by_sec[('-', f['sector'])].append(f)
    for f in add:
        by_sec[('+', f['sector'])].append(f)
    for (sign, sec), fl in sorted(by_sec.items(), key=lambda t: (t[0][1], t[0][0])):
        bb = bbox_of([v for f in fl for v in f['verts']])
        print('  %s sector %d: %d faces, %s, tex=%s, events=%s' % (
            sign, sec, len(fl), fmt_bb(bb), Counter(f['tex'] for f in fl).most_common(5),
            sorted(set(f['event'] for f in fl if f['event']))))
    for x, y in chg[:80]:
        print('  ~ sector %d tex=%s %s: attr 0x%X->0x%X event %d->%d' % (x['sector'], x['tex'], fmt_bb(bbox_of(x['verts'])),
                                                                     x['attr'], y['attr'], x['event'], y['event']))
    if len(chg) > 80:
        print('  ... %d more' % (len(chg) - 80))
    multiset_diff('lights', A['lights'], B['lights'], lambda l: (l['pos'], l['radius'], l['rgb'], l['type']),
                  lambda l: 'pos=%s radius=%d rgb=%s type=%d' % (l['pos'], l['radius'], l['rgb'], l['type']))

multiset_diff('decorations/entities', A['entities'], B['entities'], ent_key, ent_show)
multiset_diff('spawns', A['spawns'], B['spawns'], spawn_key, spawn_show)

if cosmetic:
    print('## cosmetic face-attribute changes ignored (editor re-save: IsPicked/TexAlign/Outlined/SeenByParty): %s' %
          ', '.join('xor 0x%X x%d' % kv for kv in cosmetic.most_common()))
