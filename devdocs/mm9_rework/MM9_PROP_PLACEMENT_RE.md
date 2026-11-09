# How MM9 places its props (reverse-engineered 2026-11-07)

Question: MM9 stores a prop's `Pos` in the DAT, and its ABC models have their origin at the mesh's vertical centre,
yet MM9 draws chairs, bookcases and tables standing on the floor and candles standing on tables. Our converter used a
hand list of models (`BASE_AT_POS`), then a fitted rule (`prop_pose.stands_by_base`: 4 under to 24 over a surface).
Neither is the engine's logic. This is, traced in `mm9/game/lithtech.exe` and `mm9/game/data/object.lto`.

## Answer: every non-AI ModelObject is lifted by its model's half height at its initial update

1. **Creation.** The server creates the object at its DAT `Pos` with dims (1, 1, 1) LithTech units (lithtech.exe
   object initialiser, `fld1` into `+0x178..0x180` at `0x0044af18`).
2. **Scale.** `ModelObject`'s initial update (object.lto `0x100be860`) reads `Scale` and sets it through virtual
   slot `0x20` (`0x100bce70`, server field `0x1a8`). The server's SetObjectScale (`0x0045a668`) only copies the scale
   and flags it for the network; it does not touch the dims (the dims recompute `0x0041aedd` is client-side).
3. **Lift.** `ObjectBase`'s initial update (`0x100bc710`) calls virtual slot `0x60` (`0x100bd8d0`): for a model it
   takes the user dims D of its `STATIC_MODEL` animation, else animation 0 (server vtable `0x484284` slot `0x17c` →
   CommonLT `GetModelAnimUserDims` `0x0042eddc`, which returns the raw ABC binding dims, unscaled), and passes them to
   slot `0x38`. `ModelObject`'s slot `0x38` (`0x100beb20`):
   - reads the current dims X (slot `0x158`, physics GetObjectDims) and position P (field `0x1a0`);
   - sets the dims to D × Scale without pushing (`0x100bd1f0` → slot `0x15c`, SetObjectDims flags 0);
   - sets the position to P with `P.y += D.y − X.y` (field `0x1a4`, SetObjectPos).
   With X = 1, the object rises by **D.y − 1 LT unit** (D unscaled, native ×2.56). No collision, no floor test.
4. **MoveToFloor** (`ObjectBase` initial update, property `MoveToFloor`, object.lto `0x100c1630`): after the lift,
   a ray straight down from the centre (IntersectSegment, flags 3: world and solid objects, filter `0x100c15e0`); if
   the box bottom is above the hit, the centre goes to `hit + dims.y + 0.1 − 2.0` LT (the box sits 1.9 LT into what
   it hit).
5. **Drawing.** The model is drawn at the object's position plus its binding translation (`+0x14` of the 0x20-byte
   animation record, the `AnimBindings` loader `0x00442d4e`; our reader's `anim_bindings[i].origin`), in the pose of
   its first animation (or its PropAnim.scr animation) and the full DAT Rotation, at the DAT Scale.

**Which classes.** The lift is `ModelObject`'s slot `0x38`; a class gets it when its vtable keeps that slot. From the
object.lto ClassDefs and their constructors' vtables (slot `0x38 = 0x100beb20`): BagGold, Barrel, BonePile,
ButterFlyCloud, CandleProp, Cauldron, Clover, Cookpot, Corpse, DeathMatchItem, DestructableProp, Drip,
FadeAwayInventoryItem, Fan, Fountain, InventoryItem, MeleeWeapon, ModelObject, ModelProp, PickupItem,
ProjectileWeapon, Prop, PropDamager, RUDEProp, RollingProp, SpawnedInventoryItem, Sphere, StatStone, TreasureBag,
TreasureBase, TreasureChest, Weapon, WellMMIX. All of them reach slot `0x60` = `0x100bd8d0`; the subclass initial
updates (Barrel `0x1005f220`, Cauldron, BonePile, Cookpot, StatStone, WellMMIX, Clover) chain to `Prop`'s first and
then only reset their dims (slot `0x15c`), not their position. **Not lifted:** Torch, WallTorch, Brazier
(`Fire > ObjectBase`, a dims-only setter `0x100bd1f0`), Door and the other WorldObjects, and the AI (`0x10002050`).

