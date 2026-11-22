# P5 shrine: the two great stone hands (D-56), 2026-11-21

Lane S sub-agent `xeen-s7-p5`. The Pharaoh's shrine on P5 (Clouds of the Ancients): two great open stone hands, palms
up, standing on the 64-high dais (not on columns, D-56 change 9), 768 apart, 448 tall (P5's L1 plan), holding the Cube
and the Scepter after the ceremony. A built mesh, **no Meshy, no Codex**: the Carnage Hand's rigged mesh
(`level_generation/creatures/xeen_hand_claude/work/rig_v1.blend`, read only) without its palm mouth, posed open and
cupped, on a built forearm and a round stepped plinth, in a pale ivory marble with gold veins. One right hand; the left
is its mirror (the Xeen feet's way).

| Decoration | Row / sprite | Model | Height | Radius | LOD triangles |
|---|---|---|---|---|---|
| `xeen_stonehand` (the right hand: the WEST one) | 4017 / 27017 | `worlds/xeen/models/xeen_deco_stonehand_r.glb` | 448 | 124 | 7,000 / 3,500 / 1,610 / 630 |
| `xeen_stonehand_l` (its mirror: the EAST one) | 4018 / 27018 | `worlds/xeen/models/xeen_deco_stonehand_l.glb` | 448 | 124 | same |

Bindings in `assets_dev/worlds/xeen/models/indoor_decorations.yml` (`yaw: facing`, **`yaw_offset: -1.570796327`**).
The engine shows a decoration's glTF +Z front at facing + 90 degrees (facing 270 would face east); A5's generator uses
facing as the direction the front looks (hands 270 = south), so the offset makes that true. A binding cannot mirror a
model, so the left hand has its own row and model.

## Sizes and placement (for A5)

- Origin at the plinth's bottom centre; the **palm centre is straight above the origin** at 390 (the palm slopes 14 deg
  to the front: about 400 at the heel side, 378 toward the fingers; level across). Fingertips 448.
- Plinth radius 124 (collision radius): at x = +-384 the plinths end at 508, inside the dais's 512 edge. The fingers and
  thumb reach 225 to the outside and 249 to the front, about 390 up: in the air past the dais's side edges by about 100.
- Fingers to the front (south at facing 270); each thumb points outward (west hand west, east hand east), so the pair
  reads as one giant's two hands offering.
- A5's generator already places `xeen_stonehand` at both (sx +- 384, sy + 64): the east one must be `xeen_stonehand_l`.

## Build (`build.sh`; Blender through lane S's lock)

1. `scripts/build_high.py`: the hand's fingers opened and cupped (`scripts/hand.json` `flex`, the hand project's
   `handpose.py`), the pose baked, the mouth parts (face attribute `part` != 0) deleted and the palm hole filled
   (`triangle_fill`, relaxed), the hand turned palm up (tilt 14 deg to the front) with the palm centre at 0.62 over the
   origin; a forearm swept from the plinth to the heel (superellipse section, 0.112 x 0.072 at the wrist, 1.3x at the
   base, the end sunk 6 cm into the heel); a two-step round plinth; the union voxel-remeshed (4 mm) and smoothed.
2. `scripts/lowbake.py` (from `xeen_idols_claude`): LOD0 by collapse to 7,000 triangles; UVs `claude_shared/uv_atlas.py`
   (PartUV charts, sparrow pack, 7 runs: 3 runs did not fit once); normal baked from the high hand; colour and roughness
   evaluated on the low hand: MM7 `7tws1h` grain on an ivory ramp, MM9 `marb94orui`'s veins as gold, AO and cavity.
   `scripts/bake_color.py` re-bakes colour and roughness on the saved UVs.
3. `scripts/finish_maps.py` (gutter fill last), `scripts/export_hand.py` (LOD1-3, 0.5 / 0.23 / 0.09),
   `tools/link_static_model_lods.py`, `scripts/mirror_glb.py` (x negated, windings reversed, UVs kept), winding.

Maps: 2048 base colour (sRGB luminance p1 170 / p50 210 / p99 228), 2048 normal, 1024 metallic-roughness (polished
marble, the veins smoother, crevices rougher; metallic 0). Texture quality: atlas 63.4 %, density p10/p50/p90 1022/1085/1161 (spread 1.14), 7 islands,
fragments 0 %, stretch p90 1.19. Winding: 0 inverted closed parts (both).

```sh
level_generation/decorations/xeen_p5hands_claude/build.sh
python3 tools/install_model.py level_generation/decorations/xeen_p5hands_claude/export/xeen_deco_stonehand_r.glb --world xeen
python3 tools/install_model.py level_generation/decorations/xeen_p5hands_claude/export/xeen_deco_stonehand_l.glb --world xeen
python3 level_generation/decorations/xeen_p5hands_claude/scripts/measure.py <glb> 448   # palm heights in units
```

## Checks

- Clay and textured renders: `review/high/sheet.png`, `review/tex_sheet.png`.
- In game (`build-xeen`, X6 with the scratch overlay of `xeen_p5props_claude/scripts/ingame_overlay.py`: both hands at
  +-384 facing 270 as A5 places them, the Cube and the Scepter at their spots, outdoor copies of the bindings):
  `../xeen_p5props_claude/review/ingame/sheet.jpg` and `sheet4.jpg` (front, close, three-quarter both hands, the palms
  from above, the pair from eye height). Front faces south as intended; the Cube sits in the west palm.

## Known limits

- The forearm is a clean swept tube: it reads as a sculpted forearm rising from a plinth, without muscle detail.
- The source hand is the Carnage Hand (heavy knuckles, thick fingers); collapse decimation leaves facets on the fingers
  close up.
- Not seen on P5 itself (A5 has not placed them yet); only on X6 in daylight.
