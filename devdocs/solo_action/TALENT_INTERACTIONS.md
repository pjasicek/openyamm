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
| **Paying blow** | Cleave's first monster (the crosshair's, else the nearest in the arc), Charge, Power Shot | the talent's share (Cleave 150 %, Charge 100 %, Power Shot 135/170/200 % by rank) | pays the recovery times the talent's `recovery` (Cleave and Power Shot 50 %; its clip plays in that time), less the clip's time already spent; plays the attack sound | skipped (`PartyAttackConfig::talentBlow`) |
| **Extra blow** (`PartyHitOnMonster::extraBlow`) | Cleave's other monsters; Sweeping Blows' 1/2/3 monsters beside an ordinary swing | Cleave 150 %; Sweeping Blows 30 % + 0.25 % per weapon-skill point, at most 50 % | none (the paying blow or the swing pays); no attack sound (Cleave plays `talent_cleave` at each monster struck) | skipped |
| **Talent shot** | Multishot's arrows (2/3/4 headings, twice with a Master bow) | 75 % each | one recovery for the volley | skipped |

Ordinary attacks are not talent blows. An ordinary bow shot's arrows can chain (Chaining Arrows, once Piercing
Arrows): each arrow leaps on from the monster it strikes to the nearest other within 1024, and each monster after the
first is struck at the talent's share (30 % + per weapon skill) and is an ordinary missile hit.

**No flinch** (user, 2026-11-16): Sweeping Blows' extra blows and an arrow's Chaining Arrows leaps make the monster
neither play its hit reaction (the GotHit flinch, the stagger rules' wince) nor take the knockback; the main blow or
the arrow's first monster still do. `IGameplayWorldRuntime::applyPartyAttackMeleeDamage(..., hitReaction)`:
`TalentBlow::noHitReaction` for Sweeping Blows, and a projectile that has struck a monster before
(`ProjectileState::chainStruckActorIds`) for the leaps. Cleave's other monsters still flinch. Checked headless at
0.05 s steps: the swept and chained Mercenary Captains are hurt but never in GotHit.

## Per hit, by kind

"Full" means exactly as an ordinary attack's hit. "⅓" is `ExtraBlowShare` in `MawCombatRules.cpp` (user, 2026-11-15:
"make the sweeping leech 33% as effective ... including other onhit stuff"). "**none**" is the main blow's alone (user,
2026-11-15: "these special onhits should only apply to the main target"). Retaliation used to spend its stacks on the
first monster struck, an extra blow (they strike before the paying blow), so a Knight's burst landed at Sweeping Blows'
30 % on a side monster; now the main target always gets it.

| Effect | Paying blow | Extra blow | Talent shot (Multishot) | Chained monster |
| --- | --- | --- | --- | --- |
| Leech (weapons' Vampiric/Darkness, Vampire race, Death Knight, aura 91, a dragon's Regeneration, Bloodthirst), floor included | full | **⅓** (floor included) | full, ranged rate | full, ranged rate |
| Dragon's bite SP (10, Great Wyrm 20) | full | **⅓** (3 / 7) | — | — |
| Dragon's bite push (Fangs) | full | **none** | — | — |
| Death Knight: SP a hit (10/15/20, ×1.5 on a kill) | full | **⅓** | full (physical arrows) | full |
| Death Knight: Blood Leech heal and its SP cost | full | **⅓** both | full | full |
| Death Knight: Death Grasp (15 SP, holds the monster) | full | **none** (no SP spent) | full | full |
| Shaman: Mind SP, Body heal | full | **⅓** | — (melee only) | — |
| Seraph: Body heal on the weakest member | full | **⅓** | — (melee only) | — |
| Assassin: energy cost and refund, combo points, Subtlety | full | full | full (arrows half, as MAW) | full |
| Elementalist: a weapon hit clears the stacks | yes | yes | yes | yes |
| Grandmaster spear stack, Legendary 29 (+1 % damage taken) | full | full | full | full |
| Artifacts' on-hit spells (Splitter, Thor and its push, Percival, Hades; Snake and Finality's Slow) | full | **none** | full | full |
| Mace and staff paralysis (Master: skill against the monster's level × 15 % / 10 %; 2 s, 4 s at Grandmaster) | full | **none** | — | — |
| An item's stagger (Thor's stun) | full | **none** | — | — |
| Retaliation: its stacks' bonus damage and paralysis chance (spends the stacks) | full | **none** (the stacks stay for the paying blow) | — | — |
| Legendary 24: a kill restores 10 % HP and 5 % SP | full | full | full | full |
| Onslaught: a kill adds a stack | yes | yes | yes | yes |
| Regenerating boss counts the hit; Doom modes wake the monsters near | yes | yes | yes | yes |
| Reflection (a monster's or a dimension's) | yes | yes | yes | yes |
| Charge's cooldown −1 s (`cooldown_per_attack`): ordinary attacks only, once per attack | no | no | no | — |
| Sweeping Blows follows the blow | no (talent blows never sweep) | no | no | — |
| Chaining Arrows | — | — | no (only an ordinary shot's arrows chain) | — |

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
- **Chained monsters leech in full,** floor included, at the ranged rate.
- **Legendary 24** (a kill restores 10 % HP and 5 % SP) acts in full on an extra blow's kill.

## Code

- `GameplayInteractionController.cpp`: `useSoloTalent` (Cleave, Charge, Multishot, Power Shot),
  `strikeFollowUpTalentBlows` (Sweeping Blows), `executePartyAttack` (Chaining Arrows' count, the per-attack
  cooldowns).
- `GameplayActionController.cpp`: `PartyAttackConfig::talentBlow` (skips the battle orders), `talentShare`,
  `talentExtraBlow`, `talentShot`; the hit's `extraBlow`. Until 2026-11-15 a talent blow was guessed from its share, so
  Charge's 100 % blow went through the battle orders (a spell or shoot order could replace it, Hold drop it).
- `MawCombatRules.cpp`: `applyPartyHitEffects`, `applyLeech`, `applyClassHitEffects`, the melee branch of
  `resolveCharacterAttack` (weapon stun, item stagger, Retaliation), `soloExtraBlow` and `extraBlowShare`;
  `CharacterAttackOnMonster::extraBlow` and `PartyHitOnMonster::extraBlow` carry the kind.
- Tests: `tests/MawAuditCombatSpellTests.cpp` ("The leech floor ...", "A dragon's bite gives spell points ..."),
  `tests/MawBossAffixTests.cpp` ("A solo talent's extra blow leaves Retaliation's stacks to the main blow ...").
