# MM9 actor animation blending and combat AI (reverse engineering)

How Might and Magic IX lets a monster run, strafe or backpedal while it swings or casts. Sources:
the shipped server game code and the shipped AI scripts. Research date 2026-11-02. Rizin 0.10.0 with rz-ghidra on
`mm9/game/data/object.lto` (SHA-256 `b1271f37…7bc37f162`, image base `0x10000000`); the Rizin project is
`re_mm8/work/mm9_collision/object.rzdb`. Decompiled listings and the ABC scan scripts are in
`re_mm8/work/mm9_anim_blend/` (ignored). The scripts are plain text in `mm9/extracted/SCRIPTS/SCRIPTS/`.

## Summary

- **Two animation tracks.** An actor whose model has a `Top` weight set gets a second LithTech `LTAnimTracker`
  bound to `Top`: Spine1 and everything above it, plus both arms. The main tracker keeps the locomotion clip on
  the legs. Attack clips go on the `Top` tracker only, so an attack never stops the legs.
- **The AI moves while it attacks.** The scripts never stop a monster for an attack while its target is moving.
  During the swing a 0.2 s tick keeps calling `RunTo` on the target. After the swing comes a strafe attack, then a
  backpedal or an evade. Speed throttling keeps the monster in step with a moving target.
- **The original designer's description.** The header of `BASEMELEE.inc` (Jeff Leggett, 2001-10-03) says it is
  the "Base script for melee monsters that can blend their animations and therefore be capable of strafe attacks
  along with basic evasive maneuvers". Quadrupeds use `BaseCrawl.inc` instead: "No strafe attacks, No dodging, Just
  run up and attack".

## Models: the `Top` weight set

There are 151 ABC models in the top level of `MODELS/` (props and model props are in subfolders and were not
scanned). 42 of them carry a `Top` weight set; the rest carry no weight sets. Each of the 42 also has a
`none` set (or `None`; two models list it first). The `Top` set gives weight 1 to every node from
`Bip01 Spine1` upward, both clavicle/arm/hand/finger chains, and any weapon nodes (`Xbase`, `Xmid` on the guard).
The pelvis, Spine and legs get 0.

The 42 models with `Top` include GUARD, EVILSORCERER, CLANSOLDIER, DOOKMILITIA, DWARF, LIZARDORC, TROGLODYTE,
SKELETON, SKELETONWARRIOR, TERROR, EVILEYETERROR, LICH, LICHKING, MUMMY, ZOMBIE, GHOUL, NAGATE, EBORA, IMP, WOLF,
BASILISK, BIGFOOT, MONK, STAGE1/2DEMON and others. The full list comes from
`re_mm8/work/mm9_anim_blend/wsscan.py`.

The clips are authored for this. The Guard has `walk`, `run`, `Hattack1`/`Hattack2` (with `lunge` at about
140 ms and `Rattack`, the hit, at about 460–500 ms), `Backpedal`, `BackpedalRun`, `Taunt`, `wince1/2` and
`die1/2`. The Evil Sorcerer has `run`, `rAttack1` (`rangeAttack` key at 833 ms), `hAttack1`, `Backpedal`,
`BackpedalRun` and `ResurrectSpell`.

Our converter keeps the clips but drops weight sets. Our runtime mask is the actors.yml `upper_body_root`
subtree, which matches `Top` when the root is Spine1. `Top` also includes both arm chains and the weapon nodes.
A root of Spine2 leaves out Spine1 and (on some rigs) the clavicles.

## Native animator (`object.lto`)

### Which animator an actor gets

`0x100152f0` calls `ILTModel::FindWeightSet(hObj, "Top")` (model interface `[0x102babe8]+0x270`, slot `+0xc`).

- **Found:** it builds the 0x80-byte blending animator `0x1001edf0` (vtable `0x100efac0`).
- **Not found:** it builds the plain 0x30-byte animator `0x1001e840` (vtable `0x100efa1c`).

The actor keeps the animator at `+0x510`. Its slot `+0x48` (`0x100018c0` in the blending animator) answers the
script stat `CanBlendAnim`.

### Blending animator setup

`0x1001f400`, vtable slot 0, fills these fields:

| Field | Contents |
| --- | --- |
| `+0x30` | The second `LTAnimTracker`, added with `ILTModel::AddTracker` |
| `+0x6c` | The `Top` weight set (−1 when the model has none) |
| `+0x70` | The `None` weight set, used to switch the layer off |
| `+0x74` | The state on the top layer (0x3f means none) |
| `+0x04` | The state on the main tracker |

