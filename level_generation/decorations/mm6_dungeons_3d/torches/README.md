# MM6 dungeon torches in 3D (batch C2, 2026-10-09)

Static glTF replacements for the MM6 dungeon torch decorations, built after the pilot (`../scripts/build_torch.py`)
and the common brief (`../BRIEF.md`). Everything is procedural Blender modelling traced from the restored native
frames (`assets_dev/engine/decorations_x2/`); proportions are measured in native world units (`units()`, 81.7 per
metre) and every model's bounds height equals its sprite's logical height, so the binding height scales it 1:1.

| Decoration | Placements | Model (`assets_dev/worlds/mm6/models/`) | LOD triangles | Size |
|---|---|---|---|---|
| trchb00 (lit iron torch) | 755 | `mm6_deco_irontorch.glb` / `_free` | 544/336/194, free 484/324/182 | 2.2 MB |
| nwtrchnf (unlit) | (event toggle) | `mm6_deco_irontorch_unlit.glb` / `_free` | 490/298/166, free 430/286/154 | 1.1 MB |
| torch01 (wooden wall torch) | 75 | `mm6_deco_torch01.glb` / `_free` | 424/256/86 | 3.1 MB |
| torch03 (hanging brazier) | 6 | `mm6_deco_torch03.glb` | 812/512/198 | 1.9 MB |
| torskul0 (skull torch) | 2 | `mm6_deco_torskul.glb` / `_free` | 2573/1069/450, free 3206/1314/534 | 2.4 MB |

torch2 has no decoration entry and is skipped.

## Revision 2: torch03 surfaces (2026-10-09)

After the user's gallery review ("solid colours, no texture/roughness") torch03's materials use PBR sets derived
from CC0 Poly Haven scans by `scripts/make_pbr_textures.py` (sources downloaded by
`../fire/scripts/fetch_textures.py` into `../fire/source/polyhaven/`, derivation shared in `../fire/scripts/pbr.py`;
base colour, OpenGL normal and metallic-roughness, 256 px): `t3_iron` (Rusty Metal 04, Amal Kumar) for the dish
flank, floor and finial, `t3_paint` (Blue Metal Plate, Rob Tuytel) for the blue-painted underside, `t3_brass`
(Rusty Metal 03, Amal Kumar) for the rim and ring, and `t3_chain`: the link strip with Rusty Metal 03's detail and a
normal map from the links' relief. The coal dome is a lit `Glow` material (`t3_ember`: Marble Rock 01 through a fire
ramp, its cracks glowing) with a constant emission sRGB (165, 60, 18) and `openyamm_pulse [0.15, 1.0]`, replacing the
unlit `Coals`. COLOR_0 targets: underside (50, 55, 107) as measured, darker rim top and dish floor, dome albedo
(105, 40, 13) under the emission. Geometry and budgets are unchanged. The other torch models are not rebuilt.
Gallery shots: `review/rev2_before/`, `review/rev2_after/` (`dungeon_torch03_side.png`).

## Models

- **Iron torch (trchb00 / nwtrchnf).** One iron body for both: foot ring, shaft, two collar rings about a 26-wide
  wall plate with four bolt heads, and a fluted bowl whose rim is at 92.6. The lit model has an unlit ember bed in the
  open bowl and the flame card (91-130); the unlit one has a closed cap at 93. Both have the plate back at
  y = +8.5 units and the same scale (heights 130 and 93), so a toggle keeps the bracket in place on the wall.
- **torch01.** A wall fixture: a thin stick through a chamfered wooden holder block (24 wide, 44-54) that reaches back
  to the wall, a turned collar under the block, a wound cloth head (68-82) with an ember ring, and the flame card
  (81-128). The free variant keeps a shallow block centred on the stick.
- **torch03.** A hanging fixture, not a wall one: a wide iron dish (blue-painted underside, fire-lit rim), turned
  finial, a glowing coal dome (emissive), four chains to a gold ring and one chain up to the bounds top (the ceiling end and
  the pivot a swing binding would use). Chains are crossed cut-out ribbons (`textures/chain_basecolor.png`, MASK,
  double-sided). The model starts at the finial's foot, 9.5 units above the sprite's bottom: z_offset 9.5.
