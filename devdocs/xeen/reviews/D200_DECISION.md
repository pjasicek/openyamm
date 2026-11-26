# D-200: the lake octopods never attack a party on the shore (decider, 2026-11-26)

Question: a Discord player (solo, level 110, on the shore of D4's lake; the Great Octopod's window shows Attack Water
163-245): "This looks good. But sadly, it is not attacking." The user then ruled the direction (U-19): "octopus should
act like e.g. water elemental mm6 or the sea monster in mm6 in hermits isle or something". So octopods stay in their
water and attack a party on the shore with classic AI and their ink missile, as MM6's sea serpents do (engine rows
625-627). This file settles the details.

## What the code does today (checked)

- `source/monsters.yml` family `octopods` (block 11470): `fly: Y` (from the Sea Monster stand-in), the Water missile,
  `ranged_flyer`, and D-36's `mm9_ai {archetype: swimmer, ...}` on every tier but D. Generated into `modifiers.yml`
  11470, 11471, 11472, 11474. Relation to the party `long` (`relations.yml` `xeen_octopods`, 11470-11474).
- The MM9 swimmer rule (`Mm9ActorRules.cpp` `mm9SwimmerCanTarget`: in water, only a target in water;
  `mm9SwimmerRunsFrom`: it flees a target on land) is applied outdoors in `OutdoorWorldRuntime.cpp` (~10884-10953, the
  perception gate) and in `GameplayActorAiSystem.cpp` (~5119, ~5848, the flight). A party on land is never perceived,
  so the ink never fires. Confirmed.
- The outdoor "stay in the water" step rule (D-36, `OutdoorWorldRuntime.cpp` ~12806, `outdoorSwimmerStepAllowed`) is
  keyed on `isOutdoorSwimmer()`, i.e. only on the MM9 swimmer profile.
- **How MM6's sea serpents work in OpenYAMM:** rows 625-627 are `Fly N`, `Move Free`, `Aggress`, with a Water missile,
  no MM9 profile, and the bolster kind `Swimmer` (`engine/data_tables/bolster_monsters.txt`). Outdoors that kind only
  means "may walk on water" (`canMonsterWalkOnWater`, used by `applyOutdoorWaterRestriction` and the path map). Nothing
  keeps them *in* the water: they are classic walkers that walk on water. Hermit's Isle (outa3) places them through
  spawn markers out at sea. Indoors, `Swimmer` (or the Fly column's `S`) binds an actor that starts in a scene water
  volume to that volume (`IndoorWorldRuntime.cpp` ~25690 and ~11708; this does not depend on an MM9 profile).
- **A placed leash binds a classic actor.** A placement's `leash_radius` makes any actor a post
  (`ActorBehaviorRuntime.cpp` ~1779): pursuit stops at the leash and the actor stands facing its target
  (`tacticMoveLeavesLeash`), and `keepStepOnLeash` steers every step last. D4's five octopods carry `leash_radius: 1500`,
  and D4's `gen.py` refuses a home whose leash circle comes within 500 of land (nearest land to a home 2,064, the East
  Skerry). So a leashed octopod's whole reach is open water. No engine change is needed to keep it there.
- Placements: D4 (outdoor) 3 x 11470 and 2 x 11471, groups 3-7, leash 1,500, homes at least 4,300 from the jetty, the
  Isle landing and Lakeside's waterfront; P4 (open-air BLV, sea bed -1,024, surface -64, MM9 water volumes) 5 x 11474 at
  z -512, leash 1,280; DD-14 5 x 11473 (immobile, no swimmer AI, already classic with its missile). 11472 (Kraken) is
  not placed. No MAW pack holds an octopod.

## DECISION

**Octopods become MM6-style water monsters: classic AI, walking on the water like the sea serpents, kept in the water by
their placed leash, shooting their ink at a party they notice on the shore.** This is a Xeen data change. There is no
engine change, and MM9's swimmers (Sea Monsters, Spores, Fish) and the MM6-MM8 rows stay as they are.

