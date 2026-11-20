# MM9 player ranged attacks at far monsters (native RE)

Research note, 2026-11-09. Binary: `mm9/game/data/object.lto` (SHA-256 `b1271f37e5314281…`, image base
`0x10000000`, the server game code, where the party's attacks are aimed, launched and resolved), disassembly
`re_mm8/work/mm9_collision/object_lto.asm`. Client `mm9/game/data/cshell.dll` (SHA-256 `678700ff1cc795ae…`) was
searched only. Decompiles, dumps and helper scripts are in `re_mm8/work/mm9_player_ranged/`. **Verified** = read in
the instructions; **inferred** = from the decompile, names or data, not traced to the end. Units: LithTech units (LT),
1 ft = 12 LT, 1 LT = 2.56 OpenYAMM units (OY). Continues [projectiles](MM9_PROJECTILES_RE.md) and
[native AI](monster_ai/MM9_AI_NATIVE_RE.md).

## Result

1. **Real projectiles, locked onto a target.** A bow, crossbow or thrown weapon fires its `PROJECTILE.txt` row (from
   the weapon's projectile column) through the same spawn as monster shots. Its flight ends only on impact or at the
   end of its lifetime, as monster shots do (verified). The server picks a target before every attack (verified):
   - It casts a ray 1000 LT (83 ft, 2560 OY) along the view. If the first thing hit is an actor, that actor is the
     target.
   - If not, the auto-target takes a monster (an `IsMonster` row) within 1200 LT (100 ft, 3072 OY). It tries, in
     order: the first thing on a 1200 LT view ray; the nearest within 10° of the view that is on screen with a clear
     line; the nearest on screen with a clear line.
   - With a target, the shot is aimed at its centre and **homes on it**: every update it steers straight at the
     target, with no turn limit, until it hits or its lifetime ends.
   - Without a target, it flies straight at the ray's hit point, or at a point 1000 LT ahead.
   - The same attack command melees when the target is within 96 LT (8 ft) and shoots otherwise.

   There is **no maximum range on firing**. Spells work the same way (verified): every spell goes through one cast
   routine, which also spawns a homing projectile at the target. Spells without a projectile (Curse, Poison, Turn
   Undead and the other spells marked `1 mons`) take effect at once on that target. Those can therefore reach only
   what the 1000/1200 LT targeting finds (inferred: the effect code was not read).
2. **Damage is refused beyond 320 ft.** The weapon to-hit test receives the straight-line distance from the shot's
   launch point to the impact point, in whole feet (verified). Beyond 320 ft (3840 LT, about 9830 OY) the shot always
   misses and does 0 damage. Closer in, the target's armour (+5) is multiplied by 1.0 up to 40 ft, 1.25 up to 100 ft,
   1.75 up to 200 ft and 2.0 up to 320 ft. That multiplier applies only to attacks whose damage type is
   Phys; other damage types hit without a roll inside 320 ft (verified for the test; for the party the type is
   open, see the open questions). There is no damage falloff. Arrows fly 1000 ft, so the dead band is 320-1000 ft.
   Spell damage goes through a different routine whose use of the distance was not traced.
3. **Correction: the monster chases.** In the original game, a far shot, even a 0-damage miss, still makes the monster
   take the party as its target, and the monster then runs at the party:
   - The damage message is sent with any amount. `OnDamage`/`OnDamageDone` fire, and `NewTargetCheck` targets the
     party (verified).
   - The native target tracker refreshes the party's true position every update, whether or not the monster
     perceives the party. `AggressiveTick` (every 0.2 s) measures the true distance and runs toward the party while
     it is out of reach (verified).
   - The monster drops the party only when it has not perceived it for `TargetLostTime`, 8 s by default; the clock
     starts at targeting (verified). Seeing the party within its doubled sight on the way resets the clock.

   The existing note's "leaves it standing until it gives up 8 s later" describes OpenYAMM's earlier port, in which
   the world offered the held party only within the doubled sight. It does not describe MM9 itself: there the
   monster runs toward the party for up to about 8 s, and alerts its friends (`SetupTarget` → `AlertStart`).

## 2. Aiming and launch (`object.lto`)

**Trigger** (`0x100c1ee0`, verified): each update, the server tests two client commands, `0x1e` and `0x1f`
(`ILTServer +0x148` on the player's client; inferred: attack and quick cast). Each calls the attack routine
`0x100c1f50` on the player's attack timer (`Player +0x614`).

**Attack** (`0x100c1f50`, verified):
1. `0x100c2340`: no attack within 0.25 s of the last one (`0x100eef4c`). It then gets the target from
   `0x100c6120` and the attacking character from the party (`0x100b3940`).
2. A target handle counts only if it is an `Actor` (`0x10005d70` = IsKindOf "Actor"). Its character sheet (`+0x36c`)
   becomes the target sheet.
3. Ranged (kind 2), or a weapon whose attack info has byte `+0x20` set: `0x100b3bc0` builds the attack info. Then
   `0x100caad0(player, info+0xc projectile id, fire point, direction, info, 0, info+0x20, target sheet)` spawns the
   shot (`0x100c2321`).
4. Melee (kind 1): an immediate hit with the real distance (`0x100c2141`-`0x100c22bf`).
5. Quick cast: `0x100b40f0` builds a spell info, then the spell's cast slot `+0x18` runs with the same fire point,
   direction and target sheet (`0x100c2084`-`0x100c20a5`).

**Targeting** (`0x100c6120`, verified):
- Eye = player centre raised by half its height − 10 LT (`0x100eeef0`), facing the view angles (`Player +0x580`…`+0x588`
  → `ILTServer +0x98`).
- Ray `0x10059b70` along the view, 1000 LT (`0x447a0000`).
  - No hit: aim point = eye + view × 1000, distance 1000.
  - Hit: distance to the hit point. If the hit is an `Actor`, the distance is measured to its edge instead (`+0x2a0`
    → `0x10003340`: centre distance minus both radii) and the actor is the target.
- If the distance is over 96 LT (`0x10183ab0`), the kind is ranged (2). If the ray did not hit an actor, the
  auto-target `0x10008b70` runs. If it finds a monster, that monster becomes the target and the aim point (its
  centre), and the attack melees when its edge distance is under 96.
- Ranged fire point: eye + right × 16 − up × 12 (`0x100ee5ec`, `0x100eef3c`). The direction runs from the fire point
  to the aim point and is re-aligned only when the aim distance exceeds 24 LT (`0x10183aac`).

**Auto-target** (`0x10008b70` on the actor manager `0x101abf38`, verified):
- Eligible: an active `Actor` (`+0x320`), not the player, whose `MONSTERS.txt` `IsMonster` (record `+0x14c`) is 1,
  not dead (`+0x25c`), at an edge distance under 1200 LT (`0x100ee688`).
- Order: the hit of a 1200 LT ray along the view; else the nearest eligible monster whose direction has a dot product
  over 0.9848 (`0x100ee684`, 10°) with the view and that passes `0x100c65e0`; else the nearest eligible monster
  passing `0x100c65e0` in any direction.
- `0x100c65e0` (verified, axes inferred): a ray from the player's eye whose first hit is the monster's centre, and
  the centre inside a 4:3 view frustum of 90° (|side| < depth, 1.33 × |up| < depth).
- Townsfolk (`IsMonster` 0) are never auto-targeted. The crosshair ray takes any actor it hits.
- The client holds no copy of these constants: no 1200.0 or 0.9848 in `cshell.dll`, and its one 1000.0 is unrelated
  (searched). Targeting is server-side.

**Homing** (verified, [projectiles §5](MM9_PROJECTILES_RE.md)): `Setup` (`0x100c7440`) receives spawn argument 8
as its 7th argument (`0x100cad4f`-`0x100cad88`). It looks up the target's object (`0x100089b0`), aims at its centre
and stores it in `+0x4a8`. The update `0x100c8ac0` then steers straight at it each frame. Monster weapon shots pass no
target; the party's pass the target found above.

**Spells** (verified, `re_mm8/work/mm9_player_ranged/spells.py`): all 49 spell objects (`0x10089110`) share the
cast slot `+0x18` = `0x1008ab80`. It charges and recovers, then spawns `info+0xc` with the target (argument 8).
- The spell's `+0x10` gives the projectile row: Chain Lightning, Elemental Bolt (by mastery), Fear, Magic Mine,
  Poison Cloud, Sparks and Wound have one.
- The others return −1 (`0x1008ab60`). For those, `0x100b40f0` applies the spell at once through `+0x0` →
  `0x1008a250` (`0x100b42c4`, `0x100b4483`), on the targeting's target.
- Inferred: a `1 mons` spell with no target found does nothing useful.

**What ends the flight**: unchanged from [projectiles §3](MM9_PROJECTILES_RE.md): impact, or detonation at
launch + lifetime (`0x100c7650`). Range is never checked in flight, for the party as for monsters. A homing shot
keeps chasing its target for the whole lifetime.

## 3. The hit, distance and damage

**The distance that reaches the RPG layer** (verified):
- `DamageObject` (`0x100b95b0`) computes |impact point − the projectile's launch position `+0x4ac`|, which `Setup`
  set at spawn (`0x100b967f`-`0x100b973f`). It stores the result in its first argument slot.
- For weapon infos (`+0x14` = 50, the constructor default, `0x100b351c`) it passes that distance to the weapon attack
  `0x100b46c0` (`0x100b97f3`). Spell infos (`+0x14` = spell id) go to `0x100b5300` with the same value
  (`0x100b97d8`).
- `0x100b46c0` converts it to whole feet (× 1/12, `0x100eef00`, truncated; `0x100b473c`-`0x100b4751`).
- For a party attacker (sheet type 0) it calls `attacker +0x90` (`0x10053aa0`) with (victim, melee?, feet)
  (`0x100b4bae`-`0x100b4bcf`).
- Correction to [projectiles §4](MM9_PROJECTILES_RE.md): the RPG weapon attack does see a distance, the shot's
  flight distance. The blast falloff value is still never used.

**To-hit test** (`0x10053aa0` → attacker `+0x8c` = `0x10053820`, verified; this = attacker, `+0x58` = victim set by
`0x1004aee0`):
1. No victim: miss.
2. The attacker's condition 1 (`+0x58(1)`): 50 % miss.
3. Gate `0x1004b390(0, victim type)`.
4. **Distance bands** (`0x10053879`-`0x100538e1`):

   | Flight distance | Factor |
   | --- | --- |
   | ≤ 40 ft | 1.0 |
   | ≤ 100 ft | 1.25 |
   | ≤ 200 ft | 1.75 |
   | ≤ 320 ft | 2.0 |
   | > 320 ft (or negative) | **miss** (`0x10053a95`, returns 0) |

5. Attack value: the victim's `+0x50` (getter `0x10053730`) + 2 × attacker `+0xc(1)` + a constant:
   - a ranged hit on a monster: + 5;
   - a ranged hit on a character: + 10, with −10 under victim condition `0xca` and +30 under `0xcf`;
   - melee: + 10, or + 50 on a character victim under condition `0xca`.
6. **Only when the attack's damage type is 4 (Phys)** (attacker `+0x1fc` melee, `+0x210` ranged; for monsters,
   `MONSTERS.txt` `Type1`/`Type2`, parsed at `0x100442f5`) is there a roll. The threshold is
   (victim `+0x50` + 5) × factor and the roll is rand % attack value + 1, less a penalty under condition 1. The hit
   needs roll − 1 ≥ threshold (`0x10053a14`-`0x10053a88`). Any other damage type hits.
7. A miss returns 0 damage (`0x10053e43`).

There is no damage falloff by distance anywhere on this path.

**A miss still provokes** (verified):
- `DamageObject` sends the damage message (id 1000, `0x100b9c80`) whenever there is a victim, whatever the amount.
  The player's gate slots `+0x64` and `+0x304` both return true, and `+0x358` is a no-op (`0x100b9810`-`0x100b9891`).
- The actor's handler calls `OnDamage` (`0x100bd6b4`). With 0 damage, `AIBase::OnDamage` (`0x100154a0`) skips the
  wince roll and raises `OnDamage`/`OnDamageDone` to the script ([native AI §8](monster_ai/MM9_AI_NATIVE_RE.md)).
- `BASECRAWL.inc` `OnDamageDone` → `NewTargetCheck` → `Target`, `SetupTarget`, `AggressiveStart`.

## 4. The monster's reaction (correction of the existing summary)

- **Target kept without perception** (`0x100118f0`, verified):
  - Each update: target position `+0x660` = the target's real position (`ILTServer +0x1a0`), with no perception test.
  - If `Perceive(target, sight only)` succeeds, or the last-seen time `+0x678` is 0 (just targeted): `+0x678` = now
    and the last-known position `+0x66c` is updated.
  - Otherwise, once now > `+0x678` + `TargetLostTime` (`+0x608`, 8 s by default; 30 s in `GOBLINCAMP.scr` and
    `ZOMBIECAMP.scr`): `OnLostTarget` (`+0x64c`) → `ClearTarget`.
  - The attack-range test uses the real distance.
- **Chase** (`BASECRAWL.inc`, verified):
  - `AggressiveTick` runs every 0.2 s. `AIGetDistance` gives the true distance; out of range it goes to
    `AggressiveOutOfRange`.
  - If `CanReachTarget` and `ShouldRunAfter` hold, it calls `RunTo g_hTarget` (`BaseCrawlGetHim`).
  - `MAX_CHASE_TIME` (30 s without attacking) also ends the pursuit.
- `SetupTarget` doubles sight and hearing the first time the party is targeted, and starts the alert ticks to friends
  within `AlertRadius` (native AI §5.1, §10).

So a far hit gives an MM9 monster about 8 s of running at the party, more if it sees the party on the way. That matches
neither "ignored" nor "stands still". Inferred: `RunTo` with an object handle paths toward the object's current
position; its native handler was not read.

## 5. What this means for OpenYAMM

OpenYAMM now limits the party's shots and targeted spells to the world's engagement range: MM9 declares 3800 OY
(about 1484 LT, 124 ft; 4096 before). It caps monster shots at the party to the same reach. MM9 itself had:

- **No refusal and no vanishing.** The party could always fire. Shots flew on lifetime (arrows 1000 ft), struck and
  provoked. Our "the shot vanishes" and "the targeted spell is refused" are stricter than MM9, and deliberate.
- **A comparable damage limit, farther out**: no damage beyond 320 ft (9830 OY) of flight, for every weapon hit
  that goes through the to-hit test. Monster weapon attacks of kind 1 or 2 use the same test (inferred). Our reach is
  shorter: about 124 ft, inside MM9's 1.75 band.
- **A shorter lock range**: the aim assist and homing reach 1000 LT along the crosshair (2560 OY) and 1200 LT
  automatically (3072 OY). Beyond that, shots fly unguided. Our reach is 3800, so we lock (if we lock at all) farther
  than MM9 did.
- **Instant monster spells** effectively reached only the lock range (1000/1200 LT), since they need a target.
- **Physical to-hit by distance**: armour × 1 / 1.25 / 1.75 / 2 at 40 / 100 / 200 / 320 ft. This is MM6-MM8's idea
  in finer steps. An MM9 ruleset that wants MM9's odds would use these bands (480 / 1200 / 2400 / 3840 LT =
  1229 / 3072 / 6144 / 9830 OY).
- **Provocation**: in MM9 every far hit provokes and the monster runs at the party for about 8 s. Our MM9 rule (only
  hits from within the engagement range provoke) is our own choice; MM9 had no such distance gate.

## 6. Open questions

- The party's ranged damage type. The character constructor sets `+0x1fc`/`+0x210` (melee and ranged attack type)
  to 6 (`0x100529b0`). Only the save serializer (`0x10051f..`) and the monster loader write them otherwise. If 6
  stays, party weapon shots skip the armour roll and always hit inside 320 ft. Not checked in game.
- Which monster attack kinds (2, `0x10`, `0x20`) monster shots use. In `0x100b46c0`, kinds `0x10`/`0x20` roll dice
  without the to-hit test, so they would also skip the 320 ft cutoff.
- Whether the spell routine `0x100b5300` uses the flight distance it receives (spells resolve without the weapon
  to-hit test). Also whether instant `1 mons` spells check range or line of sight in their effect code
  (`0x1008a4e0`).
- Condition 1 (the 50 % miss) and conditions `0xca`/`0xcf` were not named. `ILTServer +0x148` is taken as "client
  command on".
- The 4:3 frustum axes in `0x100c65e0` were read from the decompile only.

## Working files (`re_mm8/work/mm9_player_ranged/`)

`dec.sh` (rz-ghidra decompile), `pdf.sh` (Rizin listing with stack names), `dref.py` (data references, e.g. vtable
slots), `spells.py` (spell id → class, cast and projectile slots), `dec_*.txt`/`pdf_*.txt`/`asm_*.txt` dumps of the
functions above, and `strings_*.txt`.
