# MM9 monster AI: what the native engine does

Reverse-engineering notes on the monster AI built into Might and Magic IX's server game code
(`mm9/game/data/object.lto`), and on how it splits the work with the base scripts (`SCRIPTS/*.inc`, `*.scr`). The
goal is a native base AI for OpenYAMM that behaves like MM9's.

- Binary: `object.lto`, SHA-256 prefix `b1271f37e5314281`, image base `0x10000000`. All addresses are virtual
  addresses in this file. Key addresses were checked with Rizin; most of the reading used the existing disassembly
  `re_mm8/work/mm9_collision/object_lto.asm`.
- Working files and scripts: `re_mm8/work/mm9_ai/` (listed at the end).
- Related notes: [water and swimming §6](../MM9_WATER_SWIMMING_RE.md), [collision](../MM9_MONSTER_COLLISION_RE.md),
  [jump, cliffs and rails](../MM9_MONSTER_JUMP_RE.md), and
  [animation blending and the BaseMelee loop](../MM9_ACTOR_ANIMATION_BLENDING_RE.md).
- Units: LithTech units (LT). The update interval and all script timers are in seconds. The RPG layer's recovery
  and spell effects count game seconds, each 33 ms of real time (§7.2.1).

## 1. Summary

1. **The combat decisions live in the scripts.** Choosing to chase, attack, strafe, evade, back off, swoop, flee,
   give up on a target, call for help or resurrect is the job of the base scripts (`BaseCrawl.inc`, `BaseMelee.inc`,
   `Range.inc`, `BaseFly.inc`, `BaseSwim.inc`, `BaseRun.inc`, `BaseWander.inc`, `AICommon.inc`). The scripts run on
   timers (`Wait`) and on events that the native code raises.
2. **The native code supplies perception, targeting, movement, attacks and the RPG layer.** It handles sight and
   hearing, the search for the nearest target, keeping track of a target and losing it, attack range and readiness
   (recovery), carrying out an attack (animation state, melee hit sweep, projectile launch), damage and wince,
   push-back, rail navigation, obstacle and arrival events, the per-monster facts behind running away and evading,
   alert and help broadcasts, friend and enemy relations, and auto-deactivation.
3. **There are few native AI classes.** `object.lto` registers 289 actor classes, but almost all of them are the
   C++ class `AIBase` (or `NPC` or `AISwimFly`) created with a different **class id**. The class id is the
   `MONSTERS.txt` row number, so it selects the monster record. Only about 25 classes override any virtual method.
   Flying and swimming come from the C++ class `AISwimFly`; the `Fly` and `Move` columns are never read.
4. **Several `MONSTERS.txt` columns have no native effect.** The native code never reads `Target Pref`, `Fly`,
   `Move`, `ConcatAttk`, `Hostility Group`, `Special` or `SpellUse%2`. `WinceThreshold` and `WinceTrackTime` are
   loaded, but no code that reads them was found. A monster targets the **nearest** non-friend it can perceive.
5. **Update rate.** Every actor updates every **0.1 s** (10 Hz). Its script ticks inside the same update, so `Wait`
   timers resolve to 0.1 s. A monster without a target looks for one at most **once per second**, and only if its
   script has registered `OnFoundTarget` or `OnFoundPlayer`. 2,100 of the 2,217 placed actors have
   `AutoDeactivate 1`, so the engine stops updating them when no client is near (see §13).

## 2. Class hierarchy

### 2.1 How classes are built

`classdef.py` (prior work, `re_mm8/work/mm9_water/`) lists the ClassDefs. The class list with sizes is in
`actor_classes.txt`. `class_ids.py` follows each ClassDef's construct function (ClassDef `+0xc`). The construct
function pushes a **class id** and calls one of these C++ constructors:

| C++ constructor | C++ class | Object size | Base vtable | Used by |
| --- | --- | --- | --- | --- |
| `0x1000c0c0` | `AIBase` | `0xbac` (+8 for gibbers and the Dragon King) | `0x100ee768` (452 slots) | 155 classes (including `AIBase`): every walker, `AIGibber` and its children, `DragonKing`, animals |
| `0x1001bca0` | `AISwimFly` (derives from `AIBase`) | `0xbcc`–`0xbd8` | `0x100ef210` | 33 classes: flyers and swimmers |
| `0x10029ff0` | `Lobber` (derives from `AISwimFly`) | `0xbe4` | `0x10117570` | `Lobber`, `IceLobber` |
| `0x1003cd00` | `NPC` (derives from `AIBase`) | `0xbc0` | `0x1016e3ac` | `NPC` and 93 town NPC classes |
| `0x1003c960` | `NOEFly` (derives from `AIBase`) | `0xbac` | `0x1016dc9c` | `NOEFly`, `Concubine`, `SuccEbora` |
| `0x100c2780` | `Player` (derives from `Actor`) | `0x628` | `0x1018362c` | the party |

The `AIBase` constructor (`0x1000c0c0`) looks up the monster record with the class id (`0x10040ce0`, record table at
`[0x102babb8]`, stride `0x1b8`) and keeps it at `+0xb54`. It then creates the monster's **character sheet** at
`+0xb58`, a 0x2dc-byte RPG object (vtable `0x100ee69c`, base constructor `0x10052930`, initialised from the record by
`0x10052b00`) that holds hit points, conditions, damage, resistances and the recovery timer. **The class id is the
`MONSTERS.txt` `Number` column.** Examples: `Wolf` and `GreyWolf` 0x72 → row 114, Grey Wolf; `Shadow` 0x8a → row 138,
Shadow; `DragonKing` 0xd4 → row 212.

Each class has its own vtable, but most are identical to their parent apart from the destructor. `vt_diff.py`
compares every class's vtable with its parent's within the 452 `AIBase` slots (`vt_real_overrides.txt`):

| Class (children) | Overridden slots | What is native about it |
| --- | --- | --- |
| `AIBase` (Wolf, Horde, Trellborg, Lich, Vampire, Ghoul, Zombie, Mummy, Thrall, Imp, Basilisk, giants, guards, named bosses, …) | — | The whole base AI described below |
| `AIGibber` (Skeleton, Dagrell, Nagate, Cat, LobberPod) | 7: `+0x5c`, Update `+0x188`, `+0x218`, `+0x21c`, Die `+0x24c`, `+0x2f4`, `+0x350` | Bursts into gibs on death (`IsGibber`); gibbers are never removed while they wait to be resurrected (`AICommon.inc`) |
| `Dagrell` | `+0x190`, Jump `+0x4bc`, in-air steering `+0x670` | A real leap (see the jump note); its scripts never use it |
| `SkullThrower` | `+0x17c`, `+0x698` | Its own setup and target search |
| `LobberPod` | 12, including ShouldRunAway `+0x52c` → always false, `+0x538`, `+0x540` | Stationary pod |
| `AISwimFly` (flyers and swimmers) | 28 | Update `0x1001cba0` (base update, then faces its velocity above 10 LT/s); CanReachTarget `+0x478` → always true; can only target things in water when it is in water (`+0x374` → `0x1001c950`); `Walk`/`Run` become fly or swim; its own melee range, CanAttack, attack think, Launch (`+0x3c8`), wing `Flap` sounds; `FlyerUsesRails` property → `UsesRails` |
| `Banshee` (Terror, Dread, Fright) | 6 | Never counts as in water (`+0x328` → false); own update and touch handling |
| `DragonFly`, `JellySpore` | 7 | Gibber death on a flyer |
| `EvilEyeTerror`, `FlyingIcky`, `WingedMutant`, `Ghost`, `Fish` | 1–5 | Small overrides: not in water, Ghost visibility, Fish state handling |
| `Lobber` | 7 | Model keys and flying state |
| `DragonKing` | 20, including Update, sight `+0x404`, FindTargets `+0x4e0`, the `RangeAttack` key `+0x594`, target search `+0x698` | The dragon's own perception and breath attack (`DragonWinceDone`) |
| `GiantBase` (Forest Giant, Plain Giant, Yanmir) | 7–8: touch `+0x190`, model keys `+0x198`, RangeAttack `+0x48c`, `+0x4c0`, `+0x4c4`, `+0x708` | Thrown rocks |
| `DesertTerror` (Amphibious, Reptilian) | 3 | Touch and range overrides |
| `EvilSorcerer` | melee hit sweep `+0x6b8` | Its own hit test |
| `Zombie`, `Monk`, `Basilisk`, `MagreebBaby`, `PhantomFighter`, `RailTest` | 1–2 | Range animation choice, gaze and similar small details |
| `NPC` (93 town classes) | 11: CanTarget `+0x374` (targets are other NPCs), FindTargets `+0x4e0` (sight only), MoveTo `+0x644`, `+0x47c`, … | Peaceful townsfolk who find each other to talk |
| `Animal`, `Cat`, `Dog` | `+0x17c`, `+0x37c`; Cat and Dog also `+0x374` and `+0x4e0` | Farm animals; cats and dogs target NPCs |
| `NOEFly` | `+0x4cc` (MoveToPos) | Its own move-to |
| Others (ClanSoldier, HalfOrc, Horde, Honk, GreaterDemon, …) | `+0x17c` only | Class-specific setup (scale, attachments); no AI difference |

The other ~250 classes have no override at all: their behaviour comes from the record and the script.

### 2.2 Which monsters use which class

Cross-tab of the `MONSTERS.txt` rows (via the class id) against the native class and the `ScriptName` column:

| Native class | `Fly` column | Scripts (rows) |
| --- | --- | --- |
| `AIBase` | 0 (1 for the Dragon King) | baserange 57, basemelee 28, basecrawl 12, crawlrange 4, magreeb 4, policeman 4, guardbase 3, monkbase 3, evilsorcerer 3, lobberpod 3, titan 2, animals 8, demons 2, yanmirbase, princess, dragon |
| `AISwimFly` | 1 for 21 rows, **0 for 8** (Terrors, sea monsters, Fish, Lobbers) | flyrange 6, basefly 3, baserange 3, baseswim 5, flyingicky 3, ghost 3, banshee 3, fish 1, lobber 2 |
| `NPC` | 0 | npcbase 85, basemelee 7 (armed townsfolk), greenman |
| `NOEFly` | 0 | baserange 2 |

So the `Fly` column does not decide whether a monster flies: the Terrors and the swimmers are `AISwimFly` with
`Fly 0`, and the Dragon King flies as a plain `AIBase` with `Fly 1`. A placed object can name its own script
(`ScriptName` property: `ChessSquare.scr` 64, `MummyAwaken.scr` 39, `shopkeeper.scr` 38, `AutoResurrect.Scr` 26, …);
otherwise the record's `ScriptName` is used. The setup code is `0x1000cf40`–`0x1000d006`; which one wins when both
are set was not fully traced.

## 3. The monster record (`MONSTERS.txt`) as the native code sees it

The loader (`0x10042e00`–`0x10044674`) reads columns by spreadsheet letter (`0x10056d40`). Record offset = loader
offset − `0x4f8`. `monster_record.py` → `monster_record_columns.txt`.

| Column | Record | Native use |
| --- | --- | --- |
| Q WalkVelocity, R RunVelocity, S FlyVelocity | `+0x8`, `+0xc`, `+0x68` (swim speed `+0x14`) | Movement speeds (the `WalkVel`, `RunVel`, `FlyVel` stats); walk/run animation rate = speed / velocity (`0x1000e726`) |
| T LungeVelocity | `+0x64` | `Lunge` key impulse (see the animation note) |
| U AttackReach | `+0x3c` | **AI attack range** (the `AttackRange` stat), §7.1 |
| V AttackRange | `+0x40` | **Melee hit sweep length** × scale, §7.3. The two names are the reverse of what they do. |
| W Recovery | `+0x144` → character `+0x2a4` | Recovery after each attack, in game seconds of 33 ms real time (30 → 0.99 s), from the end of the attack clip (§7.2.1). The scripts' `RecoveryTime` stat reads value × 0.1 (30 → 3.0), 3 times the real length |
| Z AlertRadius | `+0x6c` | `SendAlert` radius × scale (1200 for 261 rows, 1600 for 9) |
| AS Always Wince? | `+0x75` (byte) | 1 → wince chance 0 (§8). 162 rows have 1, including all commoners. |
| AT WinceThreshold, AU WinceTrackTime | `+0x28`, `+0x24` | Loaded; **no reader found** |
| BH Evade Chance | `+0x148` | `EvadeChance` stat, adjusted for threat (§9.3); 40 on every row |
| BI Strafe Attack Pct | `+0x150` | `StrafeAttackPct` stat, read only by scripts |
| BJ IsMonster | `+0x14c` | `IsMonster` stat |
| BV Resurrect | `+0x1a4` | `IsResurrecter` (this monster can resurrect others) |
| AO SpellUse%1, AP Spl/Mas/Skil1, AR Spl/Mas/Skil2 | `+0x160`, `+0x164`… | Spell choice in the RPG layer: `SpellUse%1` splits two spells; `concat` parses as 0 (§7.2.2) |
| AB/AI/BQ Type, AD/AE/AF and the other dice columns, AG Projectile1 | `+0x154`…, `+0x9c`…, `+0x78` | Damage and projectile (RPG layer) |
| BG Scale | `+0x84` | Model scale (collision note) |
| BA ScriptName | `+0x44` | Default script |
| **Not read:** `Fly`, `Move`, `Target Pref`, `Att%` (2nd/3rd), `SpellUse%2`, `Special`, `ConcatAttk`, `Bonus` (loaded to `+0x2d4`, never read; §7.2.2), `Hostility Group`, `Quest`, `Type/Picture`, `Damage1/2/3` text | — | No native effect. `Hostility Group` is replaced by the class relations and script hostility includes (§10). |