- **torskul0.** A dark bronze post with the same kind of bracket plate as the iron torch, three skulls bowed 22
  degrees round a sunken fire cup, struts beneath them and the flame card (108.5-179). The skulls are the bones
  batch's Meshy skull (31 units wide, `../bones/textures/skullfire_*`, fire-lit orange) with a height gradient in COLOR_0,
  bright crowns to near-black jaws, as painted. Wall-mounted (two placements; the plate is level with the side
  skulls' backs); the free variant drops the plate and adds a fourth skull at the back.

Flames: every card uses the shared CC0 Unity Labs flipbook `../textures/flame02_basecolor.png`
(`openyamm_flipbook: [16, 4, 30]`, billboard, BLEND, double-sided, unlit), sized by `../textures/FLAMES.md`
(card width = native flame width / 0.6, lower 80 % of each frame, flat base just inside the fixture's head, card
top at the sprite's top).

Colour: each material's COLOR_0 is vertex occlusion times a tint that brings its mean to the native sprite's
measured mean (`tlib.tint`, linear), with painted gradients (`shade()` in each builder). `sheet.py` prints native
versus model band means from a flat (emission only, light one) front render; the final values are within a few
sRGB levels on most bands (see Compromises).

## Suggested bindings (indoor_decorations.yml)

```yaml
  - name: trchb00
    model: worlds/mm6/models/mm6_deco_irontorch.glb
    free_model: worlds/mm6/models/mm6_deco_irontorch_free.glb
    height: 130
    mount: wall
  - name: nwtrchnf
    model: worlds/mm6/models/mm6_deco_irontorch_unlit.glb
    free_model: worlds/mm6/models/mm6_deco_irontorch_unlit_free.glb
    height: 93
    mount: wall
  - name: torch01
    model: worlds/mm6/models/mm6_deco_torch01.glb
    free_model: worlds/mm6/models/mm6_deco_torch01_free.glb
    height: 128
    mount: wall
  - name: torch03
    model: worlds/mm6/models/mm6_deco_torch03.glb
    height: 119
    z_offset: 9
  - name: torskul0
    model: worlds/mm6/models/mm6_deco_torskul.glb
    free_model: worlds/mm6/models/mm6_deco_torskul_free.glb
    height: 179
    mount: wall
```

All scales are 1.0, so heights are the logical heights (torch03: 128 - 9.5 = 118.5, rounded; z_offset 9 puts the
chain top at the sprite top). All animated sprites are covered by the flame flipbook, so none needs `still`.
torch03 may take an optional `swing: [3, 2.5]` (natively it does not swing).

## Compromises

- Iron torch and torch01 surfaces (Revision 2): the shared CC0 PBR sets of `../torch_textures/` (glossy dark blue-grey
  `darkiron`; `torchwood` and the wound `torchrag` for torch01), see `../torch_textures/README.md`. The flat render
  shows no highlights; the iron's low roughness gives them under light.
- The trchb00 plate's scroll ornaments and torch01's carved holder pattern are left to the textures (plain boxes).
- The flame02 flipbook replaces the native flames: its bright body is shorter and broader than trchb00's tall flame
  and torskul0's thin wavy one (the torskul card is narrow, so the flame is stretched somewhat).
- torch03: the native fire's dithered black smoke is gone; one card stands for the whole brazier fire. Chains are
  ribbons, so they read thin when seen along their length.
- torskul0 (revision 2, 2026-10-09): the skulls are the bones batch's Meshy skull (`../bones/README.md`), with its
  jaw, fire-lit by `../bones/textures/skullfire_*`; the procedural skull and `textures/skulllit_*` are no longer used.
- Each GLB embeds its own copy of the flame02 atlas (about 0.8 MB of each lit model's size).

## Sources and licences

- torch03 (revision 2): `textures/t3_*`, derived from CC0 Poly Haven textures (https://polyhaven.com/license),
  see above.
- Textures: the outdoor props textures (`../../mm6_new_sorpigal_3d/props/textures/`, read only: iron, wood, leather,
  bronze, gold, embers, skull); `textures/skulllit_*` and `textures/chain_basecolor.png` are generated here by
  `scripts/make_textures.py` (procedural, project-owned). Flames: `../textures/flame02_basecolor.png`, CC0 Unity Labs
  VFX flipbook (see `../textures/FLAMES.md`).
- Iron torch (trchb00 / nwtrchnf) and torch01: CC0 Poly Haven sets (Rough Wood, Hessian 380, Rusty Metal 04, Rust
  Coarse 01), processed in `../torch_textures/` (sources and authors in its README).
- Geometry: procedural (this folder's scripts); the skull mesh follows the outdoor skull pile's builder.

## Scripts

- `scripts/tlib.py`: shared helpers (materials, flame card, tints, skull, export).
- `scripts/build_irontorch.py`, `build_torch01.py`, `build_torch03.py`, `build_torskul.py`: one per fixture.
- `scripts/make_pbr_textures.py`: torch03's PBR sets (revision 2).
- `scripts/finish.py`: this batch's FINISH table (budgets, material modes); `--install` installs at 0664.
- `scripts/review.py` + `scripts/sheet.py`: review renders and sheets in `review/<prop>/` (compare.png, lods.png).
- `scripts/run.sh <build script> <prop> <native texture> [--install] [z0:z1 ...]`: build, finish, review, sheet.
