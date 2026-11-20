# Talent tree v2: build plan and progress (2026-11-14)

**Changed in part by the solo archetypes (2026-11-18):** [ARCHETYPES_BUILD.md](ARCHETYPES_BUILD.md). One path a
character, nine talents a path, the Arms path's rage bar. Shield Wall and Resolve are gone, Onslaught is in the Any
tree with five ranks and speeds spell casts too, Spell Surge spends only on damaging spells and is fed by casts,
Overload counts the monsters a blast strikes. The table and notes below describe tree v2 as it was built.

Building the user's talent tree v2 into the MAW solo run. The design and the simulations behind it are in
[devdocs/maw/solo_sim/proposals/TALENT_TREE_V2.md](../maw/solo_sim/proposals/TALENT_TREE_V2.md) and
`TALENT_TREE_V2_RESULTS.md`; the mockups are in `level_generation/ui/solo_talents_v2_20261114/` (viewer.html).

**Scope.** Only the augmented solo run under MAW: `soloTalentsActive` (solo option and ruleset `maw`) and, inside MAW's
rules, `options().soloRun`. Standard, a MAW party, and a MAW game started with one character without the solo option
see no change.

## The tree (user decisions, 2026-11-14)

- **Points:** one per 5 levels (`levels_per_point: 5`; was 15 until the user's change later on 2026-11-14, then 10
  until the user's change on 2026-11-16).
- **Keystones:** one slot per 150 levels (levels 150 and 300), chosen from **Cheat Death** and **Unbroken**. They cost
  no points. No class Oaths; Warlord, Deadeye and Archon are dropped.
- **Trees** name what they train: Arms (was melee), Archery (bows only, never a Dragon's breath), Arcana (was caster),
  plus Any tree.
- **Innate, no points: Lone Discipline** (not shown on the page). Every solo class can learn Bodybuilding (even one
  that normally cannot) up to Expert at once, Master after the first promotion, Grandmaster after the final one, and
  Regeneration (at a temple; user, 2026-11-15) up to Expert at once and Master after the final promotion. A class
  whose own cap is higher keeps it; Bodybuilding is only learnable (`MawSkillRules::masteryCap`). **Regeneration is
  given at the start** (user, 2026-11-19): every new solo run's character has it at 1, Normal (`makeSoloRunParty`,
  `SoloRunStartSkill` in `Party.h`), and the party creation sheet shows it as a fixed starting skill once Solo run is
  ticked, so it is never one of the picks (`NewGameScreen::setSoloRun`, `refreshSkillChoices`). A solo run already
  under way is not changed: its character learns it at a temple as before. Scenario:
  `tests/scenarios/rulesets/maw_solo_start_regeneration.yml`.
- **Early monster cut** (built 2026-11-15, not a talent): in a solo run monsters' damage and, in effect, their HP
  are divided by 2.5 at character level 1, 1.6 at 10, 1.4 at 50, fading to nothing at level 75 (`early_monster_cut`
  in `talents.yml`;
  [POWER_CURVE_DIRECTION.md](POWER_CURVE_DIRECTION.md) §8).
- **Early Regeneration** (built 2026-11-18, not a talent; user): in a solo run the Regeneration skill's own healing
  is halved until character level 15, then returns to the whole along an S-curve by level 75 (0.63 at 35, 0.75 at
  45, 0.87 at 55; `early_regeneration` in `talents.yml`, `MawSkillRules::regenerationPerSecond`). The skill popup
  shows the cut numbers; the Regeneration aura, potions and items are not touched. With Lone Discipline every class
  has the skill, and at low levels it out-healed what monsters dealt. **Only classes without Regeneration of their
  own** (user, 2026-11-19): the cut applies when the character's class and race cannot learn the skill in MAW (its
  cap in `class_skills.txt` is none; `MawSkillRules::soloRegenerationShare`). Dragons, Minotaurs, Monks, Trolls,
  Vampires and Liches keep the whole at every level; a Necromancer is cut until it becomes a Lich.