`cshell.dll` (the client) also loads `data\monsters.txt`, for presentation; it plays no part in the server AI.

## 4. The per-update loop

### 4.1 Rate and entry

- The Actor constructor calls `SetNextUpdate(0.1)` (`0x1000175e`/`0x100017a4`; wrapper `0x100bd860`, minimum
  0.01 s). Each update re-arms the same interval (`ObjectBase::Update` `0x100bc860` → `0x100bd860([+0x10])`). No AI
  code changes it; it only drops to 0 (no more updates) when the object is removed (`0x1000e8f8`).
- `EngineMessageFn` `0x100bcad0` routes `MID_UPDATE` (2) to vtable `+0x188`: `AIBase::Update` **`0x1000e2e0`**
  (`AISwimFly` `0x1001cba0`, and the gibber, dragon, Banshee and DragonFly overrides). `MID_TOUCHNOTIFY` goes to
  `+0x190` (`0x10012b30`), `MID_MODELSTRINGKEY` to `+0x198` (`0x1000ed00`, the attack keys), `MID_LINKBROKEN` to
  `+0x194`. Script-to-object messages (alerts, help) arrive through the object message handler (`0x100bd7dc` →
  `+0x1c4`).

### 4.2 What one update does (`0x1000e2e0`)

1. Removed (`+0xb50`) or vtable `+0x158` → stop updating.
2. Character-sheet tick: `character->Update(gameTime)` (`[+0xb58]` vtable `+0x4`). It clears the recovery flag when
   its time has passed (`0x1004abd6`) and ticks condition timers. If the character reports death (condition 2) →
   `Die`.
3. Dying, dead or removed → the dying path (`+0x6f8`, `+0x6f0`), then return.
4. A global AI switch at `0x1019b38c` (1 in the shipped data, no writers) → otherwise the AI is skipped.
5. The animator update. It runs the **per-state think** of the current animation state through the dispatcher at
   `0x1001e870` (table `0x1001ea10`/`0x1001e9c4`):

   | State (enum `0x1019bad0`) | Think slot | Function | Purpose |
   | --- | --- | --- | --- |
   | idle 0 | `+0x5cc` | `0x10013060` | Has a target → track it (`+0x5b8`). Otherwise: fidget timer up → fidget (idle lasts 5 + rand × 7 s, `0x100168a0`), else look for a target (`+0x658`) |
   | walk 2, run 3, backpedal 56/57, fly 31 | `+0x5c0`, `+0x5c4` | `0x100113f0` | Navigation tick (`+0x5bc`, rails), track target, per-tick movement (`+0x62c`), and with no target, look for one |
   | strafe 13, wince 8 | `+0x5c8`, `+0x5dc` | `0x10011470` | Track target without turning |
   | taunt 9, aware 10, stuck 11 | `+0x5d8`, `+0x5e0`, `+0x5f4` | `0x100130b0` | Track target |
   | handAttack 4 | `+0x5e4` | `0x10013110` | Keep facing; small steps |
   | weapon, range, spell attacks 5, 6, 12 | `+0x5e8`…`+0x5f0` | `0x10013100` | Track and face the target |
   | speak 18 | `+0x5fc` | `0x10015870` | Conversation |

6. Push-back velocity (`+0x5c0`) is applied while it lasts (`+0x678` → `0x100153f0`).
7. `OnTargetWithinDist` and `OnTargetBeyondDist` are checked every update (`+0x688` → `0x10016970`): one-shot events
   0x12 and 0x11 at the distances set by the script (`+0x734`, `+0x730`).
8. Projectile awareness (`+0x6ac` → `0x10017e80`): if the script registered `OnProjectile <radius>`, the actor
   manager (`0x101abf38`, `0x10007ce0`) lists the projectiles within the radius and raises event 0x16 for each one.
9. Turn-in-place animation (states 0x38/0x39) when the facing changes quickly; walk/run animation rate.
10. `Actor::Update` tail (`0x10002220`): footsteps and ambient work every 0.2 s (`0x100ee5bc`). Then the
    **script tick**: `+0x78` (`0x1000e990`) → `0x100bf4c0` → script context vtable slot 0 → `0x1009e290`. It
    advances 31 `Wait` timers (`+0x60`…`+0x158`) and fires the label of each timer that has expired. A `Wait` can
    therefore fire no sooner than the next update: `AGGRESSIVE_TICK 0.2` fires every second update and
    `ATTACK_TICK 0.01` on the next one.

### 4.3 Events the native code raises for the script

`AIBase::FireEvent` is vtable `+0x154` (`0x10018380`). It forwards to the script (`0x100c0a10` → `0x1009dc20`),
except that a dead actor only raises events 7 and 8. Event ids (`event_ids.txt`, `fire_event_sites.txt`):

| Id | Script hook | Raised by |
| --- | --- | --- |
| 0 | `OnFoundTarget [maxDist]` | Target search, `0x10012e70` |
| 1 | `OnFoundPlayer` | Player search, `0x10012fe0` |
| 2 / 3 | `OnDamage` / `OnDamageDone` | Damage `0x100c0350` / the end of a wince `0x1000e023`, or straight away when there is no wince `0x10015785` |
| 5 / 6 | `OnStuck` / `OnStuckDone` | Navigation `0x10012cf1` / `0x10011145` |
| 7 / 8 | `OnDeath` / `OnDeathDone` | `0x1000eb6b` / `0x1000ec2a` |
| 9 | `OnLostTarget` | Target tracking, `0x100130d0` |
| 0xa / 0xc | `OnTargetOutOfRange` / `OnAttackReady` | Target tracking, `0x10013760` / `0x10013750` |
| 0xb | `OnTargetDead` | `0x1000f9cb` |
| 0xe / 0xf | `OnAlert` / `OnHelp` | Receiving an alert `0x10015190` / help `0x1001a130` |
| 0x11 / 0x12 | `OnTargetBeyondDist` / `OnTargetWithinDist` | `0x10016970` |
| 0x14, 0x28, 0x29, 0x2a | `OnObstacleAvoided`, `OnObstacle`, `OnCongestion`, `OnPathClear` | Movement `0x100110a8`, `0x10014554`, `0x10014566` |
| 0x16 | `OnProjectile <radius>` | `0x10017e58` |
| 0x17 | `OnTargetHit` | `0x10019c30` |
| 0x19 | `OnDoor` | `0x1001a496` |
| 0x1a–0x1d | `OnFear`, `OnFearDone`, `OnEnrage`, `OnEnrageDone` | Condition changes, `0x1001a57c`… |
| 0x1e | Callback of `RunTo`/`WalkTo` (arrived) | `0x10012cb0` |
| 0x1f | Callback of `Attack`/`RangeAttack`/`CastSpell` (action finished) | `0x1001334b`, `0x100133ba`, `0x1001343b` |
| 0x20 / 0x22 | Callback of `Taunt` / `Aware` | Animation end |
| 0x44+ | `Wait` timer labels | Script tick |

A command's callback label is stored in the handler table at script context `+0x920` + id × 4 + `0x158`
(`0x1009dcf0`).

## 5. Perception

Re-decoded on 2026-11-04 (hash checked), with OpenYAMM's rule and measurements alongside.

### 5.1 MM9's detection rule

**Who searches, and how often.**

- The idle think (`+0x5cc` → `0x10013060`), the fidget think (`+0x5d0` → `0x1001c7e0`) and the walk, run and fly
  thinks (`+0x5c0`/`+0x5c4` → `0x100113f0`) call `LookForTarget` (`+0x658` → `0x10012e00`) whenever the monster has
  no target. Other states (taunt, wince, strafe, the attacks) do not search.
- `LookForTarget` first runs the player search (`+0x6d8` → `0x10012f80`). That search runs only if the script
  registered `OnFoundPlayer`: a few special scripts do, the base scripts do not.
