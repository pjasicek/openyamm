# Peasant Elf Female texture pass (MM7 `mm7_m322`, descriptors 331–339)

The texture quality pass ([TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md), queue and trial notes
in [texpass_mm678/HANDOFF.md](../claude_shared/texpass_mm678/HANDOFF.md)) on the installed elf peasant woman. Mesh,
rig, weights, clips (Standing, Walking, Hit, Death, Dead, Fidget, Jog), the nine skins `m322_a1`…`m322_c3`, their
region ramps, the staff attachment and every binding are unchanged.

Related projects: [mm7_m322_claude](../mm7_m322_claude/README.md) (production, HD masters and head views),
[mm7_m322_reduce_claude](../mm7_m322_reduce_claude/README.md) (installed LOD0/LOD1, far LODs, floor fix),
`gait_rollout_20261031/h13` (the Jog clip). Lease `mm7:m322-texpass` (token in `work/LEASE.txt`).

## Texture quality pass (2026-11-01)

**User feedback (2026-11-01, in-game):** body and head textures terrible; faces show polygon-shaped lighter and
darker patches in different skin tones (face and chest), hair flat and smeared; faces must be one continuous skin
tone. **Installed 2026-11-01.** Meshy: **20 credits** (body and head 4K retexture, 10 each, backup account).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m322_texpass_claude/review/viewer/) (installed
and pass for all nine skins, ramps baked as the engine applies them) · sheets (identical cameras, every skin, head
front / 3/4 / left, chest, body 3/4, upper back): [outfit A](review/texpass_sheet_a.png) ·
[outfit B](review/texpass_sheet_b.png) · [outfit C](review/texpass_sheet_c.png)

### Cause of the patches

1. **The hair mask covered the lips, brow edges and inner ears.** The production compose marked every saturated red
   texel of the face shell as hair (`compose_m322.py` `classify(head=True)`), so the hair ramps recoloured them: white
   lips and blue-white brows on the white-haired skin B2, yellow lips on the blondes, salmon ear patches on all.
2. **Two skin tones meeting at the neck.** The body set was repainted to one flat albedo, the head set kept Meshy's
   darker, redder colour: face (178, 127, 105) against chest (205, 156, 128), a 27-level step at the head-set boundary.
3. **Smart UV fragments painted flat.** The 2080×1024 body | head atlas (two 1K sets from 2K paints) had 582 islands,
   5.6 % of the surface on fragments, each painted as one flat tone: the polygon blotches on chest, shoulders, neck.

### Route (`scripts/`)

1. `dump_lod0.py`: installed LOD0 into `work/lod0_before.npz`, with the approved head-set faces (right half of the
   atlas, 3,034 of 9,202 triangles) and per-face production pieces (skin shell, hair shell, hands, eyes, mouth, small
   pieces) from `../mm7_m322_reduce_claude/work/prod_pieces.npz`.
2. `uv_texpass.py` (Blender, `claude_shared/uv_atlas.py`, fast packer sweep): one 2048 atlas, face/scalp/neck skin,
   eyes and mouth ×1.8, hair shell ×1.25, hands ×1.3. **`work/uv_fine.npz` is the paid layout; never re-run it.**
   `max_cost` 4 and 8 (`work/uv_c4.npz`, `uv_c8.npz`, 58.3 %) were rejected: they split the face front down the
   middle; `uv_fine` keeps the whole face front (brows to chin) on one chart (`layout_stats.py`).
3. Retextures (`requests/`, meshy-7, 4K, `enable_original_uv`): body on the whole mesh with the four HD masters,
   head on the head-set faces with the four close head views. Both returns keep the layout (57.7 %, 230 islands).
4. `bake_ao.py` (3 cm reach) and `resample_approved.py` (installed colour and mask carried onto the layout for the
   luminance match and the measurements).
