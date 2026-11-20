# Held sword retexture pilot (2026-11-14)

Four of our own sword ground models, re-textured with Meshy so they hold up in the solo run's first-person hand
(`devdocs/solo_action/WEAPONS.md`, "Held weapons in the game"). Geometry, scale and orientation are the installed ones:
only the UVs and the maps changed, `tools/item_model_shapes.py --check` reports all bounds current and `held.yml` is
untouched.

| Icon | Item | Why |
|---|---|---|
| `item001` | Iron Longsword (item 1) | Horace's sword: a new-game Knight gets item 1 for the Sword skill (`starterItemIdForSkill`); the hooked bronze guard of the user's screenshot |
| `7item010` | Steel Broadsword (812) | broad single-edged steel blade (the example in the brief) |
| `item005` | Champion's Sword (5) | gold, ornate (winged guard, red grip) |
| `7item012` | Cutlass (814) | curved, knuckle bow |

Originals: `before/item_<icon>.glb`. Installed exports: `work/<icon>/export_v3.glb` (v1, v2 kept for comparison).

## Route

1. `scripts/prep.py <icon>` (Blender): weld (uv_atlas refused the weld on item001/7item010 because it reorders faces;
   unwelded they gave 670 PartUV charts, 644 under 8 triangles), `uv_atlas.unwrap()` defaults (PartUV, seam pass,
   sparrow), the upright upload and the guides.
2. `scripts/segment.py <icon> <max_aspect> <tag> [runs secs min_faces]`: **long thin props need their blade islands cut.**
   One blade face is about 20 times longer than wide, so as one island it caps the square at 9-52 % atlas use. Cutting
   islands longer than `max_aspect` x their width into equal pieces (by face centroid along the island's principal
   axis) and repacking with sparrow gave 71-79 %. Used: item001 and item005 aspect 8 (two cuts per blade face),
   7item010 aspect 3, 7item012 aspect 2 with `min_faces` 60 (without it the knuckle bow fell into 7 % fragments).
3. `scripts/finalize_layout.py <icon> <tag>`: each corner gets the source corner's normal back (matched by position; a
   nearest-surface data transfer smeared the hard edges on the thin blades: 727 instead of 92 off-face loop normals),
   `layout.blend` (locked), `upload.glb`, guides.
4. `scripts/codex_masters.py brief|run <icon>`: Codex HD masters 1024 x 1536, front/back/left/right over the guides,
   from the x2 icon. The image tool refused the edge-on left/right views of the cutlass ("violence"); its job went with
   the front master only. Silhouette IoU 0.77-0.94 (`scripts/master_check.py`).
5. Meshy retexture: `requests/<icon>_retex_v1.json` (`meshy-7`, original UVs, PBR, 4K, multiview front/left/back/right).
6. `scripts/finish.sh <icon> <job> <tag>`: 4K -> 2K once (Lanczos), `grade_basecolor.py` gentle grade on a Cycles AO
   bake, `scripts/blade_pass.py`, `gutter_fill.py` last on every map, assemble, `tools/normal_map_convention.py`
   (Meshy's maps measured -0.8 to -0.96: converted).
7. Install: `tools/install_model.py ... --world-items`, `tools/cook_models.py --verify --profile desktop --only ...`,
   plus a cook sidecar per model (below).

**2K, not 4K:** at 1600x900 the held blade covers about 1,100 px per metre; the 2K layouts give 2,900-3,800 texels per
metre, already 3x the screen, and the colour cooks at 2K at most.

### What Meshy's paint needed (`scripts/blade_pass.py`)

v1 (Meshy maps as delivered) looked worse than before in game: the blade near black and the guard spotted.
- **Weave:** Meshy painted a 4-8 texel knit/chain-mail pattern over the metal (item001 worst, item005 as fine
  striations). Metal keeps 15 % of the detail below sigma 3 texels; guards and fittings keep their broad colour only.
  A faint mottling is still visible on item001, 7item010 and 7item012 at full size.
- **Metal albedo:** the painted steel was 0.14-0.26 linear (Khronos metal range 0.5-1.0), so a metallic blade reflected
  a fifth of the sky. Metal is scaled to a median of 0.55 linear; blade steel keeps half its chroma.
- **Profile in the normal map:** Meshy's normal maps are almost flat, and the blades are flat slabs. From the mesh, each
  blade-face texel's place across the blade (exact outline where the mesh edges cross each cut) gives a ridge (both
  halves tilted 6-7 degrees) and honed edge bevels (outer 14-16 % at 22 degrees) on the double-edged blades, and a 20
  degree bevel on the edge side only of the single-edged ones (the thinner side; checked against the icons), whiteout
  blended with Meshy's normal. `scripts/normal_debug.py` renders it under grazing light: the halves swap brightness
  consistently along every UV piece.
- **Roughness:** Meshy's metal roughness stretched to 0.2-0.55, bevels glossier, a lengthwise grinding grain from the
  3D position (seamless over the cuts).
- **Metallic:** the installed model's binary metal mask carried onto the new UVs (`bake_maps.py oldmetal`), with
  Meshy's metallic as variation inside it (Meshy left the blade 0.64 metallic in places).

### Cook sidecars

`assets_source/engine/world_items/models/item_<icon>.cook.yml` raise these four models from the ground items' caps
(colour 512, normal/roughness 256: `tools/cook/model_textures.yml`, user decision 2026-10-18) to colour 2048,
normal and metal-roughness 1024. Without them the paint is invisible in the hand. Cost: about 5.4-5.8 MB of cooked
textures per model instead of about 0.4 MB, also when it lies on the ground. **Removed 2026-11-14 by the user's
decision:** the four models are cooked at the ground caps again (the hand draws the Oblivion tier skins instead, and
our ground model only with `viewmodel weapons ours`); the re-painted sources stay installed.

