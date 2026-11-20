# Talent tree v2: simulation results (2026-11-14)

What [TALENT_TREE_V2.md](TALENT_TREE_V2.md) does against the real map groups of the solo playthrough, next to today
and the current talent tree. Interactive tables are on the solo page, section "Talent tree v2 for the solo run";
the talent page mockups are in `level_generation/ui/solo_talents_v2_20261114/`. Nothing is built in the game.

## How it was run

- **Harness** (`harness/SoloHarness.cpp`):
  - Cases take `talents:` (ranks) and `cap_raise:` (Lone Discipline's Bodybuilding cap). The options carry
    `:solo`, so MAW's rules apply the solo run's passives (Weapon Training, Marksman, Attunement, Resolve) as the game
    does.
  - [gen_talent_pool.py](../scripts/gen_talent_pool.py) writes three variants of every gear case:
    - `v1`: the current tree;
    - `v2`: tree v2, points from levels;
    - `v2L`: tree v2 with Legend points.
  - With the Bodybuilding cap lifted, the character trains Bodybuilding to the new mastery's threshold.
  - Lone Discipline measured in the harness: Death Knight HP ×1.5, Seraph ×1.6, Assassin ×1.6, Archer ×1.35. The
    earlier ×2.4 was a proxy that assumed skill 77.
- **Fights** ([talentfight.py](../scripts/talentfight.py)): realfight's monsters, damage-taken grid, resistances,
  leech, regeneration and Mana Shield. Without range and talents it agrees with realfight on 99 %+ of pulls; the
  exception is the Assassin's energy, which it leaves out.
  - **New: range.** Groups start 1200 units away. Shooters stand off at 600; the rest walk in at their monster speed.
    A melee solo walks too, or uses Charge. A ranged or caster solo shoots, and escapes only with Blink, Disengage or
    Binding Circle (no free back-pedalling, a conservative assumption).
  - **New: talents.** Every active fires when it is worth the most within its cooldown. The new talents, keystones
    and Legend lines use the proposal's numbers. Talent ranks and keystones come from
    [talents_v2.py](../scripts/talents_v2.py)'s allocation, which applies each role's priority list to that level's
    points.
- **Setups:**
  - today (old model, without range);
  - today;
  - current tree (1 point per 10 levels);
  - tree v2 (levels only);
  - v2 + grinding (Legend points: 150 at level 500);
  - end of grinding (300 Legend points at level 500).
- **Grid:** 8 difficulties × levels 10/50/200/500 × 22 builds × 5 playthroughs. The Doom, Road to Insanity and BM
  runs also take one keystone or talent away at a time.
- **Work files:** `tf_main/end/norange/ablate/aoe.json` and `.md` in the work directory.

## Melee builds: weakest / median of pulls of four, seconds per monster

| Difficulty, level | Old model | Today | Current tree | Tree v2 | + grinding | End of grinding |
| --- | --- | --- | --- | --- | --- | --- |
| Nightmare 500 | 83 / 100 · 2.1 s | 81 / 96 · 3.1 | 87 / 100 · 2.2 | 100 / 100 · 1.7 | 100 / 100 · 1.5 | 100 / 100 · 1.3 |
| Doom 500 | 38 / 70 · 2.0 | 35 / 55 · 3.0 | 52 / 80 · 1.8 | 82 / 98 · 1.8 | 97 / 100 · 1.5 | 100 / 100 · 1.3 |
| Road to Insanity 500 | 25 / 54 · 2.1 | 25 / 47 · 3.1 | 44 / 73 · 1.8 | 77 / 94 · 1.7 | 91 / 100 · 1.5 | 100 / 100 · 1.3 |
| Beyond Madness 200 | 52 / 98 · 2.6 | 52 / 98 · 3.5 | 87 / 100 · 2.0 | 99 / 100 · 1.8 | 99 / 100 · 1.8 | – |
| Beyond Madness 500 | 0 / 3 · 3.5 | 0 / 2 · 4.2 | 1 / 8 · 2.9 | 23 / 43 · 3.2 | 46 / 79 · 2.9 | 79 / 90 · 2.6 |

**Whole groups at once, Beyond Madness 500, v2 + grinding:** 31 / 53 % (weakest / median), 2.6 s per monster.

Doom, Road to Insanity and BM at level 10 are 0–33 % in every setup. That is the early solo start on those
difficulties, which one talent point does not change.

## Ranged builds and casters, level 500, pulls of four

| Build | Difficulty | Old model | Today | Current tree | Tree v2 | + grinding | End |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Archer | Road to Insanity / BM | 50 / 1 | 66 / 8 | 59 / 12 | 99 / 69 | 100 / 89 | 100 / 97 |
| Arch Mage | Road to Insanity / BM | 17 / 0 | 26 / 2 | 36 / 4 | 91 / 52 | 100 / 72 | 100 / 82 |
| Master of Elements | Road to Insanity / BM | 24 / 0 | 30 / 3 | 39 / 10 | 80 / 62 | 90 / 74 | 91 / 85 |
| Priest of Light | Doom / BM | 4 / 0 | 6 / 2 | 20 / 2 | 36 / 3 | 49 / 8 | 72 / 19 |
| Dragon | BM | 84 | 87 | 88 | 94 | 100 | 100 |

**Range alone is worth a lot to casters.** Comparing "old model" with "today", the Arch Mage goes 21 → 35 % on
Doom. Blink, Binding Circle and Overload carry the rest:
- the Arch Mage on Road to Insanity goes 36 → 91 % from the current tree to tree v2;
- removing Overload costs 15–17 points on BM;
- removing Blink costs 5–15.

**The Priest stays far behind.** It is a healer with little damage, so it needs its own answer, for example TALENTS
M4's Battle Cleric or Zealot.

## What each talent does (BM level 500, v2 + grinding, pulls of four)

Taking one away, in points of the share of monsters beaten, median over the builds that have it, and the worst:

| Removed | BM | Road to Insanity | Doom |
| --- | --- | --- | --- |
| Oath | −13, worst −27 (Death Knight) | −1, worst −8 | 0, worst −4 |
| Overload (casters) | −15, worst −17 | −10 | −4 |
| Blink (casters) | −5, worst −7 | −8, worst −11 | −6, worst −15 |
| Archon (casters) | −4, worst −28 (Arch Mage) | −16 (Arch Mage) | −9 |
| Unbroken | 0, worst −24 (Arch Mage) | 0 | 0 |
| Bloodthirst | −3, worst −11 (Champion, sword and shield) | 0 | 0 |
| Piercing Arrows, Deadeye (Archer) | −5 each | 0 | 0 |
| Binding Circle | −2 | 0 | 0 |
| Warlord | 0 | 0 | 0 |
| Sweeping Blows, Cleave, Whirlwind (one at a time) | 0 | 0 | 0 |

**Melee area talents together** (all three removed; pulls of four / whole groups):

| Setting | Pulls of four | Whole groups |
| --- | --- | --- |
| BM, v2 + grinding | 46 / 79 % · 2.9 s | 31 / 53 % · 2.6 s |
| BM, without Sweeping Blows, Cleave and Whirlwind | 41 / 78 % · 3.5 s | 16 / 47 % · 3.6 s |
| BM, with Cleave or Whirlwind alone | 41–42 / 78 % · 3.5 s | 16–17 / 47 % |
| Road to Insanity, with and without the three | | 84 / 97 % against 67 / 88 % |

**Usage, melee median at BM 500:**

| Setup | Cleave | Whirlwind | Sweeping Blows | Charge |
| --- | --- | --- | --- | --- |
| Current tree | 4.3 uses/min, 12 % of damage | 3.6, 5 % | – | 10.5, 16 % |
| v2 | 0.1, 0 % | 0.5, 0 % | 9 swings/min with extra targets, 26 % | 6.8, 9 % |

Frenzy fires on every cooldown. Shield Wall fires only for shield builds.

## Findings

1. **The tree can close the gap without trivialising anything.**
   - On BM at level 500, the melee median goes 2 → 43 % from levels alone, 79 % with the grinding points, and 90 %
     at the end of grinding (whole groups 53 % at 2.6 s per monster).
   - Road to Insanity and Doom become 100 %.
   - Nightmare's time per monster halves (3.1 → 1.5 s). That is faster, not trivial, and it is the user's accepted
     price for ungated grinding.
2. **The Oath is the keystone that matters for melee** (−13 on BM, −27 for the Death Knight). Casters lean on
   Overload, Blink and Archon.
3. **Sweeping Blows makes Cleave and Whirlwind dead picks.** Once it is learned they fire about once a minute. The
   three together are worth whole groups (BM weakest 16 → 31 %) and 20–25 % less time per monster.
   - **Proposal:** keep Sweeping Blows as the melee area talent, needing Cleave.
   - Make Cleave a burst active (for example 150 % to everything in the arc, then the cooldown).
   - Drop Whirlwind, or make it a defensive spin (stagger everything around for 1 s).
4. **Warlord adds nothing in this model:** pulls of four rarely put more than two monsters next to you. Replace it,
   since the mockups also showed that each role needs five keystones for five slots. Candidates:
   - a leech keystone (overkill counts, the floor counts per struck monster);
   - Titan (+25 % max HP, −10 % damage);
   - a shield keystone (Shield Wall on every block).
5. **Unbroken only shows for casters** (Arch Mage −24). The model averages hits and cannot see the one-shots it is
   meant for, so it needs the per-hit variance check before any number is set.
6. **The Archer and casters are now carried by range plus their talents.** The Arch Mage and Master of Elements
   reach 72–74 % on BM with grinding; the Archer reaches 89 %.
7. **Still open:**
   - the Priest;
   - the Assassin, whose energy mechanic is left out of this model;
   - the Dragon, which gains only from Legend points and the Oath because its breath uses no talent.

## Design feedback from the mockups

From `level_generation/ui/solo_talents_v2_20261114/README.md`:
- **Five slots need five keystones per role.** Today there are three.
- **"Role" needs a definition.** The mockups assume the class.
- **The Legend lines rule:** "any time" (the mockups) or "after a full tree"? The tree fills at about 76 points,
  well before level 500.
- **Respec rules:** Legend points move freely, tree ranks reset at a training hall, keystones are undecided.
- **Mana Font at level 500** gives +50 SP per 5 s per rank, which is large.
- **Tooltips need live numbers:** Sweeping Blows' share by weapon skill, the Oath's cut, and the ×0.25 clamp.

## Model limits

- Expected values, no variance.
- No special attacks (paralysis, stone) and no monster buffs.
- No terrain, doors or line of sight. The range model's numbers (1200, 600, monster speeds as units per second, no
  back-pedalling) are first assumptions.