5. `compose.py` → `textures/m322_tp_*`:
   - paints 4K → 2K once; the head paint fades in over 4.5 cm of geodesic distance from the head-set boundary on
     the neck;
   - **one skin tone**: the head paint keeps its detail but takes the body paint's broad skin tone at each surface
     point (per-vertex ratio of the two paints' skin, diffused 12 rings over the head skin; global ratio for mouth
     bits and eyelid skin), so face and neck meet without a step;
   - hair strands the body paint projected onto the chest and the vest strap refilled from the nearest material;
   - gentle grade (AO 0.5 after a 5-texel grey closing that removes bake specks, local 0.3 and every blur inside
     its chart, contrast 1.06, saturation 1.0);
   - **seam levelling** (`seam_level.py`): one smooth additive correction per chart so both sides of every chart
     seam of one colour class agree (a small chart beside the right eye came back lighter): seam difference mean
     4.7 → 0.3, p95 19.8 → 1.4 levels;
   - **region masks by geometry**: G hair = the hair shell plus scalp texels under it (hair within 2.2 cm, outward
     along the surface normal) that are painted hair-coloured: never lips, brows, ears or cheeks. R cloth = green
     texels of the skin shell below 1.25 m (trousers and waistband). Inside each region the linear luminance is
     quantile-matched to the installed paint's, so the nine tiers' ramps (unchanged) give the installed colours;
   - irises: chroma ×0.55 and a light blur inside the eye shells (the head paint drew a saturated green, crackled
     iris; the HD head views and the installed paint are muted grey-green);
   - normal from both paints, tilt scaled to the installed map's p90 (×0.71); specular mask, roughness and material
     classes from the new classes with the production rule.
6. `apply_layout.py`: LOD0 and shadow get the layout (vertices 8,127 → 10,322), LOD1 and shadow are projected per
   chart (4,740 → 6,228), LOD2/LOD3 keep geometry and UVs and get their maps again from the new LOD0
   (`lod_repair_claude/scripts/transfer_textures.py`, 512 and 256 px).
7. Checks: `glb_diff.py`, `lod1_check.py`, `tier_tone.py` (engine colour per tier at the same surface points),
   `ortho.py`/`ortho_sheet.py` (bind-pose close-ups used while composing), viewer scripts, `texpass_sheet.py`.

### Results

`texture_quality.py`, LOD0 base colour (`work/quality_before.json`, `quality_after.json`):

| | Before (2080×1024 body \| head) | After (2048²) |
|---|---|---|
| Atlas use | 42.9 % | **57.7 %** |
| Equivalent square | 1,362 px | 1,556 px |
| Density p10 / p50 / p90 | 491 / 844 / 1,975 | 1,698 / 1,759 / 2,231 |
| Median per bone: thigh, hand, head | 504, 1,690, 1,922 | 1,749, 2,265, 2,187 |
| Spread p90/p10 | 4.02 | 1.31 |
| Islands / surface on fragments | 582 / 5.6 % | 230 / 0.1 % |
| Stretch p90 | 2.0 | 1.1 |
| Meshy source | 2K, downsampled to 1K | 4K on the final layout, downsampled to 2K |

Maps: colour and normal 2048² (were 2080×1024), region mask and metal/roughness 1024². LOD2/LOD3 sizes unchanged.

**Face and skin, engine colour (ramps applied), every skin** (`tier_tone.py`, `work/tier_tone.json`, installed GLB
against the installed pass GLB, area-weighted means of skin-coloured texels at the same surface points):

| Measure | Installed | Pass |
|---|---|---|
| Neck step: 2 cm band above vs below the head-set boundary (max channel) | 26.6 | **4.6** |
| Face (forehead, both cheeks, chin) vs upper chest | 22.5 | **6.0** |
| Spread across the face (forehead, cheeks, chin; largest pairwise) | 13.6 | 9.1 |
| Chart seams on face and neck skin, mean / p95 | 12.8 / 43–44 | **2.1–3.1 / 3.7–17.8** |

Skin is not ramped, so the first three rows are identical in all nine skins. Seam p95 per skin: A1 8.0, A2 4.4,
A3 3.7, B1 15.9, B2 17.8, B3 8.4, C1 8.0, C2 4.4, C3 15.9; the light-haired skins are higher because the hairline's
soft mask edge mixes the pale hair ramp into a few skin texels at the scalp.

**Tier colours held**: trousers and hair means per tier within 3 levels of installed in all nine skins (e.g. B2 hair
155.4/151.9/158.6 → 156.1/152.4/158.9, A1 trousers 27.7/86.9/26.9 → 27.3/85.9/26.5).

**Eyes**: pupils centred in both eyes, irises intact, compared with `references_head/01_front.png`; the colour is a
muted grey-green like the HD views. The head paint's eyes were kept (sharper than the installed 1K paint); only the
iris chroma was lowered.

