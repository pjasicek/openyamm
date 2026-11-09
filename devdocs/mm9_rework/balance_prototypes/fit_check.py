"""Reference-party fit check: each MM9 chapter against the matching MM7 stage, under the shared combat rules.

Run from the repository root. Read-only. One reference party of five is used in both worlds; skills, spells, item
ladders (BALANCE_PLAN.md section 3, at MM6-MM8 parity) and the hit, resistance and recovery rules are shared, so what
differs is the monsters (HP, AC, damage, attack rate, resistances, XP), the pack sizes and the party level each stage
reaches. Monster counts weight every average: MM7 from its maps (spawns at the mean of their range plus placed actors),
MM9 from the placed DAT monsters times the planned density.

Party model (the same in both worlds, so only ratios matter):
  damage per second   5 x (level + 5), half weapons (physical) and half spells (the best school for each monster)
  attack bonus        level + 10                     (characterAttackHitsArmorClass)
  armour class        2.5 x level + 15               (monsterAttackHitsArmorClass)
  hit points          5 x (6 x level + 20)
Monster resistance: up to four halvings, each stopped with chance 30 / (resistance + 30); 200 or more is immunity
(resolveMonsterIncomingDamage). A pack of N fought one at a time costs N(N+1)/2 monster-lifetimes of damage.
"""
import glob, math, os, re, statistics as st, sys
from pathlib import Path
sys.path.insert(0, 'tools/mm9_import_discovery')
import inventory_mm9_rework as inv

def dice(s):
    m = re.match(r'\s*(\d+)[dD](\d+)\s*([+-]\s*\d+)?', s or '')
    if not m:
        try:
            return float(s)
        except ValueError:
            return 0.0
    return int(m.group(1)) * (int(m.group(2)) + 1) / 2 + (int(m.group(3).replace(' ', '')) if m.group(3) else 0)

def num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default

def load(path):
    rows = {}
    for line in open(path, encoding='latin-1').read().splitlines()[3:]:
        c = line.split('\t')
        if len(c) < 38 or not c[0].strip().isdigit():
            continue
        level = int(num(c[3]))
        if level <= 0:
            continue
        attack2 = num(c[20]) / 100
        rows[int(c[0])] = dict(
            id=int(c[0]), name=c[1].strip(), level=level, hp=num(c[4]), ac=num(c[5]), xp=num(c[6]),
            rec=num(c[14], 100) or 100, dmg=dice(c[18]) * (1 - attack2) + dice(c[22]) * attack2,
            res=[num(x) for x in c[28:38]])  # fire air water earth mind spirit body light dark phys
    return rows

def resist_mult(r):
    if r >= 200:
        return 0.0
    p = 30 / (max(0.0, r) + 30)
    return sum(p * (1 - p) ** k / 2 ** k for k in range(4)) + (1 - p) ** 4 / 16

def monster_hits(ac, level):
    upper = max(1, ac + 2 * level + 10)
    return max(0, upper - (ac + 5)) / upper

def party_hits(ac, bonus):
    upper = max(1, ac + 2 * bonus + 30)
    return max(0, upper - (ac + 15)) / upper

lv = lambda x: (1 + math.sqrt(1 + x / 125)) / 2
need = lambda level: 500 * level * (level - 1)

