"""MM9 quest XP from the original scripts (script IR), its content level, and the party level per chapter.

Run from the repository root. Each GiveExp is tied to the quest keys it checks; a key's content map is the map that
grants it. Content level = median monster level of the award map and those key maps (highest). Awards with the same
amount and the same key given are one award (alternative turn-in places). Kill XP uses the planned density.
Usage: quest_xp.py [cap_levels ...]   cap = most XP one award may give, in levels' worth (1000 × content level each).
"""
import glob, math, os, re, sys, statistics as st
sys.path.insert(0, 'tools/mm9_import_discovery')
sys.path.insert(0, os.path.dirname(__file__))
import inventory_mm9_rework as inv

CH = {1: 'isleofashes sturmford sturmfordcity beethoven anskramkeep bootcamp',
      2: 'drangheim drangheimprison drangheimcity guberland guberlandcity thjoradmine tasaracademy',
      3: 'thjorgard thjorgardcity thronheim thronheimcity frosgard frosgardcity mountainpass lindisfarne '
         'lindisfarnemonastery chasmofthedead ruinedtemple inventastorca greatgate thearena dookscastle',
      4: 'yorwick lichlab wizardslab connectingtunnels yanmirsfort darkpassageway bathhouse klusoshouse traininghall '
         'verhoffinruins dungeonofsecrets',
      5: 'templeofhonk 1000terrors arslegardcity dragonstadium hallofthegods afterworld'}
chof = {m: c for c, v in CH.items() for m in v.split()}
OUTDOOR = set('isleofashes sturmford drangheim guberland thjorgard thronheim frosgard mountainpass lindisfarne yorwick '
              'beethoven greatgate'.split())
DENSITY = {'dungeon': {1: 1.4, 2: 1.1, 3: 1.4, 4: 2.0, 5: 3.6}, 'outdoor': {1: 1.4, 2: 1.1, 3: 1.4, 4: 2.0, 5: 3.6}}
BAND_END = {1: 12, 2: 25, 3: 40, 4: 70, 5: 100}

mons = inv.load_mm9_monsters()
by_class = {}
for m in mons:
    by_class.setdefault(inv.class_key(m.name), m)
by_name = {m.name: m for m in reversed(mons)}
reports = inv.build_map_reports(by_class)
map_level = {}
kill_xp = {c: 0.0 for c in CH}
for mid, rep in reports.items():
    levels = [by_name[n].level for n, k in rep.monsters.items() for _ in range(k)]
    if levels:
        map_level[mid] = st.median(levels)
    c = chof.get(mid)
    if c:
        f = DENSITY['outdoor' if mid in OUTDOOR else 'dungeon'][c]
        kill_xp[c] += f * sum(by_name[n].experience * k for n, k in rep.monsters.items())

cmds = {}
for f in glob.glob('assets_dev/worlds/mm9/events/*.script_ir.yml'):
    s = os.path.basename(f).split('.')[0]
    cs = re.findall(r'command: (\S+)\n\s*arguments_raw: (.*)', open(f, encoding='utf-8').read())
    cmds[s] = [(c.lower(), a.strip().strip("'").split(' ')[0].strip(',')) for c, a in cs]
gives = {}
for s, cs in cmds.items():
    for c, a in cs:
        if c == 'givekey':
            gives.setdefault(a, set()).add(s)

awards, seen = [], set()
for s, cs in sorted(cmds.items()):
    for i, (c, a) in enumerate(cs):
        if c != 'giveexp' or not a.isdigit():
            continue
        after = [x for cc, x in cs[i - 3:i + 3] if cc == 'givekey']
        req = [x for cc, x in cs[max(0, i - 8):i] if cc == 'haskey'][-2:]
        ident = (int(a), after[-1] if after else (req[-1] if req else f'{s}{i}'))
        if ident in seen:
            continue
        seen.add(ident)
        maps = [s] + [m for r in req for m in gives.get(r, [])]
        level = max(map_level.get(m, 1) for m in maps)
        chapter = max(chof.get(m, 1) for m in maps)
        awards.append((s, int(a), level, chapter))

lv = lambda x: (1 + math.sqrt(1 + x / 125)) / 2
print(f'{len(awards)} awards, {sum(a[1] for a in awards)/1e6:.2f}M per member (alternatives merged)')
print('largest:', ', '.join(f'{s} {x//1000}k@L{l:.0f}' for s, x, l, c in sorted(awards, key=lambda a: -a[1])[:10]))
for cap in [None] + [float(x) for x in sys.argv[1:]]:
    cum = 0.0
    row = []
    for c in range(1, 6):
        q = sum(min(x, cap * 1000 * l) if cap else x for s, x, l, ch in awards if ch == c)
        cum += q + kill_xp[c] / 5
        row.append(f'ch{c} {lv(cum):5.1f} (band to {BAND_END[c]}, quests {q/1e3:5.0f}k)')
    total = sum(min(x, cap * 1000 * l) if cap else x for s, x, l, ch in awards)
    print(f'cap {cap or "none":>4}: quests {total/1e6:4.2f}M | ' + ' | '.join(row))
