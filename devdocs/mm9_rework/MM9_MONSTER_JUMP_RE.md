# MM9 monsters at ledges: jumping, falling and climbing (reverse engineering)

How Might and Magic IX moves a monster over a height difference, from the shipped game code and data, to decide
whether our MM9 monsters should follow the party down drops. Research date 2026-11-02, Rizin 0.10.0 and
`objdump -M intel` on `mm9/game/data/object.lto` (the server game code, a Windows DLL; image base `0x10000000`;
SHA-256 `b1271f37e5314281035efe6425dd59051bb8a9b0271de0d75a5926a7bc37f162`, the same file as the
[collision RE](MM9_MONSTER_COLLISION_RE.md)). The AI behaviour scripts are the shipped text scripts in
`mm9/extracted/SCRIPTS/SCRIPTS/`; the map data is read with `transcode_mm9_dat_to_odm.read_dat_world`. Scratch scripts
and listings: `re_mm8/work/mm9_jump/` (ignored; `lto.py`, `refs.py`, `slot.py`, `survey_props.py`,
`survey_classes.py`, `prop_survey.json`). Units: LT × 2.56 = native.

## The rule

1. **A monster walks off any ledge and falls.** MM9 has no working ledge check for monsters. The game code has one
   (`CheckForCliff`: refuse a step when no floor lies within 8 half-heights straight down from the new position), but
   it reads the property `CheckForCliff` while the class declares, and every map stores, `CheckForCliffs`. The flag
   stays at its constructor value, false, for every monster. (All 2 219 placed actors store `CheckForCliffs 0`
   anyway.) Nothing else in the per-tick move limits a drop: the monster is moved horizontally with the engine's
   `MoveObject`, and LithTech gravity (`FLAG_GRAVITY`, always set) pulls it down. **There is no height limit.**