- The new talents, keystones and Legend lines are proxies of the proposal; only the passives the game code has go
  through MAW's rules.
- Allocation is one priority list per role, not an optimiser.

## Update 2026-11-14: Whirlwind dropped, talents in the generic-pack tables

- **Tree changes:**
  - Whirlwind is out of tree v2 (user).
  - Cleave stays a 120° arc (±60° in front), the same arc as Sweeping Blows.
  - The reruns without Whirlwind give the same results (Beyond Madness level 500, melee: v2 25 / 48 %, + grinding
    46 / 79 %, end 79 / 90 %).
- **Talents in the generic-pack tables.** The "Every build, every difficulty" and "One stage in detail" tables on the
  page gain two modes, "with talent tree v2 + grinding" and "end of grinding"
  ([talent_route.py](../scripts/talent_route.py), rows tagged `route_v2L` and `route_v2L300`).
  - **Included:** Grandmaster Bodybuilding from the harness, the passives, the Legend lines, the Oath, Unbroken,
    Archon, Sweeping Blows, Overload, Bloodthirst and Mana Font (`sim.py` reads them as `tf_*` fields).
  - **Not included:** actives and range, which this model has no place for.
- **Beyond Madness level 500 in that test** (4 or 10 B-tier monsters, all hitting at once, physical only):

  | Build | Today | v2 + grinding | End of grinding |
  | --- | --- | --- | --- |
  | Champion, sword and shield | dies to 4 | 4 in 3.1 s, 10 in 6.6 s | 10 in 4.6 s |
  | Lich King (Vampire race) | dies to 4 | 4 in 2.7 s, 10 in 6.6 s | 10 in 4.0 s |
  | Seraph | 4 in 16 s | 10 in 5.6 s | 10 in 4.3 s |
  | Monk | dies to 4 | 4 in 3.1 s, 10 in 7.1 s | 10 in 5.1 s |

  - Casters still die to 4 or 10 adjacent monsters. Their answer is range, which only the real-group model has.
  - Because this test is physical only, it flatters melee: in the real maps 74 % of the damage is magic.