- Then, if the script registered `OnFoundTarget` (`+0x67c` → `0x10012de0`; every base script's `InitCallbacks` does),
  it runs the target search (`+0x698` → `0x10012d80` → `FindTargets` `0x10006be0`). The party is found there.
- Each search runs **at most once per 1.0 s** (`+0x4d0` → `0x1000c8f0` returns 1.0; last-search times `+0x5a8`,
  `+0x5ac`), and only while the engine updates the monster (§13: `AutoDeactivate`).
- `FindTargets` keeps up to 50 candidates and `0x10006120` takes the **nearest**. A candidate must:
  - be alive and active;
  - pass `CanTarget`;
  - pass `Perceive(obj, 0, hearing allowed)` (`+0x404` → `0x1000d890`);
  - lie within the script's optional `OnFoundTarget` distance.

**`Perceive` (`0x1000d890`):**

1. `SightDistance` (`+0x5a0`) ≤ 0 → never (`0x1000d897`-`0x1000d8a8`). Hearing alone does not help.
2. The object must carry engine flag `0x1000` (`FLAG_RAYHIT`: it can be hit by rays), tested through `GetObjectFlags`
   (`ILTServer +0x148`).
3. **Hearing** (`+0x414` → `0x1000db70`). The distance from the monster's **centre** (`0x100bcd10`) to the object's
   centre must be below `HearingDistance` (`+0x5a4`), and the line-of-sight test (step 6) must pass. If both hold,
   the object is perceived.
   - The line-of-sight test checks `SightDistance` again, so hearing never reaches beyond sight.
   - Hearing has **no** factor for movement, running, fighting, casting or noise: it is distance and a clear ray
     only.
4. **Sight distance.** The distance from the **eye** (`+0x29c` → `0x10003280`: centre + half height − 2 LT, constant
   `0x100ee5d0`) to the object's centre must be ≤ `SightDistance`.
5. **Field of view.** The dot product of the eye-to-object direction with the **body's** forward vector `+0x570` must
   be > 0: a 180° half-space.
   - `+0x570` is the forward vector from the object's rotation, refreshed every update by `GetRotationVectors`
     (`0x1000e4fc`-`0x1000e515`). There is no head yaw.
   - The vector is rotated by `+0x57c` only when the caller asks for it or a class's `+0x430` says so. `FindTargets`
     passes 0, and AIBase's `+0x430` is `0x100d9f40` (false).
6. **Line of sight** (`+0xac` → `0x1000d540`).
   - The eye-to-object-centre distance must be ≤ `SightDistance`.
   - Then `IntersectSegment` from the eye to the object's centre (`ILTServer +0x9c`) with filter `0x1000d6b0`: the
     target always counts, other AIs never block, and the world and other objects do.
   - The test succeeds only if the **first hit is the target itself**.

**Units and defaults.** LT units (× 2.56 in OpenYAMM). The constructor's defaults are `SightDistance` 1320 and
`HearingDistance` 360; the scripts double both the first time the monster targets the player (`BaseCrawl.inc:700-708`).
Sight is measured from the eye and hearing from the centre, both to the target's **centre**, never to its edge.

**What else turns a monster on the party.** None of these come from the party being seen or heard:

- damage (`OnDamage` → `NewTargetCheck`);
- a projectile passing within 200 LT (`OnProjectile 200`);
- alerts: `SetupTarget` → `AlertStart`, to friends within scale × `AlertRadius`, at once and then every few seconds
  (§10);
- help calls from fleeing friends (§9).

Nothing wakes a monster because an ally is hurt or makes noise nearby; only the alert and help messages carry news.

**There is no rendering-based activation in `object.lto`.** The engine's `AutoDeactivate` (§13) stops updating far
monsters, which makes them notice *less*, not more.

**Nothing in the binary makes MM9 notice more readily than this.** There are no awareness or noise levels, no
widening view cone and no light factor. The one generous point is that other actors never block the ray. In practice
MM9 also has wanderers that walk into view, alerts that spread news, and monsters that face where they were placed.

### 5.2 OpenYAMM's rule (2026-11-04)

- **Rule** (`mm9Perceives`, `game/gameplay/Mm9ActorRules.cpp:212`):
  - a clear line is required for both senses;
  - hearing: distance ≤ `hearing` (× 2 after contact), with no sight bound;
  - sight: in front (`cos(yaw)·dx + sin(yaw)·dy > 0`) and distance ≤ `sight` (× 2).
- **Indoor** (`IndoorWorldRuntime.cpp:11180-11199`):
  - The distance runs from the actor at 0.75 × height to the party at z + 96.
  - The line is `hasCombatLineOfSightToParty`: a portal trace plus combat faces, from the same points.
  - The rule is evaluated on every AI step, for **active** actors only.
  - An actor is active (`5380-5575`, at most 48) when it has detected the party before, or the OE selection pass
    sees the party (within 5 120, a line from 0.9 × height to the party's eye or target point, staggered every 16
    steps, the nearest 30), or it is in the party's sector, or it is an MM9 wanderer.
- **Outdoor** (`OutdoorWorldRuntime.cpp:10136-10160`; `resolveOutdoorTargetFacts`, `4091`):
  - The party is a candidate only within the world's `partyEngagementRange`. MM9's `world.yml` sets it to **4 096**
    (1 600 LT).
  - The line runs from 0.7 × height to the party at z + 96, cached for 0.125 s.
  - Active actors are those within 5 632, at most 48.
  - The placement is read only for map actors (`!actor.spawnedAtRuntime`): runtime spawns use the defaults.
- **Defaults:** `sight` 3 379 and `hearing` 922 (1 320 and 360 LT), the same as MM9.

### 5.3 Measurements

**Arena (The Arena, a flat open pit).** One idle Skeletoid (9183), faced 90°. For each case the party is placed
along a bearing at distance d (centre to centre, OpenYAMM units), 4 s per case, headless. The cell shows the time of
the first `detect`/`taunt_detect`; "–" means none in 4 s.

| Bearing from facing | 300 | 600 | 900 | 1 200 | 1 600 | 2 000 | 2 400 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Default (3 379 / 922): 0°, 45°, 90° | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| Default: 135°, 180° | 0.01 | 0.01 | 0.01 | – | – | – | – |
| 600 LT placement (1 536 / 369): 0°, 45°, 90° | 0.01 | 0.01 | 0.01 | 0.01 | – | – | – |
| 600 LT placement: 135°, 180° | 0.01 | – | – | – | – | – | – |
| Behind the entry gate (no line), 300-900, both placements | – | – | – | | | | |

Notes on the table:

- The arena results follow the rule exactly: the full 180° front within sight, all round within hearing, and the 90°
  boundary counts as front through float rounding.
- Detection is immediate, because the rule is evaluated every step, against MM9's ≤ 1 s search.
- An outdoor arena (Guberland, party start) shows the same rule. A spawned Skeletoid sees the party at 3 300 and not
  at 3 600 even when given `sight: 4608`, because outdoor runtime spawns ignore `mm9_ai`.

**Real maps** (`clear_actors: false`, party placed by script). In Ruined Temple the party stands 700 units from the
Skeleton (actor 0, placement yaw 1 130 units ≈ 199°) along its placement facing.

- A screenshot shows it in plain view, beyond its 369 hearing and within its 1 536 sight. **It never notices the
  party.**
- The model visibly faces +X, away from the party. The same holds for actors 1, 9 and 11 and for Lich Lab and
  Drangheim Prison actors at 400-700.
- Within hearing (150-300) they all notice.
- The cause is in §5.4, item 1. Regression: `tests/scenarios/mm9/ai/perception_placed_yaw.yml`, which fails today.

**Placements** (review root `output/mm9_rework/assets_dev`, 48 maps, 2 027 placed MM9 actors):

- 1 550 carry `mm9_ai`. **11 maps have none** and fall back to the defaults: bootcamp, bootcamp_authored, drangheim,
  guberland, isleofashes, lindisfarne, mountainpass, sturmford, thjorgard, thjorgard_authored and yorwick. These are
  the outdoor maps, still in the old YAML scene format, which also lack wander paths, hostility and dormant data.
- Darkpassageway, tasaracademy and thronheimcity miss one actor each.
- `sight` (ours): 1 536 × 637 (600 LT), 3 379 × 246, 4 608 × 195, 3 072 × 112, 2 560 × 86, 2 621 × 58, 6 144 × 40, …
- `hearing`: 369 × 603 (144 LT), 922 × 455, 3 072 × 112, 655 × 87, 2 560 × 84, …
- None has `sight` 0 or `hearing` > `sight`.
- 299 have `sight` > 4 096, and 869 have doubled `sight` > 4 096.

### 5.4 Mismatches, ranked

1. **Indoor map actors start at yaw 0, not their placement yaw.**
   - `buildIndoorMapActorAiState` never sets `yawRadians` from `initialYawUnits`; the outdoor runtime does
     (`OutdoorWorldRuntime.cpp:2978`).
   - The MM9 idle loop (`AI_Mm9IdleStand`) never turns to `homeYawRadians`, unlike the MM6-MM8 idle
     (`GameplayActorAiSystem.cpp:8032-8037`).
   - So every non-wandering indoor MM9 monster looks along +X and sees the wrong half of its room. Party in front
     of the placement → unseen beyond hearing; party behind → seen. This matches the user's report.
   - **Fix:** initialise the indoor runtime yaw from `initialYawUnits` as the outdoor runtime does. That is shared
     indoor world code with no world check, and it also fixes the models' facing.
   - **Done (2026-11-04, section 5.5).** MM9 never turns an idle monster back to its placement facing (no base script
     faces its start; only markers with `UseMarkerRotation` and attacks turn it), so `AI_Mm9IdleStand` stays as it is.
2. **The outdoor maps have no `mm9_ai`.**
   - All 11 still use the old scene format: default sight and hearing (often wrong both ways), no wander (fewer
     monsters walk into view) and no hostility or dormancy.
   - **Fix:** reconvert them with the transcoder's `placement_ai` (`transcode_mm9_dat_to_odm.py:4569`), the same data
     path as the BLV maps.
   - **Open:** the map generation session gives them `mm9_ai` at their next conversion (no reconversion here).
3. **The outdoor engagement cap.**
   - MM9's `world.yml` `actorAwareness.partyEngagementRange: 4096` stops every outdoor actor from considering the
     party beyond 4 096 (1 600 LT).
   - That cuts 299 placements' own sight (4 608, 6 144) and 869 doubled sights.
   - **Fix:** raise MM9's `partyEngagementRange` to at least the largest doubled sight (12 288, or the engine
     maximum 10 240), or let an `mm9_ai` placement's own range bound the candidate. Data in the world manifest, no
     code branch.
   - **Done (section 5.5):** the placement's own range raises the limit for that actor.
4. **Indoor activation range.**
   - A non-wandering actor outside the party's sector is only evaluated once the OE pass sees the party within 5 120,
     staggered by 16 steps and limited to the nearest 30 and 48 actors.
   - Placements with sight 6 144, and doubled sights above 5 120, are cut. Dense maps (Chasm of the Dead 171 actors,
     Lich Lab 147, 1000 Terrors 114) can starve farther ones.
   - **Fix:** let the activation range follow the actor's perception range: max(5 120, sight × 2 when it has
     contact).
   - **Done (section 5.5).**
5. **Outdoor runtime spawns ignore `mm9_ai`** (`!actor.spawnedAtRuntime`). Spawned and summoned monsters use the
   defaults. **Fix:** carry the spawn request's placement (arena, summoner or death spawn) into the actor's outdoor
   state, as the indoor runtime does for arena spawns. **Done (section 5.5).**
6. **The line's end points.**
   - MM9 casts from the eye (top − 2 LT) to the target's centre. OpenYAMM casts from 0.75 h (indoors) or 0.7 h
     (outdoors) to z + 96.
   - Low railings, crates and low walls can block ours when MM9 sees over them.
   - **Fix:** for MM9 profiles, use the actor's top − 5 units as the eye; a profile-driven eye height, no world
     check.
   - **Done (section 5.5).**
7. **Small rule differences that make OpenYAMM more permissive:**
   - hearing is not bounded by sight (no placement has `hearing` > `sight`, so no effect today);
   - perception is evaluated every step instead of ≤ 1 Hz;
   - it is evaluated in every state, not only idle, fidget and move.

   Leave these, or gate the search at 1 Hz if timing fidelity matters.

### 5.5 Fixes (2026-11-04)

One shared rule each, driven by data; an actor without an MM9 loop profile takes exactly the old path.

1. **Placement yaw indoors** (item 1). `buildIndoorMapActorAiState` starts every map actor at its `initialYawUnits`, as
   the outdoor runtime does (saves keep the runtime yaw as before). `perception_placed_yaw` passes; the measurement
   `perception_placed_sight` (Drangheim Prison's Nagate Elder, facing about 215 degrees, sight 1 536, hearing 369)
   notices the party 1 444 units along its facing on its first AI step, and `perception_placed_sight_beyond` shows it
   does not at 1 628 (it takes the party only from a Hatchling's alert). The MM9 idle loop is unchanged: MM9 never
   turns an idle monster back to its start.
   - MM6-MM8: their DLV actor records carry the yaw (`+0xA2`, position + 12, in MM8's and MMerge's layout; MM7's
     own layout has it at `+0x9A`), and OpenEnroth reads it, but our scene exporter dropped it, so every placed
     MM6-MM8 actor faced +X. Most are 0 anyway (MM6 76 of 76, MM7 389 of 412, MM8 137 of 149); spawn-point monsters
     have no yaw in the original either. `tools/export_indoor_scene_yml.py` now writes `initial_yaw_units` when it is
     not 0, and the 35 placed actors with a yaw in 10 MM7/MM8 scenes have it (7d14, 7d20, 7d25, 7d29, 7d30, MM7
     d03; MM8 d07, d16, d19, d28). Their idle facing (homeYawRadians) follows. Before/after:
     `output/mm9_rework/perception_fix/mm8_d16_before_b.png`, `mm8_d16_after_b.png` (the two alcove guards, yaw
     1 724) and `mm8_d16_before.png`, `mm8_d16_after.png` (the two at yaw 0, unchanged).
2. **The outdoor engagement cap** (item 3). An MM9 loop monster considers the party as far as its senses reach:
   `mm9SenseRange(world range, mm9PerceptionRange(sight, hearing, doubled), 10 240)`, so a placement's sight raises the
   world's 4 096 for that actor only (`resolveOutdoorTargetFacts`, `OutdoorMm9Sight`). Its outdoor update range
   likewise (`OutdoorActiveActorCandidate::activeRange`, at least the shared 5 632). The world manifest is unchanged;
   MM6-MM8 actors have no such range.
3. **Indoor activation** (item 4). In `selectIndoorActiveActors` an MM9 loop monster is looked at as far as its senses
   reach (at least 5 120, at most 10 240) with MM9's one sight line (its eye to the party's centre), takes no slot of
   the shared nearest 30, and MM9 monsters are picked apart and capped by distance (the nearest 48,
   `MaxActiveMm9ActorUpdates`) instead of the shared list's insertion order. The indoor line test takes the same
   range (`hasIndoorCombatLineOfSight`'s `maximumRange`; it stopped every line at 5 120 before). Cost: the selection
   pass is 17 µs a step for Chasm of the Dead's 171 actors and 26-38 µs at a Lich Lab hotspot (98 actors within a
   doubled sight; 40 active, about two staggered line checks a step); an active actor costs about 10 µs a step to
   collect, so the cap keeps today's 48-actor budget for MM9 maps.
4. **Outdoor runtime spawns** (item 5). `OutdoorWorldRuntime::MapActorState::mm9Ai` carries a spawn's placement (an
   arena's `mm9_ai`, a death spawn's ScriptParams 1, as indoors), saved from version 150; `mm9PlacementRecord` reads it
   or the map's. A spawn with a placement starts dormant as its placement or row says, and a death spawn is no pod.
5. **Sight line end points** (item 6). Profile field `eye_below_top` (default 5.12 units, 2 LT; `mm9EyeZ`): an MM9 loop
   monster's sight line and perception distance run from its eye to the party's centre (z + half its height: 96
   indoors, as before; 84.5 outdoors on MM9) in both runtimes. MM6-MM8 keep 0.75 h / 0.7 h to z + 96.

