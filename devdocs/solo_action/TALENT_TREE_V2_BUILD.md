# Talent tree v2: build plan and progress (2026-11-14)

Building the user's talent tree v2 into the MAW solo run. The design and the simulations behind it are in
[devdocs/maw/solo_sim/proposals/TALENT_TREE_V2.md](../maw/solo_sim/proposals/TALENT_TREE_V2.md) and
`TALENT_TREE_V2_RESULTS.md`; the mockups are in `level_generation/ui/solo_talents_v2_20261114/` (viewer.html).

**Scope.** Only the augmented solo run under MAW: `soloTalentsActive` (solo option and ruleset `maw`) and, inside MAW's
rules, `options().soloRun`. Standard, a MAW party, and a MAW game started with one character without the solo option
see no change.

## The tree (user decisions, 2026-11-14)

- **Points:** one per 10 levels (`levels_per_point: 10`; was 15 until the user's change later on 2026-11-14).
- **Keystones:** one slot per 150 levels (levels 150 and 300), chosen from **Cheat Death** and **Unbroken**. They cost
  no points. No class Oaths; Warlord, Deadeye and Archon are dropped.
- **Trees** name what they train: Arms (was melee), Archery (bows only, never a Dragon's breath), Arcana (was caster),
  plus Any tree.
- **Innate, no points: Lone Discipline** (not shown on the page). Every solo class can learn Bodybuilding (even one
  that normally cannot) up to Expert at once, Master after the first promotion, Grandmaster after the final one (a
  class whose own cap is higher keeps it).
- **Dragon items ×2.5** in a solo run (built in 2.4, `MawItemRules`).

| Tree | Talent | Kind, ranks | Effect |
| --- | --- | --- | --- |
| Arms | Weapon Training | passive 5 | +2 % Might, Endurance, Speed per rank (unchanged) |
| Arms | Cleave | active 3 | Burst: 150 % to every monster in the 120° arc in front (no stagger, user 2026-11-14); cooldown 12/10/8 s |
| Arms | Sweeping Blows | passive 3, needs Cleave | Every ordinary swing also strikes 1/2/3 more in the same arc at 30 % + 0.25 % per weapon-skill point, at most 50 % |
| Arms | Onslaught | passive 3 | Each kill +1 % attack speed, at most 10/20/30 stacks; the stacks last 30 s, every kill refreshes them |
| Arms | Charge | active 3 | Unchanged |
| Arms | Shield Wall | active 3 | Unchanged |
| Archery | Marksman | passive 5 | Unchanged |
| Archery | Multishot | active 3 | 2/3/4 bow attacks at once over ±30°, 75 % each; each arrow hits the first monster in its line; cooldown 10/8/6 s |
| Archery | Piercing Arrows | passive 3 | Every ordinary bow shot also hits 1/2/3 monsters behind the target at 30 % + 0.25 % per Bow point, at most 50 % |
| Archery | Pinning Shot | active 3 | Unchanged |
| Archery | Steady Aim | passive 3 | +5 % Luck per rank while still (was 3 %) |
| Archery | Quickfoot | passive 3 | +3/6/9 % movement speed; +15/30/45 % out of combat (no yellow alert) |
| Arcana | Attunement | passive 5 | Unchanged |
| Arcana | Blink | active 3 | Unchanged |
| Arcana | Spell Surge | active 3 | Unchanged |
| Arcana | Resolve | passive 5 | Unchanged |
| Arcana | Overload | passive 3 | Area spells +10/20/30 % per monster near the target beyond the first (at most 3 more) |
| Arcana | Binding Circle | active 3 | Every hostile within 500 is held (slowed to a standstill) for 2/2.5/3 s; cooldown 20/18/16 s |
| Any | Bloodthirst | passive 3 | +2 % leech on melee, bow and spells per rank; the leech floor's ÷5 becomes ÷4/÷3/÷2.5 |
| Keystone | Cheat Death | — | A hit that would kill leaves 5 % HP, then 2 s of 95 % less damage; 3 minutes (real time) cooldown |
| Keystone | Unbroken | — | The part of one hit above 30 % of max HP is halved |

Removed: Whirlwind, Volley (became Multishot), Disengage (became Quickfoot), Frenzy (became Onslaught), Purify,
Mana Font. Saved ranks of removed talents are ignored and their points come back.

## Build steps

1. [x] `talents.yml` and `SoloTalents`: tree Any, keystones (kind, levels), `needs`, points without keystones and
   unknown ids, keystone learning by slot, tree labels.
2. [x] `MawSoloTalents` and MAW hooks: Onslaught (kill hook, recovery), Cheat Death and Unbroken (damage absorb),
   Bloodthirst (`applyLeech`), Overload (`spellDamageScale` with `monstersNearTarget`), Quickfoot (party movement
   multiplier, yellow alert), Lone Discipline (Bodybuilding cap at trainers and `applyProgressionMasteries`).
3. [x] Actives (`useSoloTalent`): Cleave burst, Multishot, Binding Circle; remove the dropped ones.
   Ordinary attacks: Sweeping Blows and Piercing Arrows as extra blows before the paying blow.
4. [x] Talents page: Arms / Archery / Arcana / Any, keystone strip (mockup A), points header.
5. [x] Tests (`tests/SoloTalentTests.cpp`, Lone Discipline in `tests/MawGapTests.cpp`), build, focused runs, a game check.
6. [x] Docs: this file (`TALENTS.md` is marked superseded).
7. [ ] Arms effects (user, 2026-11-14): red and yellow dots on the hands growing with Onslaught's stacks (MM9's
   `redyeldots`), and a glint along the weapon (blade, bow, shield, a dragon's talons) while an active talent plays.
   Written as a patch, held until the 2.4 commit is done (openyamm-03).

## Notes from the build

- **Binding Circle** uses the actor slow at a tenth (`debuffActor(Slow, …, 10)`), which also slows the monsters'
  attacks tenfold: closer to a hold than a pure root. A root-only debuff would need a new actor state in both world
  runtimes.
- **Overload** reads `CharacterSpellCast::monstersNearTarget` (living monsters within 384 of the spell's named target),
  so it counts only when the spell names a monster.
- **Sweeping Blows and Piercing Arrows** strike as talent extra blows just before the ordinary attack, which then pays
  the recovery. Melee or bow is guessed from the target's distance and a drawn bow; a battle order that casts instead
  still lets the extra blows land.
- **Lone Discipline** is `SkillRules::masteryCap` (now) and `promotedMasteryCap` (after promotions), read by the guilds'
  learnable skills, `Party::canMemberLearnSkill`, the mastery teacher, MAW's mastery regain and the skill popup's
  "needs a promotion" colouring.
- **Cheat Death** runs after Mana Shield, legendary 15 and the Seraph's Divine Protection, so it saves only when nothing
  else did. **Unbroken** and Cheat Death's 95 % cut run with Shield Wall before Mana Shield.
- **Removed talents** (Whirlwind, Volley, Disengage, Frenzy, Purify, Mana Font): saved ranks are ignored and their points
  return. Action-bar talent slots store the table index, so a 2.4 save's bar may point at other talents; forget and
  re-place them (2.4 is not released yet).

## Status (2026-11-14)

- **Built:** steps 1–6; 13 talent tests and the 442 MAW, solo, mastery, leech, trainer and combat test cases pass; the
  page was checked in the game (layout A, icons). Lone Discipline is not shown on the page (user); it still applies.
- **Icons:** 21 own icons (`assets_dev/engine/icons_x2/talent_<id>.png`, item icons stay PNG,
  ASSET_COOKING_PLAN.md §10), made by four Codex workers in `level_generation/ui/solo_talent_icons_20261114/`.
- **Representative saves:** 15 solo test-party stages in `assets_dev/engine/rulesets/maw/debug/test_parties.yml`
  (`solo_<maw|nightmare|madness>_<50|100|200|300|500>`, written by
  `devdocs/maw/solo_sim/scripts/gen_solo_stages.py` from the simulated playthroughs) and one-character parties
  (`solo_champion`, `solo_archer`, `solo_archmage`, `solo_deathknight`, `solo_seraph`, `solo_dragon`, `solo_troll`,
  `solo_minotaur`). For example `testparty solo_madness_200 solo_champion nightmare beyond_madness horizontal solo`
  (Beyond Madness is the option `beyond_madness`; MAW is `maw free solo`, Nightmare `nightmare free solo`).
  - The saves are `saves/Solo <MAW|Nightmare|Beyond Madness> L<050…500>.oysav`, copied to `output/maw_solo_saves/`, made with
    the new debug console command `savegame <name>`.
  - On MAW and Nightmare the playthrough ends below level 500, so those "L500" saves are levels 467 and 481 at its last
    map.
  - The Beyond Madness saves at 100 and 200 are taken right as the map loads: waiting there killed the solo.

## Changes after the first in-game look (user, 2026-11-14)

- **Points:** one per 10 levels (was 15). The simulation tables still use 15.
- **Talents page fills the window** (`GameplaySoloTalentsPage`, a 800 x 450 canvas scaled to fit over a dark backdrop):
  Fondamento names and headers, Lucida text, the detail card at the right with wrapped text. "Back to Skills" or Esc
  returns to the Skills page (`GameplayInputController` leaves the character screen open while the page is shown).
  Only learned talents wear a gold rim and gold pips; the teal "learnable" marks are gone.
- **The Talents button** sits in the bottom-right panel above Workbench (34 units above `CharacterAlchemyButton`,
  where the inventory page has Sort), on the Skills page.
- **Buff row** (`GameplaySoloHud` `buffTiles`): Onslaught with its stacks in the corner and its 30 s timer; a bound
  Cheat Death (lit when ready, its seconds while it protects, veiled with the cooldown after).
- **Sounds** (`engine/audio/solo_talents/`, ElevenLabs job in `level_generation/sounds/solo_talents_20261114/`):
  Cleave at its strike, Charge as the dash starts, Cheat Death when it saves (queued by `MawCombatRules` through the
  event runtime's named sounds). Cleave no longer staggers.
- **Held for the 2.4 commit (openyamm-03):** Cleave's strike at the swing's blow and the arms' Onslaught dots and talent
  glint, written as scripts.
