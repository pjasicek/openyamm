"""Write the pack mixes for tools/balance_probe_main.cpp (openyamm_balance_probe), BALANCE_PLAN.md section 4.

Run from the repository root. Uses fit_check.py's monster counts, pack sizes and party levels (each stage's mid level,
from the XP curve with the decided density and quest XP profile). Rows by stage (fit_check.STAGES: MM7's five; MM9's
acts with the clans act's early and late maps apart). Shop tiers: stage 1-5 -> tier 2-6.
Usage: probe_input.py <output.tsv> [--density d1,...,d5] [--pack-scale s1,...,s5]
  --density     MM9 monsters vs today per stage, the dat source only; default the decided factors
  --pack-scale  extra factor on MM9 pack sizes per stage only (kill XP unchanged), for trials
  --mm9-source  targets (the rebuilt scenes grown by mm9_density_targets.yml, default), scenes (as they stand)
                or dat (the original placement times --density)
"""
import math, runpy, sys
args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
OUTPUT = sys.argv[1]
sys.argv = ['fit', '--profiles', '1', '--quest-profile', '1', '--mm9-source', args.get('--mm9-source', 'targets')]
if '--density' in args:
    sys.argv += ['--density', args['--density']]
g = runpy.run_path('devdocs/mm9_rework/balance_prototypes/fit_check.py', run_name='fit')
STAGES = g['STAGES']
scale = [float(x) for x in args['--pack-scale'].split(',')] if '--pack-scale' in args else [1.0] * STAGES
D = g['DENSITY']
quests = g['quests_from_profile']()
groups9, xp9 = g['mm9_groups'](D)
lv = g['lv']

def mid_levels(xp, quest):
    out, cum = {}, 0.0
    for s in range(1, STAGES + 1):
        start = lv(cum)
        cum += xp[s] / 5 + quest(s)
        out[s] = round((start + lv(cum)) / 2)
    return out

l7 = mid_levels(g['mm7_xp'], lambda s: g['MM7_QUEST'] * g['mm7_xp'][s] / g['total_kill'])
l9 = mid_levels(xp9, lambda s: quests[s])
with open(OUTPUT, 'w') as out:
    out.write('# world stage party_level shop_tier pack_size monster_id weight\n')
    for world, groups, levels in (('mm7', g['mm7'], l7), ('mm9', groups9, l9)):
        for s in range(1, STAGES + 1):
            merged = {}
            for m, n, pack in groups[s]:
                pk = pack * (scale[s - 1] if world == 'mm9' else 1.0)
                merged[(m['id'], round(pk, 2))] = merged.get((m['id'], round(pk, 2)), 0.0) + n
            for (mid, pk), n in sorted(merged.items()):
                out.write(f'{world}\t{s}\t{levels[s]}\t{s + 1}\t{pk}\t{mid}\t{n:.2f}\n')
print('party levels MM7', l7, 'MM9', l9)