Item 2 (the outdoor maps' `mm9_ai`) stays with the map generation session; item 7 is unchanged.

## 6. Target selection and tracking

### 6.1 Looking for a target

- `LookForTarget` `0x10012e00` (`+0x658`) runs from the idle, fidget and movement thinks when there is no target (§5.1). It does
  nothing unless the script registered `OnFoundTarget` (`0x10012de0` checks the event 0 handler), and it runs at most
  once per **1.0 s** (`+0x4d0` → `0x1000c8f0`, last search time `+0x5a8`). The player search
  (`0x10012f80`/`0x10012ef0`, event 1, `OnFoundPlayer`) works the same way, timed from `+0x5ac`.
- `FindTargets` (`+0x4e0` → actor manager `0x10006be0`) walks the manager's list of **all actors**. It keeps up to
  50 candidates that are: not me; not dead; active (`+0x320`); allowed by `CanTarget` (`+0x374`: not a friend,
  §10; the swimmer and NPC overrides above); perceived (`+0x404`, hearing allowed); and, if the script gave a
  maximum distance (`OnFoundTarget <dist>` → `+0x738`; the base scripts give none), within it.
- `0x10006120` returns the **nearest** candidate. `Target Pref` plays no part. Event 0 then fires with the target.
- The scripts do the rest: `OnFoundTarget` → `SetupTarget` (`Target h, TRUE`, start the alert ticks, double the
  sight and hearing ranges) and a `Taunt` 40 % of the time (`AWARE_CHANCE`).

### 6.2 Keeping a target (`0x100118f0`, `+0x5b8`, every update while a target is set)

- Current target `+0x5c8`; its last known position `+0x660`/`+0x66c`; time last perceived `+0x678`.
- Each update: `Perceive(target, sight only)`. If the target has not been perceived for longer than
  **`TargetLostTime`** (`+0x608`, default **8.0 s**, script `SetTargetLostTime`) → `OnLostTarget` (9). If the script
  has no handler for it, the native code clears the target itself (`0x100130d0`).
- When asked, it turns to face the target at **540°/s** (`+0x94`, `0x44070000`).
- Attack range test: distance ≤ `AttackRange` (`+0x41c`) → `+0x67c` = in range; if it can also attack →
  `OnAttackReady` (0xc). Leaving the range after being in it → `OnTargetOutOfRange` (0xa).

### 6.3 Changing targets (scripts)

`NewTargetCheck` (`BaseCrawl.inc`) runs on damage, alerts, help calls and nearby projectiles. A monster without a
target takes the attacker. One with a target switches with probability 70 % (45 % if its current target is already in
attack range), halved if the attacker is farther away than the current target, × 1.15 if it is less than twice as far
(the script doubles the distance before comparing). A target that has not been attacked, and has not attacked, for
`MAX_CHASE_TIME` **30 s** is dropped (`GiveUpOnTarget`). Flyers switch to an attacker 50 % of the time.

## 7. Attacks

### 7.1 Attack range (`+0x41c` = the `AttackRange` stat)

- Melee (`+0x420`, `0x1000dd40`): `AttackReach + 1.25 × (radius − half depth)`. Here radius is the horizontal radius
  `+0x484` = √(x² + z²) of the object's dimensions (`0x10005ce0`), and half depth is the dimensions' z.
- If the monster holds a ranged weapon prop (`+0x514`): the projectile's range from the object table (`+0x428`,
  `0x1000dda0`).
- The scripts' `RangeAttackRange` = min(projectile range, `SightDistance` − 5).

### 7.2 Readiness and recovery (`CanAttack`, `+0x480` → `0x10013460`)

Attacking is allowed only when the monster is not already attacking (`0x10001f60`), the animator is free, the
current state permits it (`0x1001cfa0`), the monster is alive, and the RPG layer's combat manager (`[0x10294d3c]`,
`0x100b5690`) returns an available action:

- bit 2: melee, unless the monster has condition 0xb;
- bit 4: spell or ranged, unless it has condition 0xc;
- with both available, a d100 roll (1-100) against the character's `+0x200` (`0x10053f40`) keeps only one: at most
  that value keeps the blow, above it the spell or ranged attack (`0x100b577d`-`0x100b579d`). `+0x200` is the `Att%`
  column (record `+0x128`, copied at `0x10052bff`), not the spell-use percentage (corrected in phase 2, see
  [the plan](../MM9_MONSTER_AI_PLAN.md) "Phase 2");
- nothing is available while the character is **recovering** (busy byte `+0x68`, read by `0x1004af40` at
  `0x100b56cb`). `0x1004e110` sets busy and the time it ends (`+0x64`) after each action, and the character tick
  clears it (§7.2.1). In turn-based mode, nothing is available unless it is this actor's turn;
- conditions 9, 0xb and 0xf block all actions.

The chosen kind goes to `+0xb2c` (2 melee, 4 spell). The scripts time their chase so that they arrive as recovery
ends (`ShouldRunAfter`: run only if `RecoveryTimeLeft < distance / RunVel`), but they read recovery 3 × too long
(§7.2.1).

### 7.2.1 Recovery: its length, its clock and when it starts

Decoded on 2026-11-04 (hash checked). In short: **recovery = `Recovery` game seconds, counted from the end of the
attack clip, and one game second is 33 ms of real time.** A `Recovery` 30 monster recovers for 0.99 s, not 3 s.

**Length.** `0x1004e110` only stores its argument (`mov byte [ecx+0x68],1; mov [ecx+0x64],eax; ret 4`). The end
time is computed by its callers:

- `SetRecovery(now)` is slot `+0x78` of the AI character's vtable (`0x100ee69c`, the monster character's
  `0x1016f208` has the same entry): `0x10054080` does `end = 0x100537c0() + now`, then calls `0x1004e110(end)`.
- `0x100537c0` returns `[+0x2a4] + vtable+0x98(0xd, 0xc, 0)`. `+0x2a4` is the `Recovery` column as a plain integer.
  The loader reads it with `atoi` (`0x10056bb0` at `0x1004351d`, stored in record `+0x144`), and `0x10052c71` copies it
  unchanged. The only other writes are constructor defaults (`0x1004cf42`, `0x10052a3d`).
- `vtable+0x98` (`0x1004b2f0`) adds up the amounts (`+0x14`) of the character's active effects (a list at `+0xa8` of
  0x20-byte entries, count `+0x1ac`) whose type is 0xd and subtype 0xc. Only three spells add such an effect:
  - Curse (spell 5, `0x1008b690`), from Expert, with an amount based on the target's base recovery (`0x100537e0`);
  - Haste (spell 22, `0x1008c5f0`), with a negative amount (`neg eax`);
  - Wrath of Bugs (spell 48, `0x1008e510`).

  The effects run out with the character tick.
- **Nothing else changes it.** No speed or SPD stat, level, difficulty, action type, weapon or attack data, random
  factor or time scale is involved. Without one of those spell effects, recovery is exactly the `Recovery` value.
- **Spells use their own recovery.** `Spell::Cast` (`0x1008a250`, slot 0 of every spell vtable) sets the caster's
  end time to `now + spell[+0x7c + 4 × mastery]` at `0x1008a306`-`0x1008a320` (the same happens at `0x1008abd9`).
  That value is the `SPELL.txt` "Recovery" column for the caster's mastery: 30-120. The monster's own `Recovery` does
  not apply to a spell. The castSpell state's completion (`+0x60c` → `0x1000e9e0`) starts no recovery.

**Clock.** `+0x64` and the time passed to `character->Update` (`0x1000e361`-`0x1000e373`, `0x10055d10` on
`[0x102a49d4]`) are values of the RPG game clock. The clock is an integer count of **game seconds** at `[clock+0x28]`:
`0x10055d40` builds it from the year, month (12), day (28), hour (24), minute (60) and second (60) fields. It runs
about **30 times faster than real time**:

- The server shell's `Update(timeElapsed)` (`0x100d2140`, slot `+0x30` of vtable `0x1018f228`) passes
  `timeElapsed × 1000` (constant `0x100ee5f4` = 1000.0) to `0x10055c10`.
- `0x10055c10` adds those milliseconds to an accumulator (`+0x2c`) and advances the clock by `acc / 33`
  (`mul 0x3e0f83e1; shr edx,3`), keeping `acc % 33` (`div 0x21`). **One clock unit is 33 ms of real time**, 30.3 per
  real second (a game day lasts about 47.5 real minutes).
- Turn-based mode stops the clock (`0x10055cd0` clears `+0x4c`, called at `0x100b5d2d`), and each completed round
  adds one second (`0x100b36f2`).
- So `Recovery` 30 lasts **0.99 s** of real time and 40 lasts **1.32 s**. The character tick
  (`0x1004abd6`: `cmp ebp,[esi+0x64]; jb`, then `+0x64` and `+0x68` cleared) runs in the 10 Hz `AIBase::Update`, so the
  monster is seen as ready up to 0.1 s later.

**The scripts read recovery 3 times too long.** `GetStat RecoveryTime` returns `0x100537c0() × 0.1`
(`0x10018faa`-`0x10018fb9`, constant `0x100eef48` = 0.1), and `RecoveryTimeLeft` returns `max(0, [+0x64] − clock)
× 0.1` (`0x10018fdc`-`0x10019015`). For `Recovery` 30 they report 3.0, although the recovery lasts 0.99 s; this stat is
where the old "30 → 3 s" reading came from. Script timers run on LithTech time in real seconds (`0x1009e31d` compares
each `Wait` deadline with `+0x118`, `GetTime`). What the scripts do with the stat:

- `DoEvade` (`BaseMelee.inc:163-179`) reads `RecoveryTime` into `g_nEvadeTime`, then sets `g_nTemp = 2`. The evade
  always lasts **2 s**. It does not reset or shorten the recovery.
- `ShouldRunAfter` (`BaseCrawl.inc:345`; `Range.inc:363`) runs after the target only if `RecoveryTimeLeft <
  distance / RunVel`. Because the value is 3 times too high, the monster starts running when about a third of the
  travel time of real recovery is left, so it arrives late rather than early.
- No script sets `RecoveryTime` or `RecoveryTimeLeft`.

**When it starts: at the end of the attack clip.**

- When the current state's animation has stopped playing, the animator think (`0x1001e870`: state from `[+0x18]`,
  still-playing test `[+0xc]` = `0x1001d680`, false → `[+0x2c]`) calls the state-done dispatcher `0x1001ea50` (tables
  `0x1001eb94`, `0x1001eb5c`):
  - state 4 (handAttack) → `+0x600` `0x100132f0`;
  - state 5 (weaponAttack, with a melee or a ranged weapon) → `+0x604` `0x10013370`;
  - state 6 (rangeAttack) → `+0x608` `0x100133e0`;
  - state 12 (castSpell) → `+0x60c` `0x1000e9e0`.
- The three attack handlers call `CombatManager::StartRecovery` (`0x100b6020` on `[0x10294d3c]`, from `0x10013302`,
  `0x10013392` and `0x10013413`), which calls the character's `SetRecovery(clock)`. They then raise script callback
  0x1f (`+0x154`), which ends the script's `Attack`.
- The hit also sets a recovery. The melee sweep (`0x1000f6c6`) and the missile path (`0x1001849b`) call the RPG action
  `0x100b3bc0`, which for a monster sets `end = now + Recovery + modifier` (`0x100b4049`-`0x100b4062`). The
  completion handler then overwrites it, so the end time that counts is **clip end + Recovery**.
- **The clip length therefore adds to the time between attacks, for blows and shots alike.**

**One cycle, `Recovery` 30, 1.03 s clip.** 1.03 s is the median `AttackMelee` clip of the installed MM9 models
(0.5-1.7 s). `AttackTick` (every 0.2 s) sees `IsAttacking` false 0-0.2 s after the clip ends, and then `AttackDone`
runs:

- **No evade** (60 % at the table chance; the threat-adjusted chance in §9.3 is 0-80 %): `AggressiveStart`, then a
  tick every 0.2 s until `CanAttack`. The next attack starts 1.0-1.2 s after the clip ends, so **2.1-2.3 s** from one
  attack's start to the next.
- **Evade** (40 %): a 2 s evade (shorter if the target gets beyond 500 LT), then one 0.2 s tick (recovery ended long
  before): **about 3.3-3.5 s**.
- Average at the table evade chance: about **2.6 s**. `Recovery` 40 rows: about 2.5 s without an evade.
- Shots from a distance also wait for `Range.inc`'s shot check (every 1-2.5 s for a walker), so their interval is
  `clip + Recovery`, then the next check.

**OpenYAMM, checked 2026-11-04.** `generate_mm9_monster_tables.py` (`recovery_ticks`) uses `Recovery × 0.1` seconds
(30 → 3.0 s). `startAttack` (`GameplayActorAiSystem.cpp`) sets the cooldown when the attack starts: for a blow
3.0 s × 0.9-1.2 = 2.7-3.6 s; for a shot or spell (3.0 s + clip) × 0.9-1.2, about 3.6-4.8 s. The MM9 walker loop
(`AI_Mm9Engage`, `AI_Mm9AttackStep`) adds no wait of its own beyond `mm9ShouldRunAfter`, which is given the cooldown
left. Its 2 s evade ends inside the cooldown, so an evade does not lengthen the cycle.

| `Recovery` 30, 1.03 s clip | MM9 | OpenYAMM | OpenYAMM ÷ MM9 |
| --- | --- | --- | --- |
| Recovery itself | 0.99 s, from the clip's end | 3.0 s × 0.9-1.2, from the attack's start | 3.0 |
| Blow, no evade | 2.1-2.3 s | 2.7-3.6 s (mean 3.15) | about 1.4 |
| Blow, evade | 3.3-3.5 s | 3.0-3.6 s | about 1.0 |
| Blows, 60/40 mix | about 2.6 s | about 3.2 s | about 1.2 |
| Shot (`clip + recovery`, before the shot check) | about 2.1 s | 3.6-4.8 s (mean 4.2) | about 2 |
| `Recovery` 40 blow, no evade | about 2.5 s | 3.6-4.8 s | about 1.7 |
| Spell | the spell's recovery (`SPELL.txt`, 1-4 s) from its cast | 3.0 s + clip, × 0.9-1.2 | — |

A fix needs four changes:

1. Convert `Recovery` at 33 ms per unit (× 0.033 instead of × 0.1).
2. For MM9 actors, start the cooldown at the end of the clip, for blows and shots alike: cooldown = clip + recovery,
   measured from the attack's start, with no 0.9-1.2 random factor.
