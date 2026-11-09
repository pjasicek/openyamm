# MM9 water and swimming (reverse engineering)

How Might and Magic IX (LithTech Talon, 2002) defines water, moves the party through it (wading, swimming, diving,
surfacing, climbing out), times breath and drowning, changes the screen and sound under water, and moves monsters in
it. From the shipped binaries and the DAT worlds. Research date 2026-10-31, Rizin 0.10.0 + rz-ghidra `pdg` and
`objdump -M intel`. The integration design is [MM9_WATER_SWIMMING_DESIGN.md](MM9_WATER_SWIMMING_DESIGN.md).

| Binary (`mm9/game/`) | SHA-256 | Role here |
| --- | --- | --- |
| `data/cshell.dll` | `678700ff…f82f7ae` | client: the party's movement (movers), container tests, camera tint/fog, sounds, breath meter |
| `data/object.lto` | `b1271f37…7bc37f162` | server: `VolumeBrush` classes, their physics on monsters, breath timer and drowning damage, swimmers |
| `lithtech.exe` | `4e9ddd2b…dd39e56d8` | engine: containers (`GetPointContainers`, `GetContainerCode`) |

Work files (git-ignored): `re_mm8/work/mm9_water/` (`cshell.rzdb`, `cshell.asm`, `object.asm` → the collision study's
listing, `dis.sh <asm> <from> <to>`, `rd.py` for constants and strings, `classdef.py` for class chains,
`dat_water_volumes.py`/`.txt` and `dat_swimmers.py` for the DAT side). Both DLLs have image base `0x10000000` and file
offset = VA − `0x10000000`. The reference engine/game sources in `mm9/lithtech/` (Shogo, NOLF) were read for the
shared LithTech names; MM9's code is checked against the binaries, not assumed from them.

Units: LithTech (LT), y up. Ours = LT × 2.56 (z up). Speeds below are given as LT/s and in our units (u/s).

## Summary

- **Water is a brush volume** (`VolumeBrush` subclasses `BlueWater`, `DirtyWater`, `ClearWater`, …; container codes
  1–6 are liquids). Properties: `Viscosity`, `Current`/`CurrentPower`/`CurrentRadius`/`CurrentSource`, `Damage`/
  `DamageType`, `FogEnable`/`FogNearZ`/`FogFarZ`/`FogColor`, the surface's look. Gravity in water is a hidden
  constant, −200 LT/s². No gravity or friction property exists in any DAT.
- **The party** has no momentum in water: each frame its velocity is set from the keys. Under water (head point in a
  liquid): forward/back follow the full look direction (pitch included), strafe the camera's right, **Jump = up,
  Crouch = down**, all at the **swim speed 150 LT/s = 384 u/s** (the same as walking; no run bonus). With no key held
  it **sinks at 40 LT/s = 102 u/s** (gravity × 0.2). Gravity is off.
- **On the surface** (head out after having been under): no vertical drift, it cannot rise further; looking down while
  moving forward, or Crouch, dives. **Jump launches out of the water** with the land jump velocity (275 LT/s = 704 u/s)
  and gravity on, with air control 150 LT/s forward, 75 back and sideways.
- **Wading** (body in water, feet on a floor) is plain walking: same speeds, no slowdown. A body that falls into deep
  water falls with normal gravity until the head goes under.
- **Breath: 15 seconds** with the head under water (the HUD meter drains 100 → 0). Then every 2 s a drowning sound and
  **each party member loses 1/6 of maximum HP**. Surfacing refills breath at once. There is no Water Breathing spell
  or item in MM9.
- **Screen**: a per-liquid light-scale tint (BlueWater (0, 0.5, 0.7)), the volume's own fog if it has `FogEnable`, a
  wobbling field of view, `ModelWarble 1`, a looped `Sounds\Player\unwater2.wav`, `WaterSplash.wav` when the head goes
  under, `out_water.wav` when it comes out.
- **Combat**: ranged weapons are not fired while the head is under water. No spell restriction was found, and the
  water's physics does not touch projectiles.
- **Monsters**: swimmers (Sea Monsters, Jelly/Gelatinous/Nettle Spores, Fish) are `AISwimFly`, the same class as the
  flyers, placed with `Gravity 0, MoveToFloor 0`, moving at their `FlyVelocity` (200 LT/s = 512 u/s for Sea Monsters
  and Spores). Walking monsters in water are slowed by the viscosity (velocity × 0.5 per physics update) and sink at
  the liquid gravity.

