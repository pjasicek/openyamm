"""Kill gold, item drops and XP: MM7 by level band, MM9 by chapter (BALANCE_PLAN.md sections 5.1 and 2.4).

Run from the repository root. MM7 counts expand spawn points to the mean of the map-stats range, as allmaps.py does.
MM9 counts are the monsters placed in the original DAT worlds, multiplied by the planned density factor.
"""
import glob, math, os, re, sys
from collections import defaultdict
sys.path.insert(0, 'tools/mm9_import_discovery')
import inventory_mm9_rework as inv

BANDS = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 30), (31, 40), (41, 55), (56, 80), (81, 999)]
def band(level):
    return next(i for i, (a, b) in enumerate(BANDS) if a <= level <= b)

def parse_treasure(s):
    s = s.strip().lower()
    dice = re.search(r'(\d+)d(\d+)', s)
    gold = int(dice.group(1)) * (int(dice.group(2)) + 1) / 2 if dice else 0
    lv = re.search(r'l(\d)', s)
    pct = re.match(r'(\d+)%', s)
    chance = (int(pct.group(1)) if pct else 100) if lv else 0
    return gold, chance / 100, int(lv.group(1)) if lv else 0

def engine_rows(path):
    rows = {}
    for r in inv.read_tsv(path):
        if len(r) > 7 and r[0].strip().isdigit():
            try:
                rows.setdefault(r[1].strip(), (int(r[3]), int(r[6]), parse_treasure(r[7])))
            except ValueError:
                pass
    return rows

# MM7 by band: kills, XP, gold, items, treasure-level sum.
eng = engine_rows(inv.ENGINE_TABLES / 'monster_data.txt')
by_number, by_picture = inv.load_engine_monsters()
ms = inv.load_map_stats()
mm7 = [[0.0] * 5 for _ in BANDS]
for p in sorted(glob.glob('assets_dev/worlds/mm7/maps/*.scene.yml')):
    stem = os.path.basename(p).replace('.scene.yml', '')
    fn = stem + ('.odm' if os.path.exists(p.replace('.scene.yml', '.odm')) else '.blv')
    r = inv.baseline_report('mm7', fn, ms, by_number, by_picture)
    if not r:
        continue
    for name, n in list(r.spawned.items()) + list(r.placed.items()):
        if name not in eng:
            continue
        lvl, xp, (gold, ch, tl) = eng[name]
        a = mm7[band(lvl)]
        a[0] += n; a[1] += n * xp; a[2] += n * gold; a[3] += n * ch; a[4] += n * ch * tl

print('MM7 by monster level band')
print('band     kills      XP      gold   items  gold/kXP items/MXP  TL')
for (lo, hi), a in zip(BANDS, mm7):
    if a[0]:
        print(f'{lo:>3}-{hi:<4} {a[0]:6.0f} {a[1]/1e6:6.2f}M {a[2]/1e3:7.1f}k {a[3]:6.0f}  {1000*a[2]/a[1]:7.1f}  {1e6*a[3]/a[1]:7.1f}  {a[4]/max(a[3],1e-9):.1f}')
tot = [sum(a[i] for a in mm7) for i in range(5)]
print(f'total    {tot[0]:6.0f} {tot[1]/1e6:6.2f}M {tot[2]/1e3:7.1f}k {tot[3]:6.0f}')
gold_per_xp = [a[2] / a[1] if a[1] else 0 for a in mm7]
items_per_xp = [a[3] / a[1] if a[1] else 0 for a in mm7]
tl = [round(a[4] / a[3]) if a[3] else 1 for a in mm7]

# MM9 by chapter at the planned density.
CHAPTERS = {
    1: 'isleofashes sturmford sturmfordcity beethoven anskramkeep bootcamp',
    2: 'drangheim drangheimprison drangheimcity guberland guberlandcity thjoradmine tasaracademy',
    3: 'thjorgard thjorgardcity thronheim thronheimcity frosgard frosgardcity mountainpass lindisfarne '
       'lindisfarnemonastery chasmofthedead ruinedtemple inventastorca greatgate thearena dookscastle',
    4: 'yorwick lichlab wizardslab connectingtunnels yanmirsfort darkpassageway bathhouse klusoshouse traininghall '
       'verhoffinruins dungeonofsecrets',
    5: 'templeofhonk 1000terrors arslegardcity dragonstadium hallofthegods afterworld',
}
chapter_of = {m: c for c, ms_ in CHAPTERS.items() for m in ms_.split()}
OUTDOOR = set('isleofashes sturmford drangheim guberland thjorgard thronheim frosgard mountainpass lindisfarne yorwick '
              'beethoven greatgate'.split())
