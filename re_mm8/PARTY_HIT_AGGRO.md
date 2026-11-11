# Monsters hit by the party from far away

Investigated 2026-10-26 after a report that outdoor monsters shot from beyond their aggro range do not react.

## Result

**In original MM8 an outdoor monster hit from 5632 units or more stands where it is.** The party damage routine
marks it Active and Nearby, makes it hostile, turns it toward the attacker and plays the hit reaction, but the
outdoor full-AI list is rebuilt every pass from distance alone and drops it again. Indoors the Nearby bit keeps a
hit monster in the full-AI list within 10240 units, so it comes for the party.

**Party projectiles reach far beyond that range in real time.** Nothing removes them by distance; they fly until
their lifetime expires: 6 seconds at 4000 units per second for arrows, Fire Bolt and Ice Bolt (24,000 units), 1
second at 8000 for Lightning Bolt (8000 units). Only turn-based mode removes objects it waits on beyond 5120.

OpenYAMM deviates here on purpose (the user, 2026-11-09, replacing the 2026-10-26 outdoor-only rules):

- In every ruleset, indoors and outdoors, the party's shots vanish beyond 5120 units from the party and its targeted
  spells refuse monsters farther away, nor do its area spells take them, Armageddon aside
  (`GameplayActorService::partyHitReach`): the yellow alert range, as far as
  monsters shoot and cast at the party, and as far as turn-based combat keeps shots. A world may declare a shorter
  range (MM9's 4096, its engagement range). The party hits only what can hit it back, and a monster it hits is always
  within its own 5120 missile reach, so the earlier rule that let a far-hit monster shoot back from the distance of the
  hit (`provokedAttackReach`, 8192 outdoors under Standard) is gone.
- Outdoors a monster the party hits stays active out to the 10240 engagement range until it comes within the full-AI
  range (`provokedByParty`), ahead of other monsters in the 48 full-AI slots, so a party backing off after a shot does
  not leave it standing beyond the full-AI range.

Every monster keeps MM8's 5120 missile reach, which also holds for monsters whose only attack is a missile
(`GameplayActorAiSystem`); at the party it is no longer than the party's own reach (`ActorAiFrameFacts::partyHitReach`,
MM9's 4096), so the party can answer every shot.

## Inputs and method

`mm8_orig/MM8-Rel.exe`, SHA-256 `5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b`
([verified GOG executable](GOG_INSTALLER_VERIFICATION.md)), project `re_mm8/work/mm8-rel-5326d564-base.rzdb`,
Rizin 0.10.0 run from `third_party/rizin/build/binrz/rizin/rizin`. Addresses are preferred VAs (base `0x400000`).
MMExtension's structure declarations (`reference/mmmerge/Scripts/Structs/`) supplied field names; its global
addresses are for the patched `mm8.exe` and sit `0xe8` (objects, IndoorOrOutdoor) or `0x100` (TurnBased) above
MM8-Rel's. Annotations: [mm8_rel_5326d564_party_hit_aggro.rz](mm8_rel_5326d564_party_hit_aggro.rz).

## Party damage to a monster

`0x4378ec` is the routine its own assertion names `damageMonsterFromParty` (`F:\MM8src\MM8\Code\Damage.cpp`).
Every hit, from any distance:

- `0x4379b8` `or byte [actor+0x25], 0xc0`: attributes Active `0x4000` and Nearby `0x8000`.
- Alive (`0x438162`): `0x40332f`, the hit reaction, sets hostility type 4 (`0x403366`), faces the attacker
  (`0x4043dc`) and puts the monster in AI state 8 for its hit animation (`0x40342a`); it starts no pursuit. Then
  `0x439278` alerts the monster's faction with the Aggressor flag (see [indoor activation](INDOOR_EXPLORATION_AND_ACTIVATION.md)).
- Dead: `0x402ec9`, then the same faction alert.

## Outdoor full-AI list

`0x40151a`, for every actor: clear FullAI; if it cannot act, or its approximate distance minus radius is
`>= 0x1600` (5632, `0x4015eb`), clear Active (`0x4015f3`) and skip it; otherwise set Active and add it. Nearby is
never read, so the bits the hit set do not keep a distant monster in the list. Outside the list it only gets the
background updates: its hit reaction ends and it stands or fidgets. The indoor builder reads Nearby
(`0x40194c`), which is why the hit works there.

## Projectile lifetime and travel

The object loop `0x472b60` walks the 0x70-byte map objects at `0x692ed0` (count `0x692ecc`):

- It adds the frame's ticks (`0x51d29c`) to the object's Age (`+0x1e`). If the object list entry has the lifetime
  flag `0x04`, Age at or past the lifetime (list `+0x2a`, or the object's MaxAge `+0x20` when its Temporary bit is
  set) ends it: impact when the list entry has flag `0x40` (`0x46bd3a`), otherwise removal (`0x42ee3b`).
- It moves the object with `0x4716af` indoors or `0x472047` outdoors (`IndoorOrOutdoor`, `0x6f38b8`).
- Only when TurnBased (`0xb21628`) is set and the object has HaltTurnBased (`0x04` in `+0x1a`) does it remove an
  object farther than `0x1400` (5120) from the party (`0x472d20`).

Movement goes through the shared sweep `0x47078b` with velocity times the timer's fixed-point step `0x51d2a0`.
The timer update `0x425008` stores elapsed ticks at `+0x1c` and `(ticks << 16) / 128` at `+0x20`: seconds in 16.16,
so object speed is units per second and 128 ticks are a second. With the object list (`object_list.txt`: arrow
545 and Fire Bolt 1010 at 768 ticks and 4000, Lightning Bolt 2060 at 128 ticks and 8000) that gives the ranges above.