## Update 2026-11-14 (later): talents only

The user decided:
- No Legend lines or points. Talent points come from levels only, 50 at level 500, and builds spend leftover points
  on the other trees' passives.
- Cleave is a burst: 150 % to everything in the arc and a 1 s stagger.
- Sweeping Blows hits 1 / 2 / 3 extra monsters at no more than 50 %.
- Multishot replaces Volley; Steady Aim gives 5 % per rank.
- The trees are renamed Arms, Archery and Arcana, and each tree's keystone needs 10 points in that tree.

The tables above, those with Legend points, are superseded by these.

**Real groups, pulls of four (melee weakest / median, seconds per monster):**

| Difficulty, level | Today | Current tree | Tree v2 |
| --- | --- | --- | --- |
| Nightmare 500 | 81 / 96 · 3.1 | 89 / 100 · 2.0 | 100 / 100 · 1.9 |
| Doom 500 | 35 / 55 · 3.0 | 52 / 82 · 1.8 | 82 / 98 · 1.9 |
| Road to Insanity 500 | 25 / 47 · 3.1 | 44 / 73 · 2.0 | 77 / 94 · 2.0 |
| Beyond Madness 500 | 0 / 2 · 4.2 | 1 / 9 · 3.1 | 16 / 43 · 3.6 |

