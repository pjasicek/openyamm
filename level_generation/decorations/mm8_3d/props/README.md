# MM8 props in 3D (batch `props/`, 2026-10-15)

Static 3D replacements for the MM8 prop decorations: skeleton `dec05`, bones `dec29`/`dec21`, carrion `dec22`, barrel
`dec03`, rune posts `dec13`-`dec17`, elf statue `dec01`, tableware `dec32`/`dec36`/`dec37`/`dec39`, and the four
models shared with MM7 (`mm7_deco_cauldron`, `mm7_deco_trash_heap`, `mm7_deco_goblet`, `mm7_deco_fruit_bowl`).
Brief: `../BRIEF.md`. All installed with `python3 tools/install_model.py <glb> --engine --name <name>` (through
`scripts/finish.py <prop> --install`).

## Status (2026-10-16): all 19 models installed

Every model is installed with `scripts/finish.py <prop> --install` (`tools/install_model.py --engine`), passes
`../animated/scripts/check_winding.py` (0 inverted closed parts; `finish.py` now refuses otherwise, and
`mm8lib.export` flips inside-out closed pieces before export). Nothing is built but not installed.

| Model (`engine/models/`) | Sprite (placements) | LOD triangles | File | Extent x / up / depth (m) | Review |
|---|---|---|---|---|---|
| `mm8_deco_skeleton.glb` | dec05 (223) | 2490 / 1059 / 602 | 4.6 MB | 1.01 / 0.41 / 0.46 | `review/skeleton/` |
| `mm8_deco_bonepile.glb` | dec29 (78) | 2495 / 1145 / 478 | 1.9 MB | 1.15 / 0.40 / 0.72 | `review/bonepile/` (Meshy, below) |
| `mm8_deco_carcass.glb` | dec21 (9) | 2978 / 1356 / 594 | 2.0 MB | 1.11 / 0.68 / 1.00 | `review/carcass/` (Meshy, below) |
| `mm8_deco_carrion.glb` | dec22 (1) | 3500 / 1600 / 650 | 2.0 MB | 1.19 / 0.73 / 0.86 | `review/carrion/` (Meshy, below) |
| `mm8_deco_barrel.glb` | dec03 (144) | 1008 / 416 / 140 | 1.3 MB | 0.62 / 0.75 / 0.62 | `review/barrel/`, `review/barrel_liquids/sheet.png` |
| `mm8_deco_runepost13.glb` | dec13 (36) | 926 / 294 / 99 | 5.5 MB | 2.53* / 3.12 / 2.57* | `review/runepost13/` |
| `mm8_deco_runepost14.glb` | dec14 (33) | 776 / 254 / 91 | 5.4 MB | 1.43 / 3.12 / 1.43 | `review/runepost14/` |
| `mm8_deco_runepost15.glb` | dec15 (45) | 1016 / 332 / 132 | 5.5 MB | 1.48* / 1.52 / 1.61* | `review/runepost15/` |
| `mm8_deco_runepost16.glb` | dec16 (26) | 984 / 316 / 124 | 5.4 MB | 0.75 / 1.52 / 0.72 | `review/runepost16/` |
| `mm8_deco_runepost17.glb` | dec17 (85) | 608 / 210 / 79 | 5.5 MB | 0.80* / 0.75 / 0.81* | `review/runepost17/` |
| `mm8_deco_elfstatue.glb` | dec01 (5) | 5805 / 2360 / 874 | 6.8 MB | 1.00 / 2.15 / 0.56 | `review/elfstatue/compare.png`, `compare_views.png` |
| `mm8_deco_metalbowls.glb` | dec32 (4) | 1344 / 784 / 448 | 2.2 MB | 0.25 / 0.16 / 0.25 | `review/metalbowls/` |
| `mm8_deco_woodplate.glb` | dec36 (6) | 384 / 224 / 128 | 2.8 MB | 0.24 / 0.02 / 0.24 | `review/woodplate/` |
| `mm8_deco_woodplates.glb` | dec37 (2) | 1408 / 768 / 384 | 2.8 MB | 0.24 / 0.06 / 0.24 | `review/woodplates/` |
| `mm8_deco_metalplates.glb` | dec39 (4) | 1672 / 912 / 456 | 2.3 MB | 0.24 / 0.06 / 0.24 | `review/metalplates/` |
| `mm7_deco_cauldron.glb` | dec26 / 7dec03 (5) | 2334 / 830 / 366 | 6.4 MB | 1.12 / 1.01 / 0.93 | `review/cauldron/` |
| `mm7_deco_trash_heap.glb` | dec23 / 7dec01 (31) | 2171 / 474 / 190 | 6.0 MB | 1.50 / 1.04 / 1.44 | `review/trashheap/` |
| `mm7_deco_goblet.glb` | dec35 / 7dec48 (6) | 280 / 128 / 60 | 0.05 MB | 0.13 / 0.30 / 0.13 | `review/goblet/` |
| `mm7_deco_fruit_bowl.glb` | dec28 / 7dec08 (4) | 2857 / 1343 / 520 | 4.6 MB | 0.38 / 0.25 / 0.34 | `review/fruitbowl/` |