1. **A2, `assets_dev/worlds/xeen/source/monsters.yml`, family `octopods`** (then `gen_monsters.py`, which writes
   `monster_data.txt`, `bolster_monsters.txt`, `modifiers.yml` and `relations.yml`):
   - Delete the family's `modifiers:` (the `mm9_ai` swimmer profile). 11470, 11471, 11472 and 11474 leave
     `modifiers.yml`.
   - Add `fly: N` and `kind: Swimmer`. The `Swimmer` kind walks on water as rows 625-627 do. `Fly Y` would make a
     classic ranged flyer that hovers its radius + 512 over the party, out of the lake.
   - Add `party: short` (2,560): it notices a party within 2,560 that it has not yet engaged. Once it is hit, alerted or
     engaged it keeps the engagement range, and it shoots up to the engine's 5,120.
   - Replace `ranged_flyer:` with a comment: `# U-19/D-200: the source's Octopod hits the party from the water (A): its
     ink as a Water missile, MM6's sea serpents' way (rows 625-627)`. With `fly: N` the build no longer asks for the
     note.
   - Rewrite the D-36 comment above the tiers to say this: "D-200 (U-19): MM6's sea serpents' way; the placement's
     leash keeps it in the water".
   - Leave the speed (200), move `Free`, AI `Aggress`, missile, damage, bonuses and the Act IV numbers as they are.
   - **Tier D (11473, DD-14's cistern):** add `kind: []`, so the immobile pool-bed body is not bound to a water volume
     and lifted. Keep `fly: N`, `move: stand`, `modifiers: []`. Its only change is the family relation `short`.
   - **Tier E (11474, P4):** add `fly: Y` and
     `ranged_flyer: "P4's octopods swim inside MM9 water volumes; the volume binds a Swimmer between bed and surface"`.
     With `Swimmer` (from the family) and `Fly Y`, its placement keeps its height in the water. The volume binding keeps
     its centre in its own volume, so it attacks the walls' tops from the surface.
   - `--check` must show only these rows changing: 11470-11474 Fly / Type and ExtraType, the modifiers rows gone, and
     the relation `short`.
2. **D-87 (no ranged disabler within 5,888 of an arrival or a talking giver) counts the leash now, because the octopods
   really move and shoot.** For a placed hostile with `leash_radius > 0`, `tools/xeen/check_arrivals.py` measures the
   distance as the home distance minus the leash (a leashed actor can reach any point of its circle). This is generic.
   Run it on every map. New failures on other maps go to the orchestrator as a list and are not fixed under D-200.
   - On D4 the Paralyze Octopods (tier A) were 6,296 from the party start (the griffin perch) and 6,869 from DD-12's door
     measured from home. With the 1,500 leash that is 4,796 and 5,369: they fail. The Great Octopod's Poison3 is not a
     D-87 disabler. Fix, in this order: (a) swap the monster ids of the failing tier-A homes with tier-B homes. The
     five homes and the 3 A + 2 B count stay the same, so Act IV's count and XP do not change. (b) If a third A still
     fails, move its home inside its basin under gen.py's existing rules (leash circle at least 500 from land, at least
     2,500 from the jetty, the Isle landing and the waterfront) until home minus 1,500 is at least 5,888.
   - On P4 every octopod is Great (Poison3), so D-87 does not apply. D-122's 2,000 clear-line rule: the north group is
     3,973 - 1,280 = 2,693 from the landing, which passes.
3. **Notice rule for towns, givers and set-piece courts.** A water-bound octopod's leash circle plus 2,560 must not
   cover a town street or waterfront, a talking giver, an arrival, or a court where a set-piece fight is held. An
   unengaged octopod then never joins in there. A party that shoots at one from there gets fire back, and that is the
   party's choice.
   - D4 passes as built: home at least 4,300 minus 1,500 is 2,800 from Lakeside's jetty, the Isle landing and the
     waterfront, more than 2,560.
   - P4 fails at one place: the north group's home is 2,660 from the Whirlpool Court (the arena, the test of Water), so
     its leash edge comes within 1,380. P4's lane moves that group's home to at least 3,840 from the court
     (2,560 + 1,280), keeping D-58's other distances. Shrinking its leash instead would make it a statue.
