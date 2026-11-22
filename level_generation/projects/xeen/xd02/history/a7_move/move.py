import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# Lane A7, "into the world" for XD-02 (2026-11-20): MM7 stand-in rows -> Xeen rows. Edits text in place (by id block).
import re, sys
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4'

def block_edit(text, oid, fn):
    """Apply fn to the YAML list block that starts with '  - id: <oid>' (up to the next '  - ' or top-level key)."""
    m = re.search(r'(?m)^  - id: ' + re.escape(oid) + r'\n(?:(?!  - |\S).*\n)*', text)
    if not m:
        sys.exit('no block ' + oid)
    new = fn(m.group(0))
    if new == m.group(0):
        sys.exit('no change in ' + oid)
    return text[:m.start()] + new + text[m.end():]

def sub1(pat, rep, s):
    out, n = re.subn(pat, rep, s, count=1, flags=re.M)
    if n != 1:
        sys.exit('pattern not found: ' + pat)
    return out

o = open(L + '/objects.yml').read()
for i in (1, 2, 3):
    o = block_edit(o, f'monster:cocoon_spider_{i}', lambda b: sub1(r'^    monster: 401$', '    monster: 11321', b))
for oid in ('mole_burrow_1', 'mole_burrow_2', 'mole_flood_1', 'mole_flood_2'):
    o = block_edit(o, 'monster:' + oid, lambda b: sub1(r'^    name: Tiger Mole\n', '',
                                                       sub1(r'^    monster: 412$', '    monster: 11430', b)))
for i in (1, 2, 3):
    o = block_edit(o, f'monster:tally_guard_{i}', lambda b: sub1(r'^    monster: 229$', '    monster: 11051', b))
o = block_edit(o, 'monster:tallymaster', lambda b: sub1(
    r'^    notes: .*$',
    '    notes: "The fourth clan guard, behind the tally table: an ordinary Clan Guard (11052, level 12; CHANGES A1, '
    'XD02-1: XD-02 has no boss in MAPS §0). Until the rebase of 2026-11-20 the Tallymaster, a named Dwarven '
    'Lieutenant (230, level 20, hp 80, immobile). He carries nothing: the brake key is in the strongbox behind him. '
    'The id stays for the lock."',
    sub1(r'^    monster: 229$', '    monster: 11052', b)))
# The deep dwarf spawn points at tier b (Clan Sergeant 10); the upper ones stay a (Mad Dwarf 7).
for oid in ('deep_station', 'stope_floor_n', 'turntable_n'):
    o = block_edit(o, 'spawn:' + oid, lambda b: sub1(r'^    tier: a$', '    tier: b', b))
# relations: every Xeen family is the party's foe and leaves the others alone by the world's relations.yml.
o = sub1(r'^relations:\n(?:  - .*\n)+', '', o)
o = sub1(r'^notes: .*$',
         'notes: "Objects of the L4 brief (written by output/studio_cal/xd02/tools/gen_objects.py; Xeen rows since '
         '2026-11-20, lane A7). Placed: the tally room\'s three guards Clan Sergeants (11051, level 10) and the fourth, '
         'once the Tallymaster, a Clan Guard (11052, level 12); the four Tiger Moles 11430 (6); the cocoon\'s three '
         'Cave Spiders 11321 (10). Slots: 1 Xeen Mad Dwarf, 2 Xeen Spider, 3 Xeen Bat. No relations block: the world\'s '
         'relations.yml makes every Xeen family the party\'s foe and sets none on another. The brake key is 12011."', o)
open(L + '/objects.yml', 'w').write(o)

p = open(L + '/project.yml').read()
p = sub1(r'^world: mm7$', 'world: xeen', p)
p = sub1(r'\{monster: Dwarf, ', '{monster: Xeen Mad Dwarf, ', p)
p = sub1(r'\{monster: Spider, ', '{monster: Xeen Spider, ', p)
p = sub1(r'\{monster: Bat, ', '{monster: Xeen Bat, ', p)
p = sub1(r'^  brake_key: 2111$', '  brake_key: 12011', p)
p = sub1(r'^notes: .*$',
         'notes: "Xeen design brief, level L4: L3\'s rooms redrawn with the studio\'s words of 2026-11-13, surfaces, '
         'objects and wiring; a playable map (NOTES.md). Story step M3, first half (devdocs/xeen/QUESTS.md, A3\'s '
         'quests/m3.yml). World of Xeen since 2026-11-20 (lane A7): slot 1 Xeen Mad Dwarf (Mad Dwarf 11050 7, Clan '
         'Sergeant 11051 10; the spawn points fix a or b, never c), slot 2 Xeen Spider (Giant Spider 11320 5), slot 3 '
         'Xeen Bat (Giant Bat 11300 3); placed the tally room\'s Clan Sergeants 11051 and Clan Guard 11052 (once the '
         'Tallymaster), the Tiger Moles 11430, the cocoon\'s Cave Spiders 11321. About 55 monsters, levels 3-12. The '
         'brake key is 12011; quest bits 110020-110021 (m3.yml); the pools\' per-character bits are 11021-11024 '
         '(provisional). The map card (map_stats 9132, music, treasure 1) is A2\'s row from source/map_rows.yml: the '
         'block below is the studio\'s copy for its checks. exit:x1_adit leads to X1 (xeen_x1.odm), exit:deep_mine to '
         'XD-03 (xeen_xd03.blv); exit:x4_adit still points at Emerald Island (X4 is built in phase 2)."', p)
open(L + '/project.yml', 'w').write(p)
print('ok')