**LOD1 against LOD0** (`lod1_check.py`): colour error mean 3.7 → 2.4, p99 72.2 → 42.8.

### Checks

- `glb_diff.py`: OK, only UVs, vertex splits and images differ (nodes, skin, inverse binds, every clip sampler,
  materials, variants, ramps, LOD lists, per-corner position/normal/joints/weights unchanged).
- `check_winding.py`: 0 inverted closed parts. `flat_shading_check.py`: flat 0.00.
- Viewer `run_creature_review.py check`: 126 switches (18 models × 7 clips), no console errors.
- Installed with `flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py
  level_generation/creatures/mm7_m322_texpass_claude/export/mm7_m322.glb --world mm7`; the source equals the export;
  all 12 image URIs of the cooked `assets_dev/worlds/mm7/models/mm7_m322.glb` exist.
- `cmake --build build --target openyamm -j25`, then `mm6_mm7_mm8_actor_models_build_every_binding`: pass (647
  descriptors on 185 models). No regression case names m322. Not run: geometry-dependent audits (floor,
  detached parts: positions unchanged), an in-game look, the Android cook.

### Drift

- Skin is lighter: body about +8 levels (chest 207/156/130 → 215/166/137), face about +30 (the installed face was
  darker than its body; it now matches the body).
- Hair strands are finer and more contrasted within the same luminance distribution (strands visible in the
  white and blonde skins instead of smeared bands).
- Irises a little greener than the installed grey-green; heavier painted eyeliner and lashes (head paint).
- A small leather flap triangle at the top of the left vest strap and a stud piece there keep odd paint (geometry).

### Close-up fixes (2026-11-01, r2)

