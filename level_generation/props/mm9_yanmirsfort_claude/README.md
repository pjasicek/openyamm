# MM9 Yanmir's Fort props as 3D decorations (2026-10-30)

The furniture, ice blocks, barrels, crates, beds, chests, claw lamps, claw torches and Yanmir's key of MM9's Yanmir's
Fort (`YANMIRSFORT.dat`, the ice fortress), converted from their LithTech ABC models into OpenYAMM 3D decorations for
the native BLV ([map project](../../projects/mm9r_yanmirsfort/)). The route is Lindisfarne Monastery's props project
([`../mm9_lindisfarnemonastery_claude/`](../mm9_lindisfarnemonastery_claude/README.md)): its scripts, plus Tasar
Academy's chest kinds and DAT-light fallback, Verhoffin Ruins' tilt baking and posed-bed placement, and the Anskram flame
cards. No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the isle's
`textures.upscale`, no Real-ESRGAN).

## Outputs

- **7 models** built and installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` (0 inverted closed parts each, in
  `finish.py` and rerun on the installed sources):

| Prop | ABC / skin | Triangles (LODs) | Notes |
| --- | --- | --- | --- |
| `clawlampp180` | CLAWLAMP / ClawLamp | 396 / 172 / 99 | hanging lamp, MM9's pitch pi baked in (claw above, ice orb below); the orb glows blue (below) |
| `clawtorchr180` | CLAWTORCH / ClawTorch | 313 / 139 / 80 | wall torch, MM9's roll pi baked in (orb on top); glowing orb, **blue flame cards** on the orb's top (`card` mode) |
| `chestrusty01` | CHEST-RUSTY01 / Chest1 | 54 | the 10 rusty treasure chests (Anskram's `chest1` is CHEST1.abc, another model) |
| `crateice` | CRATE / `TEXTURES/A6Frosgaard/misc/yanmiricepillar` | 12 | the 13 ice blocks (MM9's crate cube with the level's ice texture) |
| `stool02` | STOOL02 / Stool02 | 156 | |
| `chairp270` | CHAIR / ChairPlain | 104 | Anskram's `chair` toppled (pitch 270 baked in); cut-out skin, as Anskram's |
| `stool01p90` | STOOL01 / Stool01 | 100 | the Thjorad Mine's `stool01` toppled (pitch 90 baked in) |

- **Reused** (same ABC and skin; their GLBs and rows stay with their owners, each owner found by md5 of its
  `work/mm9_deco_<prop>.glb` against the installed GLB): Anskram Keep's `barrel`, `crate` (Crate.dtx), `bed`,
  `bedmedium`, `chair`, `tableround`, `trashpile`; Drangheim Prison's `tablebench2` (the 9 DestructableProp tables and
  the Prop one), `bucket01`, `cabinet04ns`, `cabinet05ns`, `stove`, `tableround3`, `weaponscabinet02`; Verhoffin Ruins'
  `bedmedium2onside` (the 7 PropAnim.scr "onside" beds) and `chairdesk03p270` (toppled desk chairs); Dook's Castle's
  `bedornate`; Beethoven's `bonepile`; the Temple of Honk's `chairdesk03` and `key2` (Yanmir's key); Klusos House's
  `dresserfancyns`; the Bath House's `pew3`; the Lich Lab's `pew3ns`, `throne`, `blackchest`; the Thjorad Mine's
  `stool01`, `tableroundplain`, `woodbin`.
- Rows **2359-2382** (24 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 26160-26183,
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended in one run under
  `mm9r_common/locks/mm9_decorations.lock` (`tables.py --apply` takes it itself; a rerun reports 0 rows to add):
  - built here: `mm9_clawlampp180` (Scale 2), `mm9_clawlampp180_x300`, `mm9_clawtorchr180` (Scale 3),
    `mm9_chestrusty01`, `mm9_chestrusty01_x200`, `mm9_crateice`, `mm9_crateice_x110`, `mm9_crateice_x120`,
    `mm9_crateice_x200`, `mm9_stool02` (Scale 1.5), `mm9_chairp270` (Scale 1.25), `mm9_stool01p90`;
  - variant rows of reused models at this map's scales (their GLB unchanged): `mm9_bedornate_x300`,
    `mm9_blackchest_x300`, `mm9_chair_x125`, `mm9_chairdesk03_x125`, `mm9_chairdesk03p270_x125`, `mm9_crate_x120`,
    `mm9_dresserfancyns_x225`, `mm9_key2_x300`, `mm9_pew3_x100` (the Bath House's `mm9_pew3` is Scale 1.2),
    `mm9_tableround3_x90`, `mm9_tableroundplain_x95`, `mm9_throne_x250`;
  - reused rows: `mm9_barrel` (1.5), `mm9_barrel_x100`, `mm9_bed_x125`, `mm9_bedmedium_x100`, `mm9_bedmedium2onside`,
    `mm9_bonepile`, `mm9_bucket01`, `mm9_cabinet04ns`, `mm9_cabinet05ns`, `mm9_chairdesk03`, `mm9_chairdesk03p270`,
    `mm9_pew3ns`, `mm9_stool01`, `mm9_stove`, `mm9_tablebench2`, `mm9_tableround`, `mm9_tableroundplain`,
    `mm9_trashpile_x200`, `mm9_weaponscabinet02`, `mm9_woodbin`.
  No row carries a light. Collision: MM9 Solid props get half the smaller footprint side and the model height; the
  claws, the toppled plain chair and the key none; `mm9_bedornate_x300` none (Bed0 is not Solid in MM9); a reused model
  at a new scale scales its owner's row.
- `../../projects/mm9r_yanmirsfort/props.json`: **158 placements**: 122 `kind: prop`, 24 `kind: torch` (12 claw lamps,
  12 claw torches), 11 `kind: chest` (10 rusty, 1 black), 1 `kind: quest` (Yanmir's key). Each is under its DAT object name
  (`source_name`) with its `script` and `script_params`; the claws carry `blue`, `tilt_degrees` and the nearest kept
  light of the map project's `work/lights.json`. **150** are checked against the old map's baked BModel of the same object:
  **median of medians 0.51 units**, worst 0.87 (Crate12, `crate` at 1.2). Per model: claw lamps 0.46, claw torches
  0.51 (worst 0.61), rusty chests 0.49 (0.34-0.63), ice blocks 0.69 (0.17-0.78), toppled chairs 0.62-0.74, the rest
  0.29-0.72. The 8 posed placements (below) fit MM9's own pose: the beds 0.03, the key 0.09.
- `review/props_sheet.png`: contact sheet of the 7 built models (LOD0 front, three-quarter, side, behind-above, below,
  LODs; looked at: the toppled chair and stool lie on their backs, the chest has its lid, the lamp's claw holds the orb
  from above, the torch's flame stands on its orb). `review/clawtorchr180/closeup_*.png` and
  `review/clawlampp180/closeup_*.png` (`scripts/review_closeup.py`): the torch flame from the side, front,
  three-quarter and above (from the side the card stands edge-on right over the orb's top; the engine's `card` mode
  turns it about its own centre there) and the lamp's orb.

## Scripted and special entities (entity name = `source_name` in props.json)

| Entity | Decoration | Script | Notes |
| --- | --- | --- | --- |
| `Yanmir'sKey` | `mm9_key2_x300` | YanmirKey.scr `DoorTeleportRight DoorTeleportLeft` | `kind: quest`, no collision: needs a click event and a cog to hide it; lies flat on the floor (z 604) |
| `TreasureChest0`-`2`, `5`-`10`, `TChestWNote4` | `mm9_chestrusty01`, `mm9_chestrusty01_x200` | | `kind: chest` (the converter adds CHEST_EVENT + container); `TChestWNote4` has `Item1` 595 (float bits 1142210560), for the map's loot records |
| `TreasureChest12` | `mm9_blackchest_x300` | | `kind: chest` |
| `Lamp0`-`Lamp11`, `Torch0`, `Torch2`-`Torch12` (24) | `mm9_clawlampp180[_x300]`, `mm9_clawtorchr180` | | `kind: torch`, `Blue 1`; each has its own blue MM9 light |
| `Bed1`, `Bed3`, `Bed13`, `Bed16`, `Bed22`, `Bed23`, `Bed27` | `mm9_bedmedium2onside` | PropAnim.scr `onside` | posed, below |