### Animation states

The state table is `0x1019bad0`. These are the indices the AI uses:

| Id | State | Id | State |
| --- | --- | --- | --- |
| 0 | idle | 0x0c | castSpell |
| 2 | walk | 0x0d | strafe |
| 3 | run | 0x11 | custom |
| 4 | handAttack | 0x18 | swimHandAttack |
| 5 | weaponAttack | 0x20 | flyHandAttack |
| 6 | rangeAttack | 0x24 | flyRangeAttack |
| 7 | die | 0x38 | backpedal |
| 8 | wince | 0x39 | backpedalRun |
| 9 | taunt | | |

The **layered states** (the top-layer list in every switch) are 4, 5, 6, 0x18, 0x20 and 0x24: every hand,
weapon and ranged attack on land, in water and in the air. `castSpell` (0x0c) is not layered, but monster spells
in MM9 play `rAttack*` clips through `rangeAttack`. The Sorcerer's casting is `rAttack1`, so it is layered.

### SetState (`0x1001ee50`, slot 1)

When the model has no `Top` set, SetState falls through to the plain animator (`0x1001ec50`). Otherwise:

- **An attack is requested.** The animator asks the actor whether it is moving (actor vtable `+0x534`).
  - If the actor is still, the main tracker also gets the attack: it plays full-body.
  - Either way the attack goes on the top tracker (slot `+0xa4` → `0x1001f090`). That call picks one clip of the
    state at random, then sets it on tracker `+0x30` with `SetCurAnim`, `SetLooping` and `SetWeightSet(Top)`
    (`0x1001f330`).
- **Locomotion (walk, run, strafe, backpedal) is requested while a top-layer attack is still playing.** Only the
  main tracker changes, and the attack carries on above it. So a monster that starts the swing standing still
  and then chases a target that moved keeps swinging while its legs break into a run.
- **Locomotion is requested with no attack playing.** The top tracker is given the same state as the main
  tracker, so the body plays one clip.
- **Idle is requested while an attack is still playing.** SetState re-enters with the attack, so the legs join
  the attack pose.

### Update (`0x1001f1b0`, slot 5)

Update runs the plain update, then checks the top layer. When the top-layer attack has finished:

- the top tracker goes back to the main tracker's state (or to idle if the main tracker also held the attack);
- then the attack-finished callback runs (slot `+0x2c`).

The top tracker restarts the locomotion clip at time 0. It is not phase-matched to the legs.

### Keyframe commands (`0x1000ed00`)

The handler takes a tracker flag. When the animator can blend, the attack keys (`Attack`, `RAttack`, `LAttack`,
`RangeAttack`, `Lunge`, `Bite`, `DoFX`) appear to be acted on only when that flag is set. So a hit fires once
even when both trackers are playing the attack clip.

### Lunge (`0x10014b40`, the `lunge` key)

- **Blending model:** the key only sets `Lunging` (actor `+0xb98`). The script's speed throttle then raises
  `RunVel` by 1.25× for the rest of the swing.
- **Plain model:** the key gives a one-off velocity impulse toward the target. The impulse is the
  `MONSTERS.txt` `LungeVelocity` (record `+0x64`) × 2 × the key's optional factor. It is skipped for
  rangeAttack, crouchRangeAttack and flyRangeAttack.

## Which script each monster uses

The `MONSTERS.txt` `ScriptName` column decides. Rows by script:

| Script | Rows | Base |
| --- | --- | --- |
| baserange.scr | 64 | baseMelee.inc + range.inc (Type 1) |
| basemelee.scr | 35 | baseMelee.inc |
| basecrawl.scr | 12 | BaseCrawl.inc (no strafe, no evade) |
| guardbase.scr | 3 | Basemelee.scr + guard sounds (Guard, Guard Sergeant, Guard Captain) |
| policeman.scr | 4 | PoliceMan.inc → basemelee.inc (Town Guards) |
| evilsorcerer.scr | 3 | baseMelee.inc + range.inc, forced to Type 2 |
| npcbase.scr | 86 | non-combat |

Most combat monsters therefore use BaseMelee. The table supplies per row `Evade Chance` (40 almost everywhere),
`Strafe Attack Pct` (80 for most fighters, 95 for the Terrors, 20 for Town Guards, 30 for Half-Orcs),
`RunVelocity`, `LungeVelocity`, `AttackRange` and `Recovery`. The scripts read them through `GetStat`.

