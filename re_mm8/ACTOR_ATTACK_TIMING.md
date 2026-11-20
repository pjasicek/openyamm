# MM8 actor attack timing

Investigated 2026-10-14 to decide how 3D actor clips are timed against the native billboard attack.

## Evidence and scope

- Static disassembly of the GOG-verified `mm8_orig/MM8-Rel.exe`
  (SHA-256 `5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b`). Rizin was not installed on the
  investigating host, so `objdump -d -M intel` was used; addresses are the executable's virtual addresses.
- Actor records start at `0x61c458`, stride `0x3cc` (as in [Actor sounds](ACTOR_AUDIO.md)). Sprite IDs: melee
  attack `+0xc8`, ranged attack `+0xca`. Action length `+0xa8` (16-bit), elapsed action time `+0xc0`, AI state
  `+0xb8`, recovery `+0x84`. Sprite frame records are `0x3c` bytes with the animation length at `+0x38`.

## Findings

**The blow, missile or spell happens when the whole attack sprite animation has elapsed, never on a frame.**

1. The five attack starters set the action length to the attack sprite's full animation length (`<< 3`, ticks),
   reset the elapsed time, set the AI state and request the attack sound in the same call:

   | Starter | Sprite | Length written | State | Sound call |
   | --- | --- | --- | ---: | --- |
   | Melee `0x403f4e` | `+0xc8` | `0x4040be` | 2 | `0x4040d4` |
   | Ranged 1 `0x40373b` | `+0xca` | `0x4038bd` | 3 | `0x4038d3` |
   | Ranged 2 `0x403953` | `+0xca` | `0x403a97` | 12 | `0x403aad` |
   | Spell 1 `0x403b2c` | `+0xca` | `0x403c70` | 13 | `0x403c86` |
   | Spell 2 `0x403d3d` | `+0xca` | `0x403e81` | 18 | `0x403e97` |

2. The real-time actor update adds the frame time to the elapsed time (`0x4020b2`) and ages the recovery
   (`0x4020b8`). At `0x402187` it skips the action while `elapsed < length`; once the length is reached it
   dispatches on the state: melee (2) pushes the melee attack at the body's half height (`0x40276d` with `0x1400`,
   `0x402244`), ranged 1/2 (3, 12) fire the attack-1/attack-2 missile (`0x404bc6`), spells (13, 18) cast spell 1/2
   (`0x404e2f`). The same order and states as OpenEnroth's MM7 `Actor::UpdateActorAI`.

## Consequence for billboards and models

The native attack sprites are drawn with the contact or release before their last frames (the MM6 archer
releases at about 0.88 s of 1.19 s, followed by two follow-through frames; 0.75 s melee sprites usually strike at
about 0.4-0.6 s). The original therefore applies damage and spawns missiles up to ~0.3 s after the drawn contact.

OpenYAMM keeps this timing by default and can apply an attack at its sprite's drawn contact instead: a sprite listed
in `assets_dev/engine/rendering/sprite_attack_timing.yml` applies it when that frame appears, while the action still
lasts the whole animation (`attackImpactLeadSecondsForAbility` in the shared actor AI). This is a deliberate deviation
from MM8 for annotated sprites (hits up to ~0.3 s earlier); unlisted sprites, including all of MM7/MM8 until annotated,
behave as above. A 3D clip's `impact` marker is fitted to whichever moment applies (`WorldFxSystem`). The same file can
delay a sprite's attack sound (`sound_delay`, seconds on the attack's clock); MM8 always plays it as the attack starts.

## Where a melee blow on the party lands

Investigated 2026-10-27: does a party that steps back during a monster's swing avoid the blow?

- When the melee action ends, the actor update pushes the blow onto the attack list at `0x5214c8` (`0x40276d`)
  from the body's half height with reach `0x1400` (5120, `push 0x1400` at `0x402238`).
- The list is resolved at `0x4373e5`. For a melee entry against the party (the attacker's target at `0x508198`),
  the blow lands when the party's height-adjusted centre is closer than reach + 32 (`add ecx,0x20` at `0x4374bf`)
  and the line of sight test `0x408520` passes from the party's eyes; then the hit roll and damage follow.
- Nothing re-checks the 307.2 melee distance the monster needed to start the swing, so once a blow is started it
  lands unless the party breaks line of sight (a corner, a closing door). OpenEnroth's MM7 `evaluateAoeDamage`
  does the same. MAW keeps it; its only melee avoidance is the GM Dodging roll in `CalcDamageToPlayer`.

OpenYAMM follows this: `GameplayActorService::MonsterMeleeImpactReach` (5152, from the middle of the monster's body
to the party's) with line of sight, in `IndoorWorldRuntime`/`OutdoorWorldRuntime` `...CanApplyPartyMeleeImpact`;
the optional `meleeVerticalReach` of a world (Hesper) still applies there. Earlier OpenYAMM re-checked the 307.2
edge distance when the blow landed, which let a backpedalling party slip most blows.
