# Solo archetypes: as built (2026-11-18)

[ARCHETYPES_RESEARCH.md](ARCHETYPES_RESEARCH.md) (the user's decisions of 2026-11-18, §0.1) built into the MAW solo
run: one talent path a character, nine talents a path, the Arms path's rage bar. Scope as for every talent:
`soloTalentsActive` (solo option and ruleset `maw`) and, inside MAW's rules, `options().soloRun`. Standard, a MAW
party and a MAW game of one without the solo option see no change.

It replaces parts of [TALENT_TREE_V2_BUILD.md](TALENT_TREE_V2_BUILD.md): Shield Wall and Resolve are gone, Onslaught
is in the Any tree, Spell Surge and Overload work differently. What that file says of the other built talents holds.

## The table (`assets_dev/engine/data_tables/talents.yml`)

The action bar keeps talents by their place in the table, so the 19 old places keep their talents and the new ones
are appended. Two places changed their talent: 4 (Shield Wall) is Challenge and 12 (Resolve) is Arcane Ward.

| Place | Id | Tree | Effect |
| --- | --- | --- | --- |
| 0 | cleave | arms | as built |
| 1 | sweeping_blows | arms | as built |
| 2 | onslaught | any | five ranks of 6 stacks (30 % at rank 5); speeds weapon attacks **and spell casts** |
| 3 | charge | arms | as built; each kill takes 3 s off the cooldown (`cooldown_per_kill`) |
| 4 | challenge | arms | active: every hostile that has noticed the party, wherever it stands, cannot shoot or cast for 4 / 5 / 6 s (a boss: half); cooldown 30 / 26 / 22 s, 1 s off per ordinary hit |
| 5 to 9 | multishot, piercing_arrows, power_shot, steady_aim, quickfoot | archery | as built |
| 10 | blink | arcana | as built; starts Phase |
| 11 | spell_surge | arcana | the next **damaging** spell is free and +50 %; cooldown 20 / 16 / 12 s, 1 s off for each damaging cast that hits (`cooldown_per_cast`) |
| 12 | arcane_ward | arcana | Mana Shield spends 10 / 20 / 30 % fewer SP |
| 13 | overload | arcana | area spells +10 / 20 / 30 % per monster **the blast strikes** beyond the first, at most 3 more |
| 14 | binding_circle | arcana | as built |
| 15 to 18 | bloodthirst, conditioning, spell_suppression, manathirst | any | as built |
| 19 | vanguard | arms | missiles and spells loosed from more than 800 away deal 20 / 40 / 60 % less (melee weapon drawn) |
| 20 | outnumbered | arms | 2 / 3 / 4 % less damage per hostile within 768, at most 10 (melee weapon drawn) |
| 21 | battle_frenzy | arms | +2 / 3.5 / 5 % melee damage per hostile within 768, at most 10 |
| 22 | heroic_strike | arms | active, a full rage bar: one blow at 200 / 250 / 300 %, half a swing's recovery |
| 23 | demoralizing_shout | arms | active, a full rage bar: hostiles within 1,024 deal 30 % less for 6 / 8 / 10 s; cooldown 45 / 40 / 35 s |
| 24 | long_shot | archery | bow damage +0 at 1,536 rising evenly to +3 / 6 / 9 % at 5,120 |
| 25 | expose_weakness | archery | a critical bow hit: the monster takes 3 / 6 / 9 % more damage for 5 s |
| 26 | hamstring | archery | a critical bow hit: the monster's movement is 5 / 10 / 15 % slower for 3 s |
| 27 | nimble | archery | 5 / 10 / 15 % less damage while moving |
| 28 | arc | arcana | a single-target spell's missile leaps to 1 / 2 / 3 more within 1,024 at 30 % + 0.25 % per point of the best magic school (at most 50 %) |
| 29 | opening_volley | arcana | +15 / 30 / 45 % spell damage to a monster at full health |
| 30 | breach | arcana | spells ignore 5 / 10 / 15 % of a monster's resistance |
| 31 | phase | arcana | 20 / 35 / 50 % less damage for 3 s after a Blink (needs Blink) |

Top-level keys: `paths: [arms, archery, arcana]`, `rage:` (the bar's seven numbers), `damage_floor: 0.2`. New
per-talent keys: `cooldown_per_kill`, `cooldown_per_cast`, `rage_cost`, `full_distance`.

**Icons:** every talent has its own (`icon_item: talent_<id>`); see "Icons, sounds and translations" below. The
first build shipped stand-ins.

**In-game texts keep metres** (the table's convention: 1,024 units is "10 m"), the documents game units.

## Where each part is

| Part | Code |
| --- | --- |
| Table, the path lock (`talentPath`, `talentLearnRefusal`), rage rules, the kill and cast cooldown feeds | `game/rules/SoloTalents.{h,cpp}` |
| The talents' numbers: `incomingDamageScale` (Spell Suppression, Vanguard, Outnumbered, Nimble, Phase, the floor), `battleFrenzyScale`, `longShotScale`, `spellDamageBonus`, `breachShare`, `manaShieldCostScale`, rage gain | `game/rules/maw/MawSoloTalents.{h,cpp}` |
| Hits on monsters: stage `solo-talents` (Battle Frenzy, Long Shot, the spell talents, Expose Weakness) and Breach in `resistance` | `MawCombatRules.cpp` (`m_damageToMonster`) |
| Hits on the character: stage `solo-talent-cuts` (was `solo-spell-suppression`) | `MawCombatRules.cpp` (`m_damageToCharacter`) |
| Rage from blows, Expose Weakness and Hamstring on a critical arrow, the cast feed | `MawCombatRules::applyPartyHitEffects` |
| Rage from hits taken, Arcane Ward | `MawCombatRules::absorbCharacterDamage` |
| Onslaught on spell recovery; Spell Surge only on damaging spells | `MawSpellRules.cpp` |
| The actives (Challenge, Heroic Strike, Demoralizing Shout), the full-bar check, Phase on Blink, the weapon in the arms | `GameplayInteractionController.cpp` (`useSoloTalent`, `updateWorldInteractionFrame`) |
| Vanguard's distance: `ProjectileState::firedDistance`, set at spawn, carried by `CombatEvent::firedDistance` to `CharacterDamageHit::firedFromDistance` | `GameplayProjectileService.cpp`, `GameplayCombatController.cpp`, both world runtimes |
| Long Shot's distance and Overload's count: `PartyMissileSource::flightDistance` and `blastMonsters` | `GameplayProjectileService::partyMissileSource`, the blast loops of both world runtimes |
| Arc: the spell missile's `chainCount`, `chainShare`, `chainRadius` | `PartySpellSystem.cpp`, `GameplayPartySpellProjectileRequest`, both world runtimes |
| Monster states: `silenceRemainingSeconds`, `moveSlowRemainingSeconds` and `moveSlowMultiplier`, `demoralizeRemainingSeconds` (`GameplayActorHitDebuff::Silence`, `MoveSlow`, `Demoralize`) | `GameplayRuntimeInterfaces.h`, `GameplayActorService.cpp`, `GameplayActorAiSystem.cpp`, both world runtimes |
| The Talents page (nine rows a path, the lock) | `game/ui/GameplaySoloTalentsPage.cpp` |
| The rage arc round the portrait (`ArcMaterial::Rage`, `RageFull`) and the "cannot pay" veil on the two abilities | `game/ui/GameplaySoloHud.cpp`, `GameplayUiSkin.{h,cpp}` |
| The pack talents' own counts within their `distance` (`MawRules::outnumberedMonsters`, `battleFrenzyMonsters`; `talent list` prints them) | `MawCombatRules::updateCombat`, `MawSoloTalents::packReach` |
| The view model: Heroic Strike's swing, Shield Wall's guard removed | `game/render/FirstPersonViewModel.{h,cpp}` |

## Save 197

- `SoloTalentState`: rage, in the place Shield Wall's seconds had (same size, so older saves' layout holds).
  Phase's three seconds and the rage limit's running second are not saved.
- `ProjectileState::firedDistance`.
- Actors (both layouts): the three new timers and the movement multiplier.
- `ActorRulesetFacts`: `exposedPercent`, `exposedUntilGameMinutes`.
- **Migration** (`migrateTalentPaths`): Shield Wall's and Resolve's ranks go and their points return; a character
  with ranks in two or three paths keeps the one with the most (the first on a tie); action-bar keys on a talent the
  character no longer has are emptied. Onslaught keeps its ranks (rank 3 is now 18 %).

## Notes from the build

- **The spell talents act where the spell lands,** not at the roll: `rollSpellDamage` only remembers the crowd a
  named target had round it. Spell Surge's window, Overload's count and Opening Volley's "full health" are all read
  in the `solo-talents` stage, and they add (at most +185 %).
- **Overload's count.** A missile's blast knows the monsters it damaged. A spell that names its target and has no
  blast of its own keeps the count taken at the cast (as before). The spells that strike everything in view at once
  (Inferno, Armageddon, Prismatic Light, Souldrinker) still pass no count: **Overload does not apply to them yet.**
- **Arc** rides on the arrows' chain code, so it applies to spells that fly as one missile. A spell that lands at
  once without a missile does not leap; MAW's Chain Lightning keeps its own hops.
- **Arc's share** reads the best magic school (`talentSkillShare`), not the cast spell's school.
- **Hamstring** is a slow of movement alone, a new monster state. Binding Circle still uses the game's ordinary slow
  (which also slows attacks); moving it to the new state is a one-line change if wanted.
- **Challenge** makes the AI treat the monster as it treats a blinded one for its choice of attack: it falls back to
  its blow and walks in. A monster with no blow at all only stops shooting.
- **Demoralizing Shout** joins `damageDebuffed`, MAW's own 30 % cut, so it does not stack with Shrinking Ray or
  Dark Grasp.
- **The shared floor** covers the percentage cuts of `solo-talent-cuts`. Unbroken and Cheat Death act later, where
  damage is absorbed, and are outside it; so is the Shout, which is the monster's side.
- **The weapon in the arms** is set from `soloBowDrawn` each frame; without the arms (headless) an archer with
  nothing in the main hand counts as holding the bow.
- **Rage** is checked and spent in `useSoloTalent` where the cooldown starts. A Heroic Strike that waits for its
  swing has paid already; if the monster steps away the swing whiffs.
- **Localization:** the new texts are English keys; `tools/l10n.py extract` and `update` have not been run.

## Tests (run 2026-11-18)

- **Unit:** `tests/SoloTalentTests.cpp` (`--test-case='*solo*'`, 53 cases): the shipped table, the path lock, rage,
  the cuts and their floor, the damage talents, the kill and cast feeds, the damage stages. The whole suite: 3,096 of
  3,097 pass; the one failure ("the staged Hesper missiles ...") reads a local, git-ignored stage
  (`output/hesper_stage`) whose own `talents.yml` dates from 2026-11-13 and no longer loads. It fails without this
  work too; rebuilding the stage clears it.
- **Scenarios** (`tests/scenarios/rulesets/`), all passing, with the eleven older `maw_solo_*` ones and the sixteen of
  `tests/scenarios/release/scenarios.txt`:

  | Scenario | What it shows |
  | --- | --- |
  | `maw_solo_archetype_path_lock` | The first rank closes the other paths; the Any tree chooses none; a reset frees the choice; only Arms has rage; a save keeps it |
  | `maw_solo_rage_heroic_strike` | Heroic Strike does nothing on an empty bar; a blow that hits fills some; on a full bar it strikes and the bar is spent |
  | `maw_solo_challenge_shouts` | Challenge is not spent when nothing has noticed the Knight; used, the archers at 1,500 and one at 2,800 stop shooting for its six seconds and start again; Demoralizing Shout needs the full bar and its reach |
  | `maw_solo_vanguard` | Six archers at 1,500 for six seconds: the Knight keeps about 46 % of its HP without the talent and about 78 % with rank 3 (four runs: a loss of 54 % against 22 %, the 60 % cut) |
  | `maw_solo_pack_reach` | Monsters at 400, 700 and 1,100: Outnumbered and Battle Frenzy count the first two, the one at 700 lying outside MAW's 512 |
  | `maw_solo_arc` | A Fire Bolt hurts one of three monsters without Arc and all three with rank 2 |
  | `maw_solo_archer_critical_talents` | A critical arrow sets Expose Weakness at 9 % and the movement slow, and not the ordinary slow; the slow ends after its three seconds |

  Three older scenarios of the family fail now and then with the same binary (two failures in eight runs of
  `maw_solo_chaining_arrows`; `maw_solo_multishot_cooldown_per_hit` and `maw_solo_talent_battle_order` once each):
  they count on rolls the game seeds from the clock. In the failing logs read, a critical arrow killed the first
  Mercenary Captain, so only two of three were "living and hurt", and the Captain was still alive beside the archer
  when the last Power Shot should have flown. Tougher targets (a boss affix, as `maw_solo_archer_critical_talents`
  has) would steady them; they are not changed here.

- **The user's archer** (a copy of `saves/save154.oysav`, never the file itself): the save loads through the
  migration with Archery's fifteen ranks, Onslaught 3, the Any tree and both keystones kept, Shield Wall and Resolve
  gone and eight points to spend; Cleave is refused ("Your path is Archery"), Nimble and Long Shot can be learned.
- **In the game** (`./tools/run_game.sh --isolated`, native captures): the Talents page with nine rows a path, "your
  path" and "another path" on the headers, and the rage arc round the portrait (empty, filling and gold when full).
- Scenario helpers added: `console: {expect_not_contains}`; `hp atleast <percent>` and `hp atmost <percent>`;
  `talent learn <id>` (as the page learns) and `talent rage <amount>`; `turn_based.actor_effect` also takes
  `silence`, `move_slow`, `demoralize` and `exposed`.

## Changes after the first play (2026-11-18, the user)

- **Vanguard** is 20 / 40 / 60 % (was 40 / 60 / 80): "vanguard - make it 20/40/60". With Spell Suppression's 20 % it
  leaves 32 % of a hit, so the shared floor (20 %) is reached only with Outnumbered's ten monsters as well.
- **Outnumbered and Battle Frenzy** count within 768 (was 512): "make it 768 range". They no longer ride on MAW's
  count for legendaries 21 and 22, which stays at 512: `MawCombatRules::updateCombat` counts for each talent within
  its own `distance` in the table.
- **Challenge** takes "every hostile currently agroed": every living hostile that has noticed the party
  (`hostileToParty` and `hasDetectedParty`), wherever it stands and in sight or not, in place of every hostile within
  2,048. With no such monster it says "No monster has noticed you" and keeps its cooldown.
- **Long Shot and Expose Weakness** are 3 / 6 / 9 % (were 5 / 10 / 15): "expose weakness, long shot - make it only
  3/6/9%" (2026-11-19). For the reference archer, whose every arrow is a critical hit, the two together are now 9 to
  19 % more damage at rank 3, where they were 15 to 32 %.
- **The rage bar** is an arc round the right side of the portrait, from its foot up to its crown, as the party
  frame's SP arcs are (the user's sketch): red while it fills, gold when full, the weapon socket over it. The strip
  under the SP bar and its "Rage N" label are gone; the HP and SP bars have their own sizes again.

## Icons, sounds and translations (2026-11-18, the user's follow-up)

- **Icons:** fifteen painted icons, one for each talent that came with the paths (Challenge, Vanguard, Outnumbered,
  Battle Frenzy, Heroic Strike, Demoralizing Shout; Long Shot, Expose Weakness, Hamstring, Nimble; Arcane Ward, Arc,
  Opening Volley, Breach, Phase), made and installed like the first set:
  `level_generation/ui/solo_talent_icons_20261114/` (subjects in `scripts/make_icons_json.py`, its README's
  2026-11-18 entry, `viewer.html`). Every talent in the table now has `icon_item: talent_<id>`; the icons of the
  talents that left (Shield Wall, Resolve) stay in `icons_x2`, unused.
- **Sounds:** Challenge, Heroic Strike and Demoralizing Shout have their own (`engine/audio/solo_talents/`, played by
  name from `useSoloTalent`: the shouts as they are used, Heroic Strike at its blow). ElevenLabs,
  `level_generation/sounds/solo_archetypes_20261118/` (three takes each, 150 credits; `review/index.html` plays them).
  The installed takes are the tool's automatic picks: nobody has listened to them yet. Another take is
  `choice: vN.wav` in that folder's `picks.yml`, then `process` and a copy.
- **Translations:** `tools/l10n.py extract` and `update`, then machine drafts (marked for review) of the 66 texts new
  since the last templates, in all seven languages: the talents' names and texts, the path and rage lines, and the
  dimension rift texts that were waiting with them. One collision fixed: the New Game screen's "Challenge" section
  shares its English with the talent, and Russian had it as "Сложность" (difficulty); the section now asks with the
  context `rules section` (`trc`), which keeps its translations, and the talent is "Вызов". Chinese names Arc "弹射":
  the first draft used a character the Chinese fonts lack.

## Not done

- Overload on the spells that strike everything in view: left as it is by the user's decision (2026-11-18).
- The monster inspect popup does not list the three new states.
- Passive talents and Phase have no sound; Arc's leaps use the spell's own.
- Play: none of the numbers has been played. The research's parity checks (§6 there) are the next step.