3. Give spells the recovery of the spell's mastery (the `SPELL.txt` value at 33 ms per unit), counted from the cast.
4. To keep MM9's arrival timing, give `mm9ShouldRunAfter` the scripts' view, which is the real recovery left
   × 3.03.

With 1 and 2, a blow cycle becomes the clip + 0.99 s + decision latency (about 2.0-2.3 s), or the clip + 2 s with an
evade.

**Interrupted attacks.** Every state change goes through the animator's `SetState` (AIBase `+0x240` → `0x100168a0`
→ `0x100021f0` → animator slot `+0x4`). That is `0x1001ec50` for the plain animator (vtable `0x100efa1c`, models
without a `Top` node). The layered animator (vtable `0x100efac0`, models with one, chosen at `0x1001532a`) uses
`0x1001ee50`, which passes full-body changes to the same `0x1001ec50`. While an attack clip is still playing
(`[+0xc]` = `0x1001d680`):

- **A request for idle (state 0) is deferred.** `0x1001ecbb`-`0x1001ecf2` sets the pending flag `+0x2c`, returns
  success and leaves the attack running. The done dispatcher then clears the flag, runs the normal completion handler
  (`0x1001ea5a`-`0x1001ea63`) and goes idle if the handler declines.
- **A terminal state cuts through.** The terminal states are die, swimDie, flyDie, flyFall, flyFallDown and crouchDie:
  `[+0x94]` = `0x1001d030`, table `0x1001d060`, tested at `0x1001d1e9` before the exit rules. Death therefore skips
  the completion handler, which does not matter for a dead monster.
- **Old-state exit rules** (`0x1001d1f8`, byte table `0x1001d4c8`, jump table `0x1001d4b0`):
  - **handAttack (4), weaponAttack (5), castSpell (12):** only wince (8) or flyWince (0x21) may replace the clip
    (`0x1001d28a`). Any other state is refused while the clip plays. For handAttack, the animator's `[+0x48]` is asked
    first: it refuses on the plain animator (`0x100d9f40`) and allows on the layered one (`0x100018c0`).
  - **rangeAttack (6):** refused while playing, unless the caller names a specific animation (`0x1001d30b`: argument
    2 ≠ −1). A new `Attack` or `RangeAttack` command does name one.
  - **wince (8):** cannot be left until it ends, except into a new wince (`0x1001d2bf`).
- **A state that replaces an attack never runs that attack's completion.** `0x1001ec50` calls the done dispatcher for
  the old state only when it is `custom` (0x11, `0x1001ed0f`-`0x1001ed33`). So when a wince, death or named range
  animation cuts a blow, shot or spell short, `StartRecovery` (`0x100b6020`) is skipped. The wince's own completion
  (`+0x574` → `0x1000e000`) goes idle and raises script event 3; it sets no recovery. The script notices through
  `AttackTick` (`IsAttacking` false) and runs `AttackDone`.
- **What stands after an interruption:**
  - **after a blow connected:** `0x100b3bc0`'s `hit + Recovery` (`0x100b4062`). `0x100b3bc0` is reached only through
    `+0x6fc` (`0x1000f650`), called at `0x1000f5f0` once the sweep (`0x10059b70`) has hit the target or a non-actor;
    a missed blow sets nothing;
  - **after a shot or cast was released:** the shot's `hit + Recovery` from `0x1001849b`, or the spell's own
    recovery from `Spell::Cast`;
  - **cut before the hit or cast key:** no new recovery. The monster is ready as soon as the wince clip ends and the
    next script tick runs.
- **Push-back is not an interruption.** `SetPushBack` (`+0x4d8` → `0x100153b0`, called from `OnDamage` at
  `0x10015690`) only sets a velocity and a timer, and the attack clip plays on.
- **Conditions do not interrupt.** The conditions that block actions (9, 0xb, 0xf, and 0xc for spells) only make
  `0x100b5690` refuse new actions. The AI code checks no other condition than 2 (dead), 4 (berserk) and 7 (fear), and
  none of these changes the animation state, so a clip already playing finishes and starts its recovery normally.
  Whether the RPG layer freezes the model for Paralyze was not followed.
- **The wince itself is rare.** It needs HP at or below 20 %, and `Always Wince?` 1 rows never wince (§8).

