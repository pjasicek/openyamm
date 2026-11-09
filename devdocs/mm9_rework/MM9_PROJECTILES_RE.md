# MM9 projectiles: what `PROJECTILE.txt` does (native RE)

Research note, 2026-11-06. Binary: `mm9/game/data/object.lto` (SHA-256 `b1271f37e5314281…`, image base
`0x10000000`), disassembly `re_mm8/work/mm9_collision/object_lto.asm`, decompiles and helper scripts in
`re_mm8/work/mm9_projectiles/`. The client `cshell.dll` (SHA-256 `678700ff1cc795ae…`) parses the same table with the
same layout (`0x10043153`) and was checked for homing. **Verified** = read in the instructions; **inferred** = from
the decompile, LithTech API order or data, not traced to the end.

## 1. The loader and the record

`0x100418a0` opens `data\projectile.txt` and reads up to 100 rows by column position (`0x10056c90(i)`). Each row is a
`0x84`-byte record; `0x100408b0(id)` returns it (`table + 0x21374 + id × 0x84`). The projectile object keeps its record
pointer at `+0x584` (set by `SetProjectileId`, vtable `+0x22c` → `0x100c73c0`). Offsets below are from the record
start (verified, `0x1004196f`-`0x10041d25`):

| Col | Column | Record | Read by |
| --- | --- | --- | --- |
| 2 | range (ft) | `+0x10` ×12 | AI attack range only (`0x1000dda0`, native AI RE §7.1); not in flight |
| 3 | damageRadius (ft) | `+0x18` ×12 | blast radius (`0x100c7260`, `0x100b9acd`) |
| 4 | velocity (ft/sec) | `+0x1c` ×12 | launch (`0x100c8570`), each update (`0x100c8ac0`), lead solve (`0x100c8cd0`) |
| 5 | lifetime (sec) | `+0x20` | expiry (`0x100c7650`) |
| 6 | Gravity | `+0x24` byte | sets object flag `0x20000` at launch (`0x100c86c7`) |
| 9 | Player Explosion Backoff | `+0x80` (0 → 50) | explosion effect placement (`0x100c7f00`) |
| 11, 12 | PushBackVel (in), PushBackTime | `+0x30`, `+0x34` | monster push-back (`0x100155a9`) |
| 13-15 | Can Detonate, Add Actor Vel, Low Bandwidth | `+0x38`…`+0x3a` | `0x100c8990`, `0x100c864f`, `0x100c83b6` |
| 16-20 | EQ Radius … EQ Decay Rate | `+0x3c`…`+0x4c` | camera shake (`0x100c8a70`) |
| 21-25 | HS Dist, HS Angle, HS Straight Dist, HS Turn Rate, HS Seek Interval | `+0x50`…`+0x60` | **nothing** (§5) |
| 26 | HS Use LOS | `+0x64` byte | **nothing** (§5) |
| 27 | Min Radius Pct | `+0x68` | blast falloff (`0x100b9940`) |
| 28 | Can Hurt Self | `+0x6c` byte | blast (`0x100b9995`) |
| 31, 32 | Bounce Count, Bounce Dampen | `+0x70`, `+0x74` | touch handler (`0x100c7995`, `0x100c79c9`) |

## 2. Units (verified)