## Credits and measures

| Icon | Job | Credits | Atlas before -> after | Equivalent px | Density p50 (texels per model length) | Spread | Fragments | Stretch p90 |
|---|---|---|---|---|---|---|---|---|
| item001 | `01a1d8db-4b49-7022-99ed-8a6350d12184` | 10 | 1.3 % (1024) -> 75.0 % (2048) | 116 -> 1,774 | 443 -> 5,212 | 1.44 -> 1.07 | 10.6 -> 0.1 % | 1.72 -> 1.18 |
| 7item010 | `01a1d8e4-043c-72cb-bd07-dfed30b93ab5` | 10 | 2.0 % -> 78.9 % | 145 -> 1,819 | 446 -> 4,186 | 1.28 -> 1.05 | 7.1 -> 0.1 % | 1.41 -> 1.12 |
| item005 | `01a1d8db-5c8c-72fd-8771-8b03be7ee528` | 10 | 1.6 % -> 77.4 % | 128 -> 1,802 | 444 -> 4,521 | 1.37 -> 1.19 | 7.4 -> 0.1 % | 1.42 -> 1.13 |
| 7item012 | `01a1d8ee-7b7a-749d-a54e-0d216b6750d3` | 10 | 2.2 % -> 75.3 % | 150 -> 1,777 | 442 -> 4,253 | 1.45 -> 1.11 | 6.1 -> 0.1 % | 1.56 -> 1.14 |

Total 40 of the 60 credits allowed (ledger `creature_3d_progress.json`). Each Meshy return was checked to carry the
upload's layout (same atlas and islands at 4K). Winding: 0 inverted closed parts before and after.

## In-game checks

`scripts/run_ingame.sh <phase> [outdoor indoor ground]`: 1600x900, `--ruleset maw:solo`, MM6 New Sorpigal (oute3) in
daylight and Corlagon's dungeon (6d05) for a dim interior, each sword held with `viewmodel held <icon>` at idle, at
`onehandattackleft 0.15` and `onehandattackright 0.30`, and all four dropped on the grass. Captures in
`ingame/before/`, `ingame/after/` (and `ingame/v1/`, `ingame/v2/`); sheets `review/sheet_<icon>.jpg`
(`scripts/make_sheets.py`).

Verdict at full size:
- **Outdoors, fixed.** The blade is no longer one slate-blue sheet: the ridge splits it into a lighter and a darker
  half, the honed edges catch a separate band, the guard, grip and pommel read as bronze/gold, wrapped leather and
  wire. item005 is the best (polished steel, red-and-gold grip); 7item010 and 7item012 read as plain brushed steel.
- **Still wrong:** the steel takes most of its colour from the sky reflection, so outdoors every blade is blue-grey;
  a faint mottled pattern is left from Meshy's weave on the flats; the single-edged bevel band is subtle.
- **Indoors, not fixed.** In 6d05 every blade is still near black with only the ridge and edges hinting at form; this
  is the renderer (below), not the texture: the metal albedo is already in the PBR range.

## Renderer (not changed)

`game/shaders/fs_model.sc`, as used by the first-person view: a metallic texel gets its light almost only from the sky
reflection (`s_modelEnvironment`) and the sun's specular; indoors (display-space rooms) the ambient term keeps only
`1 - min(metallic, 0.8)` of the diffuse, and the key light is diffuse-only, so a polished blade has nothing to reflect
and reads black whatever its texture (before: black; after: near black). Suggestions:
- A view-model light rig for the held weapon: a camera-relative key light with specular (and a soft rim), or an
  indoor environment (a probe of the room, or a neutral studio cube) for the view model's reflection, instead of the
  outdoor sky cube or nothing.
- Outdoors, a less saturated reflection for the view model (the sky cube's blue tints every blade).
- Texture sizes: the held model needs 2K colour and 1K relief, a ground item 512; a held-only mip level (load the top
  mips when the model is in the hand) would avoid paying about 5.5 MB per sword on the ground.

## Cost and time for all 334 held models

Per model: one Meshy retexture (10 credits), one Codex masters session (10-20 min, at most 4 in parallel), the layout
(PartUV + two sparrow packs, about 10 min of CPU, several in parallel) and the post (2 min). About 3,340 credits for
334 models, about 3,800 with a 15 % redraw allowance; about 25-30 hours of Codex wall time at 4 in parallel, so 2-3 days.

| Kinds (held.yml count) | Models | Credits | Notes |
|---|---|---|---|
| Swords, daggers, greatswords | 99 | ~1,000-1,150 | this route as is (blade pass: diamond or single-edged profile) |
| Axes, two-handed axes, poleaxes | 38 | ~380-440 | blade pass on the axe head (edge band only); shafts segmented |
| Maces, hammers, clubs | 43 | ~430-500 | no blade pass; metal albedo, weave filter and roughness only |
| Spears, tridents, polearms, staves | 60 | ~600-690 | very long shafts: segmentation essential; heads take the blade pass |
| Wands, blasters | 20 | ~200-230 | small; little gain at held size |
| Bows, crossbows | 36 | ~360-410 | wood: no metal pass; the left-hand view is small |
| Shields | 38 | ~380-440 | large flat faces have the same one-reflection problem: needs a relief pass (rim, boss) |

Before a rollout: decide the cook sizes (sidecars versus a held-only mip), and fix or accept the indoor darkness; the
texture alone cannot.
