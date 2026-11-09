# MM9 Dungeon of Secrets props as 3D decorations (2026-10-31)

The claw torches, the hanging claw lamp and the demon-head wall sconces of MM9's Dungeon of Secrets
(`DUNGEONOFSECRETS.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_dungeonofsecrets/)). No paid services, no Meshy, no Codex: the one model built here
is MM9's own mesh with its skin x4 (plain Lanczos, the isle's `textures.upscale`).

**Route.** Dark Passageway's scripts ([`../mm9_darkpassageway_claude/`](../mm9_darkpassageway_claude/README.md)), which
are Yanmir's Fort's family ([`../mm9_yanmirsfort_claude/`](../mm9_yanmirsfort_claude/README.md): one material per MM9
skin, the isle's `blib` and `finish` checks, the Anskram flame cards in `card` mode), plus Yanmir's
`review_closeup.py` for the flame. `build.py` gained two things for the sconce: a flame seat found on the head's crown
(`crown_seat`) and vertex occlusion without a floor for wall-hung props (Chasm of the Dead's `hung`).
`tables.py --apply` runs under the decorations lock.

## Outputs

The DAT holds **55** Prop and Torch objects (35 `Prop`, 20 `Torch`), not 57: 34 claw torches, 1 claw lamp, 20
sconces (`work/raw_objects_compact.json`, the map project's `work/dat_objects.json`: the same 55).

- **1 model** built and installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_sconce2.glb`), through `check_winding.py` (0 inverted closed parts, in
  `finish.py` and run on its own before the install):

| Prop | ABC / skin | Triangles (LODs) | Notes |
| --- | --- | --- | --- |
| `sconce2` | SCONCE2 / Sconce2 | 380 / 183 / 98 + 2 flame cards | demon's head on the wall; **orange** flame cards (the isle's CC0 Flame02 flipbook, not recoloured) on the crown, `card` mode |