## BaseMelee combat loop

Files: `BASECRAWL.inc`, `BASEMELEE.inc`, `BASEEVADE.inc`, `SPEEDTHROTTLE.inc`.

1. **Aggressive tick (every 0.2 s).**
   - Target out of range: `RunTo` it, but only if `RecoveryTimeLeft < distance / RunVel`. The monster times its
     run so that it arrives just as it can attack again.
   - Target in range but the attack is not ready: if the monster is within 0.75 × range and the target is still,
     it stops. A moving target is not given up on.
   - In range and ready: `DoAttack`.
2. **`PreAttack`.** The monster faces the target (`FaceObject`, 360°/s) and keeps facing it (`Target …, TRUE`).
   It sets `OnTargetBeyondDist` → `AttackTargetMoved` → `RunTo`. **It does not stop.**
3. **`MeleeAttack`.** `Attack` starts the clip (on the top layer when moving) and an attack tick every 0.2 s:
   - target moving: `RunTo` the target (keeps running during the swing);
   - target still and within attack range: `Stop`.
4. **`PostAttack` (strafe attack).** It runs right after the attack starts. If the monster is still moving and the
   target is not, there is a `StrafeAttackPct` chance of a strafe: the monster runs (`Strafe … run`) at ±45° to the
   target direction while facing the target. Its legs play the strafe/run locomotion and its torso the swing.
   During a strafe attack, the throttle halves `RunVel` until the blow lands (`g_bAttackPerformed`).
5. **`AttackDone`.**
   - **`EvadeChance` roll succeeds → `DoEvade`.**
     - If the target is still or is coming straight at the monster (its velocity within 30° of the line between
       them), the monster backpedals: it runs backwards, aimed directly away from the target ±5–35°, still
       facing the target (`BackpedalRun` clip). This lasts half the evade time, then it switches to strafe ticks.
     - Otherwise it does strafe ticks: a run at ±65° around the target every 0.1–0.4 s.
     - The evade lasts 2 s (the script overwrites the `RecoveryTime` value with 2). It ends early if the target
       gets beyond 500 units. Then the aggressive loop restarts.
   - **No evade, but the attack was a strafe attack:** a 0.3 s backpedal, then a 40 % chance of `Taunt`, then the
     aggressive loop.
   - **Otherwise:** stop if the target is still, then the aggressive loop.
6. **Speed throttle (every 0.1 s while moving).** Within 0.9 × attack range of a target that moves faster than
   20 units/s within 45° of the line to it, the monster runs at 0.95 × the target's speed (never above its own
   `RunVel`), so it stays next to the target. `Lunging` multiplies its own speed by 1.25.
7. **Obstacle rules.** During a strafe attack, bumping into the target makes the monster backpedal at walking
   speed. Bumping into anything else stops it.

Turn-based mode skips the strafe attack and the post-strafe taunt.

## Ranged (`range.inc`) and the Evil Sorcerer

**Type 1** (`baserange.scr`, for example the Oculus, Skeleton Warrior, Lizard-Orcs, Dwarves and Half-Orcs):

- It prefers melee and chases.
- Every 1–2.5 s it tries a ranged attack, if the target is outside melee range and within `RangeAttackRange`.
  The chance depends on what `EstimateRangeAttackHit` says the shot would hit:

  | Shot would hit | Chance |
  | --- | --- |
  | the target | 100 % |
  | nothing | 20 % |
  | some other object | 15 % |
  | another AI or the world | 0 % |

- `PreRangeAttack` stops only if the target is less than 1 s of running away. Otherwise the shot (on the top
  layer) is fired on the run.
- `ShouldRunAfter` holds back the chase when 5 s have passed since the last shot and a clear shot exists.

**Type 2** (`EvilSorcerer.scr` sets it on every Evil Sorcerer row):

- It never chases (`BaseCrawlGetHim`, `TargetMoving`, `TargetStill` and `ShouldRunAfter` are emptied).
- It checks for a shot every 0.2–0.4 s and stops before each shot.
- It keeps the BaseMelee melee, strafe attack and evade. The evade's backpedal/strafe ticks keep restarting
  `Strafe` for 2 s, so a shot taken during an evade plays on the torso while the legs backpedal or strafe-run.
  That is the "running while casting" seen in the Oculus versus Grand Evil Sorcerer fight.