**Beyond Madness 500 by build (tree v2):**
- Seraph 88 %, Troll 84 %, Dragon 94 %.
- Minotaur Lord 50 %, Lich King 45 %, Champion 35–38 %, Monk 26 %, Assassin 16 %.
- Archer 67 %, Arch Mage 47 %, Master of Elements 58 %, Priest 2 %.

**Usage:**
- Cleave now earns its place: 21 % of a two-handed Champion's damage, against 34 % for Sweeping Blows.
- Multishot gives the Archer 28 %.

**Taking one away (Beyond Madness):**

| Removed | Median | Worst |
| --- | --- | --- |
| Oath | −12 | −22 |
| Overload | −15 | −26 |
| Archon | −13 | −25 |
| Deadeye | −22 | |
| Piercing Arrows | −19 | |
| Bloodthirst | −5 | |
| Cleave | −4 | |
| Sweeping Blows | −4 | |
| Unbroken | −1 | −19 (Arch Mage) |
| Warlord | 0 | |

**Generic packs, Beyond Madness 500, tree v2:**
- Every melee build except the Monk survives a pack of 4 (today only the Seraph, Troll and Dragon do).
- A pack of 10 still kills all of them except the Seraph and the Dragon.
- Killing one monster takes 2.3–4.1 s, and each monster deals 3.5–5.5 % of HP per second.