2. **Falling is not animated or punished.** No monster code selects the `fall`, `runningJump`, `climb` or
   `climbReverse` animations (those are only set by the player's movement code). A monster falls in whatever animation
   it was moving in (run or walk), keeps moving forward while it falls, and lands. No fall damage for monsters was
   found; the only fall-damage property (`FallDamageHitPoints`) belongs to the falling-debris trap class.
3. **The route decides when a monster goes down.** A chase is a `RunTo` on the target. Off rails the monster steers
   straight at the target; on rails it follows a rail path built by a depth-first search over `RailLink0-3` links. The
   path search has **no height test**, and every link is made in both directions. So a monster follows the party down
   a drop when the party is below and ahead of it (direct steering), or when its rail path leads over the edge.
4. **Monsters do not jump up or climb.** Going up is only the engine's stair-step (`FLAG_STAIRSTEP`, always set),
   whose height is engine code and was not established here. The `Jump` AI command only plays the `jump` animation in
   place, except for the three Dagrell classes, which leap forward. Rails flagged `IsLadder` would send a monster
   straight up, but no shipped rail has the flag. Hired followers climb ladders by a script (gravity off, scripted
   upward move), not by the AI.
5. **Real "jumping down at the player" is scripted.** The `Jumper.inc` script (Jeff Leggett, 2002): "Base script used
   by AI that jump off cliffs at the player". It is used by four Yetis in Frosgard and four bandits in Thjorgard.
   They wait hidden, step 60 LT forward, play a custom `JumpingDown` animation and leap (100 LT/s up, 250 LT/s
   toward the player) until they touch ground.
6. **Designers stop monsters with `AIBarrier` volumes, not with height rules.** A monster with `CheckForAIBarrier 1`
   (413 of 2 219 placed actors) refuses any step whose path crosses an active `AIBarrier` (294 of them, on 24 maps).

A second, separate rule exists for the "can I reach the target" question (AI scripts' `CanReachTarget` and the
navigation tick): the target's feet must lie between 7 half-heights below and half a half-height above the monster's
feet (with `TerrainMode`, no lower limit and 10.5 half-heights above). It is bypassed by `CanReachAll`, and **every
placed actor in every shipped map has `CanReachAll 1`**, so for placed monsters it never applies. Script-spawned
monsters get no DAT properties; whether the class default is 1 was not established (the constructor writes 0).

In native units, for a body of height `H` (half-height `h = H/2`): the disabled cliff check and the reach rule both put
the deepest acceptable floor 7h = 3.5 H below the feet (a 157-tall monk: 550; a 256-tall Terror: 896). The reach
rule's step up is 0.5h = H/4 (monk 39, Terror 64). Neither is active for placed monsters.

## Evidence (`object.lto`)

Vtable slots are byte offsets in the actor vtables (the 289 vtables whose `+0x3a0` slot is `0x10001bf0`; "287 of
289" means every monster class shares the function). The server interface is `[0x102babe8]`
(`+0x9c` IntersectSegment, `+0x158` GetObjectDims, `+0x7c` GetRotationVectors, `+0x138` GetPropGeneric,
`+0x230`/`+0x22c` touching objects and their type, `+0x144` HandleToObject). The actor animation enum is the
pointer table at `0x1019bad0` (0 idle … 42 flyFall, 43 flyFallDown, 46 jump, 49 climb, 50 climbReverse,
58 runningJump, 59 fall); the model animation name sets are filled per enum at `0x1001d7f0` (set offset =
enum × 0x2c: `Jump` → 46, `RunningJump` → 58, `Fall` → 59 and 42, `FallDown` → 43).

| Address | Slot | What it does |
| --- | --- | --- |
| `0x10001c80` | — | Actor precreate: object flags `|= 0x22003` (visible, shadow, solid, **gravity**) and `|= 0xd1000` (touch notify, **stair-step**, model keys). |
| `0x1000c33a`, `0x1000c340`, `0x1000c68a`, `0x1000c5d1` | — | Actor constructor: `CheckForAIBarrier` (`+0x729`), `CheckForCliff` (`+0x728`), `CanReachAll` (`+0xb52`), `TerrainMode` (`+0xb21`) all start false; `UsesRails` (`+0xb30`) starts true. Cliff probe length `+0x64c` starts at 12.0. |
| `0x1000d031`–`0x1000d052` | — | Actor setup, after the scale is applied: cliff probe length `+0x64c` = 8 × the object's half-height (GetObjectDims y). |
| `0x1000b5b8` | — | Class property definition **`CheckForCliffs`** (`0x1019b594`), default 0. |
| `0x1000d190` (`0x1000d2f5`) | — | Actor ReadProp: reads **`CheckForCliff`** (`0x1019b6c0`, no "s") into `+0x728`; also `CheckForAIBarrier` → `+0x729`, `CanReachAll` → `+0xb52`, `TerrainMode` → `+0xb21`, `UsesRails` → `+0xb30`, `RailDist`, `RailCheckInterval`, `MaxRailPath`. `0x100be160` leaves the field unchanged when the property is missing (it then only consults the `SetPropNumber` override list `0x102b8c8c`, exact case-insensitive name compare `0x100e4bc0`). No other code writes `+0x728` except save/load (`0x10016023`). |
| `0x10014630` | `+0x62c` | Per-tick movement (287 of 289). Clears horizontal velocity, keeps vertical velocity when `FLAG_GRAVITY` is set, applies push-back, then moves `pos + dir × speed × dt` through slot `+0x644`. If the move covered less than 80 % (`0x100eef28`) it flags the monster blocked (`+0x67d`). No floor or drop test. |
| `0x10012160` | `+0x644` | MoveTo (all classes; `0x1003d470` forwards to it). If `CheckForCliff`: ray from the new position along −up (`+0x57c`, the up vector from GetRotationVectors) of length `+0x64c`; no hit → do not move. If `CheckForAIBarrier`: horizontal ray toward the new position, length + radius; an active `AIBarrier` hit (`0x10076720`) → do not move. Otherwise engine MoveObject (`0x100bceb0`). |
| `0x10011a90` | — | Segment test used by both checks: IntersectSegment from a point along a direction × length; true if it hits within the length. |
| `0x100123c0` | `+0x46c` | Vertical reach test (my centre `a`, target point `b`, my half-height `h`): true if `CanReachAll`; else false if (no `TerrainMode` and `b.y < a.y − 8h`) or `b.y > a.y − 0.5h (+10h with TerrainMode)`. Constants `0x100ee5b8` 0.5, `0x100eeef0` 10.0. |
| `0x100125a0` | `+0x470` | Calls `+0x46c` with the target's feet (position y − its half-height). |
| `0x10012450` | `+0x474` | Calls `+0x46c` with the floor under a point (a 1000 LT ray down). |
| `0x10012620` | `+0x468` | CanReachObject: `+0x470`, then the horizontal sweep test `+0x464` (`0x10012970`). |
| `0x10013a80` | `+0x5bc` | Navigation tick: uses `+0x468`/`+0x464` for the target and ends in the rail logic `+0x6a4` with the monster's position. |
| `0x100178a0` | `+0x6a4` | Rail logic: current rail (`+0x69c`, `0x10016eb0`: an active `AIRail` volume the monster touches), the target's rail (`0x10017810`), `FindRail From [%s] to [%s]` and path build (slot `+0x700`). |
| `0x100170b0` | `+0x6a0` | Move direction: off rails the facing; on a rail toward the next rail or destination. `OneWayOnly` (`0x1003e270` → `+0x6d4`): use the rail's own direction (`0x1003e240`). `IsLadder` (`+0x6d5`, test at `0x10017370`): if the destination is higher, return (0, 1, 0), straight up. `UseRotation` (`+0x6d6`). |
| `0x1003e280` | — | `AIRail` ReadProp: `OneWayOnly`, `IsLadder`, `UseRotation`, `NoRunZone`, `UserData`, `RailLink%d`. Each named link is resolved by name (`0x1003d9d0`) and added **both ways** (`0x1003e3e0` twice), or logs "Invalid rail reference". |
| `0x1003e430` | — | BuildRailPath: recursive depth-first search over the link lists, skipping inactive rails (`+0x6d7`), depth limit `MaxRailPath`, 5 000-step guard ("Infinite loop in BuildRailPath"). No height comparison. |
| `0x1001aa80` | — | `IsInNoRunZone`: the current rail's `NoRunZone`. Only exposed to scripts (`0x100991b6`), which use it to walk instead of run. |
| `0x10097xxx`–`0x10099xxx` | — | AI script command factory (`Speak`, `WalkTo`, `RunTo`, `Attack`, `Jump`, `Launch`, `Land`, `CanReachTarget`, `IsInNoRunZone`, …). `Jump` (`0x10099db0`) calls slot `+0x4bc`. |
| `0x10014ad0` | `+0x4bc` | Jump (284 classes): plays animation 46 `jump`, nothing else. |
| `0x1002ffd0`, `0x10030080` | `+0x4bc`, `+0x670` | Jump override in three classes (constructors `0x1002ff70`/`0x100302a0`/`0x100303c0`, monster 147: Dagrell, Venomous, Spectre Dagrell): velocity = facing × `JumpVel` with the up component replaced by 0.2 × `JumpVel`, animation `jump`; slot `+0x670` steers horizontally in the air. `JumpVel` (script stat getter `0x10004630`) is monster record `+0x10`, initialised from `MONSTERS.txt` column R, RunVelocity (`0x1004463d`); Dagrells: 400 → 400 forward, 80 up. |
| `0x100c4a30` | — | Player only (`0x100c3820`, the client movement update: "Player [%s] can't seem to teleport…"): movement states 4/5/6/12 → `jump`/`runningJump`/`fall`/`climb`. The only users of 49, 50, 58 and 59 in the binary. |
| `0x10018b60` | — | Script `SetStat` on actors: `Gravity` toggles `FLAG_GRAVITY`; `CheckForObstacles`, `WalkRunMode`, speeds. No cliff or jump settings. |
| `0x10002580` | — | Animation keyframe commands. `Velocity` (slot `+0x3ac`, `0x10018220`) is a no-op in every class; `Launch` (`+0x3c8`) is overridden only by the 35 flyer classes. |
| `0x1005d7ab` | — | `FallDamageHitPoints`, `FallVelocity`, `HideUntilFall`, `FallDelayTime`: the falling-debris trap class, not actors. |

## Evidence (data and scripts)

| Source | Finding |
| --- | --- |
| All `WORLDS/*.dat` (`survey_props.py`) | Placed actors: `CheckForCliffs 0` 2 219 / 2 219; no `CheckForCliff` property anywhere; `CanReachAll 1` 2 216 / 2 216; `CheckForAIBarrier 1` 413, 0 1 806; `TerrainMode 1` 305; `UsesRails 1` 2 129. |
| All `WORLDS/*.dat` | 8 133 `AIRail` on 32 maps: `OneWayOnly 0` and `IsLadder 0` on all, `NoRunZone 1` on 105. 294 `AIBarrier` on 24 maps. 68 `Ladder` volumes on 21 maps (player containers; no actor code reacts to them was found). |
| `SPAWNCREATURE.scr`, `ISLE_SPAWNCREATURE.scr` | `SetPropNumber CheckForCliffs, TRUE` and `CheckForAIBarriers, TRUE` (the property override list for later spawns); both names differ from what the actor reads, so neither takes effect. |
| `BASE.inc` | The chase is `RunTo g_hTarget` (`BaseGoGetHim`); `CanReachTarget` only gates flying targets and `BaseObstacle`. No ledge handling. |
| `JUMPER.inc` / `JUMPER.scr`, `THORGARD_ACTOR.scr` | Scripted cliff jumpers: hidden with `FLAG_GOTHRUWORLD` and gravity off; on trigger, move 60 LT forward, `JumpingDown` animation, `SetVelocity 0,100,0`, push-back 250 LT/s toward the player (or straight ahead when the player is more than 45° off), stop on ground touch. Frosgard `Yeti6`–`Yeti9`, Thjorgard `Jumper0`–`Jumper3`. |
| `DAGRELLOLD.scr` | Dagrell leap attack (`Jump JumpDone` within `minJumpDist`), disabled in its own Main ("was getting stuck") and not used by any map or row; the Dagrell rows run `basemelee.scr`/`dagrell.scr`, which never jump. |
| `DRAGONAZURE.scr` (Hall of the Gods) | `Jump` to leave the water: the base Jump, the animation in place. |
| `FOLLOWPLAYER.inc` | Followers (hired goons, Mary's sheep, some NPCs) climb a ladder with gravity off and `MoveDir 0,1,0` by the ladder's height; going down is gravity on. |

## Confidence and open points

- **High:** no active ledge check (the name mismatch, the constructor default, no other writer, and 0 in all data);
  rail paths without height tests and with two-way links; no fall, climb or running-jump animation for monsters;
  the Jump command's behaviour; the scripted jumpers.
- **Medium:** that a missing property leaves the field unchanged in the engine. `object.lto`'s fallback is traced;
  the engine's own lookup is assumed to be an exact name match as in the LithTech reference
  (`mm9/lithtech/tools/shared/world/PropList.cpp` `strcmp`), not traced in `lithtech.exe`.
- **Medium:** no fall damage for monsters. This rests on not finding any: no fall-damage property or landing check
  in actor code, and no `DT_` fall type except `DT_ENDLESS_FALL` (the `EndlessFall` volume).
- **Not established:** the engine's stair-step height for monsters (LithTech physics in `lithtech.exe`; the Jupiter
  reference defaults to half the object's half-height, but MM9's engine is older and may differ). This decides which
  of the 82–123 native step-ups along rail links MM9 monsters could actually climb.
- **Not established:** whether rails without `RailLink` properties also join (the path setup at `0x1003db20` calls
  further helpers, `0x1003e960` and `0x1003eaa0`, that were not read); what a script-spawned monster's `CanReachAll` is; what happens when a monster is blocked at a wall on a
  rail link that goes up (the stuck handling, slot `+0x694`, was not read).
- The fall itself is engine physics (gravity value, air control). The monster keeps its horizontal move speed while
  airborne, because the movement tick keeps moving it.

## What this means for OpenYAMM

MM9 monsters follow the party down drops of any height: they walk off the edge and fall, still running, without a
special animation or damage, whenever direct steering or a rail path leads over the edge. They never jump or climb up;
going up is limited to what the engine's stair-step allows. To match this, our MM9 actors should be allowed to drop
much more than `IndoorActorMaxDropHeight` (100 native). If we want a limit at all, MM9's own (disabled) intent is
about 3.5 body heights below the feet (7 half-heights, the `CheckForCliff` and reach rule), well above 100 for every
walker. Keep the step-up small; MM9 gives no reason to raise it, and its two-way rail links over 82–123 native steps
are not evidence that monsters climbed them. Treat a downward rail link or a drop toward the target as walkable in
one direction only, and play the normal move animation while falling. Places where MM9 kept monsters back from an
edge did so with `AIBarrier` volumes on monsters with `CheckForAIBarrier 1`; the converter could carry those over as
actor-only blockers. The eight scripted cliff jumpers (Frosgard Yetis, Thjorgard bandits) are map scripts, not AI
behaviour. Any change to the shared drop limit must keep MM6–MM8 monsters as they are (an MM9 or per-actor setting).

## A target below a ledge, in water (2026-11-07)

Checked after a play-test on Verhoffin Ruins: the zombies on the walkway at z -328 walked off into the canal after a
party swimming at (-2293, -3207). The question was whether MM9 keeps them at the edge. **It does not**: MM9 sends them
in the same way.

- **The barrier is elsewhere.** All nine Verhoffin zombies are placed `CheckForAIBarrier 1`, but the map's one active
  barrier (`AIBarrier0`, brush x -1600..-640, z -1312..-416 LT) is a diagonal wall from about (-4096, -1065) to
  (-1638, -3359) in our units. The walkway's zombies and that spot of water lie on the same side of it. The converted
  barrier faces (`actor_barriers` 4939-4951) match the brush.
- **The rail logic uses rails only when the direct move is blocked.** `0x100178a0` (`+0x6a4`) first asks
  `+0x49c` (`0x10012690`) whether the way to its destination (`+0x610`) is clear; when it is, the rail path is cleared
  and the monster steers straight at it. A monster on no rail (`+0x69c` returns null) skips the rail logic too.
- **The direct-move test sees walls, not drops.** `0x10012690` casts three horizontal segments (direction with the
  vertical component zeroed) from the monster's centre lowered by half its half-height (`0x100ee5b8` = 0.5 of the dims'
  y), and from the points one radius (`+0x484`) to either side, as far as the destination, through `0x10011a90`
  (IntersectSegment, query flags 1, filter `0x1003d870`). The filter counts an active `AIBarrier`, any solid object
  except AIs and `Actor`s, and the world. A floor ending under the segment is no hit, so a drop is a clear way.
- **Water hides nothing.** `BlueWater` carries `FLAG_RAYHIT` (`0x1000`), but Perceive's line of sight (`0x1000d540`,
  called from the sight test and the hearing test with argument 1) queries with flags 3, which adds IGNORE_NONSOLID,
  and a container is not solid. A monster on the bank sees and hears a party in the water as on land, keeps it as its
  target and steers at it.
- With no working cliff check (section "The rule", item 1) and `CanReachAll 1` on every placed actor, the zombie steps
  off, falls into the water, sinks and walks the bed after the party (MM9_WATER_SWIMMING_RE.md: × 0.5 viscosity).

OpenYAMM does the same (headless, party at the play-test spot: `pursue direct`, the zombie at z -655 in the canal after
12 s). No change was made. Keeping walkers on the bank would be a deliberate departure from MM9 (the water design's
original proposal, "deeper water closed to walkers"), for the user to decide.
