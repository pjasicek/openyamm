# Solo talents: interactions with on-hit effects

How each damaging solo talent (MAW solo run only, [talent tree v2](TALENT_TREE_V2_BUILD.md)) meets the rest of the
combat rules: leech, the classes' on-hit gains, item and artifact effects, kills, recovery, sounds and other talents.
Regular MAW, party games and Standard never make a talent blow, so none of this reaches them. The rules also check
`options().soloRun` before cutting anything.

## Blow kinds

A talent strikes through `executePartyAttack` (`GameplayInteractionController.cpp`) with a `TalentBlow`, so every hit
is an ordinary hit for the rules (`MawCombatRules::applyPartyHitEffects`). Three kinds:

| Kind | Made by | Damage | Recovery, sound | Battle orders |
| --- | --- | --- | --- | --- |
| **Paying blow** | Cleave's first monster (the crosshair's, else the nearest in the arc), Charge, Pinning Shot | the talent's share (Cleave 150 %, Charge and Pinning Shot 100 %) | pays the recovery, less the clip's time already spent; plays the attack sound | skipped, except Charge's 100 % blow (see open points) |
| **Extra blow** (`PartyHitOnMonster::extraBlow`) | Cleave's other monsters; Sweeping Blows' 1/2/3 monsters beside an ordinary swing | Cleave 150 %; Sweeping Blows 30 % + 0.25 % per weapon-skill point, at most 50 % | none (the paying blow or the swing pays); no attack sound (Cleave plays `talent_cleave` at each monster struck) | skipped |
| **Talent shot** | Multishot's arrows (2/3/4 headings, twice with a Master bow) | 75 % each | one recovery for the volley | skipped |

Ordinary attacks are not talent blows. An ordinary bow shot's arrows can pierce (Piercing Arrows): each monster after
the first is struck at the talent's share (30 % + per weapon skill) and is an ordinary missile hit.

## Per hit, by kind

"Full" means exactly as an ordinary attack's hit. "⅓" is `ExtraBlowShare` in `MawCombatRules.cpp` (user, 2026-11-15:
"make the sweeping leech 33% as effective ... including other onhit stuff").

| Effect | Paying blow | Extra blow | Talent shot (Multishot) | Pierced monster |
| --- | --- | --- | --- | --- |
| Leech (weapons' Vampiric/Darkness, Vampire race, Death Knight, aura 91, a dragon's Regeneration, Bloodthirst), floor included | full | **⅓** (floor included) | full, ranged rate | full, ranged rate |
| Dragon's bite SP (10, Great Wyrm 20) | full | **⅓** (3 / 7) | — | — |
| Dragon's bite push (Fangs) | full | full | — | — |
| Death Knight: SP a hit (10/15/20, ×1.5 on a kill) | full | **⅓** | full (physical arrows) | full |
| Death Knight: Blood Leech heal and its SP cost | full | **⅓** both | full | full |
| Death Knight: Death Grasp (15 SP, holds the monster) | full | full (each monster grasped costs 15 SP) | full | full |
| Shaman: Mind SP, Body heal | full | **⅓** | — (melee only) | — |
| Seraph: Body heal on the weakest member | full | **⅓** | — (melee only) | — |
| Assassin: energy cost and refund, combo points, Subtlety | full | full | full (arrows half, as MAW) | full |
| Elementalist: a weapon hit clears the stacks | yes | yes | yes | yes |
| Grandmaster spear stack, Legendary 29 (+1 % damage taken) | full | full | full | full |
| Artifacts' on-hit spells (Splitter, Thor, Percival, Hades; Snake and Finality's Slow) | full | full | full | full |
| Legendary 24: a kill restores 10 % HP and 5 % SP | full | full | full | full |
| Onslaught: a kill adds a stack | yes | yes | yes | yes |
| Regenerating boss counts the hit; Doom modes wake the monsters near | yes | yes | yes | yes |
| Reflection (a monster's or a dimension's) | yes | yes | yes | yes |
| Charge's cooldown −1 s (`cooldown_per_attack`): ordinary attacks only, once per attack | no | no | no | — |
| Sweeping Blows follows the blow | no (talent blows never sweep) | no | no | — |
| Piercing Arrows | — | — | no (only an ordinary shot's arrows pierce) | — |

Measured on a level-100 Great Wyrm against three Chaos Overlords (2026-11-15): before the cut, each monster Cleave
struck healed about +430 to +520 HP and gave +20 SP. The proportional heal, not the floor, made most of it: it is the
share of a B-tier monster's bar the hit took, so a killing blow counts a whole bar.

## Talents with no blows

Shield Wall, Blink, Binding Circle (holds monsters, no damage), Spell Surge, Quickfoot and the passives strike nothing.
Overload and Spell Surge change spells, which leech and gain by the spell rules (the spell rate); a spell is never an
extra blow.

## Open points (not decided)

- **Multishot leeches in full per arrow:** eight arrows (rank 3, Master bow) into a crowd heal eight times, floor
  included, at the ranged rate.
- **Pierced monsters leech in full,** floor included, at the ranged rate.
- **Legendary 24 and Death Grasp** act in full on extra blows.
- **Charge's blow consults the battle orders:** its share is 100 % and it is neither extra nor a shot, so
  `GameplayActionController::executePartyAttack` does not treat it as a talent blow; an order may pick another attack
  (a spell, the bow) for it.

## Code

- `GameplayInteractionController.cpp`: `useSoloTalent` (Cleave, Charge, Multishot, Pinning Shot),
  `strikeFollowUpTalentBlows` (Sweeping Blows), `executePartyAttack` (Piercing Arrows' count, the per-attack
  cooldowns).
- `GameplayActionController.cpp`: `PartyAttackConfig::talentShare`, `talentExtraBlow`, `talentShot`; the hit's
  `extraBlow`.
- `MawCombatRules.cpp`: `applyPartyHitEffects`, `applyLeech`, `applyClassHitEffects`, `extraBlowShare`.
- Tests: `tests/MawAuditCombatSpellTests.cpp` ("The leech floor ...", "A dragon's bite gives spell points ...").