- **Reused** (GLBs and rows stay with their owners):
  - Dark Passageway's `clawtorch` (CLAWTORCH / ClawTorch, upright, Scale 1: these 34 are upright too) at its own row
    `mm9_clawtorch`;
  - Yanmir's Fort's `clawlampp180` (CLAWLAMP, pitch pi baked in) for Prop46 (Rotation [3.142, 3.142, 0]: pitch pi,
    yaw pi), at a new scale row. **Skin:** MM9 skins this lamp with ClawTorch.dtx, Yanmir's with ClawLamp.dtx. The two
    skins share one layout (blue ice orb, scales, brass band; `work/skin_compare.png`, mean difference 13/255); the
    torch skin only adds a wood patch, and none of the lamp's 1263 UVs falls in it. Reused as is, not rebuilt.
  - Chasm of the Dead's `bluesconce` is SCONCE2 too, but with blue flame cards: not reused (its flames are blue; MM9's
    fire here is orange). No other installed model is SCONCE2 (`mm9_deco_sconce1*` and `sconcetorch` are SCONCE1 /
    TORCH2, `walltorch` WALLTORCH, `torchmetal` another model; Yanmir's `work/survey_models.json`).
- Rows **2436-2437** (2 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26237-26238**,
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended in one run under
  `mm9r_common/locks/mm9_decorations.lock`. No row carries a light; none has collision (wall- and ceiling-hung, not
  Solid in MM9). Decoration per prop and DAT scale (the names props.json uses):

| Prop | Scale | Decoration (row) | Height | Collision | Placements |
| --- | --- | --- | --- | --- | --- |
| sconce2 | 1.5 | `mm9_sconce2` (2437) | 97.8 (flame included) | none | 20 (`Prop0`-`Prop19`) |
| clawtorch | 1.0 | `mm9_clawtorch` (2386, reused) | 77.7 | none | 34 |
| clawlampp180 | 1.0 | `mm9_clawlampp180_x100` (2436, new row of Yanmir's model) | 49.8 | none | 1 (`Prop46`) |

  As in Yanmir's Fort, the scale nearest 1 takes the plain name: `mm9_sconce2` is Scale 1.5; Yanmir's
  `mm9_clawlampp180` is Scale 2, so Scale 1 is `_x100`.
- `../../projects/mm9r_dungeonofsecrets/props.json`: **55 placements**, all `kind: torch` (Dark Passageway's kind for
  its claw torches), each under its DAT object name (`source_name`; no name repeats, none is a decoration's name),
  `script`/`script_params` null (no prop here is scripted). **All 55** are checked against the old map's baked BModel
  of the same object: **median of medians 0.54 units**, worst 0.74 (Prop10-Prop19). Per model: claw torches 0.54 (all
  34), claw lamp 0.44, sconces 0.61 (Prop0-9, yaw 270) and 0.74 (Prop10-19, yaw 89.5).
- `review/props_sheet.png`: contact sheet of the built model (LOD0 front, three-quarter, side, behind-above, below,
  LODs; looked at). `review/sconce2/closeup_*.png` (`scripts/review_closeup.py`) and `review/sconce2/closeup_sheet.png`:
  the flame from the side (both sides), front, three-quarter and above (looked at: from the side the card stands
  edge-on on the crown's apex, over the skull between the face and the horns, not over the wall side).

## Flames

- **Sconces (`mm9_sconce2`): orange flame cards on the crown.** MM9's `Torch` class draws a particle fire (Fire 1,
  FireColor 220,180,0 -> 255,215,0, FireRadius 2 LT, rising about 15 LT over its 1 s life) at the object origin +
  FireOffset (0, 2, 0) LT. That point is inside the head, low (the ABC origin is 11 units above the base of a 47-unit
  head; Chasm's README puts the `FireNode` socket inside the head at the chin too), so in MM9 the fire rises through
  the head and shows above the crown. Here the
  cards stand on the crown: `crown_seat` takes the highest vertex within 12 % of the width of the head's centre line
  (the horns stand out at the sides) and found (0.000, 0.074, 0.518) m in the asset frame, the same point Chasm of the
  Dead picked by hand for `bluesconce`. Card sizes: the Anskram torch's (Chasm's `TORCH_FLAME`) divided by the Scale
  1.5, so the placed flame is the same size as every other MM9 wall torch's (MM9's fire is not scaled by the prop's
  Scale). Material: the isle's FIRE (unlit, BLEND, `openyamm_billboard: card`, 16x4 flipbook at 30 fps).
- **Claw torches and the claw lamp: no flame.** They are `Prop` class objects here (not `CandleProp` as in Dark
  Passageway and Yanmir's Fort), which have no fire in MM9. The reused models keep their owners' orb: the claw torch's
  orb glows blue (emission, flicker), the lamp's orb glows blue (no flame cards on either).

## Notes for the map

- **Which entries carry flames:** the 20 `Torch` entries (`decoration: mm9_sconce2`, `"flame": true`). The 35 claw
  entries have `"flame": false`.
- **Lights:** every entry names its nearest MM9 light (`light`; from the DAT Light objects, since the map project's
  `work/lights.json` did not exist when this ran: rerun `python3 scripts/placements.py` after `convert.py` writes it to
  name the kept lights instead). Each claw has its own MM9 light **at its exact position** (distance 0, radius 100 LT =
  256 units, BrightScale 0.45): mostly warm 255/201/147, blue (100-128/100-128/255) at Prop32-35, red 255/0/0 at
  Prop42-44, Prop46 and Prop55, 255/193/193 (radius 500 LT) at Prop52-53. Each sconce has its own red light 206/0/0
  (radius 40 LT = 102 units, BrightScale 0.95) 29 units away. Keep them as BLV lights; 55 distinct lights for 55 props.
  The Torch objects' own `LightColor1` 255/190/130 has `LightMaxRadius` 0 (no light of their own).
- **Blue orbs under warm light:** the reused claw torch's orb glow is blue (Dark Passageway's), while most claws here
  sit in warm or red MM9 lights; MM9's ClawTorch skin paints the orb pale blue too, so it is not wrong, but the glow
  is ours. If it reads odd in game, a warm-orb variant is one `ORB` change in a rebuilt copy (not done: the brief said
  reuse).
- **TintColor (45, 0, 0) on all 35 claws: not carried.** MM9 multiplies a prop's lit colour by TintColor/255 when it
  is set (`MM9_RENDER_LIGHTING_RE.md`, object colour), so MM9 likely draws these claws very dark red; the engine has no
  per-placement tint (`MM9_VISUAL_PROPERTIES.md` D: a tinted variant). The entries carry `"tint": [45, 0, 0]` so the map
  can list it as a deviation. Not built: whether MM9 really draws them near black is not proven by a screenshot (none
  of this map in `overnight/real_mm9/`), and the brief asked to reuse the claw models.
- Positions are the old bake's base centres in the old map's frame (`overrides.yml` offset 0). The sconces' base is 32
  units under the DAT origin (the ABC origin is 11 units above the base, x1.5).
- No collision on any row; not Solid in MM9.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_dungeonofsecrets_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_dungeonofsecrets_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose           # names work/lights.json's kept lights once the map writes it
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
blender --background --factory-startup --python scripts/review_closeup.py
```

`textures/flame02_basecolor.png` is the isle's orange flipbook (md5 c6e0be48..., unrecoloured). A rerun of
`tables.py --apply` reports 0 rows to add.

## Not done

- Not looked at in game (no game run: the map is not built yet). The flame's side view is judged from the Blender
  closeups only; the map agent should look at one sconce's flame from the side in game, as the brief asks.
- TintColor (45, 0, 0) of the claws (above). The claw lamp's ClawTorch.dtx skin (Yanmir's ClawLamp.dtx used, same
  layout).
