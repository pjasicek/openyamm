"""Party level per chapter for MM9 quest XP: original amounts against the 2026-11-06 proposal (QUEST_XP_AUDIT.md).

Small awards (up to 15,200) keep their amounts in the chapter of their map. Promotions keep theirs; a party of five is
assumed to take four first-tier and four second-tier promotion quests. Story and large awards are placed by hand at
the chapter and monster level of the content they reward, and the proposal caps each at 1,500 x that level.
"""
import math, subprocess, sys

# (label, original XP, chapter, content level)
STORY_LARGE = [
    ('Rescue Ivsar (Drangheim Prison)', 42000, 2, 20), ('Clear Anskram Keep', 20000, 1, 10),
    ('Sigmund: Crona Kiga (Chasm of the Dead)', 52000, 3, 30), ('Markel: Dook (Dook\'s Castle)', 40000, 2, 20),
    ('Sigmund: Fort Stenig spy', 32000, 2, 15), ('Markel: Ivan / Book of Rules', 26000, 2, 15),
    ('Orb of Linking', 20000, 3, 25), ('Nicolai\'s job', 20000, 2, 20), ('Tryggva: Yanmir', 58000, 4, 45),
    ('Thronheim: prize at the Thing', 53000, 2, 20), ('Black Orb of Knowledge', 50000, 4, 40),
    ('Kira: Honk worshippers', 40000, 3, 25), ('Tryggva: break the ice', 30000, 3, 25), ('Unite the clans', 26500, 3, 30),
    ('Brewmaster', 20000, 3, 25), ('Training Hall', 20000, 4, 40), ('Yorwick sheep', 20000, 4, 45),
    ('Sven: Thjorad / dragon', 68004, 5, 60), ('Afterworld fire 1', 52000, 5, 70), ('Afterworld fire 2', 52000, 5, 70),
    ('Afterworld fire 3', 52000, 5, 70), ('Afterworld reborn', 52000, 5, 70), ('Fateman', 46000, 5, 70),
    ('Capstone of Order obtained (Thorir, the capstone or Igrid: one of three)', 146000, 4, 55), ('Stop Tamur Leng', 412000, 5, 85),
    ('Forad Darre dies', 194000, 4, 55), ('Kira: Mountain Pass', 120000, 3, 35), ('Lindisfarne relic', 80000, 3, 40),
    ('Writ of Fate (Verhoffin)', 162000, 4, 60), ('Capstone placed', 154000, 4, 60),
    ('Dark Passageway (Igrid)', 92000, 4, 60), ('Yorwick: Sven', 114000, 4, 50),
    ('Bathhouse', 80000, 4, 65), ('1000 Terrors: Njam imprisoned', 234000, 5, 90),
    ('Arslegard: Njam chase', 226000, 5, 90), ('Hall of the Gods: Krohn', 218000, 5, 90),
    ('Arslegard: Writ man', 170000, 5, 70), ('Golden Honk', 80000, 5, 80),
]
SMALL = {1: 52000, 2: 47000, 3: 88800, 4: 18000, 5: 22000}       # audit "small" group summed by chapter
PROMO = {2: 4 * 24300, 3: 4 * 63000}  # Scholar's 24,500 and 11,000 are alternatives (key 205)                               # first and second tier, four of each
PROPOSED_SECOND_TIER = 50000
KILL = {1: 0.10e6, 2: 0.25e6, 3: 0.87e6, 4: 1.84e6, 5: 0.88e6}     # economy.py at +20-40% density, split over 5
BAND = {1: 12, 2: 25, 3: 40, 4: 70, 5: 100}
lv = lambda x: (1 + math.sqrt(1 + x / 125)) / 2
for name, cap in (('original', None), ('proposal', 1500)):
    cum = 0.0; out = []; total = 0
    for c in range(1, 6):
        q = SMALL.get(c, 0) + PROMO.get(c, 0)
        q += sum(min(x, cap * l) if cap else x for _, x, ch, l in STORY_LARGE if ch == c)
        total += q
        cum += q + KILL[c] / 5
        out.append(f'ch{c} {lv(cum):5.1f} (band to {BAND[c]})')
    print(f'{name:9} quest XP {total/1e6:4.2f}M per member | ' + ' | '.join(out))