The DAT repeats two unscripted names: `RdTable` (objects 100, 146, 155) and `Bench0` (145, 170). The converter makes
one entity and one `DECOR_<name>` marker node per name, so a repeat would share the first one's node: the later ones are
`RdTable_146`, `RdTable_155` and `Bench0_170` (`dat_name` keeps the DAT's name). The DAT name `Bucket` (object 173) is
also a decoration's name, which the converter refuses (playbook, "Entity names"): it is `Bucket_173` (map agent,
2026-10-31, `placements.py`).

## Notes for the map

- **Blue flames: decided, and different from the brief's picture.** Every CandleProp here is `Blue 1`, and its MM9 light
  is blue (0/0/255). The pipeline has a blue flame: Chasm of the Dead's recolour of the shared CC0 Flame02 flipbook
  (`textures/flame02_basecolor.png`, also the Ruined Temple's), used here. But both claw models put MM9's flame socket
  (`Glow-Node`, a one-triangle marker piece) at the **centre of an opaque ice orb** the claw holds (a closed 38-vertex
  piece 5.5 LT round it), so a card seated on the socket is hidden; the first build showed only a blue tip. So:
  - each orb's faces have their own material `<prop>_orb` with a blue emission (`emissiveFactor` 0.12/0.28/0.62) and
    `openyamm_flicker` [0.15, 3] (`finish.py`), so the globes read as lit from every side;
  - the **claw torch** (orb on top, open above) also gets two blue flame cards rising from the orb's top cap (seat 0.75
    orb radii above the socket, cards 0.17 m wide and up to 0.26 m above the seat at Scale 1, x3 as placed);
  - the **hanging claw lamp** has no flame card: its claw grips the orb from above, so a flame on the orb would burn
    through the wrist. The lamp is a glowing orb only.

  Not looked at in game: the emission and flicker strength and the flame size are guesses from the renders. Turn the
  emission down in `finish.py` (`ORB`) if the globes bloom too much.