- Hiding places were disabled on 2002-02-18 (`CheckForHidingPlace` exits at once).

## OpenYAMM implementation (2026-11-02)

Before this, OpenYAMM had the upper-body layer but never used it for melee. The renderer could already play an attack
over the gait under the `upper_body_root` mask while the actor moved. But `AI_StartAttack` stopped every attacker and
kept it standing for the whole action, nothing selected a strafe, backpedal or evade, and backing away played the walk
or run reversed.

**The `skirmisher` monster modifier** carries MM9's footwork ([Monster modifiers](../MONSTER_MODIFIERS.md)). It is
opt-in per world through `modifiers.yml`, so MM6–MM8 monsters keep the native stand-and-swing AI.

- **Data.** `assets_dev/worlds/mm9/modifiers.yml` lists it for the 101 MM9 rows whose script builds on
  BaseMelee.inc, with the table's `Strafe Attack Pct` and `Evade Chance`. For the 81 whose actors.yml binding plays a
  `taunt` script clip it also gives `taunt_seconds`, the length of the MM9 model's Taunt clip. The file is generated
  by `tools/mm9_import_discovery/generate_mm9_monster_modifiers.py`; regenerate it rather than editing it.
- **AI** (`GameplayActorAiSystem.cpp`, the `AI_Skirmish*` helpers). It is active in real time only, for a mobile actor
  with a target. The AI now knows the target's horizontal velocity: the party's is estimated each frame from its
  position (`ActorPartyVelocityTracker`), and an actor target's is its own. A target moving slower than 51 units/s
  (MM9's 20) counts as standing.
  - **Approach.** It starts a chase only when its attack will be ready as it arrives (recovery left × run speed ≥ the
    distance beyond its melee reach, MM9's ShouldRunAfter). Otherwise it waits, facing the target. So it usually
    arrives running with its attack ready, which is when a strafe attack can happen.
  - **Strike.** It runs after a moving target until within a quarter of its melee range. A standing target it steps
    after only beyond 3/4 of that range, stopping within half.
  - **Speed during a strike** (MM9's SpeedThrottle). Beyond 0.9 of its reach before the blow lands, it lunges at
    1.25× its run. Nearer, it keeps 0.95× the pace of a target moving away within 45°, never faster than its run.
  - **Strafe attack.** A strike that begins while it was running at a standing target may become a strafe attack:
    45° off the line to the target, at half speed until the blow lands.
  - **Evade.** After the strike comes the evade roll (2 s).
    - A target moving away within 30° is only circled: 65° off the line to it, re-aimed every 0.1–0.4 s.
    - Otherwise it backpedals for the first half, 5–35° off straight back, then circles.
    - It ends early beyond 1280 units.
  - **Back-off.** A strafe attack without an evade backs off for 0.3 s.
  - **Taunt.** With `taunt_chance` (MM9's 40 %) it taunts when it first notices the party and after a back-off. It
    holds still facing the target for `taunt_seconds` while the world runtimes give its model the `taunt` script clip
    (`GameplayRuntimeActorState::scriptedClip`).
  - **Speeds.** Backpedalling runs at walking pace, half the doubled pursuit speed, close to MM9's BackpedalRun.
    Circling, chases and strafe attacks use the pursuit speed.
  - **While evading** it may shoot or cast on the way but does not strike. A shot is also fired on the run when the
    target is more than a second of running away.
  - **Facing.** The actor always faces its target (`keepYawWhileMoving`).
  - **Rolls.** The rolls mix the decision seed through an integer hash (`skirmishUnit`). The shared decision seed's
    low bits barely move when its counter advances by the steady number of steps between two strikes, and the first
    check rolled 0.69–0.82 on five evades in a row.
- **State.** `ActorRuntimeFacts::skirmishPhase/skirmishSeconds/skirmishSide`, carried in both world runtimes. It is
  runtime only and not saved; a loaded game starts without footwork.
- **Collisions.** A bump or a wall now stops an attacking actor's step, not its attack (`buildPostMovementBlock`).
  Before this, attacking actors never moved, so the guard changes nothing for other actors.
- **Rendering** (`WorldFxSystem`). Moving while attacking plays the gait with the attack on the upper-body layer, as
  before. Backing away plays the model's `backpedal` or `backpedal_run` script clip forwards when it has one (most MM9
  humanoids); otherwise the gait plays reversed.
- **Tests.** `tests/GameplayActorAiSystemTests.cpp` (the skirmisher cases) and `tests/MonsterModifierTests.cpp`.

Fixed alongside:

- **MM9 monster speeds.** `generate_mm9_monster_tables.py` now writes half of MM9's fastest velocity as the table
  speed. The shared AI doubles it while pursuing (the MM8 rule), so the chase runs at MM9's RunVel and the walk is
  half of it. A Guard pursued at 1000 (640 doubled, then capped) and now runs at 640.
- **Line of sight on BModel-ground maps.** `OutdoorWorldRuntime::hasClearOutdoorLineOfSight` skipped nothing on MM9's
  BModel-world maps. Their flat placeholder terrain (height 0) lies above floors such as Guberland's at −123, so every
  ray across such a floor read as underground. A Guard approaching the party from the east in Guberland stalled about
  290 units away: within reach by distance but without sight, so it kept "pursuing" and its path steering flipped
  back and forth. The terrain test now runs only when the terrain is the ground (`m_usesBModelGround`, the predicate
  movement and picking already use). Classic ODM maps are unchanged.

Not reproduced:

- **Lunge timing.** The lunge is a fixed window (the wind-up before the blow) rather than MM9's `lunge` keyframe,
  which the converter does not keep.
- **Other taunts.** There is no taunt after killing a target (MM9's KilledTargetTaunt) and no aware taunt for actor
  targets.
- **Mask coverage.** The upper-body mask is still the single `upper_body_root` subtree rather than MM9's `Top`
  weight set (Spine1 and up, both arms and the weapon nodes).

The [animation audit](MM9_ANIMATION_AUDIT.md) (2026-11-04) checks the presentation against this animator arena by arena,
fixes the flicker of an attack's legs, the backpedal choice and the gait choice for MM9 actors, compares every model's
mask with its `Top` set and lists what remains.

## Strafe clips, backpedal fallbacks and fliers attacking in flight (2026-11-06)

These answer two open questions of the [animation audit](MM9_ANIMATION_AUDIT.md) ("Not established"). Same binary
and image base as above. Working files are in `re_mm8/work/mm9_anim_blend/`: `cliplists_1001d7f0.asm` and
`cliplists.py` (the list builder), `plain_setstate.c`, `swimfly*.c`, `strafe_cmd_10018270.c`, `setstate_callers.py`,
and `state_lists.py` with its output `state_lists.txt` (the model survey). "Verified" means read in the code; the
rest is marked as inferred.

### The clip list of each state (verified)

`0x1001d7f0` (plain animator slot 0, also called by the blending animator's setup) runs once per model record
(`+0xad4` flag). Each state owns a 0x2c-byte list at record `+state × 0x2c`: up to 10 animation indices and a count
at `+0x28`. For each prefix, `0x1001d6f0` adds the animation named exactly as the prefix if it exists, otherwise
`<prefix>0` … `<prefix>9`. The lookup is actor slot `+0x48` (`0x100bd420`): a name starting with a digit is an index,
anything else goes to the server's `GetAnimIndex`. Case-insensitive matching is inferred (LithTech), not verified.

| State | Prefix | State | Prefix |
| --- | --- | --- | --- |
| idle 0 | `Stand` | strafe 0x0d | `Strafe` (`0x1019c044`) |
| walk 2 | `Walk` | backpedal 0x38 | `BackPedal` |
| run 3 | `Run` | backpedalRun 0x39 | `BackPedalRun` |
| handAttack 4 | `hAttack` | fly 0x1f | `Flap` |
| weaponAttack 5 | `wAttack` | flyIdle 0x1c | `StandAir` |
| rangeAttack 6 | `rAttack` | flyHandAttack 0x20 | `HAttackAir` |
| castSpell 0x0c | `CastSpell` | flyRangeAttack 0x24 | `rAttack` (the same prefix as on the ground) |

After all prefixes, the builder fills some empty lists from others (`0x1001e126`-`0x1001e575`):

| Empty list | Filled from |
| --- | --- |
| strafe 0x0d (`0x1001e4b4`) | **all `Walk` clips** |
| backpedal 0x38 (`0x1001e266`) | all `Walk` clips |
| backpedalRun 0x39 (`0x1001e2b7`) | all `Run` clips |
| fly 0x1f `Flap` (`0x1001e460`) | all `StandAir` clips |
| flyLanding, flyRetreat, flyLaunching | all `StandAir` clips |
| castSpell 0x0c | the first `hAttack` clip |
| speak 0x12 | the `Stand` clips |
| swimIdle 0x13 | the first `Swim` clip, else the first `Stand` clip |
| climb, climbReverse | `Walk`, then climb |
| taunt 9 | `Aware`, else `Fidget` |

`flyHandAttack` (`HAttackAir`) and the ground attacks have no fallback.

**A state whose list is empty plays nothing new.** The plain SetState (`0x1001d110`) picks no clip, puts the previous
state back (`0x1001d3e1`) and returns false, so the clip that was playing carries on. The top tracker does the same
(`0x1001f090` returns 0 before touching tracker `+0x30`).

### The Strafe command never uses the strafe state (verified)

The script command `Strafe x, y, z, run` (command vtable `0x10181370`, execute `0x1009ae50`) calls actor slot
`+0x4f0`, which is `0x10018270` for every actor class:

1. It sets the strafe flag `+0x740` and stores the direction at `+0x744`.
2. It measures the angle between that direction and the actor's facing (`+0x530`), folded to 0-180°.
3. With `run` it calls Run (`+0x4b4`, `0x10014a70`), otherwise Walk (`+0x4b0`, `0x10014a00`). Speed 0 keeps the
   current speed. The second argument is "forward": the angle is 100° or less.
4. Run plays **run (3)** when forward and **backpedalRun (0x39)** otherwise. Walk plays walk (2) or backpedal (0x38).

The actor update adds one more check (`0x1000e56a`-`0x1000e6d5`). While the strafe flag is set, if the velocity is
more than 100° off the facing, the state is walk or run, and the clip started more than 0.5 s ago, the actor switches
to backpedal or backpedalRun. Nothing in this code switches back to forward.

No code was found that requests state 0x0d. No caller of SetAnimState (`+0x240`, `0x100168a0`) or of the animator
pushes 0x0d. The callers that pass the state in a register belong to other classes or restore a saved state (for
example the NPC at `0x1003d289`). Stop (`0x10012d2b`) only tests for it. That the state is unreachable is inferred
from this search, not proven. The rate code (`0x1000e70f`) would play strafe at rate 1.0, and its think is
`0x10011470`.

So the strafe attack (±45°) and the evade circle (±65°) of `BASEEVADE.inc` and `BASEFLY.inc` (all pass `run` TRUE)
play the **Run** clips, forwards, at speed / `RunVelocity`. The audit's assumption was right for a different reason.
DoEvade's backpedal (aimed away ±5-35°) is more than 100° off the facing, so it plays **BackPedalRun**. A model
without BackPedal or BackPedalRun clips plays its Walk or Run clips forwards (the fallbacks above). MM9 never plays a
clip in reverse.

### Fliers and swimmers get their own animator (verified)

`AISwimFly` overrides the animator factory (`+0x2ec`, `0x1001c480`). Only when both class tests `+0x764` and `+0x768`
are false does it use the walker's factory (`0x100152f0`). Otherwise it always builds a 0x84-byte animator derived
from the blending animator (`0x1001b4c0` → `0x1001edf0`), whether or not the model has `Top`:

- `0x1001b990`, vtable `0x100ef0b0`, when only `+0x768` is set (the AISwimFly default `0x100018c0`, so fliers);
- `0x1001b8e0`, vtable `0x100ef000`, when only `+0x764` is set;
- `0x1001bab0`, vtable `0x100ef160`, when both are set.

Reading `+0x764` as "swims" and `+0x768` as "flies" is inferred from the remaps below.

The difference is slot `+0x54`, which maps the requested state (SetState calls it first). The fly map is
`0x1001b9b0`, skipped while `+0x26c` (`0x1001c870`) reports a grounded fall:

| Requested | Played |
| --- | --- |
| idle 0, fidget 1, aware 0xa, stuck 0xb | flyIdle 0x1c, flyFidget 0x1d, flyAware 0x1e, flyStuck 0x23 |
| walk 2, run 3, strafe 0x0d, backpedal 0x38, backpedalRun 0x39 | **fly 0x1f** (`Flap`, else `StandAir`) |
| handAttack 4 | **flyHandAttack 0x20** (`HAttackAir`) |
| rangeAttack 6 | **flyRangeAttack 0x24** (`rAttack`) |
| die 7, wince 8 | flyDie 0x22, flyWince 0x21 |
| weaponAttack 5, castSpell 0x0c | not remapped |

The swim map (`0x1001b900`) is the same idea with the swim states. Walk, run and strafe become swim 0x16, but
backpedal is not remapped. A flier never backpedals or plays a walk or run: every Strafe or RunTo in the air plays
`Flap`, forwards. The flight clip's rate is a constant 1.0 (`0x1000e744` for state 0x1f), not speed / velocity.

### A flier attacking in flight (verified, except where noted)

`BASEFLY.inc` `BaseFlyAttack` always starts the blow on the move: `AttackStrafe` (±45° with `run` TRUE, so fly 0x1f),
then `Attack`, so handAttack is remapped to flyHandAttack. The flier's SetState is `0x1001b8b0`, which calls the
blending SetState `0x1001ee50`:

- **Model with `Top`** (Banshee, Dragonfly, Evil Eye Terror, Flying Icky, Ghost and Winged Mutant, all with `Top`
  weight 1 on every node):
  - the attack is a layered state;
  - AISwimFly's "am I moving" (`+0x534`) is `0x100c6110`, which always returns true;
  - so the main tracker never takes the attack and keeps `Flap` (or `StandAir`);
  - the `HAttackAir` clip goes on the top tracker with the `Top` weight set (`0x1001f090` → `0x1001f330`).

  Because `Top` covers every node, the whole body plays the attack. That the top tracker fully overrides the main
  one at weight 1 is inferred from LithTech's weight-set semantics. When the attack ends, Update (`0x1001f1b0`)
  gives the top tracker the main state again, so `Flap` restarts there at time 0.
- **Model without `Top`** (Crow, Lobber, Wyvern; `+0x6c` = −1): SetState goes straight to the plain path, and the
  attack replaces the flight clip on the single tracker.

Either way, the attack replaces the whole visible body. The flight clip does not show under it. The flying attack has
its own prefix, `HAttackAir`. A flier's ranged attack uses the ground prefix `rAttack`. A model without `HAttackAir`
clips plays nothing new for its blow, and its flight clip carries on.

### Model survey (151 top-level `MODELS/*.abc`, `state_lists.py`)

| Clip family | Models |
| --- | --- |
| `Strafe` or `Strafe<n>` | 0 |
| `Walk`, `Run` | 66, 59 |
| `BackPedal`, `BackPedalRun` | 31, 30 |
| `Flap` | 7 (Dragonfly, Ebora, Evil Eye Terror, Flying Icky, Ghost, Winged Mutant, Wyvern) |
| `HAttackAir` | 8 (Banshee, Crow, and the flier list above less Ebora) |

Models that run but have no BackPedalRun: 29. They include the Dwarf, Giant, Nagate, Basilisk, Dagrell, Thrall,
Yanmir and Nobleman, the farm animals and most peasant bodies. MM9 plays their Run forwards when they back away.

Some shipped models leave a flight list empty:

- The Banshee has no `Flap`, so it flies on `standAir`; its `Fly` and `WalkAir` clips match no prefix.
- The Banshee's `RattackAir*` clips do not match `rAttack`.
- The Crow has only `fly`, so its flyIdle and fly lists are empty.

How those monsters animate in the shipped game (scripts, class overrides) was not traced.

### Against OpenYAMM (`WorldFxSystem::syncActorModels`, `assets_dev/worlds/mm9/models/actors.yml`)

- **Strafe attacks and circling** play the gait forwards, facing the target: the same as MM9. No binding has or needs
  a strafe clip.
- **Backpedal** plays the backpedal clip during the AI's backpedal phase. MM9 chooses it by angle (more than 100° off
  the facing), and DoEvade's backpedal always passes that test, so the two agree in practice.
- **Backpedal without a backpedal clip** differs. Ours plays the gait in reverse (`reversed`, `WorldFxSystem.cpp`
  near "A model's own backpedal clip plays forwards"). MM9 plays the walk or run forwards, and a flier its `Flap`.
  The audit's three reversed-gait lines are the Oculus (`EVILEYETERROR.abc`, a flier) beating its wings backwards.
- **Fliers attacking.** The P2 masks (`Scene Root` for the whole-body `Top` fliers, no layer for those without
  `Top`) give the same whole-body attack over the moving flight. This matches MM9 and needs no change.