User close-up review of the installed pass (r1): blocky, shattered eyes; pale shards in the lip opening; white
triangles on the left vest strap (character's right); a dark lace stroke on the cleavage. `scripts/closeup_fixes.py`
runs after `compose.py` on its maps (`textures/m322_tp_*`) and writes `textures/m322_tp2_*` on `work/uv_final.npz`
(`work/closeup.log`, `textures/m322_tp2_closeup_report.json`). No Meshy credits. Sheets (review-viewer shots,
identical cameras, every skin, r1 against r2; eyes front, eyes 3/4, mouth, chest/strap):
[A](review/closeup_sheet_a.png) · [B](review/closeup_sheet_b.png) · [C](review/closeup_sheet_c.png). The viewer has
three versions per skin (installed before the pass, r1, r2) and close-up presets in the Focus list: Eyes (close),
Mouth (close), Chest / lacing (close).

1. **Eyes: procedural, in eye-local coordinates.** The head paint had painted each eye triangle on its own at
   18 px/cm, so the iris came apart in shards. Per eyeball shell (pieces 4 and 5; `eyes_geom.py`):
   - a sphere fit (radius 12.3 and 12.9 mm);
   - the visible part: the shell in front of the face skin, since the eyeballs pass through the closed skin shell
     and there is no lid hole (20 % and 16 % of the shells);
   - the pupil at the centre of that visible part, and the iris radius a quarter of its width (19.4° and 17.6°).
     The lid opening is taller than in the HD view, so the iris spans it as it does there.
   - Colour from the angle to the axis:
     - grey-green iris with radial fibres, crypts and a darker limbal ring; radial colours measured on
       `references_head/01_front.png`;
     - round pupil at 0.27 iris radii;
     - off-white sclera, darker and pinker toward the corners and shaded where it meets the lids;
     - a small soft highlight at the upper right.
   - The original paint is kept only where it was lid skin: within 2 iris radii (the lid opening) every texel that
     was not skin-coloured is procedural (old liner strokes and the crackled iris included), and beyond that only
     paint that was sclera-white or grey-green. 87 % of the visible eye is procedural; sclera (210, 202, 192),
     edges (184, 164, 154).
   - **Repack:** the visible faces of each eyeball (103 of 292) moved to free atlas space at **3.0× their
     density** (54.7 px/cm; 3.5× and up did not fit). The hidden rest keeps its UVs (18.2 px/cm), so the cut is
     invisible: the paint depends only on the 3D point.
2. **Mouth.**
   - The mouth pieces (8, 9, 11; one piece-9 face sits 3.4 mm from the mouth line) and the inward-facing lip faces
     take a dark gradient by depth: (104, 50, 47) at the lip edge to (26, 12, 12) 7 mm in. Inward-facing means
     facing the mouth line, behind the lips' front in their 1 mm column of x, and within 3.2 mm of the line. Lip
     surface more than 2 mm behind the front, near the line, is darkened too.
   - The weight is blurred so the gap reads as one soft shadow. It fades out toward the corners; the gap reaches
     further left than right.
   - Specular is off and roughness is 1 there, so no sheen shows on the dark inner faces.
   - The outer lip paint is unchanged.
3. **Vest strap and small pieces.**
   - The white triangles were back faces of the upper back, seen from the front through a hole in the mesh at the
     top of the strap. Every back-side skin face near either strap top that the hair hides from behind (37 faces,
     never visible from behind) takes the vest leather (49, 27, 6), as does the reddish flap triangle.
   - The strap stud (piece 33) takes the vest studs' brass.
   - Trouser grommets painted skin (pieces 21–48, 6,088 texels) take the other grommets' dark metal (41, 32, 12).
4. **Cleavage and bare skin.**
   - The "lace stroke" was the dark outline paint of the top lacing strip (piece 6, a thin band floating 12 mm in
     front of the cleavage). It now takes the cleavage skin tone, and the dark stroke paint on the skin just above
     it is refilled (217 texels).
   - A scan of the bare skin (chest, shoulders, belly, arms, upper back) refilled leather-, hair- and green-coloured
     paint whose 1.5 cm surroundings are mostly skin: 21 spots, 1,013 texels, from the surrounding skin of the same
     chart. They were at the cleavage, under the arms near the waist, and on the upper back under the hair.
   - The painted laces in the side-lacing gaps and between the front lacing are kept, as are the other lacing strips
     (7, 10, 12), which carry the painted X laces.

Checks on r2:
- `glb_diff.py` OK (only UVs, vertex splits and images); winding 0; flat 0.00.
- Atlas 58.0 % (the eye charts moved, every other chart unchanged).
- LOD1 against LOD0: mean 2.7, p99 55 (r1 2.4, 43), from the sharper eye and mouth detail that LOD1's coarser
  geometry does not follow exactly.
- Viewer check: 189 switches (27 models × 7 clips), no console errors.
- Installed 2026-11-01 with the shared lock (source equals the export); all 12 cooked texture URIs present;
  `cmake --build build --target openyamm` and `mm6_mm7_mm8_actor_models_build_every_binding` pass (647 descriptors).

Rebuild r2: `python3 scripts/compose.py textures/m322_tp`, then `python3 scripts/closeup_fixes.py`, then
`apply_layout.py work/before_texpass/mm7_m322.glb work/uv_final.npz textures/m322_tp2 export/mm7_m322.glb`.
`work/uv_final.npz` is `uv_fine` with only the eye faces moved; it is rebuilt by `closeup_fixes.py` deterministically
(first free position per scale). The r1 GLB is kept as `work/export_r1_installed.glb`.

### Eyes r3 (2026-11-01)

Coordinator review of the r2 close-ups: chest, strap and mouth accepted. The eyes were not:
- the iris too small and too dark (an olive disc);
- the sclera too white, with hard edges on triangle boundaries;
- a dark stitched line across the sclera in the 3/4 view, at the cut between the repacked visible faces and the
  hidden rest.

`closeup_fixes.py` now follows the eye route of [mm7_m342_texpass_claude](../mm7_m342_texpass_claude/README.md)
(`face_geom.py`, `uv_eyes.py`, `face_paint.py`), adapted to this eye.

- **One disc per eyeball.** Every face of each eyeball (pieces 4, 5) is re-charted as one disc: an azimuthal
  projection around the eye's forward axis. It keeps full density to 1.25 iris radii, half density over the sclera
  to 0.9 rad, and 0.15 over the hidden back. Both discs sit in the two largest free circles of the atlas (radius 50
  and 49 px) at one common density, **2.68× the old one**: iris 47.5–49.3 px/cm, visible eye 39 px/cm (was 18.2).
  No seam crosses the eye, so the r2 cut and its stitched line are gone. The disc border is padded (raster grown by
  1.5 texels, then the atlas gutter fill). Since every eye face is painted, faces that turn visible in other clips get
  the same paint.
- **Axis and size.** The axis runs through the centre of the visible eye (the part of the shell in front of the face
  skin), raised 4°, so the iris tucks just under the upper lid. The iris spans **55 % of the visible width** (21.4°
  and 19.4°; the HD front view: about half); the pupil spans 0.3 iris radii.
- **Colours** (the HD head view's muted grey-green, its brightest quartile lifted, since the photo is dimly lit):
  - iris (118, 128, 114) to (86, 96, 88) at the rim, measuring (118, 120, 102) mid-iris after the fibres;
  - warm collarette (132, 116, 84) round the pupil;
  - radial fibres (m342's four-frequency pattern);
  - dark limbal ring (54, 60, 56);
  - pupil (10, 10, 12);
  - a small soft highlight.
- **Sclera.**
  - Off-white (196, 188, 180), darkening to (120, 100, 95) toward the corners and the hidden back.
  - A soft shade by the distance along the eyeball to the lid line: 2.5 mm wide toward the lower lid and corners,
    4.5 mm under the upper lid, from ×0.55 at the line. The edge is a smooth contour, not the triangle edges.
  - Specular 0.45, roughness 0.3 (m342), flat normal.
- **Lid margins.**
  - The head paint had painted a bigger eye than the geometric opening: sclera and iris colour on the lid skin round
    each eyeball. These 737 texels are refilled from the surrounding lid skin.
  - Skin within 0.6–1.9 mm of an eyeball then takes a shadow (78, 58, 52) on the upper margin and a pinkish
    waterline (150, 104, 96) on the lower, so the eye's outline follows a smooth contour.

Sheets (review-viewer shots, identical cameras, every skin, r2 against r3; eyes front, 3/4 and side in Standing, front
and 3/4 in Fidget): [A](review/eyes_r3_sheet_a.png) · [B](review/eyes_r3_sheet_b.png) · [C](review/eyes_r3_sheet_c.png).
The viewer shows installed, r1, r2 and r3 per skin.

Limits:
- The lid line is still the geometry's jagged intersection of eyeball and skin. The paint softens it on both sides,
  but cannot round it.
- A small fold of skin at the inner corner of the character's right eye shows a lighter facet.

Checks on r3: `glb_diff.py` OK (only UVs, vertex splits and images); winding 0; flat 0.00; atlas 57.9 %, 226 islands
(each eye one chart); LOD1 against LOD0 mean 2.7, p99 55.7; viewer check 252 switches (36 models × 7 clips), no console
errors. Installed 2026-11-01 under the shared lock (source equals the export), all 12 cooked texture URIs present, the
game builds and `mm6_mm7_mm8_actor_models_build_every_binding` passes (647 descriptors). The r2 GLB is kept as
`work/export_r2_installed.glb`.

### Rebuild and rollback

```sh
P=level_generation/creatures/mm7_m322_texpass_claude
python3 $P/scripts/compose.py $P/textures/m322_tp          # maps from the two paid paints (never re-run uv_texpass.py)
python3 $P/scripts/closeup_fixes.py                       # close-up fixes (r2): textures/m322_tp2_*, work/uv_final.npz
python3 $P/scripts/apply_layout.py $P/work/before_texpass/mm7_m322.glb $P/work/uv_final.npz \
    $P/textures/m322_tp2 $P/export/mm7_m322.glb              # input: the pre-pass GLB
python3 $P/scripts/glb_diff.py $P/work/before_texpass/mm7_m322.glb $P/export/mm7_m322.glb
python3 $P/scripts/viewer_variants.py $P/export/mm7_m322.glb r3
python3 $P/scripts/viewer_manifest.py m322_a1_r3 before=installed r1="texture pass r1" r2="close-up fixes r2" r3="eyes r3"
```

`apply_layout.py` refuses an input whose LOD0 differs from `work/lod0_before.npz`; after a later layer on the
installed file (new clips), run it on that file instead of the backup. Rollback to r2 or r1: install
`work/export_r2_installed.glb` or `work/export_r1_installed.glb`; to the pre-pass state: install
`work/before_texpass/mm7_m322.glb` through the same `flock … tools/install_model.py … --world mm7`. The staff
(`mm7_m322_staff.glb`) was not touched (backup copy in `work/before_texpass/`).