- **Lights:** no row carries a light. Each claw's entry names its own MM9 light (24 distinct, all blue 0/0/255): the
  torches' are 28-29 units away, the lamps' 82 (Scale 2) or 164 (Scale 3) units under the lamp's origin, i.e. under
  the hanging orb. The BLV should keep them (they are the fort's blue lamp light).
- **Tilts:** the claws and the toppled chairs and stool have their DAT pitch/roll baked into their model (decorations
  turn about z only); `yaw_degrees` is the DAT yaw. Their fits (0.46-0.81) confirm the direction of each tilt.
- **Posed, not checked against the bake** (the old import baked the ABC's bind pose):
  - the seven onside beds: Verhoffin's `bedmedium2onside`, base on the floor under the DAT position (MoveToFloor 1,
    `floor_below` of the world geometry: 655, 0 or -41; the bind-pose bake's base is 1 unit higher), centred across on
    MM9's onside pose (fit 0.03 to it);
  - **Yanmir's key**: KEY2.abc's `Static_Model` (the pose MM9 shows, and the one Blender's glTF import evaluates, so the
    Temple's installed `mm9_key2` already has it) lays the key flat (LT extents 6.81 x 0.51 up x 2.67); its bind pose,
    which both this map's and the Temple's old bakes show, stands it on its edge (this map: 44 x 36 x 21 at Scale 3,
    and the reused model fit it to 2.84 only). It lies on the floor under its DAT position (604), centred on the
    Static_Model pose (fit 0.09). For the Temple of Honk (not changed here): its `key0` placement fit (0.92) is the same
    bind-pose difference, and its z (142.4) is the upright bake's centre, 2.4 units above the bake's base (140, the
    surface the key lies on).
- The 13 ice blocks are DestructableProps (Pushable, 100 HP) in MM9; here they are static Solid decorations.
  Destruction and pushing are not carried. The same goes for the barrels, the Crate and the Table_Bench tables
  (DestructableProp).
- `Fire` objects (scripted frost and dust effects), `ObjectLight` and the lights are not props: not in props.json.
- Giant furniture, as MM9 scales it (fits 0.46 and 0.56 to the bake): `bedornate` at Scale 3 (Bed0) is 808 units
  tall and walk-through, as in MM9 (not Solid); the throne at 2.5 is 670 units tall (radius 180).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_yanmirsfort_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
python3 scripts/tables.py --apply                 # takes mm9r_common/locks/mm9_decorations.lock itself
python3 scripts/placements.py --verbose           # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
blender --background --factory-startup --python scripts/review_closeup.py
```

`tables.py --apply` must not run under an outer `flock` on the same lock file. `textures/flame02_basecolor.png` is a
copy of Chasm of the Dead's blue flipbook. `work/survey_models.py` lists every MM9 props project's (ABC, skin) -> prop
table (`work/survey_models.json`), the reuse search; `work/debug_key_import.py` shows Blender's import of a raw GLB
(it evaluates the first animation: how the key's Static_Model pose was found).