4. **No placement moves for the attack itself.** The D4 basins stay the trap. A party now gets inked when it stands on a
   basin's shore within about 2,000 of the water's edge near an octopod, when it water-walks or swims near one, or when
   it shoots one. Because the leash circles keep 500 off land, there is no melee at the waterline (see WHY).
5. **The proof: `tests/scenarios/xeen/d4_octopods_shore.yml`** (A6; tags `[xeen, outdoor, regression]`; run it through
   `tools/heavy.sh 6`). It must not use `clear_hostiles`.
   1. A new game on `xeen_d4.odm` with one member (the reported solo case, level 50, so ink damage shows).
   2. **Town leg:** `set_pose` at the end of Lakeside's jetty facing the lake, then `advance_runtime` 30 s, then
      `assert: {party_health: {full: true}}` (nobody is inked in town).
   3. **Shore leg:** `set_pose` on the land cell A6 picks on the shore of the basin of an Octopod group (for example
      group 3 at (-2048, 0)), about 1,800-2,200 from its home and facing the water, then `advance_runtime` 30 s, then
      `assert: {party_health: {full: false}}`. Also check, by a projectile or log probe, that the hit was the octopod's
      Water missile.
   4. **Containment:** after both legs, every 11470/11471 actor stands on a water tile within 1,500 of its home. Use the
      runner's actor position probe, or `tools/octo_check.py` (D4's own checker) over the scenario log.
   - P4's lane adds `tests/scenarios/xeen/p4_octopods_walks.yml`. A party standing on a wall top within 2,000 of an
     octopod is hurt within 30 s. Every 11474 stays inside `water:sea` (z between -1,024 and -64) and within 1,280 of
     home. The party at the court and the landing for 30 s each stays at full health (after the home move in 3).
   - Regressions to rerun: D4's `playtest_hostility.yml`; `tests/scenarios/xeen/d4_skerry_water_walk.yml` (it clears
     hostiles, so it should pass unchanged); DD-14's walk; `check_arrivals.py` on D4 and P4; the MM9
     `tests/scenarios/mm9/ai/` swimmer scenarios (they should not change, since no engine code changes);
     `openyamm_unit_tests` `*Mm9*`.
   - Update D4's `playtest_hostility.yml`. Its D-36 step "on the East Skerry they stay at home" no longer holds: an
     octopod within 2,560 now comes to its leash edge and shoots. It becomes "on the East Skerry the nearest octopod
     attacks from the water and stays within its leash".
6. **Notes.** A6 rewrites the "The octopods" paragraph and the D-87 section of `devdocs/xeen/briefs/d4/L4/NOTES.md`.
   A6's planes sub-agent writes the P4 note, the orchestrator the `source/map_rows.yml` comment (~354: still the trap,
   counted in Act IV, now one that bites the shore), and A2 the `monsters.yml` `where:` line (`D4 lake (trap; shoots
   the shore, D-200)`).

## WHY

- **U-19 settles the "whether".** The user named MM6's sea serpents and water elementals, which are classic AI. D-36's
  water-only trap was the MM9 Sea Monster's rule (BaseSwim.inc), and on D4 it made the X2 p8 ink missile dead data.
- **Data, not an engine rule.** Everything the user wants already exists:
  - the `Swimmer` kind walks on water, as on Hermit's Isle;
  - the placed leash, enforced last on every step and guaranteed by gen.py to lie in open water, keeps the octopod in
    its basin;
  - the classic ranged attack does the rest;
  - indoors (P4), the `Swimmer` kind already binds a monster that starts in a water volume to it.

  Rejected:
  - Changing `mm9SwimmerCanTarget` / `RunsFrom`, or adding a "shoots from water" flag to the MM9 loop. That changes
    MM9's swimmer behaviour, or forks it, for one Xeen family.
  - Keying D-36's outdoor step rule on the `Swimmer` kind. That would change MM6-MM8's sea serpents and water
    elementals: they walk ashore today, and the user holds them up as the model.
  - A new `water_bound` modifier. It is only needed if a future map wants leashless or spawned water monsters, or
    octopods that hug the shoreline for melee. Then A1 adds it generically by extending `isOutdoorSwimmer()` to the
    Fly column's `S` / a modifier, with no MM6-MM9 row using it today.
