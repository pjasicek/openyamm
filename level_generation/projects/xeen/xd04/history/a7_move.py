import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[5])  # the repository root
#!/usr/bin/env python3
# Lane A7, "into the world" for XD-04 (2026-11-20): MM7 stand-in rows -> Xeen rows.
import re, sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import *
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd04/L4'
GOB, WIT, TOAD = [11010, 11011, 11012], [11160, 11161, 11162, 11163], [11450, 11451, 11452]
CHILDREN = [430, 433, 439, 442]
o = open(L + '/objects.yml').read()
o = set_monster(o, 'monster:head_witch', 215, 11163)
o = block_edit(o, 'monster:head_witch', lambda b: sub1(r'^    notes: .*$',
    '    notes: "The Head Witch (her boss row 11163, level 20) at the window over the shaft, between the Rosebud door and '
    'the bridge (set:head_witch)."', b))
o = set_monster(o, 'monster:schoolmistress', 214, 11160, drop=())
o = block_edit(o, 'monster:schoolmistress', lambda b: sub1(r'^    notes: .*$',
    '    notes: "The schoolmistress at her desk (a Wicked Witch, 11160, level 10)."', b))
for i in (1, 2):
    o = set_monster(o, f'monster:sister_{i}', 214, 11161)
o = set_monster(o, 'monster:warden', 273, 11012, drop=())
o = block_edit(o, 'monster:warden', lambda b: sub1(r'\(a Goblin Lord, level 10\)', '(a Gremlin Guard, 11012, level 10)', b))
for i in (1, 2):
    o = set_monster(o, f'monster:familiar_{i}', 207, 11452)
o = block_edit(o, 'monster:familiar_1', lambda b: sub1(r'^    notes: .*$',
    '    notes: "A familiar called up from the witch-marks (set:head_witch): a Swamp Toad (11452, level 11), the plan\'s '
    'summoned toad."', b))
o = sub1(r'^relations:\n(?:  - .*\n)+',
         'relations:\n' + ''.join('  - {of: [%s], toward: %d, relation: friendly, both_ways: true}\n'
                                  % (', '.join(map(str, GOB + WIT + TOAD)), c) for c in CHILDREN), o)
o = sub1(r'^notes: .*$',
         'notes: "Objects of the L4 brief (first written by output/studio_cal/xd04/tools/gen_objects.py; Xeen rows since '
         '2026-11-20, lane A7). Slots: 1 Xeen Goblin, 2 Xeen Witch, 3 Xeen Toad (the toads of the larder, the steam, the '
         'vats and the bed, MM7 bats before). Placed: the Head Witch her boss row 11163 (20), the schoolmistress a Wicked '
         'Witch 11160 (10), the two sisters Witches 11161 (14), the Goblin Warden a Gremlin Guard 11012 (10), the two '
         'familiars Swamp Toads 11452 (11); the caged children stay MM7 peasants (430, 433, 439, 442), kept apart from '
         'the three families both ways (`relations`): the families\' hostility to the party is the world\'s '
         'relations.yml."', o)
open(L + '/objects.yml', 'w').write(o)

w = open(L + '/wiring.yml').read()
w = sub1(r'if HasItem\(214\) then', 'if HasItem(12033) then', w)
open(L + '/wiring.yml', 'w').write(w)

p = open(L + '/project.yml').read()
p = sub1(r'^world: mm7$', 'world: xeen', p)
p = sub1(r'\{monster: Goblin, ', '{monster: Xeen Goblin, ', p)
p = sub1(r'\{monster: Cleric Moon, ', '{monster: Xeen Witch, ', p)
p = sub1(r'\{monster: Bat, ', '{monster: Xeen Toad, ', p)
for k, old, new in (('alacorn', 214, 12033), ('coven_key', 2187, 12034), ('crystal_key', 2110, 12031),
                    ('warden_ring', 629, 12032)):
    p = sub1(r'^  %s: %d$' % (k, old), '  %s: %d' % (k, new), p)
open(L + '/project.yml', 'w').write(p)

M = {271: 11010, 272: 11011, 273: 11012, 214: 11160, 215: 11161, 216: 11162, 205: 11450, 206: 11451, 207: 11452}
ITEMS = {214: 12033, 2187: 12034, 2110: 12031, 629: 12032}
for f in ('playtest.yml', 'playtest_m4.yml', 'playtest_hostility.yml'):
    t = open(L + '/' + f).read()
    t = sub1(r'^world: mm7$', 'world: xeen', t)
    t = re.sub(r'(has_item\(|item_id: |HasItem\()(\d+)', lambda m: m.group(1) + str(ITEMS.get(int(m.group(2)), int(m.group(2)))), t)
    t = map_ids(t, M)
    open(L + '/' + f, 'w').write(t)
print('ok')
