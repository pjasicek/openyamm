import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[5])  # the repository root
#!/usr/bin/env python3
# Lane A7, "into the world" for XD-03 (2026-11-20): MM7 stand-in rows -> Xeen rows.
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import *
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4'
o = open(L + '/objects.yml').read()
for i in range(1, 6):
    o = set_monster(o, f'monster:barracks_{i}', 229, 11050)
for i in range(1, 4):
    o = set_monster(o, f'monster:far_bank_{i}', 229, 11051)
o = set_monster(o, 'monster:gong_sentry', 229, 11051, drop=())
for i in (1, 2):
    o = set_monster(o, f'monster:gate_guard_{i}', 229, 11052)
for i in range(1, 5):
    o = set_monster(o, f'monster:guard_{i}', 229, 11052)
for i in (1, 2):
    o = set_monster(o, f'monster:bat_queen_{i}', 207, 11302)
o = set_monster(o, 'monster:clan_king', 230, 11053)
o = block_edit(o, 'monster:clan_king', lambda b: sub1(r'^    notes: .*$',
    '    notes: "The Clan King on the throne floor: his own boss row (11053, level 18; CHANGES A1, A2\'s rows), '
    'named by the row, carrying the hoard key. He fights from the dais until his guard falls (set:clan_king)."', b))
# Spawn points: the mad dwarves 7/10/12 (a/b/c), the spiders at b (Cave Spider 10: c is 14, over the band), the moles
# 6/9/12 (a/b/c), the warrens' troglodytes before.
for oid, t in (('gallery', 'a'), ('near_bank_1', 'a'), ('near_bank_2', 'b'), ('lookout', 'b'), ('tower', 'c'),
               ('geode_lower', 'b'), ('warren_east', 'a'), ('warren_south', 'b'), ('warren_west', 'c')):
    if t != 'a' or oid.startswith('geode'):
        o = set_tier(o, 'spawn:' + oid, t)
o = sub1(r'^relations:\n(?:  - .*\n)+', '', o)
o = sub1(r'^notes: .*$',
         'notes: "Objects of the L4 brief (first written by output/studio_cal/xd03/tools/gen_objects.py; Xeen rows since '
         '2026-11-20, lane A7). Placed: the barracks\' five Mad Dwarves (11050, 7), the far bank\'s three and the Gong '
         'Sentry Clan Sergeants (11051, 10), the two gate guards and the King\'s four Clan Guards (11052, 12), the Clan King '
         'his boss row (11053, 18), the geode\'s two hidden Mine Bats (11302, 9). Slots: 1 Xeen Mad Dwarf, 2 Xeen Spider, '
         '3 Xeen Mole. No relations block: the world\'s relations.yml makes every Xeen family the party\'s foe and sets none '
         'on another."', o)
open(L + '/objects.yml', 'w').write(o)

p = open(L + '/project.yml').read()
p = sub1(r'^world: mm7$', 'world: xeen', p)
p = sub1(r'\{monster: Dwarf, ', '{monster: Xeen Mad Dwarf, ', p)
p = sub1(r'\{monster: Spider, ', '{monster: Xeen Spider, ', p)
p = sub1(r'\{monster: Troglodyte, ', '{monster: Xeen Mole, ', p)
p = sub1(r'^  clan_king_key: 2108$', '  clan_king_key: 12021', p)
p = sub1(r'^notes: .*$',
         'notes: "Xeen design brief, level L4: L3\'s plan redrawn with the studio\'s words of 2026-11-13, surfaces, objects '
         'and wiring; a playable map (NOTES.md). Story step M3, second half (devdocs/xeen/QUESTS.md, A3\'s quests/m3.yml): '
         'kill the Clan King. World of Xeen since 2026-11-20 (lane A7): slot 1 Xeen Mad Dwarf (Mad Dwarf 11050 7, Clan '
         'Sergeant 11051 10, Clan Guard 11052 12; the spawn points fix the tier), slot 2 Xeen Spider (its spawn points at '
         'b, Cave Spider 11321 10; out of rest encounters, whose a and c tiers are under and over the band 6-12), slot 3 '
         'Xeen Mole (Tiger Mole 11430 6, Rock Mole 11431 9, Tunnel Mole 11432 12) in the warrens; placed Mad Dwarves, Clan '
         'Sergeants and Clan Guards, the Clan King his boss row 11053 (18), the geode\'s Mine Bats 11302. About 40 '
         'monsters, levels 6-12 and the King 18. The King\'s key is 12021; quest bits 110030-110031 (m3.yml). The map card '
         '(map_stats 9133, music, treasure 1) is A2\'s row from source/map_rows.yml: the block below is the studio\'s copy '
         'for its checks. exit:x1_shaft leads to X1 (xeen_x1.odm), exit:deep_cart to XD-02\'s Deep Line station '
         '(xeen_xd02.blv)."', p)
open(L + '/project.yml', 'w').write(p)

M = {229: 11050, 230: 11051, 231: 11052, 400: 11320, 401: 11321, 402: 11322, 412: 11430, 413: 11431, 414: 11432,
     205: 11300, 206: 11301, 207: 11302}
for f in ('playtest.yml', 'playtest_alarm.yml', 'playtest_hostility.yml'):
    t = open(L + '/' + f).read()
    t = sub1(r'^world: mm7$', 'world: xeen', t)
    t = t.replace('has_item(2108)', 'has_item(12021)')
    if f == 'playtest.yml':
        # A cleared room has no mad dwarf of any tier left (the placed ones are now three rows).
        t = re.sub(r'(?m)^(  - assert: \{actor_count: \{)monster_id: 229(, near: \[[^\]]*\], max: 0\}\})$',
                   lambda m: '\n'.join(m.group(1) + 'monster_id: %d' % i + m.group(2) for i in (11050, 11051, 11052)), t)
    t = map_ids(t, M)
    open(L + '/' + f, 'w').write(t)
print('ok')