**Reading:** the tree makes Road to Insanity and Doom solo-able for every build and gets Beyond Madness to the 40 %s.
The rest of "roll through" has to come from gear grinding (ITEMS_AND_CRAFTING), about ×3 damage and ÷3 damage taken
on top of the tree (POWER_GAP's ×14 less what the tree gives).

### Target numbers for the "One stage in detail" table (Beyond Madness, level 500; a proposal for the user)

| Column | Today (melee) | Tree v2 (melee) | Target: a maxed solo completes BM (tree + campaign gear) | Target: rolls through (after gear grinding) |
| --- | --- | --- | --- | --- |
| Kill one | 2.3–4.1 s | 2.3–4.1 s | ≤ 2.5 s | ≤ 1 s |
| Incoming per monster | 4.1–14 %/s | 3.2–5.5 %/s | ≤ 3 %/s | ≤ 1.5 %/s |
| Magic per monster | 6–25 %/s | 5.5–10 %/s | ≤ 5 %/s | ≤ 2.5 %/s |
| Pack of 4, no potions | dies (most) | survives, 17–94 % HP left, 4.5–8.5 s | survives with ≥ 30 % HP, ≤ 8 s | ≥ 60 % HP, ≤ 4 s |
| Pack of 10 | dies | dies (most) | survives with ≤ 2 drinks | survives without drinks, ≤ 15 s |
| Largest pack | 2–3 | 4–8 | ≥ 8 | ≥ 20 |
| Real groups, pulls of four | 0–3 % | 16 / 43 % | every melee ≥ 75 %, median ≥ 85 % | 100 %, whole groups ≥ 90 % |

## Update 2026-11-14 (latest): Onslaught, no Purify or Mana Font

The user's changes:
- Frenzy becomes the passive **Onslaught**: each kill adds +1 / 2 / 3 % attack speed, at most 5 stacks, lasting
  10 s and refreshed on every kill.
- Purify and Mana Font are dropped.
- Multishot, Steady Aim at 5 %, and the trees Arms / Archery / Arcana with tree-gated keystones are as above.

These numbers supersede the "talents only" section.

**Real groups, pulls of four (melee weakest / median, seconds per monster):**

| Difficulty, level | Weakest / median | Seconds per monster |
| --- | --- | --- |
| Nightmare 500 | 100 / 100 | 2.0 |
| Doom 500 | 82 / 97 | 2.1 |
| Road to Insanity 500 | 71 / 93 | 2.1 |
| Beyond Madness 200 | 100 / 100 | 2.0 |
| Beyond Madness 500 | 10 / 38 | 3.9 |

**Beyond Madness 500 by build:**

| Build | Pulls of four |
| --- | --- |
| Dragon | 94 % |
| Seraph | 87 % |
| Troll | 83 % (staff 67 %) |
| Archer | 67 % |
| Master of Elements | 56 % |
| Minotaur Lord | 46 % |
| Arch Mage | 44 % |
| Lich King | 42–44 % |
| Nosferatu | 41 % |
| Champion | 30–35 % |
| Shaman | 35 % |
| Monk | 20 % |
| Assassin | 10 % |
| Priest | 2 % |

**Onslaught against the old active Frenzy:**
- Onslaught is weaker than Frenzy's flat +25 % for 6–8 s every 30 s, because in pulls of four few kills come fast
  enough to hold the stacks.
- Taking it away costs 0 (median), −3 at worst. The BM median fell from 43 to 38 %, partly from this and partly
  from Mana Font.
- If Onslaught should matter, it needs bigger stacks or a longer window (for example +2 / 4 / 6 % per kill), or it
  keeps its stacks between pulls while you rest.

**Taking one away (BM 500):**

| Removed | Median | Worst |
| --- | --- | --- |
| Overload | −16 | −24 |
| Archon | −14 | −25 |
| Oath | −11.5 | −21 |
| Deadeye | −22 | |
| Piercing Arrows | −19 | |
| Blink | −5 | −21 (Arch Mage) |
| Bloodthirst | −4 | |
| Cleave | −3.5 | −11 |
| Sweeping Blows | −3.5 | −13 |
| Unbroken | −1 | −16 |
| Warlord | 0 | |

**Onslaught at 20 s** (user, 2026-11-14), with the stacks carried into the next pull of four of the same group (5 s
between pulls):

| Difficulty, level 500 | Weakest / median (melee) |
| --- | --- |
| Beyond Madness | 10 / 38 % |
| Road to Insanity | 75 / 93 % |
| Doom | 82 / 97 % |

- Taking Onslaught away costs −0.5 at the median and −4 at worst (the two-handed Champion).
- It is still worth little in pulls of four, because a stack is only +1 to +3 % and fights are short. Its share grows
  only where kills chain (whole groups, the "mash" phase).

## Update 2026-11-14 (latest): one point per 15 levels, Dragon items ×2, Archery bows only

The user's changes:
- Tree v2 gives one point per 15 levels: 33 at level 500.
- Keystones come one per 150 levels.
- Archery talents and Deadeye never touch a Dragon's breath.
- Onslaught is +1 % per kill, at most 10 / 20 / 30 stacks, lasting 30 s; by design it barely matters in slow pulls.
- In a solo run a Dragon's items count ×2 instead of ×3. This is built in `MawItemRules.cpp` and tested. The current
  tree and tree v2 columns are solo runs, so they include it; "today" is MAW as it is.

**Real groups, pulls of four (melee weakest / median):**

| Difficulty, level 500 | Weakest / median |
| --- | --- |
| Nightmare | 100 / 100 |
| Doom | 82 / 97 |
| Road to Insanity | 77 / 93 |
| Beyond Madness | 10 / 37 |

**Beyond Madness 500 by build:**

| Build | Pulls of four |
| --- | --- |
| Seraph | 85 % |
| Troll | 83 % (staff 71 %) |
| Dragon | 68 % (was 94 % at ×3) |
| Archer | 65 % |
| Master of Elements | 58 % |
| Arch Mage | 50 % |
| Minotaur Lord | 48 % |
| Lich King | 42–44 % |
| Nosferatu | 41 % |
| Champion | 29–35 % |
| Shaman | 35 % |
| Monk | 21 % |
| Assassin | 10 % |
| Priest | 2 % |

- With one point per 15 levels, each build still fills its main tree and its key talents by level 500. The results
  are within a couple of points of one per 10; the fewer points only cut the other trees' passives.

## Update 2026-11-14 (latest): Dragon items ×2.5, Lichborne removed

- **Dragon ×2.5** (built and tested in `MawItemRules.cpp`). Beyond Madness level 500, real groups pulled four at a
  time: 85 % with tree v2 (current tree 76 %), against 87 % for MAW today with ×3. Doom and Road to Insanity stay at
  98–100 %.
- **Lichborne removed:** the Death Knight has no Oath, and its keystones are Unbroken and Warlord.

  | Build | Beyond Madness 500 | Road to Insanity | Doom |
  | --- | --- | --- | --- |
  | Lich King (Vampire race) | 27 % | 87 % | 87 % |
  | Lich King (Minotaur race, dual) | 28 % | 80 % | 87 % |
  | Lich King (Minotaur race, one axe) | 8 % | 68 % | 79 % |

  Melee weakest / median at level 500:

  | Difficulty | Weakest / median |
  | --- | --- |
  | Beyond Madness | 8 / 35 % |
  | Road to Insanity | 68 / 90 % |
  | Doom | 79 / 97 % |

## Update 2026-11-14 (latest): Lone Discipline with Bodybuilding actually trained

- **What changed:** the classes whose Bodybuilding cap Lone Discipline lifts now plan their skill points again with
  Bodybuilding weighted like the natural Grandmaster classes (0.8, `gen_talent_pool.py` `replan`). The extra levels
  come out of their other skills.
- **Bodybuilding at Beyond Madness level 500** (40 or less before):

  | Build | Bodybuilding | Given up |
  | --- | --- | --- |
  | Death Knight | 73 | weapon 99 → 92, Blood and Unholy 70 → 64 |
  | Seraph | 74 | |
  | Assassin | 69 | |
  | Nosferatu | 72 | |
  | Archer | 87 | |

- **HP at Beyond Madness level 500:**

  | Build | Today | Tree v2 |
  | --- | --- | --- |
  | Lich King (Vampire race) | 15.0k | 36.1k |
  | Seraph | 10.7k | 28.2k |
  | Assassin | 9.1k | 26.1k |

- **Real groups, pulls of four, level 500, tree v2:**

  | Build | Beyond Madness | Road to Insanity | Doom |
  | --- | --- | --- | --- |
  | Lich King (Vampire race) | 38 % | 93 % | 96 % |
  | Lich King (Minotaur race, dual) | 31 % | 87 % | 95 % |
  | Lich King (Minotaur race, one axe) | 12 % | 83 % | 86 % |
  | Seraph | 82 % (less damage) | 99 % | 100 % |
  | Nosferatu | 38 % | 91 % | 98 % |
  | Assassin | 15 % | 87 % | 96 % |
  | Archer | 69 % | 99 % | 100 % |
  | Arch Mage | 41 % | 67 % (fewer Fire points) | 96 % |

  Melee weakest / median:

  | Difficulty | Weakest / median |
  | --- | --- |
  | Beyond Madness | 12 / 35 % |
  | Road to Insanity | 81 / 91 % |
  | Doom | 86 / 97 % |