\* the bramble skirt cards (alpha tested, mostly transparent) widen the bounds; the stone is the sprite's width.
Sizes are the source GLBs; the cooked runtime copies are smaller.

### Suggested bindings

Lying and flat props are bound so the model's width matches the sprite's (the sprites' opaque heights include the
ground seen from above). Every prop is static except the cauldron.

```yaml
  - {name: dec05, model: engine/models/mm8_deco_skeleton.glb, height: 83, height_jitter: 0.05}
  - {name: dec29, model: engine/models/mm8_deco_bonepile.glb, height: 39, height_jitter: 0.05}
  - {name: dec21, model: engine/models/mm8_deco_carcass.glb, height: 78}
  - {name: dec22, model: engine/models/mm8_deco_carrion.glb, height: 77}
  - {name: dec03, model: engine/models/mm8_deco_barrel.glb, height: 117, height_jitter: 0.05}
  - {name: dec13, model: engine/models/mm8_deco_runepost13.glb, height: 255}
  - {name: dec14, model: engine/models/mm8_deco_runepost14.glb, height: 255}
  - {name: dec15, model: engine/models/mm8_deco_runepost15.glb, height: 124}
  - {name: dec16, model: engine/models/mm8_deco_runepost16.glb, height: 124}
  - {name: dec17, model: engine/models/mm8_deco_runepost17.glb, height: 61}
  - {name: dec01, model: engine/models/mm8_deco_elfstatue.glb, height: 217}   # yaw from the placement (directional)
  - {name: dec32, model: engine/models/mm8_deco_metalbowls.glb, height: 37}
  - {name: dec36, model: engine/models/mm8_deco_woodplate.glb, height: 6}
  - {name: dec37, model: engine/models/mm8_deco_woodplates.glb, height: 14}
  - {name: dec39, model: engine/models/mm8_deco_metalplates.glb, height: 16}
  - {name: dec26, model: engine/models/mm7_deco_cauldron.glb, height: 128}    # animated: flipbook + pulses
  - {name: dec23, model: engine/models/mm7_deco_trash_heap.glb, height: 92, height_jitter: 0.05}
  - {name: dec35, model: engine/models/mm7_deco_goblet.glb, height: 30}
  - {name: dec28, model: engine/models/mm7_deco_fruit_bowl.glb, height: 40}
```

The rune posts' `Rune` material is alpha tested, emissive (0.55, 0.03, 0.02) with `openyamm_pulse [0.3, 3.0]` (the
runes glow faintly, out of step per post). The cauldron: `Fire` (shared Flame02 flipbook, `[16, 4, 30]`,
billboard, blended, unlit, last primitive), `Brew` unlit, `Coals` emissive with `openyamm_pulse [0.35, 1.7]`,
`Char` logs with a faint `[0.35, 1.3]` pulse; no `still` needed.

### Meshy rebuild of the bone pile, carcass and carrion (2026-10-16, paid generation approved by the user)