DENSITY = {'dungeon': {1: 1.4, 2: 1.1, 3: 1.4, 4: 2.0, 5: 3.6}, 'outdoor': {1: 1.4, 2: 1.1, 3: 1.4, 4: 2.0, 5: 3.6}}

mons = inv.load_mm9_monsters()
by_class = {}
for m in mons:
    by_class.setdefault(inv.class_key(m.name), m)
reports = inv.build_map_reports(by_class)
by_name = {m.name: m for m in reversed(mons)}

# MM9 quest XP per chapter, one award per (amount, key given), finale excluded.
quest = defaultdict(float); seen = set()
for f in glob.glob('assets_dev/worlds/mm9/events/maps/*.lua'):
    stem = os.path.basename(f)[:-4]
    lines = open(f, encoding='latin-1').read().split('\n')
    for i, l in enumerate(lines):
        m = re.search(r'MM9\.giveExperience\((\d+)\)', l)
        if not m:
            continue
        keys = re.findall(r'giveKey\((\d+)\)', '\n'.join(lines[max(0, i - 3):i + 1]))
        ident = (int(m.group(1)), keys[-1] if keys else f'{stem}:{i}')
        if ident in seen or stem == 'hallofthegods':
            continue
        seen.add(ident)
        quest[chapter_of.get(stem, 3)] += int(m.group(1))

def level_for(x):
    return (1 + math.sqrt(1 + x / 125)) / 2

print('\nMM9 by chapter at the planned density (kill XP split over 5; quest XP to every member)')
print('ch  kills  killXP  per-member  questXP  cum/member  level   gold@MM7curve  gold@XP-parity  items@MM7  items@parity')
cum = 0
for c in range(1, 6):
    kills = kxp = g7 = gp = i7 = ip = 0.0
    for mid, rep in reports.items():
        if chapter_of.get(mid) != c:
            continue
        f = DENSITY['outdoor' if mid in OUTDOOR else 'dungeon'][c]
        for name, n in rep.monsters.items():
            mm = by_name[name]; b = band(max(mm.level, 1))
            n *= f
            kills += n; kxp += n * mm.experience
            avg7 = mm7[b]
            g7 += n * avg7[2] / avg7[0]; i7 += n * avg7[3] / avg7[0]
            gp += n * mm.experience * gold_per_xp[b]; ip += n * mm.experience * items_per_xp[b]
    cum += kxp / 5 + quest[c]
    print(f'{c}  {kills:5.0f}  {kxp/1e6:5.2f}M  {kxp/5e6:6.2f}M   {quest[c]/1e6:5.2f}M   {cum/1e6:5.2f}M   {level_for(cum):5.1f}'
          f'   {g7/1e3:8.0f}k   {gp/1e3:8.0f}k   {i7:6.0f}   {ip:6.0f}')

print('\nMM9 drop table at XP parity: gold per kill and item chance for an MM9 monster of median XP per band')
med = defaultdict(list)
for m in mons:
    if m.is_monster and m.experience:
        med[band(max(m.level, 1))].append(m.experience)
for b, (lo, hi) in enumerate(BANDS):
    if med[b] and mm7[b][0]:
        xs = sorted(med[b]); x = xs[len(xs) // 2]
        print(f'{lo:>3}-{hi:<4} XP {x:6d}  gold {x*gold_per_xp[b]:6.0f} (MM7 {mm7[b][2]/mm7[b][0]:5.0f})'
              f'  item {100*x*items_per_xp[b]:5.1f}% (MM7 {100*mm7[b][3]/mm7[b][0]:4.1f}%)  TL {tl[b]}')