- **Why `fly: N`:** a classic `Fly Y` row with a missile is MM's ranged flyer. Outdoors it rises to hover over the party,
  and without the MM9 profile nothing clamps it to the surface. MM6's serpents are `Fly N`. P4 is the exception
  (tier E `fly: Y`), because there the water volume clamps a bound Swimmer between bed and surface, and its placement
  needs the flyer's "keep my height" (the water's `swims`-only placement rule does not cover the kind).
- **Why `short`:**
  - With `long` (the 10,240 engagement range) every octopod would notice Lakeside's waterfront from its home and shell
    it from 2,800 away (5,120 ink range). That breaks town safety (D-15's spirit; Lakeside is a town of Act IV).
  - With `medium` (5,120) the same happens at the leash edge.
  - `short` (2,560) keeps D4's town clean without moving a home, and still bites any party that stands on a basin's
    shore near an octopod.
- **The source's adjacency:** in Xeen an octopod hits the party from a water square next to it. Here the leash circles
  stay 500 off land, so the octopods never melee at the waterline. Their attack is the ink, which is what the source
  note (X2 p8) and the player ask for. Letting them reach the shoreline would need the engine water-tile rule above.
  It is not worth it for one family, and it would bring them within reach of the jetty.
- **D-87:** until now the octopods could never shoot a party on land, so D-87 measured them from home only. They now
  move up to 1,500 and shoot, so the honest measure subtracts the leash. Swapping A and B homes keeps D4's balance
  exactly.
- **Solo vs party:** no special case. The ink hits one member, as MM's missiles do. A solo character takes every shot
  but can step back out of sight or out of range. Act IV's Great Octopod at 6D8+18 (about 45 a hit, more under MAW's
  scaling) with Poison3 is a fair shore threat for a level 50-60 party member. The reported level-110 solo hero is
  exactly the player who wants the fight.

## WHO ACTS

- **A2** (monsters.yml family and tiers D/E, regenerate tables, `--check`): small, under an hour.
- **A6**:
  - D4: `check_arrivals.py` leash measure, the A/B home swap if needed, rebuild and install, hostility playtest update,
    NOTES, the new `d4_octopods_shore.yml`: half a day.
  - A6's planes sub-agent, P4: move the north group's home, `p4_octopods_walks.yml`, NOTES: a few hours.
- **Orchestrator:** the `map_rows.yml` comment and the DECISIONS row; collect any other maps' leash-measure failures
  from `check_arrivals.py`.
- **A1:** none (only if a scenario shows a classic leashed post refusing to shoot at the leash edge, which is a bug
  for A1).

## REVERSIBLE

Yes: one family block and two placements. Confidence 75 %. The two risks are a classic post's shot at its leash edge
and P4's volume binding with `Fly Y` + `Swimmer`. The two scenarios prove both, and if either fails the fix is A1's,
not a data workaround.

## SUMMARY ROW

| D-200 | 2026-11-26 | The lake octopods never attack a party on the shore (U-19's details) (decider) | Octopods (11470-11474) become MM6 sea serpents' kind: drop D-36's `mm9_ai` swimmer profile, `fly: N`, `kind: Swimmer` (walks on water), party relation `short` (2,560); the placed leash (D4 1,500, circles ≥ 500 off land by gen.py) keeps them in the water, classic AI shoots the Water ink up to 5,120. Tier D (DD-14) `kind: []`, else unchanged; tier E (P4) `fly: Y` + Swimmer (bound to its water volume). No engine change; MM6-MM9 rows unchanged. D-87 measures a leashed placement at home − leash: D4's Paralyze Octopods failing that swap homes with the Great Octopods (count and XP kept). Leash + 2,560 clear of towns, givers, arrivals and set-piece courts: D4 passes (2,800); P4's north group moves ≥ 3,840 from the Whirlpool Court. Proof `tests/scenarios/xeen/d4_octopods_shore.yml` (solo; jetty 30 s unhurt, basin shore 30 s inked, all octopods on water within leash) and `p4_octopods_walks.yml`. 75 % | A2 (monsters.yml), A6 (D4, check_arrivals, scenario), A6 planes (P4), orchestrator |