What OpenYAMM should do: arm an MM9 actor's cooldown in three places, not only at the attack's start. Arm it at the
hit or release (hit time + recovery, or the spell's recovery). Re-arm it from the clip's end when the clip finishes.
If a wince cuts the attack before its hit, do not arm it at all. Knock-back and conditions should not cancel an
attack that is already playing.

**Turn-based mode.** The combat manager is `[0x10294d3c]`. Its participant list holds entries of 0x14 bytes from
`+0x4`: the character, an *acted* byte at `+0x8`, a millisecond counter at `+0xc`, the start time at `+0x10` and a
skip byte at `+0x14`. The count is at `+0xfa4` and the current entry at `+0xfa8`.

- **Entering turn-based mode** (`0x100b5b90`, on):
  - The manager lists the active actors (`0x100b5bff`-`0x100b5c75`), then the party (`0x100551f0`, count
    `[mgr+0x60]`) and a second list (`0x100548a0`, count `[mgr+0x64]`).
  - The party and the second list get `now + 30` (`0x100b5cb3`, `0x100b5d09`). **Monsters keep their real-time
    recovery**, so a monster that is not recovering acts first.
  - The clock stops (`0x10055cd0`), and the turn starts with entry 0.
- **Choosing the next actor (`NextTurn`, `0x100b36a0`).** It clears the current entry's *acted* byte and counter,
  then scans from current + 1 (wrapping) for the first entry that is alive and **not recovering** (`0x1004af40` at
  `0x100b3773`). Each time the scan comes back to the current entry, the clock advances one game second
  (`0x100b36f2`) and every participant's `character->Update(clock)` runs (`0x100b3723`), which clears the recoveries
  that have ended.
  - **So Recovery both orders and delays turns.** Actors take turns in the order their recoveries end, in whole game
    seconds, and ties go to list order after the current actor.
  - A turn has no fixed length in clock units. The clock moves only while nobody is ready, one second per empty scan.
- **During a turn** (`0x100b58c0`, called from `0x1000e145` in AIBase `+0x6f8` → `0x1000e0f0`):
  - Only the current actor updates. Every other actor is frozen: its animation is paused (animator `+0x78`), and
    `AIBase::Update` returns at `0x1000e39e` before the animator and the scripts run. The character tick at
    `0x1000e373` still runs before that point.
  - The current actor has **one real second** (`timeGetTime` `[0x100ee128]`, `cmp ...,0x3e8` at `0x100b59a0`). If
    it has not acted by then, it gets `now + 30` (`0x100b59d5`) and the turn moves on. The counter does not start
    while the actor is wincing (the second argument).
  - `0x100b5690` allows one action per turn: it returns nothing once the current entry has acted
    (`0x100b5819`-`0x100b5844`).
- **When the turn ends.** A blow or shot (`0x100b3bc0`) marks the entry as acted (`0x100b403b`) and sets
  `now + Recovery` (`0x100b4062`).
  - **An ordinary monster's turn ends on the one-second timeout.** Being marked as acted only spares it the
    `now + 30` penalty (`0x100b59c0`).
  - **Only characters of kind 2 end their turn at the action** (`0x100b409c`-`0x100b40b6`, and the spell's
    `0x100b4599`-`0x100b45b2`). The kind getter `0x100542a0` returns 2 only for class ids 252 (Forad Darre) and
    279-292 (the joinable heroes); other characters return their `+0x44` field.
  - The spell path has a second `NextTurn` at `0x100b4426`, in a branch that was not followed.
  - A party member gets `now + 0x3c` (60) in one branch (`0x100b3d0a`).
- **The clip-end rule still applies, with a cost.**
  - Once its turn has passed, the monster is frozen mid-clip until its next turn.
  - On that turn the rest of the clip plays, and the completion handler calls `StartRecovery`. The monster is then
    recovering again (`now + Recovery`) for the turn it was just given.
  - It cannot act, and the one-second timeout gives it `now + 30`, because it has not acted in that turn.
  - As read, a turn-based attack whose clip outlasts the turn therefore uses two of the monster's turns. This looks
    like an unintended side effect of the native design.

What OpenYAMM should do: the shared turn engine already grants MM9 actors their turns
(`actorAttackReady`, turn-based branch). Order the turns by recovery end, in MM9 game seconds (`Recovery`, or 30
for a turn that passed or timed out), with the party at `now + 30` when combat starts. Start the recovery at the
action. Do not copy the mid-clip freeze and the lost second turn unless exact fidelity is wanted.

### 7.2.2 Attack kind, spell choice, `RangeAttack` and `concat`

Decoded on 2026-11-04 for the [spell mapping](../MM9_SPELL_MAPPING.md) (§1.4 and §6).

**What the loader keeps** (`0x10042e00`; columns are read by spreadsheet letter through `0x10056d40`; record offset
= loader offset − `0x4f8`). The character copies are made at `0x10052cba`-`0x10052d2a`.

| Column | Parse | Record → character | Notes |
| --- | --- | --- | --- |
| AO `SpellUse%1` | `atoi` (`0x10056bb0` at `0x100435bd`) | `+0x160` → `+0x2b4` | The word `concat` becomes **0** |
| AP `Spl,Mas,Skil1` | `strtok` on `,` (`0x10043e5c`-`0x10044050`) | id `+0x164` → `+0x2ac`; mastery `+0x16c` → `+0x2bc`; skill `+0x174` → `+0x2c4`; 4th field `+0x178` → `+0x2c8` | `0` or an empty cell becomes id 50 (none) with mastery −1. Masteries: `N` 0, `E` 1, `M` 2, `G` 3 |
| AR `Spl,Mas,Skil2` | the same (`0x10044056`-`0x1004424a`) | id `+0x168` → `+0x2b0`; mastery `+0x170` → `+0x2c0`; skill `+0x17c` → `+0x2cc`; 4th `+0x180` → `+0x2d0` | A missing mastery token writes −1 into spell **1**'s mastery (`0x10044222`, a loader bug) |
| AH `Att%` | `atoi` | `+0x128` → `+0x200` | The attack-versus-spell roll below |
| Y `Bonus` | string list (`Brkitem` 0 … default 0x16, `0x100438f0`-`0x10043e52`) | `+0x1a0` → `+0x2d4` | **Nothing reads `+0x2d4`.** Its only accesses are the writes at `0x1004cfbe`, `0x10052a73` and `0x10052e76` |
| AQ `SpellUse%2`, BK `ConcatAttk` | — | — | **Never read.** The binary has no `AQ` or `BK` column-letter string, and none of the names `ConcatAttk` or `SpellUse` |

The 3rd and 4th fields of `Spl,Mas,Skil` are the spell's two element skills. `Spell::Init` (`0x10089fe0`) gives a
monster caster mastery `+0xc` = `Mas`, `e1` points `+0x4c` = `Skil` and `e2` points `+0x50` = the 4th field. It
takes them from spell 1's set when the spell id equals spell 1 (`0x1008a1e4`-`0x1008a20d`), and otherwise from spell
2's set (`0x1008a21c`-`0x1008a235`). `SPELL.txt` defines the effect amounts and durations with these points: for
example Paralyze, "Monster slows to n1% speed", "2 per point in e1".

**Choosing the spell (`ChooseSpell`, `0x10053210`, character vtable `+0x44`):**

- spell 1 is none → spell 2;
- spell 2 is none → spell 1, **whatever `SpellUse%1` holds**;
- both present → a d100 roll (1-100) ≤ `SpellUse%1` → spell 1, otherwise spell 2.

So `SpellUse%1` only splits the casts between two spells, and spell 2's share is `100 − SpellUse%1`. It is not a
chance to cast at all. There is no check of range, mastery, or whether the target already carries the effect. A
recast is passed to the effect list, which keeps the stronger effect (`0x1004b100`).

**Choosing the kind of attack (`0x100b5690`, from `CanAttack` `0x10013460` and `CanRangeAttack` `+0x4c0` →
`0x10014ca0`):**

- bit 1: attack 1 has damage (`0x10053ee0`: dice × sides + bonus from `+0x1f0`-`+0x1f8`), and there is no
  condition 0xb;
- bit 2: attack 2 has damage (`0x10053f00`, `+0x204`-`+0x20c`), there is no condition 0xb, and the target's `+0x328`
  is false;
- bit 4: `ChooseSpell()` is not none and there is no condition 0xc;
- with bits 2 and 4 both set: a d100 ≤ `Att%` keeps bit 2 and drops the spell; otherwise the spell stays
  (`0x100b577d`-`0x100b579d`). **The chance of a spell is therefore `100 − Att%` when attack 2 exists, and 100 % when
  it does not**;
- if spell 1 and spell 2 are both present and both of type defense or healing (`SPELL.txt` `SpellType` → spell
  record `+0x8c`: offense 0, defense 1, else 2; parsed at `0x100426b4`), bit 4 is dropped (`0x100b57a9`-`0x100b5816`).
  Such a monster never casts through this path.

`CanAttack` stores kind 2 when bit 2 is set, otherwise kind 4 when bit 4 is set; it returns true with the kind
unchanged when only bit 1 is set. `CanRangeAttack` does the same but returns false for bit 1 alone, and also refuses
during a taunt. No row with a projectile lacks both attack 2 and a spell, so that case does not arise. The roll is
made again on every call.

**`RangeAttack` decides at the release** (`0x100187d0` → AIBase `+0x6e8` → `0x10018420`, with the kind from
`+0xb2c`):

- **Kind 4 (or 0): a spell.** It calls `ChooseSpell` **again** (`+0x6e4` → `0x10018400` → `+0x44`) and casts the
  result with `CastSpell` (`0x100b40f0`). That sets the spell's own recovery (§7.2.1). The spell's normal effect and
  duration apply, from the mastery and points above. A kind-2 character (the joinable heroes) picks its spell again
  inside `0x100b4446`.
- **Kind 2 (or anything else): the physical shot.** `0x100b3bc0` is called with type 2 and fires `Projectile1`
  (character `+0x224`, copied at `0x10052b80` from the `AG` column; type 0x20 would use `Projectile2`, `+0x264`).
  `Projectile1 = Spell` rows have `Att%` 0, so they always cast while a spell is available.
- **A blow** (`Attack` → the melee sweep → `0x1000f650`) is always the physical attack: `0x100b3bc0` with type 1. The
  kind and the spells play no part in it.

**`concat` is not implemented in `object.lto`:**

- the word becomes `SpellUse%1` 0, and nothing marks the spell as riding on a hit;
- `ConcatAttk` and `Bonus` are never read;
- no spell is created on a melee hit. The only spell created during hit resolution (`0x100b46c0`) is Pain
  Reflection (spell 28, `0x100b4e68`), reflected by a target that carries the effect (0xd, 0xb);
- `cshell.dll` (the client) only has `data\concat.csv` and a treasure-level message ("Couldnt match level %d concat
  to %s", `0x100b722a`). Neither is about spells.

So a `concat` row's spell is an ordinary spell:

- **BaseCrawl and Dagrell scripts** never call `RangeAttack`, so those monsters never use it: grey, red and black
  wolves, Canopic and Embalmed Mummies, Venomous and Spectre Dagrells.
- **Rows with a ranged script** cast it as a normal ranged spell, at `100 − Att%`:
  - Basilisks (`crawlrange.scr`, `Att%` 50): 50 % of their shots;
  - Ghast, Revenant (`baserange.scr`, `Att%` 0): every shot;
  - Ghoul: always Disease, because its spell 1 Paralyze gets `SpellUse%1` 0 and loses every roll to spell 2;
  - Dripper (`Att%` 100): never.

A `ConcatAttk` of 0 means nothing different from any other value.

**Oculus (row 230).** Spell 1 is Paralyze `E,10,1` with `SpellUse%1` 25, spell 2 is Curse `M,8,5`, and `Att%` is
50. It has attack 1 (with `BlueLine`) and attack 2, and uses `baserange.scr` (`Range.inc`).

- Each shot check that fires (`CanRangeAttack` → `RangeAttack`) has a 50 % chance (`Att%`) of the `BlueLine` shot
  and a 50 % chance of a spell.
- A spell is Paralyze 25 % of the time and Curse 75 % of the time. Per shot that is about **12.5 % Paralyze,
  37.5 % Curse and 50 % `BlueLine`**: Curse is three times as common as Paralyze.
- Neither spell is withheld when the target is already affected.
- In melee range, `Range.inc` swings (`Attack`), and its blows are always physical.
- Paralyze uses mastery Expert, `e1` 10 and `e2` 1; Curse uses Master, `e1` 8 and `e2` 5. The cast recovery comes
  from `SPELL.txt`: Paralyze Expert 120, Curse Master 90 (× 33 ms).

What OpenYAMM should do, data-driven (done 2026-11-04: [spell mapping 6.6](../MM9_SPELL_MAPPING.md#66-spell-choice-and-concat-as-mm9-plays-them-2026-11-04)):

- **Generator.**
  - Total spell chance = `100 − Att%` when the row has attack 2 damage, else 100. Zero when both spells are
    non-offensive.
  - Split it by `SpellUse%1` only when both spells exist; a single spell takes the whole share.
  - Drop the `100 − SpellUse%1` rule for a lone spell and every use of `ConcatAttk`.
  - With OpenYAMM's sequential rolls, write `spell1 = T × S1` and `spell2 = T × (1 − S1) / (1 − T × S1)`, where
    T is the total spell chance and S1 is `SpellUse%1`, both as fractions.
- **`concat` rows.**
  - Give the BaseCrawl and Dagrell rows no on-hit condition and no spell (MM9 has none).
  - Import the others as ordinary ranged spells. The `Bonus` column has no native effect either.
  - Keeping on-hit conditions for those melee rows would be an OpenYAMM design choice, not MM9 behaviour, and
    should be recorded as such.
- **`mm9RangedAbility` (`GameplayActorAiSystem.cpp:4639`).** Today a row with a ranged attack 1 can never reach
  spell 2, which is why the Oculus never cursed. Pick spell versus shot by the spell chance above; then pick spell 1
  versus spell 2 by `SpellUse%1` when both exist; otherwise fire attack 1's projectile.

### 7.2.3 Which rolls happen in reach and out of reach; the Lobbers

Decoded on 2026-11-04.

**The scripts decide where a shot is possible; the native code only sets the kind.**

- **In reach** (BaseCrawl and BaseMelee `AggressiveInRange`, used by `baserange.scr`, `crawlrange.scr` and the
  melee scripts):
  1. `CanAttack` runs `0x100b5690`. That is **the only `Att%` roll**, made when bits 2 and 4 are both set, and it only
     stores kind 2 or 4 in `+0xb2c`.
  2. If it returns true, `ShouldAttack` (clear shot) → `DoAttack` → `PreAttack`, `MeleeAttack` → **`Attack`**.
     `Range.inc`'s `MeleeAttack` also restarts the shot-check timer (`CheckRangeAttackStart`, `RANGE.inc:262-271`).
  3. `Attack` (`0x100134f0`) ignores the kind. With no prop, or a melee prop, it plays handAttack or weaponAttack,
     and the hit is the physical type-1 action (`0x1000f650` → `0x100b3bc0`).
  - **So in reach the action is always a blow**, whatever `Att%` and the spells say. This holds even for a row
    without attack 2 (the Initiate) and for a row with only a projectile.
  - The only in-reach shot or spell comes from a monster that **holds a ranged weapon prop**. Its `Attack` becomes
    `RangeAttack` (`0x1001350d`-`0x1001351b`), which fires by the kind `CanAttack` has just rolled: kind 2 →
    `Projectile1`, kind 4 → `ChooseSpell` → the spell.
- **Out of reach** (`Range.inc` `CheckRangeTick`, every 1-2.5 s for a walker and 0.2-0.4 s for a holder;
  `RANGE.inc:151-225`):
  - The tick returns while the target is within `AttackRange` (`RANGE.inc:173-176`).
  - Otherwise `CanRangeAttack` (`0x10014ca0` → `0x100b5690`) makes **one `Att%` roll**, again only when bits 2 and
    4 are both set, and stores the kind.
  - Then comes the line check (100, 20, 15 or 0 %), and finally `RangeAttack`.
  - At the release (`0x10018420`), kind 2 fires `Projectile1`, and kind 4 calls `ChooseSpell` (the `SpellUse%1`
    roll between the two spells, with no second `Att%` roll) and casts.
  - **`Att%` is therefore rolled exactly once per action, and only matters for shots.**
- **Probabilities per out-of-reach action** (no prop):

  | Row has | Kind 2 (`Projectile1`) | Kind 4 (spell) |
  | --- | --- | --- |
  | attack-2 damage and a usable spell | `Att%` | `100 − Att%`, split by `SpellUse%1` if two spells |
  | attack-2 damage, no spell | 100 % | — |
  | no attack-2 damage, a spell | — | 100 % |
  | attack 1 only | `CanRangeAttack` false, no shot (no MM9 row is like this) | — |

  Here "usable" means not blocked by condition 0xc, and not one of two non-offensive spells (§7.2.2).
- **Oculus (row 230, `baserange.scr`):**
  - In reach: 100 % blows. The `Att%` roll still happens in `CanAttack` but changes nothing.
  - Out of reach, per shot: 50 % `BlueLine`, 12.5 % Paralyze, 37.5 % Curse.
  - Shots come only from the shot check (every 1-2.5 s, with the line chance) once recovery has ended.

**Lobber (row 86, class `Lobber` < `AISwimFly`, `lobber.scr`).** It routes its normal shot like AIBase:

- `AISwimFly`'s `CanAttack` (`0x1001c2a0`) only refuses during flyRetreat, and `AISwimFly`'s key handler
  (`0x1001c2d0`) only adds `Flap`.
- Its seven overrides deal with pods:
  - the `CanLob` stat (`+0xfc` → `0x1002a090` → `0x1002a160`);
  - the `LaunchPod` key (`+0x198` → `0x1002a1a0` → `0x1002a1f0`);
  - the pod list (`+0xbcc`, count `+0xbe0`, emptied on `MID_LINKBROKEN`, `+0x194` → `0x1002a0f0`);
  - falling when dead (`+0x26c` → `0x1002a050`), and the rest.
- `lobber.scr` `AttackCheck` runs every 1 s:
  1. If `CanLob` holds, it launches a pod: `PlayAnim LaunchPod`.
  2. Otherwise `CanAttack`. If that is true, the target is within `RangeAttackRange`, and either the line is clear
     or a 25 % roll passes, it calls `RangeAttack`.
- `CanLob` = `0x100b5690` returns any action (alive, not recovering, not blocked) **and** fewer than 5 pods live
  (`cmp eax,5; setb al` at `0x1002a191`).
- The script's 5-10 s pod spacing is dead code: `g_lastLobberLaunch` is never set, so its test always passes
  (`LOBBER.scr:145-160`). A Lobber therefore launches a pod whenever it is ready and has fewer than 5, and shoots
  only while 5 are alive or `CanLob` fails.
- At the `LaunchPod` key, `0x1002a1f0` calls `0x100b3bc0` with type 2 and no target (`0x1002a211`-`0x1002a223`).
  That sets the Lobber's recovery (`now + Recovery`) and frees the result: no damage and no projectile. The pod
  itself is spawned by `0x1002a7d0`.
- **Its shot:**
  - Attack-2 damage (Dark 2D4+1) and the spell Poison N1 (`SpellUse%1` 0, a lone spell) with `Att%` 0: the roll can
    never keep kind 2, so every `RangeAttack` **casts Poison**.
  - `GreenYellowThingy` (`Projectile1`) is fired only when the spell is unavailable (condition 0xc).
  - **OpenYAMM's 100 % Poison Spray matches MM9.**
- **Ice Lobber (row 106, class `IceLobber` < `Lobber`, no overrides of its own):** the same pod logic. Its shot has
  `Att%` 50, attack-2 damage and Elemental Bolt E6, so it is 50 % `BlueThingy2` and 50 % Elemental Bolt.
- **Lobber Pods (84, 85) and the Ice Lobbercicle (105)** are `LobberPod` < `AIGibber` with `lobberpod.scr`
  (BaseCrawl + `Range.inc`).
  - `g_bIsRangeAttacker` is 0 and nothing sets it: the name occurs only in the script, and no placed property or
    data file sets it. So `CanRangeAttack` is overridden to false, and **they only melee**, then evade for
    1.8-2.2 s after every attack (`LOBBERPOD.scr` `AttackDone`, `DoEvade`).
  - The Lobbercicle's `BlueThingy` and its `Att%` 100 are never used.

**What OpenYAMM should do** (data-driven, no world branches):

- **`mm9BlowOrShot`.** For an MM9 walker in reach, return the blow whenever it has one, with no `Att%` roll and no
  ranged choice. Only an actor flagged as holding a ranged weapon should go to the ranged choice in reach. That flag
  would be a profile field from the MM9 model's weapon prop, if the importer records one. Today `Att%` is applied
  twice, and an in-reach shot or spell is possible that MM9 never makes.
- **`mm9RangedAbility` and `mm9RangedSpellSlot`** keep the single out-of-reach rule:
  - spell 1 = T × S1 and spell 2 = T × (1 − S1) / (1 − T × S1), with T = `100 − Att%` (100 without attack-2
    damage) and S1 = `SpellUse%1` as a fraction, then fall through to attack 1's projectile;
  - attack 1 only: no shot.
- **Lobber family:**
  - The Lobber and the Ice Lobber are correct under that rule.
  - Pods first whenever fewer than 5 live and the Lobber is ready, with no 5-10 s spacing.
  - The launch sets recovery like an attack.
  - Lobber Pods and the Lobbercicle: melee-only walkers with a 1.8-2.2 s evade after each attack. Their ranged
    attack and `Att%` should not be used.

### 7.3 Carrying out an attack

- `Attack` (`+0x444` → `0x100134f0`) records `LastAttackTime` (`+0x724`). With a ranged weapon prop →
  `RangeAttack`; with a melee prop → `weaponAttack` (state 5, `0x10013200`); otherwise `handAttack` (state 4,
  `0x100131c0`). It turns to face the target at 540°/s. Completion raises callback 0x1f.
- `RangeAttack` (`+0x48c` → `0x10013270`): faces the target; state 5 with a ranged weapon, otherwise
  `rangeAttack` (state 6, animation chosen by `+0x5b4`).
- `CastSpell` (`+0x434` → `0x1000ecf0`): `castSpell` state; the spell comes from the RPG layer.
- **Damage happens on the animation keys** (`0x1000ed00`): `Attack`, `RAttack`, `LAttack`, `Bite`, `LKick`/`RKick`
  → melee hit; `RangeAttack` → launch (`+0x594` → `+0x6e0` → `0x100187d0`); `Lunge` (`+0x590`); `DoFX`.
- **Melee hit sweep** (`+0x6b8` → `0x1000f3d0`, overridden by `EvilSorcerer`): a swept test (`0x10059b70`) from the
  monster toward the target. Its length is about radius + scale × the `AttackRange` column + the target's radius.
  Only the current target, or a non-actor, can be hit. Hits then go to the RPG damage code.
- **Projectile aim** (`0x100188c3`): the target's centre, raised by (0.3 + 0.8 × rand) × the target's half-height.
  Lead aiming was not found.
- `EstimateRangeAttackHit` (`+0x4c4`) and `IsClearShot` (`+0x4e4`, `0x10016ca0`) cast a ray and return what it hits
  first. The scripts fire only when that is the target, or 20 % of the time when nothing is hit.

## 8. Damage, wince and push-back (`AIBase::OnDamage`, `+0x1b4` → `0x100154a0`)

1. HP ≤ 0 → `Die`.
2. The largest single hit so far is kept in `+0xac4` (used by running away, §9).
3. Push-back (`SetPushBack` `+0x4d8`): from the projectile's object record (force `+0x30`, time `+0x34`), or for
   melee a random horizontal shove of 4 × the monster's radius over 0.25 s.
4. **Wince roll**: chance = 100 when the monster has no record; otherwise `0x10019e00`: **0 if `Always Wince?` = 1**,
   0 while HP > 20 % of maximum, and **20–50 %** (`20 + rand % 31`) once HP ≤ 20 %.
   - Roll succeeds: `OnDamage` (2) goes to the script. If the script does not handle it, the native **Wince**
     (`+0x3f0` → `0x1000df70` → state 8) runs. When the wince ends, the monster returns to idle and `OnDamageDone` (3)
     fires.
   - No roll: `OnDamage`, then `OnDamageDone` at once.
5. The scripts' `OnDamage`/`OnDamageDone` handlers start retargeting (`NewTargetCheck`). `BaseFly` backs off if it
   cannot attack yet.

The column name `Always Wince?` reads as the opposite of what the code does with it. `WinceThreshold` and
`WinceTrackTime` (40 and 0.5 on 135 rows) were never seen to be read. Real-game captures should settle how often
monsters wince.

## 9. Fleeing, hiding, evading

### 9.1 `ShouldRunAway` (`+0x52c` → `0x1001a1a0`)

Every placed actor rolls once, when its properties are read, whether it is a **runner**: `RunawayChance` (default 0.25)
> rand (`0x1000d462`, flag `+0xac8`). In the data, 1,783 actors have 0.25, 256 have 0.05 and 96 have 0. Then:

- dead → no;
- condition 7 (**Fear**) → **yes**, for every monster;
- not a runner → no;
- a runner flees only if it has a **hiding place** (`FindHidingPlace(namedOnly)`, below) **and** one of these holds:
  - it has no ranged attack, cannot reach the attacker (`CanReachObject`) and the attacker is not flying;
  - its HP ≤ 2 × the largest hit it has taken.

Only 183 of the 2,217 placed actors name a `HidingPlace0`, so running away by morale is rare. Fear works everywhere.
The scripts also stop a monster fleeing again within 30 s (`MIN_RUN_AWAY_AGAIN_TIME`). Swimmers (`BaseSwim.inc`)
always "run away" from a target that is not in water.

### 9.2 Hiding places (`+0x520` → `0x10019f00`)

Up to three named objects (`HidingPlace0`–`2`, `+0xab4`). A hiding place is usable when the current target cannot
see it (`+0xac` from the target). If none is usable and the caller allows it, the actor manager's global hiding-place
list is searched (`0x10006d60`, filter `+0x524`). The flight itself is script code (`BaseRun.inc`): run directly away
with a random 15–45° turn and a 100-LT ray to avoid walls, or run to the hiding place. While running it calls `Help`.
It stops after 15 s or beyond 1,000 LT, or cowers if the monster has a `Cower` animation (10 % of runners cower at
once). `IsInNoRunZone` reads the current rail's `NoRunZone`.

### 9.3 Evade chance (`EvadeChance` stat, `+0x538` → `0x1001a290`)

The table value (40 everywhere) is adjusted against the current target. Here D is each side's maximum damage
(character `+0x84`: count × sides + bonus) and HP is current hit points:

| Condition (checked in order) | Result |
| --- | --- |
| Table value 0, or no target | Table value |
| Target's D/2 > my D | 80 |
| 2 × my D > the target's HP (I can kill it in about two hits) | 0 |
| 4 × the target's D > my HP | 80 |
| 10 × the target's D < my HP | Table value / 2 |
| Otherwise | Table value |

What the scripts do with it is in the BaseMelee notes: back off or strafe after an attack (`DoEvade`).

## 10. Friends, enemies and calling allies

- `IsEnemy` (`+0x338` → `0x10018070`): the other actor's class is in my enemy list (`+0x6c8`) and not in my friend
  list (`+0x6c4`); or my character has condition 4 (it attacks everything); or the other is an `AIBase` with
  condition 4.
- `IsFriend` (`+0x33c` → `0x10018130`): yes for null or myself. No if I have condition 4, if I consider it an enemy,
  or if it considers me one. Yes if it has the same class id, or is in my friend list. Otherwise the **default
  relation** `0x100d0990`: **friendly unless one of the two is the Player** (class id 0x131).
- So by default **all monsters are friends of each other and enemies of the party**. Factions come only from scripts:
  `AddEnemy`/`AddFriend`/`RemoveEnemy`/`RemoveFriend <class>` (`+0x54c`…`+0x558`), the `HateAll`/`HateAllOthers`
  triggers (`AICommon.inc`), and the per-area hostility includes (`DookHostility.inc` and 33 others that make guards
  neutral until provoked). The `Hostility Group` column is not used.
- **`SendAlert target`** (`0x10015210`): queues an alert with radius **scale × `AlertRadius`** around the sender
  through the actor manager (`0x100074d0`). Each receiver gets `OnAlert` (0xe) with (sender, target) through
  `0x10015190`. The scripts send an alert from `AlertTick` while they have a target (the interval is the last
  `g_nRandom` value) and from `BackoffDone` in `BaseFly`. A receiver checks `IsFriend(sender)`, then
  `NewTargetCheck`.
- **`Help target`** (`0x10015280`): radius **10 × the sender's half-height** (`0x100eeef0`), queued through
  `0x100075d0`; receivers get `OnHelp` (0xf) through `+0x528` (`0x1001a130`) and join only if they have no target.
  Used while fleeing and hiding.
- No line-of-sight test was seen on alerts or help calls. The actor manager's filter was not fully traced.

## 11. Movement and steering

Covered in detail in the [jump and rails note](../MM9_MONSTER_JUMP_RE.md); here only the AI view.

- `RunTo`/`WalkTo <object>, <range>, <label>` (`+0x450` `0x100112b0`, `+0x44c` `0x10011170`): the destination
  object goes to `+0x624` and the arrival range to `+0x620` (default: the melee range). Then
  `MoveToPos(running)` (`+0x4cc`). Arrival → callback 0x1e. `RunToPos`/`WalkToPos` move to a point.
- Navigation tick (`+0x5bc`, `0x10013a80`): straight at the destination if it can be reached, otherwise along the
  **`AIRail` graph** (depth-first search, `MaxRailPath`) when `UsesRails` (2,129 of 2,217 placed actors; flyers only
  with `FlyerUsesRails`, 9 of 492). There is no navmesh and no A*.
- Per-tick movement (`+0x62c`): a direct move. Less than 80 % of the intended distance → blocked; this raises
  `OnObstacle`/`OnStuck` for the script to handle (the wander, evade and run-away scripts turn by the hit normal).
  Optional cliff and **`AIBarrier`** probes (`CheckForAIBarrier` on 413 actors), and `OnCongestion`/`OnPathClear`.
- Doors: `OnDoor` → `BaseDoor.inc` stops the monster, triggers the door with `Use`, pauses all `Wait` timers for the
  door's opening time, then carries on.
- `Strafe dir, run` (`+0x4f0`): move along a direction while facing elsewhere (strafe and backpedal states). The
  scripts' strafe attack (45° to the target), evasive moves (65° strafes, backpedal at 180° ± 5–35°) and the flyers'
  swoop and back-off are all built from `Strafe`.
- **Flying altitude**: no native altitude-holding code was found. A flyer moves in 3D straight toward its destination
  (`CanReachTarget` is always true). Height changes come from the scripts: `BaseFly` backs off with an up component of
  0.6 when the target is on the ground, swoops in level (`y = 0`) and strafes level. `Launch`/`Land`/`GetAltitude`
  exist as commands, and flyers use `FaceVelocity`.
- **Wandering, home and leash**: script only (`BaseWander.inc`): marker paths (`WanderPathName%d`), or random
  walking for 3–8 s with 3–8 s pauses. The leash (`WanderLeash`, script default 500; placed values are 0 on 2,188
  actors) turns the monster back toward where wandering started. There is **no native return-home**. After losing or
  giving up a target, the monster simply resumes wandering where it stands.

## 12. Death and resurrection

- Death (`Die` `+0x24c`): the death states, the `OnDeath`/`OnDeathDone` events, treasure
  (`TreasureBag … AIDrop 1`), `FadeOnDeath`/`BuryOnDeath`, gibbing for `AIGibber`.
- Resurrection is script-driven (`AICommon.inc`). A dead monster that can be resurrected (`CanBeResurrected` and a
  `Resurrect` animation) sets `WaitForResurrect`. Every 5 s (2 s in turn-based mode) it calls on an `IsResurrecter`
  (`Resurrect` column = 1, 16 rows) within 1,000 LT that targets the same enemy. The resurrecter waits 3–6 s (1–2 s in
  turn-based mode), plays `ResurrectSpell`, and on its `DoResurrection` key sends `Resurrect`. The dead monster plays
  `Resurrect` once no actor is within twice its radius. A resurrecter with nobody to raise it raises itself after
  2–10 s. Others are removed (gibbers stay).

## 13. Cost and update-rate characteristics

| What | How often | Cost |
| --- | --- | --- |
| Actor update (animator, state think, movement, script tick) | Every 0.1 s for every **active** actor | Fixed |
| Target tracking (sight line-of-sight ray to the target) | Every update while a target is set | 1 ray |
| Target search | ≤ 1/s per actor with no target, only if the script registered `OnFoundTarget`/`OnFoundPlayer` | Walks all actors; distance, front and ray tests on up to 50 candidates |
| Within/beyond distance, projectile query | Every update, only if registered | Small |
| Script `Wait` timers | Checked each update | Base melee loop: aggressive tick 0.2 s, speed throttle 0.1 s, range check 1.0–2.5 s (0.2–0.4 s for Type 2), run-away tick 0.3–0.8 s, wander 3–8 s, leash 0.25 s |
| Actor manager queues (alerts, help) | Delivered as object messages | Radius search |

**Sleeping.** The base `ReadProp` (`0x100be940`) gives an object with `AutoDeactivate` a 12 s engine deactivation
time (`SetDeactivationTime(12.0)`). `AIBase`'s `ReadProp` (`0x1000d0e5`–`0x1000d137`) additionally puts it into the
engine's auto-deactivate state at once (object state `|= 3` through `0x100bd940`), except when it is spawned at run time
(`0x1028e450`, set around `CreateObject` at `0x1007ff7e`). It records this in `+0xb40`. LithTech then gives no
`MID_UPDATE` to an inactive object until a client is near it, so far monsters cost nothing. The engine's exact wake rule
(which region or distance) is inside the LithTech server, not `object.lto`, and was not traced. There is no other LOD
in the AI: a monster that is awake runs the full loop at 10 Hz.

## 14. Native or script: who does what

### 14.1 Script commands and their native handlers

The AI command factory is at `0x10097835`–`0x10099338` (`script_cmd_factory.txt`); the general command factory
(`Wait`, `PlayAnim`, `GetStat`, `SetStat`, …) is around `0x1009f9a6`–`0x100a2400`. Each command is an object with a
vtable: slot 1 parses the arguments, slot 2 runs it. `0x10097730` returns the owning actor.

| Command | Handler | Native call | Notes |
| --- | --- | --- | --- |
| `RunTo`, `WalkTo`, `RunToPos`, `WalkToPos` | `0x100995a0`, `0x100994b0`, `0x1009a2e0`, `0x1009a140` | `+0x450`, `+0x44c`, `+0x4cc` | Arrival callback 0x1e |
| `Run`, `Walk`, `Stop`, `Strafe`, `Jump`, `Launch`, `Land` | `0x10099d80`, `0x10099d10`, `0x100ab950`, `0x1009ae50`, `0x10099db0`, `0x10099ff0`, `0x1009a080` | `+0x4b4`, `+0x4b0`, `+0x4f0`, `+0x4bc`, `+0x2d8`, `+0x2dc` | |
| `Attack`, `RangeAttack`, `CastSpell` | `0x10099670`, `0x10099de0`, `0x100999e0` | `+0x444`, `+0x48c`, `+0x434` | Done callback 0x1f |
| `CanAttack`, `CanRangeAttack`, `IsTargetInRange`, `IsAttacking` | `0x10099b10`, `0x1009b790`, `0x10099b40`, `0x10099b70` | `+0x480`, `+0x4c0`, `+0x4a0`, `0x10001f60` | §7.2 |
| `EstimateRangeAttackHit`, `IsClearShot`, `CastRay` | `0x10099e80`, `0x1009a9d0`, `0x1009b010` | `+0x4c4`, `+0x4e4`, `+0x378` | |
| `Target`, `GetTarget`, `FindTargets`, `SetTargetLostTime` | `0x10099aa0`, `0x10099e10`, `0x1009a7d0`, `0x1009a580` | `+0xa8`/`+0x440`, `+0x110`, `+0x4e0`, `+0x608` | |
| `CanReachTarget`, `CanReachObject` | `0x1009aec0`, `0x1009b3d0` | `+0x478`, `+0x47c` | |
| `ShouldRunAway`, `FindHidingPlace`, `IsInNoRunZone`, `IsFear` | `0x1009b470`, `0x1009b150`, `0x1009b7c0`, `0x100018c0` | `+0x52c`, `+0x520`, `+0x564` | §9 |
| `SendAlert`, `Help` | `0x10099ed0`, `0x1009b340` | `0x10015210`, `0x10015280` | §10 |
| `IsEnemy`, `IsFriend`, `AddEnemy`, `RemoveEnemy`, `AddFriend`, `RemoveFriend` | `0x1009ac20`, `0x1009acc0`, `0x1009b620`… | `+0x338`, `+0x33c`, `+0x54c`…`+0x558` | |
| `Taunt`, `Aware`, `Wince`, `SetIdle`, `SetStuck`, `Die` | `0x10099780`, `0x10099820`, `0x1009b600`, `0x10099740`, `0x10099760`, `0x100993b0` | SetState `+0x240` (9, 10, 8, 0, 11), `+0x24c` | Callbacks 0x20, 0x22 |
| `BlendAnim`, `PlayAnimSound`, `AttachProp`, `DetachProp`, `SetPushBack`, `SetCrouch` | `0x1009b5a0`… | | Presentation |
| `On…` event registrations | `0x1009f900` (general), `0x1009ab20` (`OnFoundTarget`), `0x1009abe0` (`OnProjectile`), `0x1009a5b0`/`0x1009a670` (within/beyond distance) | `0x1009dcf0` | §4.3 |
| `GetStat`/`SetStat` on actors | `0x100abfa0`/`0x100ac2e0` | `AIBase` stat tables `0x10018b60`, `0x10018f29`… | `RunVel`, `AttackRange`, `RecoveryTimeLeft`, `EvadeChance`, `StrafeAttackPct`, `VisibleRange`, … |

### 14.2 The split

| Behaviour | Native | Script |
| --- | --- | --- |
| Update loop and rate | ✔ 0.1 s, state machine, script tick | |
| Sight, hearing, field of view, line of sight | ✔ | Doubles the ranges after first contact |
| Acquiring a target (nearest perceived non-friend) | ✔ 1/s, only if a handler is registered | Reacts: taunt, alert |
| Losing a target (8 s unseen) | ✔ | Give up after 30 s without combat |
| Switching to an attacker | | ✔ 70/45 % rule |
| Attack range, readiness, recovery | ✔ (RPG layer) | Times its approach |
| Choosing melee, ranged or spell | ✔ spell-use roll; spell ammo and conditions | ✔ when to shoot (Range.inc), chance from the clear-shot test |
| Carrying out the attack, hits, projectiles | ✔ | Starts it (`Attack`/`RangeAttack`) |
| Chase, stop, strafe attack, evade, backpedal | Primitives (`RunTo`, `Strafe`, `Stop`) | ✔ all the decisions |
| Flyer swoop and back-off, altitude changes | Primitives | ✔ |
| Wince | ✔ roll and state | Can take over through `OnDamage` |
| Running away | ✔ decision inputs (`ShouldRunAway`) | ✔ the flight, hiding, cowering |
| Evade chance | ✔ threat-adjusted value | ✔ the roll and the move |
| Calling allies | ✔ broadcast within the radius | ✔ when to call; the receiver's decision |
| Factions | ✔ default player-versus-monsters and class lists | ✔ `AddEnemy`, hostility includes |
| Wander, leash, patrol markers | | ✔ |
| Doors | ✔ detection | ✔ opening and pausing |
| Resurrection | ✔ flags and animations | ✔ the protocol |
| Sleeping far actors | ✔ engine auto-deactivation | |

## 15. The base combat scripts in brief

Which script a row uses is given in §2.2. All numbers come from the `.inc` files.

- **BaseCrawl** (four-legged, `basecrawl.scr`) and **BaseMelee** (`basemelee.scr`, and `baserange.scr` with
  `Range.inc`): the aggressive tick every **0.2 s**. Out of range → `RunTo` the target (stopping at 0.95 × range)
  if it can reach it (re-checked every 0.4 s) and if recovery would be over on arrival. In range and ready →
  `PreAttack` (face at 360°/s, follow; if the target moves beyond 0.7 × range, run after it) → `Attack` → attack tick
  every 0.2 s (chase a moving target, stop for a still one). The speed throttle every 0.1 s matches the target's speed
  inside 0.9 × range and adds ×1.25 while lunging. BaseMelee adds a **strafe attack** after the swing starts
  (`StrafeAttackPct`, at 45°, only when moving and the target is still) and the **evade** after the attack
  (`EvadeChance`: backpedal or strafe, ending after 2 s or beyond 500 LT; otherwise a backpedal for 0.3 s, then a
  taunt 40 % of the time). A full description of this loop is in the
  [animation blending note](../MM9_ACTOR_ANIMATION_BLENDING_RE.md#basemelee-combat-loop).
- **Range.inc**: Type 1 (default; 2,184 placed actors) prefers melee and shoots when it is beyond melee range and
  within `RangeAttackRange`. The check runs every 1.0–2.5 s with a chance of 100 % (clear shot), 20 % (nothing hit),
  15 % (a world object in the way) or 0 % (an actor in the way). It does not run after a target if it has not shot
  for 5 s and has a clear shot. Type 2 (`RangeAttackType 2`, 33 actors, the Evil Sorcerers) stays put, checks every
  0.2–0.4 s and only melees within 3 × melee range. The Type 2 hide-after-shot code is disabled ("Killed it on
  2/18/2002").
- **BaseFly** (`basefly.scr`) and **FlyRange**: aggressive tick 0.2 s. In range and ready → strafe attack at ±45°
  past the target; not ready → **back off** (away and upward at y = 0.6 for 1 s), then alert allies and **swoop in**
  at 30–50° for 1 s. Attack flying speed is capped at 200. FlyRange shoots after backing off, or from the range check
  every 0.3–1.3 s (60 % chance, clear shot, at least 2 s apart).
- **BaseSwim** (`BaseSwim.scr`): BaseCrawl, but it treats any target that is not in water as one to run from. With the
  native rule that swimmers only target things in water, this keeps swimmers in water.
- **NPCBase**: wander, flee from attackers and projectiles, walk over to talk to other NPCs (`Converse`), and the
  dialogue (RUDE) pauses the script.

## 16. What could not be traced

- Readers of `WinceThreshold` (record `+0x28`) and `WinceTrackTime` (`+0x24`): none found, through either the actor's
  record pointer or the record lookup functions. They may be unused, or read through a path not found.
- The intent of the `Always Wince?` byte (1 → wince chance 0), and whether scripts wince those monsters themselves.
- Recovery, interrupted attacks and turn-based scheduling are decoded in §7.2.1; spell choice, `RangeAttack` and
  `concat` in §7.2.2; in-reach and out-of-reach rolls and the Lobbers in §7.2.3. Still open:
  - what the target's `+0x328` check is (it blocks attack 2), and which damage a type-1 blow and a type-2 shot use;
  - which monsters hold a ranged weapon prop (`+0x514`, prop `+0x23c` true), the only case of an in-reach shot
    (§7.2.3); the Lobber family is decoded there;
  - where the Lobber increments its pod count (`+0xbe0`; probably in `0x1002a7d0`).
  - that the party's player object is in the actor manager's list `FindTargets` walks: assumed, because the base
    scripts register only `OnFoundTarget` (§5.1), but the registration was not traced;
  - whether the RPG layer freezes a Paralyzed monster's model mid-clip;
  - which object type 1 is in the turn check's other-actor branch (`0x100b59e8`);
  - what the second turn-based list (`0x100548a0`) holds.
- The actor manager's filters for alert and help receivers (`0x100074d0`, `0x100075d0`, `0x10007396`), and the global
  hiding-place filter (`+0x524`, `0x1001a020`).
- LithTech's wake rule for auto-deactivated objects (engine side).
- `DragonKing`'s own perception and breath code (20 overrides, `0x1003be50`…) was not read; nor were the `GiantBase`
  rock throw or the `Lobber` details.
- Projectile lead aiming: none seen in `0x100187d0`, but `+0x6ec` (direction building) was not read in full.
- Whether the placed object's `ScriptName` or the record's takes precedence when both are set.

## 17. What this means for an OpenYAMM base AI

A faithful native base AI should reproduce the native layer exactly and turn the base scripts into native code (they
are small, timer-driven state machines):

1. 10 Hz think; sleep when far from the party (MM9 relies on engine deactivation); search for targets at 1 Hz, and
   only for monsters that react to targets.
2. Perception: sight radius with a front half-space and a line-of-sight ray; hearing radius, also with line of sight;
   both doubled after first contact with the party. Lose the target after 8 s unseen; give up after 30 s without
   combat.
3. Target: the nearest perceived non-friend. Switch to an attacker 70 % of the time (45 % if the current target is in
   range; halved if the attacker is farther). Monsters are friends of each other unless scripts or factions say
   otherwise.
4. Attack range from `AttackReach` and body size; hit reach from `AttackRange` × scale; readiness from the RPG
   recovery (`Recovery` × 33 ms after the end of the attack clip, §7.2.1); arrive as recovery ends.
5. The BaseMelee (strafe and evade), Range Type 1/2, BaseFly (swoop and back-off) and BaseSwim patterns, with the
   timers and percentages in §15 and the threat-adjusted evade chance in §9.3.
6. Wince only at low HP (20–50 % once HP ≤ 20 %), never for `Always Wince?` = 1 rows; push-back on hits.
7. Flee on Fear always; otherwise only runners (25 %) with a hiding place, when hurt (HP ≤ 2 × the largest hit) or
   unable to reach a ground attacker.
8. Alerts within scale × `AlertRadius` (1200) to friends; help calls within 10 × half-height while fleeing.

## Working files (`re_mm8/work/mm9_ai/`)

| File | Content |
| --- | --- |
| `actor_classes.txt` | All 289 actor ClassDefs with parent chain, size, construct function |
| `class_ids.py` → `class_ids.txt` | Class id, C++ constructor and vtable of each class |
| `vtables.py`, `class_vtables.py`, `vt_diff.py` → `vt_overrides.txt`, `vt_real_overrides.txt` | Vtable overrides against the parent |
| `factory.py` → `script_cmd_factory.txt`, `all_stricmp_sites.txt` | Script command factories: name → command vtable → handler |
| `cmd_slots.py` → `cmd_slots.txt` | Which `AIBase` slot each AI command calls |
| `event_ids.py` → `event_ids.txt`; `fire_event_sites.txt` | Script event ids and where the native code raises them |
| `monster_record.py` → `monster_record_columns.txt` | `MONSTERS.txt` column → record offset |
| `recuse.py` | Finds code reading given record fields |
| `strxref.py`, `aibase_strings.txt` | String references in a code range |
| `survey_ai_props.py` → `ai_prop_survey.json` | AI properties of the 2,217 placed actors in all `WORLDS/*.dat` |
| `aibase_update_1000e2e0.asm`, `f_10012d50_targets.asm`, `f_10006be0_findtargets.asm`, `f_100153f0.asm` | Disassembly extracts |