def evaluate(monsters, party_level, pack, mm9):
    """monsters: list of (row, weight). Returns per-stage averages."""
    w = sum(n for _, n in monsters)
    ttk = cost = xp = hp = ac = dps = lvl = spell = phys = 0.0
    for m, n in monsters:
        hpm = m['hp']
        rec, dmg = m['rec'], m['dmg']
        if mm9:
            hpm *= 0.95 if 41 <= m['level'] <= 60 else 0.90 if m['level'] > 60 else 1.0
            rec = 75 if m['level'] <= 20 else 59
            dmg *= 0.75 if m['level'] <= 5 else 1.0
        best_school = max(resist_mult(r) for r in m['res'][:7])
        if mm9 and PROFILES:
            # BALANCE_PLAN.md section 5.2: each family gets one weak school, as MM6-MM8 monsters have.
            best_school = max(best_school, resist_mult(min(m['res'][:7]) * 0.25))
        weapon = resist_mult(m['res'][9])
        hit = party_hits(m['ac'], party_level + 10)
        out = 5 * (party_level + 5) * (0.5 * hit * weapon + 0.5 * best_school)
        t = hpm / max(out, 1e-6)
        incoming = dmg * monster_hits(2.5 * party_level + 15, m['level']) / (rec / 60)
        ttk += n * t
        cost += n * incoming * t * (pack + 1) / 2          # this monster's share of a pack fought one at a time
        xp += n * m['xp']; hp += n * hpm; ac += n * m['ac']; dps += n * incoming; lvl += n * m['level']
        spell += n * best_school; phys += n * weapon * hit
    party_hp = 5 * (6 * party_level + 20)
    return dict(n=w, level=lvl / w, hp=hp / w, ac=ac / w, dps=dps / w, ttk=ttk / w, spell=spell / w, phys=phys / w,
                cost=pack * cost / w / party_hp, xp_pack=pack * xp / w / 5 / max(1, need(party_level + 1) - need(party_level)))

# MM7: stages by the median monster level of each map.
eng = load('assets_dev/engine/data_tables/monster_data.txt')
by_name = {}
for m in eng.values():
    by_name.setdefault(m['name'], m)
by_number, by_picture = inv.load_engine_monsters()
ms = inv.load_map_stats()
STAGE_OF = lambda median: 1 if median <= 8 else 2 if median <= 20 else 3 if median <= 35 else 4 if median <= 55 else 5
# MM9's chapters are its story's acts (the user, 2026-11-07; mm9_density_targets.CHAPTER_MAPS): the prologue, uniting
# the clans (an open act with both promotions, as MM7's middle from Erathia to Bracada and Tatalia), the war, the
# finale. Both worlds are measured by stage: MM7's by a map's median monster level, MM9's by act, its open clans act
# as its early maps (the Jarls next to Sturmford, mm9_density_targets.CLANS_EARLY_MAPS: stage 2) and the rest (stage 3),
# which a party takes in that order. A median-level split does not work for MM9: Thronheim, Lindisfarne, the Mountain
# Pass and Yanmir's Fort have medians of 15-20 with many monsters of 30-70.
ACTS, STAGES = 4, 5
ACT_OF_STAGE = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}
STAGE_LABEL = {1: '1', 2: '2 early', 3: '2 late', 4: '3 (+ act 2 dungeons)', 5: '4'}

def mm9_stage(act, stem):
    # The clans act's optional promotion and side dungeons (mm9_density_targets.CLANS_LATE_DUNGEONS) are taken last:
    # measured with the war (stage 4); at the late act's party level they read 2.3-4.2x MM7's damage.
    if act == 2 and stem in _acts.CLANS_LATE_DUNGEONS:
        return 4
    return {1: 1, 3: 4, 4: 5}.get(act) or (2 if stem in _acts.CLANS_EARLY_MAPS else 3)
# The share of placed monsters a party kills (the user, 2026-11-07): MM7 parties fly over or walk past half of an
# outdoor map's monsters and leave a tenth of a dungeon's; MM9 has no Fly, so its packs are forced fights, all of a
# dungeon's and most of an outdoor map's. Every kill count below (XP, party levels, the probe's mixes, gold, drops) is
# placed monsters times this share; chests are opened in both games and are not scaled. --clear 1 counts everything.
CLEAR = {'mm7': {'outdoor': 0.5, 'dungeon': 0.9}, 'mm9': {'outdoor': 0.85, 'dungeon': 1.0}}
if '--clear' in sys.argv and sys.argv[sys.argv.index('--clear') + 1] == '1':
    CLEAR = {world: {kind: 1.0 for kind in shares} for world, shares in CLEAR.items()}