The loader multiplies **only** range, damageRadius and velocity by the float at `0x100eef04` = **12.0**
(`0x100419f4`, `0x10041a0f`, `0x10041a2a`). So 1 ft = 12 LithTech units (consistent with NPCBASE.inc's 1200 = 100 ft)
= 30.72 OpenYAMM units. Every other column is used raw: HS Dist, EQ Radius and PushBackVel are already in LT units
(inches), times in seconds. Examples: FireBolt/DragonFireBolt radius 25 ft = 300 LT = 768 OY, speed 125 ft/s = 1500 LT/s
= 3840 OY/s; push-back 300 in/s for 0.5 s.

## 3. Flight

- **Launch** (`Setup` `+0x230` → `0x100c7440`, then `+0x280` → `0x100c8570`): direction normalised; velocity =
  speed × direction, plus the shooter's velocity when `Add Actor Vel` is set (verified).
- **Every update** (`+0x188` → `0x100c7650`): when now ≥ launch time + lifetime, the projectile detonates where it is,
  with no struck object (verified). Then `0x100c8ac0` re-sets the velocity to speed × the object's forward vector
  (or toward a homing target, §5). Speed stays constant.
- **Range is not checked in flight.** In the table range = velocity × lifetime on almost every row (Arrow 200 × 5 =
  1000, FireBolt 125 × 5 = 625), so lifetime is what ends the shot; range is the monster's ranged-attack distance.
- The monster launch is `0x100187d0` → spawn `0x100caad0` (class from the record's class name, `SetAttackInfo`
  `+0x238`, `Setup`).

## 4. Impact and the blast

Chain (verified): touch `+0x190` → `0x100c7700` (bounces while `Bounce Count` lasts) → `HandleImpact` `+0x284` →
`0x100c7d60` (once only, flag `+0x494`) → effect `+0x268`, then `ImpactDamage` `+0x278` → `0x100c7c90` with the
struck object (the world counts as an object), the impact point and a base damage of **0** (`0x100c7ebb`).

`ImpactDamage` (`0x100c7c90`):
- radius 0: `DamageObject` (`0x100b95b0`) on the struck object only; nothing when there is none (expiry).
- radius > 0: `DamageObject` on the struck object (if any), then `AreaDamage` (`0x100b9900`) around the impact point
  with the struck object **excluded**, so it is hit once. A wall, floor or expiry blast still runs `AreaDamage`.

`AreaDamage` (`0x100b9900`, verified):
1. Objects from the server's sphere query (`ILTServer+0xb0`, inferred `FindObjectsTouchingSphere`) at the impact point.
2. Skipped: the shooter (`+0x4a4`, or the projectile when it has none) unless `Can Hurt Self`; the projectile itself;
   the excluded struck object; every object of class `NPC` (`0x1003d480`); an `Actor` whose `+0x320` (active) is false.
3. d = distance from the impact point to the object's **position** (centre), at least 1. Only d < radius counts.
4. Damage (the only falloff formula): min = base × `Min Radius Pct`; if min ≠ base,
   `damage = (base − min) × (1 − d / damageRadius) + min` — linear from base at the centre to base × pct at the edge.
5. Push direction = unit vector from the impact point to the object; then `DamageObject` with that damage.
6. **No line-of-sight test**: the blast reaches through walls and floors.

**Why the falloff never matters (verified).** The base damage from `HandleImpact` is 0, so min = base = 0. The real
hit comes from the attack info the launcher attached (`+0x478`, present for monster and spell launches):
`DamageObject` fills the victim (party character `0x10054ea0`, or the actor's sheet `+0x36c`) and calls the RPG attack
`0x100b5300` (`0x100b46c0` for kind `0x32`), whose result **replaces** the damage (`0x100b97e9`). That RPG attack does
not see the distance or the falloff value (its distance argument is unused), so **every victim in the radius takes
one full, normally resolved attack**. The engine message then carries 0 (10 for a non-character such as a prop).
`Min Radius Pct` only acts for the beam classes (`CBlueLine`, `CYellowLine`, `CRedLine`, `CLightning`, `CPurpleThingy`:
override `0x100c9a30` adds a caster bonus to the base), and those rows have radius 0. In the shipped data it is dead.

**Who the blast hurts** (verified gates, inferred RPG outcome): the party, and actors. In `0x100b5300`, when both
sides are monsters and the attacker's `IsFriend` (`+0x33c`) says the victim is a friend, there is no damage, unless the
victim is the attacker's current target (`+0x110`). Monsters are friends by default (native AI RE §10), so a
monster's blast hurts the party and only monsters it is hostile to. Its own blast: `IsFriend(self)` is true, so
`Can Hurt Self` = 1 (most rows) has no effect for monsters (inferred). Party-owned shots never hurt `NPC` objects.

**Push-back** (`AIBase::OnDamage` `0x100154a0`, verified at `0x1001559c`): when the damager is a projectile, the
monster is pushed at `PushBackVel` × the damage direction for `PushBackTime` s: flight direction for a direct hit,
outward from the centre for a blast victim. Only the FireBolt rows (300, 0.5) and KBYellowLine (600, 0.5) have one.

## 5. Homing

**The `HS *` columns are loaded and never read** (verified as far as a search can show): no instruction in
`object.lto` or `cshell.dll` reads record `+0x64` (`HS Use LOS`), no access to `+0x50`…`+0x60` was found through the
record pointer (`+0x584`, `0x100408b0`, `0x100423c0` in the client, stack copies), and the classes of the rows that
carry them (`CRedThingy`, `CGoo1`, `CScreamingSkull`, `CIceblast`, `CElemental*`, `CPurpleThingy3`, `CCrossBowBolt`)
override nothing that steers (vtable diff, `re_mm8/work/mm9_projectiles/vtables.txt`). RedThingy, Goo1-3, Iceblast
and ScreamingSkull fly straight in MM9.

The only steering: `Setup` takes an optional target character (8th spawn argument). When given, it aims at it and
stores it (`+0x4a8`); every update `0x100c8ac0` points the velocity straight at the target's position at full speed
while the target has object flag `0x2000` (inferred `FLAG_SOLID`): an unlimited turn rate, no cone, no delay, no sight
check. Monster weapon launches pass no target (`0x10018b32`). Spell casts (`0x1008ab80`, a slot in every spell
vtable) pass their target; whether monster spellcasting fills it was not traced.

## 6. Side finding: aim lead

The monster's aim builder `0x100184e0` (from the launch) branches on record byte `+0x7c`, which the MONSTERS.txt
loader sets to 1 on every row (`0x10044649`). The taken branch calls `0x100c8cd0`: an intercept solve with the
projectile speed, using the target's velocity × (rand × `Accuracy`) (`0x100185aa`-`0x100185b0`). `Accuracy` is
blank on all 285 rows, so the lead is always 0: MM9 aims at where the target is (native AI RE §7.3 holds). The
other branch (random spread of ±`Accuracy` degrees) is dead.

## 7. What this means for OpenYAMM

- A missile with an explosion radius: on any impact (actor, wall, floor) and on lifetime expiry, attack every
  eligible target whose centre is within the radius, with no line-of-sight test. The struck target is attacked once.
  Each victim gets the full attack with its own roll. MM9 has **no distance falloff in effect**; an optional edge share
  would be our own feature (MM9's dormant formula: linear from 100 % at the centre to pct at the edge).
- Eligibility to mirror: skip the shooter, skip friends of a monster shooter (except its target), skip NPC-class
  townsfolk.
- Homing: implementing turn rate, cone, straight run, seek interval or sight from `HS *` would add behaviour MM9 never
  had. Faithful MM9 is straight flight; the one native homing is a targeted spell that re-aims fully every frame.
- Range should drive the AI's attack distance; lifetime (≈ range / speed) should end the flight.

## 8. Open questions

- The exact meaning of object flag `0x2000` and `ILTServer+0xb0` (sphere query by bounding box or by centre).
- Whether monster spell casts pass a target to `0x1008ab80` (would make some monster spells home).
- The attack handlers behind `0x10089110` (to-hit and resistance per blast victim) were not read.
