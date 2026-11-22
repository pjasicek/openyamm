import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[5])  # the repository root
#!/usr/bin/env python3
# Lane A7, "into the world" for XD-01 (2026-11-20): MM7 stand-in rows -> Xeen rows.
import re, sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import *
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd01/L4'
o = open(L + '/objects.yml').read()
for pid in ('pen_1', 'pen_2', 'pen_2b', 'pen_3', 'pen_4', 'pen_5', 'pen_5b', 'pen_6'):
    o = set_monster(o, 'monster:' + pid, 385, 11380, drop=())
for who, name in (('mr', 'Mr'), ('mrs', 'Mrs')):
    o = set_monster(o, f'monster:{who}_wobbles', 387, 11383, drop=('hp',))
    o = block_edit(o, f'monster:{who}_wobbles', lambda b: sub1(r'^    notes: .*$',
        f'    notes: "{name} Wobbles, one of the mated pair of Breeder Slimes: the Wobbles\' boss row (11383, level 4, '
        f'about three times a Breeder Slime\'s hit points), named. When {"he" if who == "mr" else "she"} dies the slime '
        f'splits into two Slimes (wiring evt:{who}_splits: two of encounter slot 1 at tier a, Slime 11380, at the nest, '
        f'in the pair\'s group). The brief\'s split below half health needs an actor script (not a word); the split on '
        f'death is the nearest the wiring says."', b))
o = sub1(r'^relations:\n(?:  - .*\n)+', '', o)
o = sub1(r'(^notes: "Objects of the L4 brief\.)', r'\1 Xeen rows since 2026-11-20 (lane A7): slots 1 Xeen Ooze and 2 '
         r'Xeen Swarm; the pens\' eight Slimes 11380 (2), Mr and Mrs Wobbles the boss row 11383 (4); no relations block '
         r'(the world\'s relations.yml makes every Xeen family the party\'s foe and sets none on another).', o)
open(L + '/objects.yml', 'w').write(o)

w = open(L + '/wiring.yml').read()
w = block_edit(w, 'evt:invoice_crate', lambda b: sub1(r'^    effects:\n', '    effects:\n      - autonote: 4002\n', b))
w = block_edit(w, 'evt:mr_splits', lambda b: sub1(r'two Slime 2 \(stand-in Giant Rats of slot 1\)',
                                                    'two Slimes 2 (slot 1 at tier a, Slime 11380)', b))
open(L + '/wiring.yml', 'w').write(w)

p = open(L + '/project.yml').read()
p = sub1(r'^world: mm7$', 'world: xeen', p)
p = sub1(r'\{monster: Rat, ', '{monster: Xeen Ooze, ', p)
p = sub1(r'\{monster: Dragonfly, ', '{monster: Xeen Swarm, ', p)
for k, old, new in (('joes_invoice', 1530, 12002), ('pen_key', 2110, 12003), ('warehouse_key', 2176, 12001)):
    p = sub1(r'^  %s: %d$' % (k, old), '  %s: %d' % (k, new), p)
p = sub1(r'^notes: .*$',
         'notes: "Xeen design brief, level L4: L3\'s rooms redrawn with the studio\'s words of 2026-11-12 (sixteen-sided '
         'cistern under a brick dome, pens behind barred gates, the culvert as a tunnel with a cross-section, the loft as a '
         'gallery inside the grain hall under a ridged roof, stairs with treads), themes, objects and wiring; a playable '
         'map (NOTES.md). Story step M2 (devdocs/xeen/QUESTS.md, A3\'s quests/m2.yml). World of Xeen since 2026-11-20 (lane '
         'A7): slot 1 Xeen Ooze (Slime 11380 2, Breeder Slime 11381 4; the spawn points fix a or b), slot 2 Xeen Swarm '
         '(Doom Bug 11340 2, Insect Swarm 11341 4); the pens\' Slimes 11380, Mr and Mrs Wobbles the boss row 11383 (4), '
         'their splits Slimes of slot 1. About 28 monsters, levels 2-4. Items: warehouse_key 12001, joes_invoice 12002, '
         'pen_key 12003; quest bits 110010-110012 (m2.yml). The map card (map_stats 9131, music, treasure 1) is A2\'s row '
         'from source/map_rows.yml: the block below is the studio\'s copy for its checks. Both neighbours lead to X1 '
         '(xeen_x1.odm), each to its own door."', p)
open(L + '/project.yml', 'w').write(p)

M = {385: 11380, 386: 11381, 387: 11383, 226: 11340, 227: 11341, 228: 11342}
ITEMS = {2176: 12001, 1530: 12002, 2110: 12003}
for f in ('playtest.yml', 'playtest_perception.yml', 'playtest_hostility.yml'):
    t = open(L + '/' + f).read()
    t = sub1(r'^world: mm7$', 'world: xeen', t)
    t = re.sub(r'(has_item\(|item_id: )(\d+)', lambda m: m.group(1) + str(ITEMS.get(int(m.group(2)), int(m.group(2)))), t)
    t = map_ids(t, M)
    open(L + '/' + f, 'w').write(t)
print('ok')