- **Experience surcharge 0.25 %** (built 2026-11-15, not a talent): a solo character's levels past 100 cost 0.25 %
  more per level above 100 instead of MAW's 0.5 % (`experience_surcharge` in `talents.yml`); banks, monster levels and
  kill awards keep MAW's curve (POWER_CURVE_DIRECTION.md §8).
- **Dragon items ×3** in a solo run, as in MAW (the 2.4 build's ×2.5 was reverted on 2026-11-15, `MawItemRules`).

| Tree | Talent | Kind, ranks | Effect |
| --- | --- | --- | --- |
| Arms | Cleave | active 3 | Burst: 150 % to every monster in the 120° arc in front (no stagger, user 2026-11-14); cooldown 12/9/6 s |
| Arms | Sweeping Blows | passive 3, needs Cleave | Every ordinary swing also strikes 1/2/3 more in the same arc at 30 % + 0.25 % per weapon-skill point, at most 50 % |
| Arms | Onslaught | passive 3 | Each kill +1 % attack speed, at most 10/20/30 stacks; the stacks last 60 s, every kill refreshes them |
| Arms | Charge | active 3 | Unchanged, but each ordinary weapon attack takes 1 s off its cooldown (`cooldown_per_attack`, user 2026-11-14) |
| Arms | Shield Wall | active 3 | Unchanged |
| Archery | Multishot | active 3 | 2/3/4 bow attacks at once over ±12° (was ±30°), 75 % each; each arrow hits the first monster in its line; cooldown 10/8/6 s, 1 s off for each ordinary attack that hits a monster (`cooldown_per_hit`, user 2026-11-16) |
| Archery | Chaining Arrows (was Piercing Arrows; the id stays `piercing_arrows`) | passive 3 | Every arrow of an ordinary bow shot leaps on from the monster it strikes to the nearest other within 1024, up to 1/2/3 times, at 30 % + 0.25 % per Bow point, at most 50 % |
| Archery | Power Shot (replaced Pinning Shot, user 2026-11-16) | active 3 | One bow shot at 135/170/200 % of a normal shot (`share_by_rank`), cooldown 6/5/4 s; each critical hit of an ordinary attack's own arrows or blow takes 0.5 s off (`cooldown_per_crit`, user 2026-11-16; Chaining Arrows leaps, Sweeping Blows and talent shots do not count); a save's Pinning Shot ranks become Power Shot's (save 189). Its sound `talent_power_shot` plays over the bow shot's: the shot an octave down, a sub thump, a charged whoosh and a shimmer, made by `level_generation/sounds/power_shot_20261116/make_power_shot.py` |
| Archery | Steady Aim | passive 3 | +10/20/30 % Luck while still (user 2026-11-16; was 5 % a rank, first 3 %) |
| Archery | Quickfoot | passive 3 | +3/6/9 % movement speed; +15/30/45 % out of combat (no yellow alert) |
| Arcana | Blink | active 3 | Unchanged |
| Arcana | Spell Surge | active 3 | Unchanged |
| Arcana | Resolve | passive 5 | 2 % a rank of every resistance, the armour and Shield skills', staves' and Luck's included (MAW's sheet rows; before, only the base and magical ones, about a tenth of a late character's) |
| Arcana | Overload | passive 3 | Area spells +10/20/30 % per monster near the target beyond the first (at most 3 more) |
| Arcana | Binding Circle | active 3 | Every hostile within 500 is held (slowed to a standstill) for 2/2.5/3 s; cooldown 20/18/16 s |
| Any | Bloodthirst | passive 5 | +2 % leech on melee, bow and spells per rank; the leech floor's ÷5 shrinks by 0.5 a rank, ÷2.5 at rank 5 (user 2026-11-17: 2.5 had three ranks; three and five were tried in the solo sim with Manathirst, and five kept) |
| Any | Conditioning (user 2026-11-16) | passive, no last rank | +10 % to all seven stats at rank 1, +1 % each rank after, of the whole stat (base, permanent bonuses, items and buffs; user 2026-11-18: the raw base stat alone moved a late character's Might by a point a rank), counted in HP and SP; takes every point the character has (ranks are two bytes in the save) |
| Any | Spell Suppression (user 2026-11-16) | passive 41 | less damage from every hit that is not physical: 4 % at rank 1, 0.4 % more each rank after, 20 % at rank 41 (`first_rank` in the table; halved by the user on 2026-11-17 from 8 %, 0.8 % and 40 %): the last stage of MAW's damage pipeline (`solo-spell-suppression`), after armour, resistances and their 90 % floor, so it still counts at the cap; Unbroken and Cheat Death then take theirs. Last in the table so the bar's indexes keep. Why: at solo level 703 on Beyond Madness (the solo sim's real groups) a spell lands 2.3 times as hard as a blow with both defences at or near the cap; a Bowman's median spell takes 66 % of its HP and 18 % of spells kill outright (blows: 30 %, never), and the original full 40 % cut the one-shots to 0.2 % |
| Any | Manathirst (user 2026-11-16) | passive 5 | Bloodthirst for the SP bar: 2 % a rank of the full SP back the way leech heals (the bar share of the monster the hit took, at least the floor, ÷5 less 0.5 a rank like Bloodthirst's), on melee, bow and spells, never a breath; an extra blow gives a third, and an area spell's hits give SP for at most three monsters within half a second (`takeAreaManaLeech`). Why: a Grandmaster Mana Shield turns an SP into 5 HP, so a caster's pool is 3-6 times its HP and Bloodthirst refills only the HP part. In the solo sim's real groups (Nightmare) 6 % takes deaths from 21.2 to 17.9 % (Archmage, level 300) and 20.5 to 16.1 % (Elementalist, 500), as Bloodthirst's 6 % does for a Knight (8.1 to 6.0 %, level 100); 10 % goes further (15.4 %, 11.8 %, 4.9 %); the user kept five ranks for both (2026-11-17); Beyond Madness past level 500 is burst and leech changes nothing. Last in the table so the bar's indexes keep |
| Keystone | Cheat Death | — | A hit that would kill leaves 5 % HP, then 2 s of 95 % less damage; 3 minutes (real time) cooldown |
| Keystone | Unbroken | — | The part of one hit above 30 % of max HP is halved |

Removed: Whirlwind, Volley (became Multishot), Disengage (became Quickfoot), Frenzy (became Onslaught), Purify,
Mana Font. Saved ranks of removed talents are ignored and their points come back. Weapon Training, Marksman and
Attunement went on 2026-11-16 (user: Conditioning in their place; Attunement's spell damage and healing went with it).
Save 190 drops their ranks and moves the action bar's talent keys up past their three places in the table
(`migrateRemovedTalents`; the bar keeps talents by index).

## Build steps

1. [x] `talents.yml` and `SoloTalents`: tree Any, keystones (kind, levels), `needs`, points without keystones and
   unknown ids, keystone learning by slot, tree labels.
2. [x] `MawSoloTalents` and MAW hooks: Onslaught (kill hook, recovery), Cheat Death and Unbroken (damage absorb),
   Bloodthirst and Manathirst (`applyLeech`), Overload (`spellDamageScale` with `monstersNearTarget`), Quickfoot (party movement
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
- **Sweeping Blows** strikes as talent extra blows just before the ordinary attack, which then pays the recovery
  (Piercing Arrows did too at first; Chaining Arrows rides on the arrows, below). Melee or bow is guessed from the
  target's distance and a drawn bow; a battle order that casts instead still lets the extra blows land.
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

- **Points:** one per 10 levels (was 15; one per 5 since 2026-11-16). The simulation tables still use 15.
- **Talents page fills the window** (`GameplaySoloTalentsPage`, a 800 x 450 canvas scaled to fit over a dark backdrop):
  Fondamento names and headers, Lucida text, the detail card at the right with wrapped text. "Back to Skills" or Esc
  returns to the Skills page (`GameplayInputController` leaves the character screen open while the page is shown).
  Only learned talents wear a gold rim and gold pips; the teal "learnable" marks are gone.
- **The Talents button** sits in the bottom-right panel above Workbench (34 units above `CharacterAlchemyButton`,
  where the inventory page has Sort), on the Skills page.
- **Buff row** (`GameplaySoloHud` `buffTiles`): Onslaught with its stacks in the corner and its 60 s timer; a bound
  Cheat Death (lit when ready, its seconds while it protects, veiled with the cooldown after).
- **Sounds** (`engine/audio/solo_talents/`, ElevenLabs job in `level_generation/sounds/solo_talents_20261114/`):
  Cleave once per monster its strike hits, at that monster (the user's `CleaveTarget.ogg`), Charge as the dash starts, Cheat Death when it saves (queued by `MawCombatRules` through the
  event runtime's named sounds). Cleave no longer staggers.
- **Cleave strikes at its clip's blow** (with the arms shown): the press starts the clip and the cooldown and sets
  `ViewModelLink::talentAtBlow` with `swingWaiting`; the blow's release runs `useSoloTalent(..., atBlow)`, which picks
  the targets in the arc then. Without arms it strikes at once. Trace: `viewmodel trace on` logs the talent's clip and
  its hit time. A dragon's forelegs have no power attacks: Cleave plays the claws' sideways swipe (`clawsattackleft`,
  blow at 0.2 s). Before 2026-11-15 they played nothing and the strike waited for the 2 s fallback.
- **Extra blows gain a third** (user, 2026-11-15): Cleave's other monsters and Sweeping Blows' blows are
  `PartyHitOnMonster::extraBlow`, and in a solo run their leech (floor included) and their classes' on-hit gains (a
  dragon's bite SP, a Death Knight's SP and Blood Leech, a Shaman's and a Seraph's) are a third
  (`MawCombatRules` `ExtraBlowShare`). The special on-hit effects (stuns, paralysis, pushes, slows, artifact
  spells, Death Grasp, Retaliation's stacks) are the main blow's alone. The blow that pays the recovery gains in full.
  Every talent's interactions: [TALENT_INTERACTIONS.md](TALENT_INTERACTIONS.md).
- **Arms effects** (`FirstPersonViewModelFx`): Onslaught's red and yellow dots rise off both hands (a dragon's talon
  tips; **off for now**, user 2026-11-14: `GameApplication` does not pass `Input::onslaught`), about 12 a second per hand at one stack and 60 at thirty, larger as they grow (`Input::onslaught`, stacks / 30);
  a non-cast active talent (Cleave, Charge, Multishot, Power Shot) sends gold sparks along the weapon (blade, bow;
  around the hands for fists and talons) while its clip plays, and Shield Wall around the guarding hands while it holds
  (no shield is shown in the first person).
  Review: `talent stacks <n>` sets Onslaught's stacks for its duration (60 s).

## Fixes after the talent check (user, 2026-11-14)

- **Quickfoot outdoors:** the party's movement multiplier was folded into `OutdoorMovementInput::movementSpeedScale`,
  which the driver clamps to 1 (a stick's share), so every speed-up outdoors was lost: Quickfoot, and MM9's Fleet Foot
  too. It is now `partySpeedMultiplier`, unclamped. Measured: 1428 units in 1.5 s at rank 0, 2079 at rank 3 out of
  combat (+46 %).
- **Charge:** each ordinary weapon attack (melee or bow, not a talent's blow) takes 1 s off its cooldown
  (`cooldown_per_attack` in `talents.yml`); measured 2 s off for two attacks. Without a monster under the crosshair it
  takes the nearest hostile within reach in a 12° cone ahead.
- **Cleave:** cooldown 12/9/6 s.
- **Onslaught** ends on every map load (`endMapTalentEffects`, after `mapLoaded` in both world loads): travel, Town
  Portal, Lloyd's Beacon, doors.
- **Multishot** is one shot of 2/3/4 arrows fanned over ±12° (`PartyAttackConfig::talentFanArrows`, the volley fan
  MAW's shots use), each on its own heading; measured: four arrows, one into each of four monsters across the fan.
- **Multishot's `cooldown_per_hit`** (user, 2026-11-16): each ordinary weapon attack, melee or bow, that hits a
  monster takes 1 s off its cooldown, once per attack. A bow attack's arrows share one credit
  (`ProjectileState::hitCredit`, spent in `GameplayCombatController` when the first of them hits), so a Master bow's
  second arrow, MAW's volley and Chaining Arrows' leaps (`chainArrow` drops the credit) add nothing; a melee blow
  credits in `executePartyAttack`. Talent blows (Cleave, Sweeping Blows, Multishot's own arrows) credit nothing.
  Measured in `tests/scenarios/rulesets/maw_solo_multishot_cooldown_per_hit.yml`.
- **Multishot and Power Shot** wait for the bow's release like Cleave waits for its blow, when the arms hold the bow;
  with the melee weapon drawn they shoot at once.
- **Chaining Arrows** (user, 2026-11-16; it replaced Piercing Arrows, whose arrows flew straight on through the monsters
  behind) rides on the arrows (`ProjectileState::chainLeft`, `GameplayProjectileService::chainArrow`): every arrow of an
  ordinary bow shot, a Master bow's two included, leaps on from the monster it strikes to the nearest other living
  hostile one it has not struck, up to 1/2/3 times at the share. The next monster must stand within the talent's
  `distance` (1024 since 2026-11-16, first 512; to its body) of the struck one, in clear sight of the hit point; with
  none the arrow ends there. It leaves aimed at the monster and homes on it, never strikes one twice, and a leap's
  monster it misses spends no leap. A miss on the shot's own target ends the arrow there (user, 2026-11-16): only a hit
  starts the chain, so a miss never becomes a full-damage shot at a neighbour. The talent's id is still
  `piercing_arrows` (saves and its icon keep it).
- **Sounds:** Cleave plays once per monster it hits, at that monster; Blink plays the user's `569766.ogg`
  (`talent_blink.wav`).
- **Checked in the game:** Cleave, Sweeping Blows, Onslaught, Charge, Shield Wall, Multishot, Piercing Arrows,
  Power Shot, Quickfoot, Blink, Binding Circle, Cheat Death's tile. The passives, Spell Surge, Overload, Bloodthirst,
  Unbroken and Cheat Death's save rest on `tests/SoloTalentTests.cpp`.
- **Talent timing = an attack's** (user, 2026-11-14): a waited talent's clip (Cleave, Multishot, Power Shot) plays
  fitted to the member's recovery for that attack (`attackRecoverySeconds`, the swing's own rule), and the clip's time
  comes off the recovery the paying blow sets (`TalentBlow::recoverySpent`). Measured: Multishot and Power Shot
  release at 0.70 s with 0.14 s left (an ordinary shot's 0.85 s; were 0.9 s plus the full 0.85 s), Cleave strikes at
  0.24 s with 0.12 s left (an ordinary swing's 0.37 s). They quicken with attack speed as attacks do.
- **Multishot with a Master bow** shoots each heading's arrow twice, the second beside the first, as the bow's ordinary
  shot does (`arrowsPerHeading` in `GameplayActionController`): rank 3 is eight arrows.
- **Multishot's volley** leaves close together (sources 4 units apart across the aim) in a fan of ±12° (was ±30°, which
  read as shrapnel; user, 2026-11-14).
- **Bow talents need the bow drawn** (user, 2026-11-14): with the melee weapon in the arms, Multishot and Power Shot
  refuse ("… needs the bow drawn") and spend no cooldown; without the arms they shoot at once as before.
