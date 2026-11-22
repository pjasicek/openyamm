# D-91: druid bodies, blind cave mouths, D6's split blast door (2026-11-22, fourth orchestrator's decider)

I recommend changing all three: re-place the two druids on bodies that match their portraits, turn the five dead-end cave mouths into shallow shelters or blocked mouths with no new dungeons, and rebuild D6's blast door so each leaf shows the whole picture. I edited no files.

## 1. The seasonal druids' bodies

**DECISION:** Keep the portraits and change the bodies, and fix the pronouns to match.
- The Autumn Druid (4321) moves from male peasant row 362 to Druidess A (row 517). Luna already stands on that row.
- The Winter Druid (4529) moves off Druidess A onto an old man's robed body. S chooses it from the robed male families (Mage 292–294, Cleric 46–48 or 217–219, Monk 304–306). A new `characters:` row is best, Sablewing style, so the name shows without waiting for A1's F9-R2 name fix.
- Make the set of four consistent: the Summer Druid (X6, a woman on peasant 377) goes to Druidess A, and the Spring Druid (X1, a man on peasant 371) goes to the Winter Druid's row.
- `key_npcs.py` `BODY_EXPECTATIONS` gets entries for 4321, 4529, 4048 and 4601.
- Pronoun fixes for the Autumn Druid ("his" becomes "her"):
  - `briefs/x4/L4/sketch.yml:299`
  - `briefs/x4/L4/playtest.yml:581`
  - `tools/xeen_site/story/promotions.yml:52`
  - `tools/xeen_site/story/side_cloudside.yml:269`
- Pronoun fix for the Winter Druid ("her" becomes "his"): `briefs/x5/L4/playtest.yml:822`.

**WHY:**
- The MM4 source says nothing about their genders. `ORIGINAL_LINES.md` has the relay lines without pronouns, and Q-C1 in `research/MM4_CLOUDS_CONTENT.md` names only the seasons.
- The portraits were a deliberate design. `level_generation/ui/xeen_npc_portraits_20261120/descriptions.yml` asks for a "druid woman" for Autumn and an old bearded man for Winter. The four portraits form a set: Summer and Autumn are women, Winter and Spring are old men.
- The portraits are finished, good art. The mismatch is only a body picked off a peasant row and pronouns written around it.
- Moving a body costs one placement line per map. Redrawing portraits would throw away approved art to fit a placeholder.

**WHO ACTS:**
- S: the male druid row and its binding.
- A5: X4 and X6 now; X1 at its pending cave-mouth rebuild. X6 goes in the same batch as its question 2 work.
- A6: X5.
- A3 or the site owner: the two story files.
- Each map lane reruns `key_npcs.py --write` after its install.
- npc.txt does not change, so A4 has nothing to do.

**REVERSIBLE:** Yes. These are placement rows and text.

## 2. Dead-end cave mouths

**DECISION:** No dark mouth may lead nowhere. Each of the five becomes one of two shapes, and none gets a new dungeon:
- **Shelter:** a shallow, open rock overhang. The back wall and floor can be seen and are lit from the approach, there is a fire or light inside, and the contents sit under it.
  - Sablewing's cave: he and his hoard sit in it, which is what D-5.2 intended.
  - The orc den, which is also the gate pickets' den: hides and poles, with the den chest moved under the overhang.
- **Blocked:** rubble and fallen timbers fill the mouth at its face, with a short click line ("The adit has fallen in.").
  - The miner's adit. Its title already says its props have fallen.
  - X6's werewolves' den, a barrow on level land with no way in: either blocked, or a mound with no doorway, and the pack stays outside it.

The "There is no way on" line is withdrawn.

To make this hold for every map, `door_check.py`'s `caves.blind_mouth` becomes an error for any `cave_mouth` with no `into` (way in) unless its form is shelter or blocked. A6's kit (`house_doors.py`) supplies the two forms. If the studio's `cave_mouth` can't express them, A1 adds them through REQUESTS. The F8 agent found that a rock back placed a short way in "read as a solid lump", so the shelter has to pass a capture check: from the approach, the floor visibly goes in and the back wall is lit.

**WHY:**
- In MM6–MM8 a dark opening in rock means a way in. Barrows, mines and dens are entrances, and decorative niches are shallow and visibly closed. The user's "can't go in?" is that convention speaking.
- A click line explains the fault rather than removing it.
- Five one-room BLVs would each need a build, a bake, a walk test, an act-balance count and D-89's name test. That cost is out of proportion for set dressing, especially with D-89's rebuilds already queued.
- A shelter shows its contents at a glance, so it needs no name test.

**WHO ACTS:**
- A6: the kit forms and the `door_check` rule. A1 only if the studio needs a change.
- A5: X7 (folded into the X7 rebuild F9's job is waiting on, so it is one reconversion) and X6 (in the finisher batch or the next one).

**REVERSIBLE:** Yes. Each is one sketch attribute, and any of them can later gain an `into` and a real BLV if a quest ever needs one.

## 3. D6's blast door (`swdoora`)

**DECISION:** It must change. Today the 512-wide gate has two 256 leaves, each showing half the picture, with the right leaf showing the left half mirrored (`door_check.py` lines 141–143). Each leaf should instead show the whole `swdoora` once, with the right leaf mirrored. Delete the `split` exemption in `door_check.py`, so that a single door's picture split over a pair becomes `doors.part_picture` again.

**WHY:**
- `swdoora` is a complete single-leaf door, not one wing of a pair. It is square, framed on all four sides, with an off-centre boss (`level_generation/textures_x4/masters/mm6/swdoora.png`).
- Half of it on each leaf, mirrored, is neither "each leaf its own wing picture" nor the picture shown whole. It shows the left half twice and only slivers of the boss, and repeating a half is the tiling the rule forbids.
- The halves are also stretched twice as wide as they are tall: half the width over 256 against the full height over 256. That breaks the texture-fit rule.
- Two whole square panels on 256×256 leaves fit without stretching. Mirroring the right one turns the bosses toward the seam, which reads as a proper blast-door pair.
- The exemption was written to let this case pass. It should not survive.

**WHO ACTS:** A6 (the D6 gatehouse, the kit and `door_check`). A1 mirrors the rule in `oymap audit --doors`. A8 checks that DD-17's matching inside gate does not use the same split.

**REVERSIBLE:** Yes. It is one door's leaves and a check.

## Summary row

| D-91 | 2026-11-22 | Druid bodies, blind cave mouths, split blast door | Portraits win: the Autumn Druid goes on Druidess A, the Winter Druid on a robed old man's row (Summer and Spring follow at their maps' rebuilds), pronouns fixed and `BODY_EXPECTATIONS` added. No dark mouth leads nowhere: Sablewing's cave and the orc den become lit open shelters, the adit and the werewolves' den are blocked, no new BLVs, `caves.blind_mouth` is an error and the "no way on" line is withdrawn. D6's gate shows a whole `swdoora` per 256 leaf (right one mirrored) and `door_check`'s split exemption is removed. | S (male druid row), A5 (X1, X4, X6, X7), A6 (X5, D6, cave and door kits, `door_check`), A1 (studio forms if needed, audit rule), A3 or site owner (story texts), A8 (check DD-17's gate) |