Project `meshy/` (receipts `meshy/creature_3d_progress.json`, requests `meshy/requests/`, downloads `meshy/meshy/`):
1. HD masters by Codex (`meshy/<prop>/references_hd/`: `CODEX_BRIEF.md`, `generation_runs.json`,
   `selected_views_review.png`) from the ORIGINAL native bitmaps (`assets_dev/_legacy/sprites_original/DEC29.bmp`,
   `dec21.bmp`, `dec22.bmp`, cropped and enlarged 6x on magenta) plus the archived x2 frame as surface material only:
   `00_three_quarter.png` and `01_front.png`, 1536 x 1024. Three parallel Codex runs, one corrective regeneration
   each. The returns had near-opaque alpha (252-253) and a faint glow, so `00_three_quarter_meshy.png` (binary
   alpha, threshold 100, hashes in `meshy/references_selected.json`) is what Meshy received.
2. Meshy image-to-3D (`ai_model` latest, PBR texture, remeshed to 30k triangles): 30 credits each, **90 in total**
   (bonepile `01a14351-2132-73a6-8e86-3c741e003c42`, carcass `01a14351-2a65-72e4-990f-1d1327d1dd3e`, carrion
   `01a14361-b078-77e1-a6f5-30463ff9bb24`).
3. `scripts/meshy_prop.py -- <prop>`: weld, drop crumbs, yaw +35 degrees (Meshy's front is the three-quarter camera),
   scale to the sprite width, flatten the base onto the ground; LOD0 = voxel remesh decimated to the budget with
   Smart UV in [0, 0.875]^2; LOD2 = a 4x coarser voxel remesh with its own charts in the atlas corner (collapsing
   LOD0 that far shattered it); both baked together on the CPU from the Meshy mesh (base colour, roughness,
   normal, AO; 1024). LOD1 = LOD0 collapsed. `scripts/meshy_textures.py` grades the bakes: AO into the colour,
   luminance contrast 1.35, per-channel linear gains so the culled review render's mean matches the sprite's
   (`meshy/prop_overrides.json`; neutral texels keep a neutral gain, so the carcass's grey skin stays grey),
   roughness rescaled to 0.62-0.8 (bone) / 0.6-0.75 with the glossiest 4 % as wet spots at 0.35 (meat).
   Rendered means vs sprite: bone pile 131, 120, 99 / 127, 116, 94; carcass 157, 117, 81 / 152, 112, 76;
   carrion 147, 93, 62 / 147, 91, 57.
4. COLOR_0 is white (the light is in the bake). Winding check 0 inverted closed parts; reviews with back faces
   culled (`review.py` now sets it for every material).
The earlier procedural builds (`build_bonepile.py`, `build_carcass.py`, `build_carrion.py`) remain for reference.

### Stat barrel liquids (2026-10-16)

`scripts/build_liquids.py` (copied from the MM6 barrel's builder, read only) writes seven discs in
`mm8_deco_barrel.glb`'s asset space, installed as `engine/models/mm8_deco_barrel_liquid_<red|yellow|blue|orange|green|
purple|white>.glb`: one 161-triangle disc each, no LOD chain (as the MM6 liquids), the MM6 colours, foam and bubbles,
glossy and 50 % transparent (BLEND) with a faint glow and a slow `openyamm_uv_scroll [0.016, 0.011]` drift. The
surface is at y 0.645 (85 % of the inner height between the floor at 0.09 and the stave tops at 0.74) with radius
0.256, just inside the inner wall on every LOD; the overlay uses the barrel's placement, so it lines up at the
barrel's binding height 117. The barrel was rebuilt for it: LOD2 is now open as well (inner wall and floor) and
every level has a closed base. States (Global.lua 268-275): 0 empty, 1 red, 2 yellow, 3 blue, 4 orange, 5 green,
6 purple, 7 white. Review with back faces culled: `review/barrel_liquids/sheet.png` (each liquid from three-quarter
above, the empty barrel, LOD1/LOD2 with liquid, low and below views; `scripts/review_liquids.py`).

## Models (details)

- **Skeleton `dec05`, rev 2** (coordinator review: compact curled heap): the MM6 skeleton creature on its back,
  rolled toward the viewer, posed by joint targets traced on the x2 sprite (`TRACE`, `LIMBS`: spine and skull by
  aiming, limbs by two-bone IK): skull on the ground at the left facing the viewer, near arm along the ribcage top
  down to the pelvis, far hand on the ground before the ribs, knees drawn up and shins folded down to the feet at
  the right. A 2.4 : 1 mound. Chest x1.25 / 1.3, skull x1.2, long bones x1.25 across. LOD0 is decimated per bone
  group (`LOD0_SHARE`: long bones whole, skull 640, ribcage 470, ...; the separate teeth dropped); LOD1 is the
  creature's LOD2 mesh posed the same way, LOD2 a per-bone decimation of it. Texture: aged ivory, the atlas's AO
  folded in plus brown grime in the crevices and in noise patches. Rendered mean 145, 130, 95 (sprite 151, 136, 99).
- **Bone pile `dec29`, rev 2**: long bones only (vertebra and pelvis pieces read as dark lumps), x1.35 across, their
  cut joint caps rounded into condyles (`bonekit.round_ends`: one subdivision level, the cap faces mapped to a shaft
  texel), three base bones on the ground, the skull (x1.4) on them, the heap dropped round it (front bones stay low
  so the face shows), the jaw apart in front. Texture graded darker with the joint AO weakened to a quarter;
  occlusion only in the crevices. Rendered mean 132, 121, 99 (sprite 127, 116, 94).
- **Carcass `dec21` and carrion `dec22`, rev 2**: the `meat` texture is now striated muscle (fine fibres in bundles
  with dark seams and pale sinew streaks), roughness 0.6-0.75 with small wet spots, orange brown-red; specular 0.4.
  The masses are torn and flattened (`mm8lib.slice_top`: a tilted, noisy cut plane presses each lump's top flat);
  the carrion is six flat slabs, the carcass keeps its bare ribcage. COLOR_0 tints the meat toward the sprites'
  orange (`MEAT_TINT`).
- **Rune posts `dec13`-`dec17`** (`scripts/build_runeposts.py`): faceted lathe spikes with seeded facet radii and
  noise relief (graded CC0 lichen_rock), a column of carved Elder Futhark runes as on each sprite (an alpha-tested
  strip ray-projected onto the front, 6 % of the radius out), dec15/dec16 a second lower spike behind, dec13/15/17 a
  skirt of bramble cards, dec13 a white rose at its foot.
- **Elf statue `dec01`** (`scripts/build_elfstatue.py`): the MM6 fighter (`mm6_fgt.glb`, B_* rig) posed from the five
  views (feet apart, knees bent, both hands on a two-handed sword at the right hip, blade raised past the head to
  his right), fingers closed round the grip, hair pressed onto the skull, pointed ears added, the upper body widened
  (x1.2) toward the sprite's armoured bulk; procedural sword. Texture `elfstone`: the fighter atlas's luminance on
  the CC0 mossy_rock scan graded grey-green, the fighter's normal map blended with the rock's.
- **Tableware** (`scripts/build_tableware.py`): plate cross-sections traced from the sprites (foot, sloped rim with a
  rolled edge, recessed well); stacked plates rest on the plate below with darkened undersides as grooves; nested
  bowls show the band of wall below each lip. Wood: CC0 rosewood_veneer1 (planar grain across the plate, rim edges
  mapped round); metal: CC0 metal_plate_02 graded to worn pewter / dark tarnish, metallic 0.6.
- **Cauldron** (`scripts/build_cauldron.py`): lathed iron pot (CC0 rust_coarse_01) with a flared rim and a glowing
  brew, five glowing coal lumps (CC0 rock_boulder_dry), two crossed charred logs (CC0 bark_willow), three shared-
  flame cards between the coals.
- **Trash heap** (`scripts/build_trashheap.py`): a lumpy mossy core (CC0 brown_mud_leaves_01) shingled with 230 curled
  bark flakes (CC0 pine_bark, double-sided) ray-cast onto it, with gaps low down where the moss shows.
- **Goblet** (`scripts/build_goblet.py`): a 10-facet flat-shaded lathe (cup, knobbed stem, foot), deep red glass
  texture with pale streaks, opaque and glossy.
- **Fruit bowl** (`scripts/build_fruitbowl.py`): a lathed bowl (CC0 fine_grained_wood) heaped with the CC0 Poly
  Haven food_apple_01 (one big, four small), bananas (two), food_lime_01 recoloured as an orange, 22 low-poly
  grapes in the lime's grade, two leaves.

## Scripts

- `mm8lib.py`: MM6 `props_lib` (read only) with this batch's `textures/`, map units, COLOR_0 helpers
  (`colour`, `set_colour`, `tint_material`), per-piece decimation, metaball flesh, noise displacement, box mapping,
  buried-piece removal.
- `bonekit.py`: bone kit and skeleton posing from `mm6_ske.glb` (`Kit`, `place`, `along`, `drop`, `pose_skeleton`).
- `make_textures.py [name ...]`: every texture in `textures/` (graded scans and procedural sets; `means.json`).
- `fetch_pbr.py`: CC0 Poly Haven sources into `source/` (git-ignored with the rest of `level_generation/`).
- `build_*.py`, `review.py -- <prop> <export.glb> <yaw> [elevation]`, `sheet.py <prop> <sprite>`,
  `measure.py <render> <sprite>` (mean colours), `finish.py <prop> [--install]` (materials, LOD link, validation,
  install).

Rebuild example: `python3 -I scripts/make_textures.py skeleton && blender --background --python
scripts/build_skeleton.py && blender --background --python scripts/review.py -- skeleton work/skeleton_export.glb 0 28
&& python3 scripts/sheet.py skeleton dec05 && python3 scripts/finish.py skeleton --install`.

## Sources and licences

- Bones (skeleton, bone pile, carcass, carrion): the project's own MM6 skeleton creature
  (`assets_source/worlds/mm6/models/mm6_ske.glb`, built by `level_generation/creatures/mm6_ske_claude/` from paid Meshy
  generations owned by the project's account); its atlas is regraded here, not edited in place.
- Elf statue body: the project's own MM6 fighter (`assets_source/worlds/mm6/models/mm6_fgt.glb`, read only); its
  atlas luminance and normal map are reused inside `elfstone_*`.
- Poly Haven (CC0, https://polyhaven.com/license), all in `source/` via `scripts/fetch_pbr.py`: textures
  `weathered_planks`, `metal_plate_02` (barrel, tableware), `lichen_rock` (rune posts), `leather_white` (meat relief,
  hide), `mossy_rock` (elf statue), `rosewood_veneer1` (wooden plates), `fine_grained_wood` (fruit bowl),
  `pine_bark`, `brown_mud_leaves_01` (trash heap), `rust_coarse_01`, `rock_boulder_dry`, `bark_willow` (cauldron);
  models `food_apple_01`, `bananas`, `food_lime_01` (fruit).
- Shared flame: the CC0 Unity Labs Flame02 flipbook (`../../mm6_dungeons_3d/textures/flame02_basecolor.png`).
- Procedural (this batch): meat fibres, rune glyph atlas (Elder Futhark letters), bramble cards, rose, cauldron
  brew, goblet glass.

## Compromises

- Skeleton: the Meshy bones are slimmer than the painted ones (widened and thickened, still lighter in mass than the
  sprite); three LODs (a fourth shatters into shards); hands keep straight fingers.
- Bone pile: long bones only (no vertebrae or pelvis, whose source pieces read as dark lumps).
- Carcass and carrion: metaball flesh, flattened and torn, not the sprite's sliced muscle; the meat texture is
  procedural (no CC0 meat scan); the carcass is an animal body built from human bones (stretched ribcage).
- Barrel: the rim notch is a simple V; hoops partly metallic (0.6) so they do not go black in dungeons (engine
  deviation from binary metallic, GAME_ASSET_MODELLING_GUIDELINES.md section 5; also the tableware metals).
- Rune posts: the bramble cards widen the bounds of dec13/15/17; runes are a projected strip, not carved geometry.
- Elf statue: lower contrast than the painted sprite; the hair is pressed to the skull (a faint cap line remains);
  fingers are pulled round the grip, not posed; LOD0 5805 triangles (one-off budget).
- Cauldron: the fire lighting on the belly is left to the engine's light 128 (COLOR_0 can only darken).
- Trash heap: flakes are bent cards (double-sided), 6 MB source GLB (2k bark textures).
- Goblet: opaque red glass (no transparency, so no sorting issues); it reflects the sky in outdoor light.
- Fruit bowl: fruit decimated hard (the apple scan 7k -> 130-340 triangles); grapes are low-poly spheres.