**Consequences.** A chair stored with its Pos on the floor stands on it. A candle stored with its Pos on a table top
stands on the table (Tasar's Candle0: Pos 92.2, D 16.1 native, lift 13.5, mesh bottom 89.7 on a table top at ~90);
nothing below it is consulted, which is why the designers could put table items on non-world tables. A lamp, sign or
chandelier rises by its own half height too (wall candles +23, chandeliers +28..+79, mine lanterns +36 against the
old bake). A Scale ≠ 1 prop rises by its unscaled half height while its box and mesh are scaled. A model whose mesh
reaches below its dims box goes that far into the floor (chair03's legs, 5 units).

## Checked against the real game and the rebuild

- Real MM9 at Verhoffin Ruins' spawn (`overnight/mm9_real_verhoffinruins_spawn.png`) against our build at the same
  pose: the wall lantern hangs at the height of the far ceiling beam in MM9; R7c (no lift) draws it clearly lower, R8b
  (lifted) where MM9 does (`output/mm9_rework/prop_lift_re/verify/verhoffin_spawn_lantern_real_r7c_r8b.jpg`).
- R8b (`output/mm9_rework/final_r8b_20261107/`, all 44 maps, review roots only): 2,211 decorations move against R7c,
  mostly hanging things rising by their half height (wall candles +23, chandeliers +28..+79, mine lanterns +36,
  tapestries +90, bells +170, the 1000 Terrors treasure openings and skulls, Arslegard's weapon racks); standing
  furniture changes by a few units (chair03 −8: its legs reach 5 units under its box). 171 of 174 scenarios pass; the
  three failures fail the same way on R7c's assets with today's build (Beethoven doors_exits and Dark Passageway swim:
  the water-exit replay climbs ~250 Z against ~170 recorded, an engine change since the recording; Verhoffin scripted is
  the known flaky one).
- Cases the data alone would have argued against, which the code decides: Lich Lab's hanging cages (their chains end
  at the ceiling without the lift, 100-150 units into it with it), Drangheim's tilted windmill sails (+1,137),
  Thjorad's `DwarfAxeOnSide` mining axes (their model lies in an upright axe's box: +97).

## Rotations are a separate rule

The lift moves a prop vertically only. The quarter turns the conversion had to fix come from the pose MM9 draws a prop
in: its model's first animation at its first key, or for a prop running PropAnim.scr the animation its ScriptParams
name ("ns", "ew"). The `*NS` furniture (bookcases, dressers, desks, cabinets, pews, stoves) is mostly its `*EW` twin's
file whose animation turns the root a quarter; Anskram Keep's bed, Kluso's weapon cabinets and trestle table, the stone
benches and the raised coffins turn by their PropAnim animation. `dungeon/prop_pose.py` (`placement`, `pose_turn`)
applies it from each model's own data, with no model list. This rule is confirmed from data only: posing the meshes
reproduces every turn that had to be fixed, but the lithtech.exe code that picks the animation for drawing has not
been traced.

## Superseded: the box push-out

The first reading of this RE (earlier on 2026-11-07) took the dims fit `0x00447451` / `0x0044766b` (SetObjectDims with
`SETDIMS_PUSHOBJECTS`) as the mechanism. It is real engine code, but props never reach it at load: `ModelObject` sets
its dims through slot `0x15c` (flags 0). An R8 build with the push (vertical only) left small items on prop tables
7-24 units sunk and lifted nothing that hangs; the traced lift above explains both.

## Implementation

`level_generation/projects/mm9r_common/dungeon/prop_pose.py`: `LIFT_CLASSES`, `CREATE_DIMS`, `model_box`, `lift`,
`lifted`, `mm9_mesh`. `content.props` places every MoveToFloor-0 entry of a lifted class drawn with MM9's own model
by `lifted`: its props.json plan position, and for an upright one the height at which its GLB's lowest point meets
MM9's mesh at the lifted position (some props.json heights were raised by hand against the old bake); a tilted one
moves from its props.json height by the lift. MoveToFloor-1 entries keep the mesh-based drop
(`prop_pose.move_to_floor`), which approximates step 4 (it drops the mesh, not the box, and does not sink 1.9 LT).
`prop_audit.py` draws MM9's reference mesh with the same lift.

## Tools used

rizin 0.10 with rz-ghidra (`pdg`) and binutils `objdump -M intel` on lithtech.exe (`pD` hangs on it). The vtable
offsets come from each constructor's vtable store (server object `0x00455fad`: final vtable `0x484284`, physics at
`+0x26c`, common at `+0x268`, model at `+0x270`) and the struct of function pointers filled at `0x00458974`. Working
files: `output/mm9_rework/prop_lift_re/` (data tests; the listings `object_lto_initialupdate_lift.c`,
`object_lto_basewrappers_0x100bcc00.c` and `object_lto_class_dims_setters.txt`).