mm7 = {s: [] for s in range(1, STAGES + 1)}
mm7_stage_of_map = {}   # map stem -> stage (chests.py)
mm7_xp = {s: 0.0 for s in range(1, STAGES + 1)}
for p in sorted(glob.glob('assets_dev/worlds/mm7/maps/*.scene.yml')):
    stem = os.path.basename(p).replace('.scene.yml', '')
    outdoor = os.path.exists(p.replace('.scene.yml', '.odm'))
    r = inv.baseline_report('mm7', stem + ('.odm' if outdoor else '.blv'), ms, by_number, by_picture)
    if not r:
        continue
    share = CLEAR['mm7']['outdoor' if outdoor else 'dungeon']
    ms_ = [(by_name[k], v * share) for k, v in list(r.spawned.items()) + list(r.placed.items())
           if k in by_name and v > 0]
    if not ms_:
        continue
    levels = sorted(m['level'] for m, v in ms_ for _ in range(max(1, round(v / share))))
    s = STAGE_OF(levels[len(levels) // 2])
    mm7_stage_of_map[stem] = s
    mm7[s] += [(m, v, 2.5 if outdoor else 3.4) for m, v in ms_]
    mm7_xp[s] += sum(m['xp'] * v for m, v in ms_)
MM7_QUEST = 1.7e6
total_kill = sum(mm7_xp.values())

# MM9: acts (mm9_density_targets.CHAPTER_MAPS), placed monsters times the planned density.
sys.path.insert(0, 'tools/mm9_import_discovery')
import mm9_density_targets as _acts
CH = dict(_acts.CHAPTER_MAPS)
chof = {m: c for c, v in CH.items() for m in v.split()}
OUTDOOR = set('isleofashes sturmford drangheim guberland thjorgard thronheim frosgard mountainpass lindisfarne yorwick '
              'beethoven greatgate'.split())
DENSITY = {kind: {s: _acts.FACTOR[ACT_OF_STAGE[s]] for s in range(1, STAGES + 1)} for kind in ('dungeon', 'outdoor')}
# Optional overrides (the dat source): --density d1,..,d5 per stage (both map kinds) and --quest q1,..,q5.
ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
if '--density' in ARGS:
    f = [float(x) for x in ARGS['--density'].split(',')]
    DENSITY = {k: {c + 1: f[c] for c in range(STAGES)} for k in DENSITY}
QUEST_FACTOR = [float(x) for x in ARGS['--quest'].split(',')] if '--quest' in ARGS else [1.0] * STAGES
PROFILES = ARGS.get('--profiles', '0') == '1'   # MM6-MM8-style resistance profiles on MM9 monsters
PACK = {'dungeon': 2.1, 'outdoor': 1.8}
QUEST9 = {1: 52000, 2: 47000 + 4 * 24300 + 25000 + 12500 + 25000 + 18750 + 18750 + 20000 + 25000,
          3: 88800 + 4 * 50000 + 37500 + 20000 + 31250 + 30000 + 26500 + 20000 + 43750 + 50000,
          4: 18000 + 56250 + 50000 + 20000 + 20000 + 68750 + 68750 + 75000 * 3 + 62500 + 80000,
          5: 22000 + 68004 + 52000 * 4 + 46000 + 106250 + 112500 * 3 + 87500 + 80000}   # QUEST_XP_AUDIT.md proposal
# (the quest audit's five chapters are the five stages: its chapters 2 and 3 are the clans act's early and late maps)
w9 = load('assets_dev/worlds/mm9/data_tables/monster_data.txt')
mm9_rows = inv.load_mm9_monsters()
by_class = {}
for m in mm9_rows:
    by_class.setdefault(inv.class_key(m.name), m)
number_of = {m.name: m.number for m in reversed(mm9_rows)}
# MM9's monsters: --mm9-source targets (default) reads the rebuilt maps' scenes with the frozen density targets of
# tools/mm9_import_discovery/mm9_density_targets.yml (what the rebuild will ship); scenes reads the scenes as they stand
# (after the rebuild: as shipped); dat reads the original DAT placement times the DENSITY factors (the first model).
MM9_SOURCE = ARGS.get('--mm9-source', 'targets')
mm9_base = {c: [] for c in range(1, STAGES + 1)}
mm9_stage_of_map = {}   # map stem -> stage (the targets and scenes sources)
if MM9_SOURCE == 'dat':
    for mid, rep in inv.build_map_reports(by_class).items():
        c = chof.get(mid)
        if not c or mid == 'bootcamp':
            continue
        kind = 'outdoor' if mid in OUTDOOR else 'dungeon'
        c = mm9_stage(c, mid)
        for name, k in rep.monsters.items():
            m = w9.get(9000 + number_of[name])
            # Scripted specials (Njam the Meddler L200, the Dragon King L500) are story encounters, not density.
            if m and m['dmg'] > 0 and m['level'] < 150:
                mm9_base[c].append((m, k * CLEAR['mm9'][kind], PACK[kind]))
else:
    import yaml as _yaml
    sys.path.insert(0, 'tools/mm9_import_discovery')
    import mm9_density_targets as _targets
    _rows = _targets.monster_rows()
    _frozen = (_yaml.safe_load(open('tools/mm9_import_discovery/mm9_density_targets.yml'))['maps']
               if MM9_SOURCE == 'targets' else {})
    for c, stems in _targets.CHAPTER_MAPS.items():
        for stem in stems.split():
            path = Path(f'assets_dev/worlds/mm9/maps/{stem}.scene.yml')
            if not path.exists():
                continue
            scene = _yaml.load(path.read_text(encoding='utf-8'), Loader=_yaml.CSafeLoader)
            actors = [a for a in (scene.get('initial_state') or {}).get('actors') or []
                      if _targets.counted_actor(a, _rows, stem)]
            if not actors:
                continue
            if MM9_SOURCE == 'targets':
                # Scale each map to its target from today's count: a map already grown counts as it stands, so the
                # targets stay right while the rebuilds land (the frozen counted_today would scale grown maps twice).
                entry = _frozen[stem]
                scale = max(1.0, entry['target_total'] / len(actors))
                pack = entry['mean_pack_target']
            else:
                scale, pack = 1.0, len(actors) / len(_targets.packs_of(actors))
            counts = {}
            for a in actors:
                counts[int(a['monster_info_id'])] = counts.get(int(a['monster_info_id']), 0) + 1
            share = CLEAR['mm9']['outdoor' if stem in _targets.OUTDOOR_MAPS else 'dungeon']
            stage = mm9_stage(c, stem)
            mm9_stage_of_map[stem] = stage
            for monster_id, k in counts.items():
                m = w9.get(monster_id)
                if m and m['dmg'] > 0:
                    mm9_base[stage].append((m, k * scale * share, pack))

def mm9_groups(density):
    """Monsters, counts and pack sizes per chapter; `density` applies to the dat source only."""
    if MM9_SOURCE == 'dat':
        groups = {c: [(m, k * density['dungeon'][c], pack * density['dungeon'][c]) for m, k, pack in v]
                  for c, v in mm9_base.items()}
    else:
        groups = {c: list(v) for c, v in mm9_base.items()}
    return groups, {c: sum(m['xp'] * n for m, n, _ in v) for c, v in groups.items()}

def stage_rows(groups, xp, quest_of, label):
    out, cum = [], 0.0
    for s in range(1, STAGES + 1):
        start = lv(cum)
        cum += xp[s] / 5 + quest_of(s)
        end = lv(cum)
        party = (start + end) / 2
        # Packs differ by map kind; evaluate each kind and weight by monster count.
        parts = {}
        for m, n, pack in groups[s]:
            parts.setdefault(pack, []).append((m, n))
        evals = [(evaluate(v, party, pk, label == 'MM9'), sum(n for _, n in v)) for pk, v in parts.items()]
        total = sum(n for _, n in evals)
        merged = {k: sum(e[k] * n for e, n in evals) / total for k in evals[0][0]}
        merged['n'] = total
        out.append((s, start, end, merged))
    return out

r7 = stage_rows(mm7, mm7_xp, lambda s: MM7_QUEST * mm7_xp[s] / total_kill, 'MM7')

def report(density, quest_factor, show=True):
    groups, xp = mm9_groups(density)
    r9 = stage_rows(groups, xp, lambda s: QUEST9[s] * quest_factor[s - 1], 'MM9')
    rows = []
    for (s, a7, b7, e7), (_, a9, b9, e9) in zip(r7, r9):
        gap7, gap9 = (a7 + b7) / 2 - e7['level'], (a9 + b9) / 2 - e9['level']
        rows.append((s, e9['ttk'] / e7['ttk'], e9['cost'] / e7['cost'], gap9 - gap7, b9, b7))
        if show:
            print(f'{s} MM7 | {a7:4.1f}-{b7:4.1f} | {e7["level"]:5.1f} | {e7["n"]:5.0f} | {e7["ttk"]:5.2f} | '
                  f'{100*e7["cost"]:5.1f} | {100*e7["xp_pack"]:5.1f} | {e7["spell"]:.2f} | {e7["phys"]:.2f}')
            print(f'{s} MM9 | {a9:4.1f}-{b9:4.1f} | {e9["level"]:5.1f} | {e9["n"]:5.0f} | {e9["ttk"]:5.2f} | '
                  f'{100*e9["cost"]:5.1f} | {100*e9["xp_pack"]:5.1f} | {e9["spell"]:.2f} | {e9["phys"]:.2f}')
            print(f'  ratio MM9/MM7: kill time {e9["ttk"]/e7["ttk"]:.2f}, pack cost {e9["cost"]/e7["cost"]:.2f}, '
                  f'pack XP {e9["xp_pack"]/e7["xp_pack"]:.2f}, party-minus-monster level {gap9:+.1f} (MM7 {gap7:+.1f})')
    return rows

def quests_from_profile():
    """Quest XP per member by chapter from the audit and mm9_quest_xp_profile.yml: every award once, with a party of five
    taking four first-tier and four second-tier promotion quests."""
    import csv, runpy
    pr = runpy.run_path(os.path.join(os.path.dirname(__file__), 'quest_xp_profile.py'), run_name='profile')
    prof = {(o[0], o[1], o[2]): o[3] for o in pr['out']}
    q = {c: 0.0 for c in range(1, STAGES + 1)}
    for r in csv.DictReader(open('output/mm9_balance/quest_xp_audit.tsv'), delimiter='\t'):
        key = (r['map'], r['routine'].lower(), int(r['xp']))
        if pr['PROMOTION'].search(r['routine']) or key in pr['PROMOTION_ROWS']:
            continue
        stage = AWARD_STAGE.get(key, pr['CONTENT_CHAPTER'].get(key, int(r['chapter'])))
        q[stage] += prof.get((r['script'], r['routine'], int(r['xp'])), int(r['xp']))
    level = pr['CHAPTER_LEVEL']
    # Both promotion tiers are in the clans act: the first in its early maps' towns, the second in its late maps.
    q[2] += 4 * min(24300, pr['PROMOTION_CAP_LEVELS'] * 1000 * level[2])
    q[3] += 4 * min(63000, pr['PROMOTION_CAP_LEVELS'] * 1000 * level[3])
    return q

# Awards whose work moved into the clans act with its maps (the audit's chapter 4), at their map's stage: Tryggva's
# Yanmir (Yanmir's Fort, median level 20: early), the Training Hall (27: late).
AWARD_STAGE = {('frosgardcity', 'yanmir', 58000): 2, ('thjorgard', 'onbreak', 20000): 3}

if __name__ == '__main__':
    if ARGS.get('--quest-profile') == '1':
        quests = quests_from_profile()
        print('quest XP per member by chapter:', {c: round(v) for c, v in quests.items()})
        QUEST_FACTOR = [quests[c] / QUEST9[c] for c in range(1, STAGES + 1)]
    print('Stage | party level (start-end) | monster level | monsters | kill time per monster s | '
          'pack cost % party HP | pack XP % of a level | best-school spell x | weapon x hit')
    report(DENSITY, QUEST_FACTOR)
