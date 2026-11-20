"""Build tools/mm9_import_discovery/mm9_quest_xp_profile.yml from the quest XP audit (BALANCE_PLAN.md section 5.4).

Run from the repository root after quest_xp_audit.py. Rule (decided 2026-11-06 from fit_check.py):
  - an award pays at most 1.5 levels' worth at its content level in chapters 1-2 and 0.5 from chapter 3
    (1,000 x level is one level's worth), never below 2,000;
  - a promotion pays at most 1.5 levels' worth: 1,500 x level;
  - the content level is the count-weighted monster level of the chapter the quest's work belongs to.
Awards whose work lies in another chapter than the map that pays them are placed by hand below.
"""
import csv, re, sys

CHAPTER_LEVEL = {1: 7, 2: 11, 3: 25, 4: 37, 5: 45}   # fit_check.py, monsters weighted by count at the planned density
AWARD_CAP_LEVELS = {1: 1.5, 2: 1.5, 3: 0.5, 4: 0.5, 5: 0.5}
PROMOTION_CAP_LEVELS, FLOOR = 1.5, 2000

# (map, routine, original XP) -> chapter of the quest's work, where it differs from the map's chapter.
CONTENT_CHAPTER = {
    ('sturmfordcity', 'ivsar', 42000): 2, ('sturmfordcity', 'loveletter2', 15200): 3,
    ('sturmfordcity', 'gladiator', 63000): 3, ('drangheimcity', 'cronakiga', 52000): 3,
    ('drangheimcity', 'checkall', 20000): 3, ('drangheimcity', 'promo', 63000): 3,
    ('guberlandcity', 'priest', 63000): 3, ('guberland', 'capstone', 146000): 4,
    ('frosgardcity', 'stoptamur', 412000): 5, ('frosgardcity', 'ondeath', 194000): 4,
    ('frosgardcity', 'yanmir', 58000): 4, ('thronheimcity', 'blackorb', 50000): 4,
    ('thjorgard', 'onbreak', 20000): 4, ('greatgate', 'exitin', 46000): 4, ('arslegardcity', 'exitin', 46000): 4,
    ('frosgard', 'promo', 63000): 3, ('arslegardcity', 'united', 26500): 3,
    ('thjorgardcity', 'toscholar', 24500): 2, ('thjorgardcity', 'toscholar', 11000): 2,
    ('guberlandcity', 'dook', 40000): 3,
}
# (script, routine, original XP) -> the key the award really sets, where the audit's last given key is another one
# (checked against the original SCR by the rework session, 2026-11-06).
KEY = {('npc129.scr', 'priest', 63000): 261, ('bjarni.scr', 'loveletter2', 15200): 151,
       ('sixfires.inc', 'Absolution', 52000): 492, ('npc336.scr', 'OnReborn', 52000): 391}
PROMOTION = re.compile(r'promo|gladiator|ranger|priest|paladins|toscholar|nurtigan', re.I)
PROMOTION_ROWS = {('thjorgardcity', 'reward', 63000), ('lichlab', 'onpromo', 63000)}

rows = list(csv.DictReader(open('output/mm9_balance/quest_xp_audit.tsv'), delimiter='\t'))
out, totals = [], {c: [0, 0] for c in range(1, 6)}
for r in rows:
    key = (r['map'], r['routine'].lower(), int(r['xp']))
    chapter = CONTENT_CHAPTER.get(key, int(r['chapter']))
    level = CHAPTER_LEVEL[chapter]
    promotion = bool(PROMOTION.search(r['routine'])) or key in PROMOTION_ROWS
    cap = (PROMOTION_CAP_LEVELS if promotion else AWARD_CAP_LEVELS[chapter]) * 1000 * level
    xp = min(int(r['xp']), max(FLOOR, int(round(cap / 250.0)) * 250))
    totals[chapter][0] += int(r['xp']); totals[chapter][1] += xp
    if xp != int(r['xp']):
        # One entry per script and routine that pays this award (other turn-in places, alternative branches).
        for occurrence in r['occurrences'].split():
            script, routine = occurrence.split(':', 1)
            out.append((script, routine, int(r['xp']), xp, chapter, level, promotion, r['map'], r['npc'],
                        KEY.get((script, routine, int(r['xp'])), (r['keys given'].split() or [''])[-1])))

with open('tools/mm9_import_discovery/mm9_quest_xp_profile.yml', 'w') as f:
    f.write('# MM9 quest XP balance profile (devdocs/mm9_rework/BALANCE_PLAN.md section 5.4, QUEST_XP_AUDIT.md).\n'
            '# mm9_scr_to_lua.py emits MM9.giveExperience with `xp` for a GiveExp of `original` in `routine` of `script`;\n'
            '# `key` is the MM9 quest key the award sets, for converters that know the quest rather than the script.\n'
            '# Built by devdocs/mm9_rework/balance_prototypes/quest_xp_profile.py; edit the rule there, or an entry here.\n'
            '# Rule: at most 1.5 levels\' worth in chapters 1-2 and 0.5 from chapter 3 (promotions 1.5) at the chapter\'s\n'
            '# monster level, never below 2,000.\n'
            'format_version: 1\nawards:\n')
    for script, routine, original, xp, chapter, level, promotion, mid, npc, key in sorted(out, key=lambda o: (o[4], o[7])):
        f.write(f'- script: {script}\n  routine: {routine}\n  original: {original}\n  xp: {xp}\n'
                + (f'  key: {key}\n' if key else '')
                + f'  # {mid}, {npc}; chapter {chapter}, level {level}{", promotion" if promotion else ""}\n')
print(len({(o[2], o[7], o[8]) for o in out}), 'awards changed,', len(out), 'profile entries')
for c in range(1, 6):
    print(f'chapter {c}: original {totals[c][0]/1e3:6.0f}k -> {totals[c][1]/1e3:5.0f}k')
print(f'total: {sum(v[0] for v in totals.values())/1e6:.2f}M -> {sum(v[1] for v in totals.values())/1e6:.2f}M')
