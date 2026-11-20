# MM6 dungeon decorations in 3D

Static 3D replacements for the decoration sprites of the 51 MM6 dungeons (BLV maps), bound in
`assets_dev/worlds/mm6/models/indoor_decorations.yml`. Plan: `../MM6_3D_DECORATIONS_IMPLEMENTATION_PLAN.md`. Builder
brief: `BRIEF.md`. Engine side: `engine/render/MODEL_RENDERING.md` section 10.

- `inventory.json` lists every decoration placed in the MM6 dungeons, with its count, native frames, size and scale.
- `source/unity_labs_vfx/` holds the CC0 flame flipbooks (licence in that folder).
- `textures/` holds the shared flames (`FLAMES.md`) and the project's own textures.
- `torch_textures/` holds the CC0 PBR texture sets shared by the wall torches (pilot, iron torch, torch01).
- `scripts/` holds the pilot torch build, the flame generator, `dungeon_lib.py` and `finish.py`.
- One folder per builder batch holds its own scripts, textures, review sheets and README: `torches/`, `fire/`,
  `containers/`, `crystals/`, `hanging/` and `leftovers/`.

## Flames

Every fire decoration, indoor and outdoor, uses one flame. It is the CC0 Unity Labs Flame02 flipbook (Flame03 for
candles), recoloured by `scripts/make_flames.py` to the brightness ramp of the native MM torch flame, with the smoke
faded out. The upscaled native flame frames were too poor. See `textures/FLAMES.md` for the card recipe. The outdoor
props share it through `props_lib.flame_material()`.

## Pilot: the wall torch (`scripts/build_torch.py`)

| GLB | Decoration | Triangles (LOD0 / 1 / 2) | Notes |
|---|---|---|---|
| `mm6_deco_torch.glb` | `6torch01` (3441 placements in 37 maps) | 454 / 267 / 149 | wall plate, arm, open ring clamp (hoops and bars), tarred head, embers, flame card |
| `mm6_deco_torch_free.glb` | `6torch01` without a wall in reach | 382 / 243 / 125 | open ring clamp only |
| `mm6_deco_torch_unlit.glb` | `torchnf` | 412 / 237 / 127 | charred head, no flame |
| `mm6_deco_torch_unlit_free.glb` | `torchnf` without a wall | 340 / 213 / 103 | |

Proportions come from the native sprite: stick 7 units wide, an open clamp at 26-43 (two flat hoops joined by thin
bars, a solid ring at LOD2), head at 60-74, flame to 128. The torch
axis is the model origin. The plate is at Blender +y (the model's back), so `mount: wall` hangs it on the nearest
face. In the MM6 dungeons, 3398 torches mount on a wall and 43 stand free; those are stray placements in the
original maps, such as Goblinwatch entity 141.

Surfaces (Revision 2): the shared CC0 Poly Haven PBR sets of `torch_textures/` (weathered wood stick, tar-soaked
wound rag, rusty forged iron), which the iron torch and torch01 also use. See `torch_textures/README.md`.

Colour: the native torch is painted very dark, and a self-lit flame sprite is drawn at light one. Each material
therefore carries a COLOR_0 tint (`TARGETS`, `tlib.tint`) that brings its texture to the sprite's measured colour:
stick (44, 22, 9), clamp (36, 19, 10), head (38, 21, 10). The unlit torchnf sprite is lit by its sector and painted
lighter, so it has its own targets: stick (67, 43, 21), clamp (63, 47, 32), head (72, 47, 26).

Rebuild: `make_flames.py`, then `torch_textures/scripts/run_all.sh --install torch torch_free torchnf torchnf_free`
(textures, `scripts/build_torch.py`, `scripts/finish.py`, review sheets in `torch_textures/review/`).

Checks: the regression `mm6_decoration_models_indoor_wall_torches` (Goblinwatch: wall mounts, free-standing, picking
head-on and of the turned flame card), and captures in `output/indoor_torch_pilot_20261009/` (`v5/` with the Unity
flame; `flame_before_after.png`).