## 1. Water in the world: the volume brushes

### Classes and container codes (`object.lto`)

The class definitions sit in `.data` (`name, parent, …, constructor, destructor, prop count, props, size`):
`VolumeBrush` at `0x101a6558` (constructor `0x1008eff0`, object size `0x6c0`), `BlueWater` `0x101a65e8` (constructor
`0x10090950`), `DirtyWater` `0x101a6618` (`0x10090cd0`), then `ClearWater`, `CorrosiveFluid`, `Kato`, `LiquidNitrogen`,
`PoisonGas`, `Electricity`, `EndlessFall`, `ZeroGravity`, `Vacuum`, `Ladder`, `TotalRed`, `TintScreen`,
`DamageBrush`, `PortalZone`, `SoftLandingZone` (name strings `0x101a6584`–`0x101a6a70`). This is Shogo's set, and the
codes are Shogo's `ContainerCodes.h`:

| Code | Class | Liquid | In the MM9 DATs |
| --- | --- | --- | --- |
| 1 | BlueWater | yes | 70 volumes |
| 2 | DirtyWater | yes | 6 |
| 3 | ClearWater | yes | 14 |
| 4 | CorrosiveFluid | yes | 0 |
| 5 | Kato (lava in MM9: `lavasplash.wav`, `out_lava.wav`) | yes | 0 |
| 6 | LiquidNitrogen | yes | 0 |
| 14 | Ladder | no | 68 |
| 18 | VolumeBrush (the base, `CC_VOLUME`) | no | 1 (Lich Lab's `PromoVol1`) |

`BlueWater`'s constructor `0x10090950` calls the base constructor `0x1008f060`, then sets code 1 (`[esi+0x588] = 1`)
and flag `0x1000`. Every "is it a liquid" test in both DLLs is `0 < code ≤ 6`.

### Properties (`object.lto 0x1008f600`, `0x1008f6d0`; base constructor `0x1008f060`)

| Field | Property | Default | Use |
| --- | --- | --- | --- |
| `+0x564` | `Viscosity` | 0 | clamped to 0..1, then stored as `1 − v` (`0x1008f3c3`…`0x1008f41a`): the factor velocities are multiplied by |
| `+0x534` | `Current` | 0 | vector added to a body's velocity |
| `+0x598`, `+0x5a8`, `+0x5ac` | `CurrentSource`, `CurrentPower`, `CurrentRadius` | — | a pull toward a named object, `Power × (Radius − d)/Radius` inside `Radius` (`0x1008fe86`…`0x1008ffc1`) |
| `+0x568`, `+0x584` | `Damage`, `DamageType` | 0 | damage to bodies inside, once a second per body (`0x100900dd`…`0x1009023e`) |
| `+0x570` | (no property) | **−200.0** | liquid gravity, `0x1008f14f` |
| `+0x56c` | `SurfaceHeight` | 5.0 | thickness of the drawn surface |
| `+0x574/578`, `+0x558`, `+0x590` | `FogFarZ`, `FogNearZ`, `FogColor`, `FogEnable` | 300, −100, black, off | the camera fog while the head is inside |
| `+0x58c`, `+0x594` | `ShowSurface`, `Hidden` | | surface sprite on; a hidden volume does nothing |
| | `SpriteSurfaceName`, `SurfaceColor1/2`, `SurfaceAlpha`, `X/YScale*`, `NumSurfacePolies`, `SpinRate` | | the surface's look |
| `+0x588` | `Code` | 18 | container code (set by the subclass) |

MM9 adds `CurrentSource/Power/Radius`, `SpinRate` and script hooks to Shogo's list. `ScriptName` scripts drive some
volumes: `DrainWater.scr` moves the whole volume up or down at 10 LT/s (Verhoffin Ruins' `WaterTrap`, Bathhouse's
`BlueWater2`), `DP2waterdamage.scr` switches `Damage`/`DamageType DT_BURN` on and off (Bathhouse's boiling water),
`TM_SteamWater.scr` (Training Hall).

### What the DATs hold (`dat_water_volumes.txt`)

90 liquid volumes in 35 worlds. Every one has `Viscosity 0.5`, `Damage 0` and `BoxPhysics 1`; 68 have no current.
Depths (the brush's vertical extent; the bed under it can be shallower):

| Map | Volume (class) | Depth LT → u | Fog | Notes |
| --- | --- | --- | --- | --- |
| Verhoffin Ruins | `BlueWater0`, `BlueWater1` (crevasse) | 143 → 366 | off | TreasureChest0 on the bed |
| | `WaterTrap` | 192 → 492 | off | `DrainWater.scr`: rises and drains |
| | `ElectricWater1` (pit) | 128 → 328 | off | damage from a separate `ElectricDamager1` |
| Dark Passageway | `BlueWater0` (bridge lake) | 512 → 1311 | off | |
| | `TubeRoomWater` (Dirty) | 448 → 1147 | off | `Current (0,−90,0)`, `CurrentPower 1500`: pulled down the tube |
| | `TubeRoomWater0` (Dirty), `Ocean` | 352 → 901, 396 → 1014 | off | Sea Monster M/F |
| Bathhouse | `WaterthatBoilsA/B` | 540–606 → 1382–1551 | off | `DP2waterdamage.scr` (burn) |
| | `BlueWater2` | 322 → 824 | off | `DrainWater.scr` |
| | 9 more pools | 6–113 → 15–289 | off | wading |
| Beethoven | `GrandEntrance Water` (Clear) | 368 → 942 | off | `Current (−1,0,0)` (below the threshold, no effect) |
| | 6 baths | 20–60 → 51–154 | off | wading |
| Dook's Castle | `ClearWater0` | 608 → 1556 | 500–2000, black | chest on the bed |
| Dungeon of Secrets | `ClearWater0` | 272 → 696 | off | |
| Training Hall | `BlueWater0` (pole room), `BlueWater1` | 168 → 430, 48 → 123 | off | |
| Yanmir's Fort | `BlueWater0` | 80 → 205 (bed ≤ 62 LT) | −100–300, (0,64,128) | wading only |
| Inventa Storca | `BlueWater0/1/2` | 320–384 → 819–983 | off | swim down `BlueWater2`, up the well |
| 1000 Terrors | `BlueWater0–6` | 117–160 → 300–410 | three with fog | 2 Sea Monsters, weighted lifts under water |
| Lich Lab, Thjorad Mine | 4 × 96, `DirtyWater1` 256 | 246, 655 | Thjorad: on | |
| Isle of Ashes | `BlueWater0` (sea, 720 polys) | 384 → 983 | off (colour set) | 10 Jellyspores |
| Sturmford, Thronheim, Thjorgard, Guberland, Yorwick, Drangheim, Frosgard City | the sea/lakes | 232–544 → 594–1393 | on, dark blue | Thjorgard's rivers: `Current (0,0,−96/−128)` |

## 2. The party in water (`cshell.dll`)

### State and tests

The client move manager is the singleton `[0x100df848]` (vtable `0x100c9490`, constructor around `0x100977c7`). Each
frame `0x10099270` updates the containers and picks one **mover**: a stateless object with `OnEnter`, `Update`,
`GetName` and helpers (vtable slots 0, 2, 3; slot 5 `+0x14` applies the velocity, slot 6 `+0x18` gives flattened
camera vectors, slot 7 `+0x1c` full ones).

| Field | Meaning | Set by |
| --- | --- | --- |
| `+0x1590` | **body in liquid**: the body's box touches a code 1–6 volume | `0x10098a30` → `0x10098980` |
| `+0x1584` | **head container code**: the code at one point, the box top minus 10 LT | `0x100ab8a0` (`GetPointContainers`, `+0x32c`) |
| `+0x1594` | on a ladder (code 14) | `0x100989d0` |
| `+0x1580` | standing on a floor | collision |
| `+0x1599` / `+0x1598` | was submerged / **on the surface** | `0x10099339`…`0x10099352` |
| `+0x159a` | surface jump in progress | `0x10099df0` |
| `+0x15c8`, count `+0x1670` | up to 6 container records from the server: code, `Current`, gravity, hidden, a byte | message reader `0x10098690`/`0x10098870` (Shogo's `CContainerInfo`) |
| `+0x15a8` | in-liquid gravity: the record's gravity (−200), else −100 | `0x10098980` |
| `+0x1698..16a0` | summed `Current` of the touched, non-hidden containers | `0x10098c3e`…`0x10098c87` |

`0x100999a0` ("head under liquid") is `0 < [+0x1584] ≤ 6`, false in Wizard Eye. The body test uses the whole box
(`0x1009ab10` position, `0x1009acc0` dims, `ILTClient+0x330` with up to 10 hits); the head test one point 10 LT under
the top of the box (`0x100ab8a0`: `pos.y + dims.y − 10.0`).

### Mover selection (`0x10099270`, `0x100994e1`…`0x10099590`)

In priority order: Spectator / GameSpectator (`[+0x156c]` 1/2), Wizard Eye, Jump (`+0x168d`), Ladder (`+0x1594`),
**SwimmingJump** (`+0x159a`), **SwimmingOnSurface** (`+0x1598`), Falling (`+0x168e`), **WalkingInWater** (body in liquid
and on a floor), **UnderWater** (head under), **WalkingOnWater** (`+0x46`, a server flag, message `0x26` → `0x100ab470`;
no MM9 spell or item sets it), else **Land**. The flags (`0x10099339`…`0x100993ab`):

- head under → "was submerged" set, surface cleared, jump and fall flags cleared;
- head out, body in, and it was submerged → **on the surface**;
- body out of all liquid → both cleared.

So a party that steps or falls into deep water uses Land/Falling (gravity on) until the head goes under; it can only be
"on the surface" after having been under.

| Mover (global, vtable) | Update | Movement |
| --- | --- | --- |
| UnderWater (`0x100df804`, `0x100c934c`) | `0x100953b0` | `OnEnter` `0x10095390` clears the gravity flag `0x20000`. Velocity starts at **zero** each frame (`0x10095459`). Forward/Backward (cmd 0/1) ± the full camera forward × speed; StepLeft/Right (27/28, or Strafe 9 + Left/Right 10/11) ± camera right × speed; **Crouch (24) − world up × speed, Jump (25) + world up × speed** (`0x100956a8`: up = (0, 1, 0)). The terms add up unnormalised. No key: idle animation and `v.y += [+0x15a8] × 0.2` (`0x100957fb`, constant `0x100c5d40` = 0.2): **−40 LT/s** |
| SwimmingOnSurface (`0x100df800`, `0x100c936c`) | `0x10095880` | Gravity off (`0x10095860`, `0x10095c20`). Velocity from zero. Slot 7 `0x10095bb0`: camera forward and right with **y clamped to ≤ 0** (no rising). Forward/back/strafe as above; Crouch moves along −camera up (dives). No idle drift. **Jump → `0x10099df0`** (surface jump) |
| SwimmingJump (`0x100df7f8`, `0x100c938c`) | `0x10095c50` | First frame in liquid: `v.y` = jump velocity (`0x10098310(0)`: party record `+0x10`, ×1.41 while a timer `[+0x167c]` runs), **gravity flag on**. Air control: Backward × 75, Forward × 150, strafe × 75 LT/s (`0x100c5c00` = 75, `0x100c777c` = 150). Ends on landing or when the head goes under again |
| WalkingInWater (`0x100df7f0`, `0x100c93ac`) | `0x10095ff0` | **Land's vtable entries exactly** (Update, speeds, jump): wading is walking |
| WalkingOnWater (`0x100df7e8`, `0x100c93dc`) | `0x10096390` | in liquid: gravity off and `v.y` clamped to ≥ 0 (stands on the surface); out of it: Land |

`velocity += summed current` when its length exceeds 1 (`0x100995d4`…`0x10099654`, `[+0x15c4]` = "in a current"); Beethoven's
`(−1, 0, 0)` is exactly at the threshold and does nothing. The current is a velocity (LT/s), not an acceleration.

### Speeds (`0x10097b20`, `0x10097b50`, `0x10097bc0`, `0x10098310`; `data\player.txt` loader `0x100443a0`)

The party's movement record is a single struct (`[0x100df7dc]+0x212e8`, defaults at `0x10041310`: walk 60, run 150,
jump 280, swim 120). `0x100443a0` overwrites it from **the first data row** of `data\player.txt` (it reads one row and
stops, `0x10044715`): column 4 `walk vel` → `+0x8`, 5 `run vel` → `+0xc`, 6 `jump vel` → `+0x10`, 7 `Run Jump Vel` →
`+0x54`, 8 `Swim Vel` → `+0x14`. The row (Warrior):

| | LT/s | u/s | Note |
| --- | --- | --- | --- |
| walk | 150 | 384 | = our `walkSpeed` 384 |
| run | 250 | 640 | |
| jump | 275 | 704 | |
| run jump | 235 | 602 | |
| **swim** | **150** | **384** | used by UnderWater and SwimmingOnSurface |
| sink (no key) | 40 | 102 | −200 × 0.2 |

`GetSwimSpeed` (move manager slot `+0x48`, `0x10097bc0`) returns the swim velocity, doubled while the timer `[+0x1678]`
runs (set by `0x1007cc80` from a timed effect; the same ×2 applies to walking, `0x10097b50`; the effect was not
identified). Run does not change it. With `[+0x46]` set it returns walk/run speed instead. Crouch halves walking but is
refused in water (`0x10099f30`: not with the head under or on the surface).

Gravity on land: `lithtech.exe` holds a single −2000.0f (file `0xd670`), probably the default global force
(−2000 LT/s² = −5120 u/s²); not traced. With it the surface jump rises 275²/4000 ≈ 19 LT ≈ 48 u.

### Other consumers of the water state

- Rest-like screen `0x100a5480` opens only on a floor and out of the water (otherwise screen `0x16`, presumably the
  refusal; not identified).
- Landing handler `0x100996b0` returns at once with the head under water (likely the fall-damage path; not confirmed).

## 3. Breath and drowning

**Server (`object.lto`)**, the player object's update `0x100c3d20`:

- `0x100c5600` "head under water": a point at the box top minus 10 LT (`0x100c5638`, constant `0x100eeef0` = 10.0),
  `GetPointContainers` (`+0x238`, up to 20), any code 1–6.
- Not under: `[+0x5a4]` (last breath) = now (`0x100c3edf`).
- `0x100c5560`: if `now − [+0x5a4] > 15.0` (`0x10183a84`) and the player is not in two excluded states (vtable `+0x25c`,
  `+0x260`, not identified): **drowning tick**, then `[+0x5a4] += 2.0` (`0x100ee5d0`): one tick every 2 s.
- The tick (`0x100559c0`): for each of the party object's 7 member slots, `Damage(GetMaxHP() / 6)` (character vtable
  `0x1016f0c0`: `+0x3c` = `0x1004c6e0` maximum HP, `+0x38` = `0x1004c590` subtract HP), then a random
  `drown01.wav`/`drown02.wav`.

So with full health a character goes from full to 0 HP in 6 ticks, **12 s after the breath runs out (27 s under
water)**. The client plays `drownmale.wav` on a damage message of type 16 (`0x100ab4b0`).

**Client HUD** (`0x1001a6f0`, `hud\breathmeter.pcx`, `hud\BreathMeterBar.pcx`): the meter appears while the head is
under (`0x1001acd0`), its start time stamped on entry; value `100 × (1 − (t − t₀) / 15)` (`0x1001ac90`, constants
`0x100bf61c` = 1/15, `0x100bf618` = 100), maximum 100. Hidden again on surfacing, and the timer resets at once.

**No breath extension**: MM9's 49 spells (`DATA\SPELL.txt`) have no Water Breathing or Water Walk, and no item in
`MASTERITEMLIST.csv` mentions water or breath. Levitate/Fly do not exist (Fleet Foot only speeds up).

## 4. Screen and sound under water (`cshell 0x100ab8a0`)

When the head container code changes (and the camera is the party's, not Wizard Eye or a cutscene camera):

| Effect | Detail |
| --- | --- |
| Tint | a light scale (multiplies the scene's lighting): BlueWater **(0, 0.5, 0.7)**, DirtyWater (0.25, 0.3, 0.05), ClearWater (0.3, 0.8, 0.8), CorrosiveFluid (0.3, 0.4, 0), Kato (0.5, 0.15, 0), LiquidNitrogen (0, 0.5, 0.7) plus 0.1 light add (switch at `0x100ac07c`); reset on leaving (`0x10072bb0`) |
| Fog | if the volume has an effect object with `FogEnable`, console `FogEnable`, `FogNearZ`, `FogFarZ`, `FogR/G/B` from it (`0x100abc0f`…, strings `0x100d8ae8`–`0x100d8b18`); otherwise the world's fog is restored (`0x100830e0`) |
| Lens | `0x10091910`: the field of view oscillates (±40 px of a 640×480 frame, rate 0.02 × frame time), only at the default 90° FOV |
| Models | console `ModelWarble 1` (`0x100ad250`), off on leaving |
| Ambient | `Sounds\Player\unwater2.wav` looped for codes 1–3 and 5 (`0x10046080`), stopped on leaving |
| Crossing | head goes under: `WaterSplash.wav` (`lavasplash.wav` for code 5); comes out: `out_water.wav` (`out_lava.wav`); radius 500 LT (`0x100abeec`…`0x100abf4d`) |

The surface is a sprite polygrid drawn at the volume's top (`ShowSurface`, `SurfaceAlpha`); no separate underside look
was found.

## 5. Combat and spells under water

- **Ranged weapons are not fired with the head under water.** The party attack routine `object.lto 0x100b3bc0` takes
  the ranged path (`0x100b3ec7`: equipment slot 15, the ranged slot) only if `0x100c5600` says the party is not under
  water (`0x100b3ede`). Under water it goes to `0x100b3fca` (no shot). The projectile kinds there: thrown daggers and
  axes (items 34, 185) → 35, crossbows (40, 186) → 7, bows (55, 51, 187) → 15, Blackpowder (188) → 68.
- **Spells**: no water test on the casting path was found (the callers of the client's two in-liquid predicates are
  all accounted for above; the server's under-water test `0x100c5600` has only the breath and ranged-attack callers).
  Treated as allowed.
- **Projectiles**: the volume physics (`0x1008fdb0`) only acts on objects of class `Actor` (`0x10005d70` =
  `IsKindOf(obj, "Actor")`), so projectiles keep their speed and gravity in water.

## 6. Monsters

**Class.** Every swimmer is an `AISwimFly`, the class the flyers use (`classdef.py`): `SeaMonster` (`SeaMonsterMale`,
`SeaMonsterFemale`), `JellySpore` (`GelatinousSpore`, `NettleSpore`), `Fish`, beside `DragonFly`, `Lobber`, `Ghost`,
`Banshee` (the Terrors), `EvilEyeTerror` and others. Their speed for the AI's `SwimVel` query (`0x100193ab`) is the
record's `+0x14`, which the `monsters.txt` loader fills from column S, **FlyVelocity** (`0x10043232` → `+0x560` →
`0x10043662` → `+0x50c`): Sea Monster 200 LT/s (512 u/s), Jellyspore family 200, Fish 30.

**Placement** (`dat_swimmers.py`): every swimmer in water has `Gravity 0, MoveToFloor 0`. 24 Spores and 5 Sea Monsters
sit inside liquid volumes (Isle of Ashes 10, Thronheim 5, Sturmford 5, Thjorgard 4, Guberland 4; 1000 Terrors 2, Dark
Passageway 2). Bathhouse's three JellySpores stand in rooms (`Gravity 1, MoveToFloor 1`): they are not in water. The
78 `Fish` are not inside any volume (decorative schools: 1000 Terrors 64, Anskram 8, Temple of Honk 6).

**Water physics on monsters** (`VolumeBrush::UpdatePhysics` `0x1008fdb0`): for an `Actor` that is not an `AISwimFly`,
velocity and acceleration × `(1 − Viscosity)` = × 0.5 each physics update, `Current` plus the radial current added,
and for liquids (`+0x240` → `0x10090250`) the gravity flag replaced by `accel.y += −200`. The frame time read at
`0x1008fe20` is discarded, so these act per update, not per second. Swimmers and flyers are untouched. Monster
animations have water variants (`StandWater`, `Swim`, `SwimReverse`, `AwareWater`, `HAttackWater`, `WinceWater`,
`DieWater`, `FidgetWater`) chosen through `IsInWater` (Actor vtable `+0x328`). Walkers are therefore allowed into water
and walk (slowly) on the bed.

**Not traced**: how an `AISwimFly` swimmer is kept inside its water (no container test was found in the `AISwimFly`
code `0x10019000`–`0x1001d600`; it may rely on its AI rails, 54 of 1000 Terrors' and 44 of Isle of Ashes' `AIRail`
points lie in water, or on not having targets outside). Monsters take no drowning damage (the breath timer is the
player object's alone).

## Measurements the real game would settle

The user takes real-game captures; these four would confirm the numbers above (Verhoffin Ruins' crevasse, reached by the
NW ramp from the start, is the easiest place):

1. **Breath.** Walk off the crevasse rim into the water and hold Crouch. Time from the splash to the first drowning
   sound (expect 15 s), the HP lost per sound (expect 1/6 of each member's maximum) and the gap between sounds (2 s).
2. **Sinking.** Under water, release all keys next to a wall with a visible texture seam; time how long the view takes
   to sink one wall texture's height (expect 40 LT/s; a 128 LT texture in 3.2 s).
3. **Climbing out.** At the surface next to the rim (123 units, 48 LT above the water), press Jump while moving
   forward; note whether the party gets onto the rim, and with the sea of Isle of Ashes, whether a low beach step
   (under 20 LT) can be climbed by Jump.
4. **Under-water look.** One screenshot looking up at the surface from below and one looking along the bed, in the
   crevasse and in Dook's Castle's lake (fog on), for the tint and fog targets.
