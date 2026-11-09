# Mage texture pass (MM7 `mm7_m274` Sorcerer / Wizard / Archmage)

Separate texture-pass project for the installed Mage. It follows the
[texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) and the
[MM6–MM8 handoff](../claude_shared/texpass_mm678/HANDOFF.md). Production projects: [mm7_m274_claude](../mm7_m274_claude/README.md)
(model, rig, tiers) and [mm7_m274_reduce_claude](../mm7_m274_reduce_claude/README.md) (installed LOD0/LOD1). The staff
(`mm7_m274_staff.glb`) is untouched. Lease `mm7:m274-texpass` (token in `work/LEASE.txt`).

## Texture quality pass (2026-11-01)

User feedback (2026-11-01, in-game tier B "Wizard"): body and head textures terrible; the face is not one continuous
skin tone and shows seams; the beard follows the tier, but the scalp hair does not match the master or the icon.

### Causes

- The installed atlas was 2080×1024: a 1K body set (transferred Meshy layout, 663 islands with the head, 10.6 % of the
  surface on fragments, stretch p90 1.95) beside a 1K head set.
- The head paint had drawn ginger swept-back hair on the scalp, but `compose_m274.py` classed the scalp as skin: it
  was repainted with the skin tone (pale, blond-looking "slicked" hair) and left out of the beard mask. Only beard and
  braids took the tier ramp. The beard mask also covered the lips and chin (the orange / grey "lip block").

### What changed

Only UVs (with the vertex splits they need), the four LOD0 images, the LOD2/LOD3 images and the region mask. Node
names, skin, inverse binds, every clip (including the gait rollout's Jog), materials, variants, ramps and LOD lists are
the installed ones (`glb_diff.py`: OK). `actors.yml` is unchanged.

1. **Layout** (`uv_texpass.py`, `claude_shared/uv_atlas.py` fast packer sweep `fine=250 steps=0`): one 2048 atlas,
   head set (face, scalp, ears, beard, braids) ×1.8 and hands ×1.3. **`work/uv_fine.npz` is the paid layout; never
   re-run it.**
2. **Meshy** (backup account, `meshy-7`, 4K, `enable_original_uv`), **20 credits**:
   - body: whole mesh, the four HD body masters (`requests/body_retexture_v2.json`);
   - head: head-set faces only, three head views (front, profile, three-quarter; the back view drew a collar and
     black hair) (`requests/head_retexture_v2.json`).
   Both returns keep the layout (59.6 %, 155 islands).
3. **Compose** (`compose.py`):
   - colour and normal 4K → 2K once; the head is a separate mesh piece, so the head paint covers the whole head set;
   - gentle grade (recipe values) with AO baked on the layout (`bake_ao.py`);
   - **hair**: head-set texels with hair saturation and hue (hair ~0.8 / 27°, skin ~0.5 / 15°) are one region with the
     beard: scalp, temples, eyebrows, moustache, beard and braids all take the beard ramp (ginger / dark grey / white),
     as in the native sprites, where hair and beard share palette indices 137–155. Hair luminance is mapped by
     quantiles onto the installed beard's distribution, so the installed ramps apply unchanged;
   - **skin**: face, ears, hands and the neck stump take per-channel curves onto the face skin of the head paint, the
     broad colour (8–12 texel scale) is evened towards the skin mean, and magenta smudges (blue above green) at the
     outer eye corners take the mean chroma;
   - **eyes**: the eyeballs (their own mesh pieces) keep the installed eye paint, carried at the same surface points.
     The 4K head paint drew greyer irises with pink-tinged whites and red rims;
   - **robe and cape**: per island, the installed robe/cape luminance low-passed (σ 6 texels) times the 4K paint's
     detail (ratio limited to 0.7–1.4). The body paint left surfaces the masters could not see (skirt sides behind
     the sleeves, under the cape) near black. Those texels take the installed colour, and their region comes from the
     installed mask. Cape stars and the dark front panel come back;
   - gold and shoes: per-channel curves onto the installed gold and shoes. Shoes are a class of their own (foot, toe
     and calf triangles); their first classification took tier colours;
   - **seam healing** (`seam_heal.py`) on skin and hair: along every UV seam each side is pulled halfway to the other,
     fading over 6 texels inside its island;
   - region mask 1024 RGBA (R robe, G cape, B hair; feather 0.7 texel at 2048); metal/roughness from classes as
     `compose_m274.py`; normal from the paints, tilt scaled to the installed p90 (×0.958); class map
     `textures/m274_tp_material_classes.png`.
4. **Build** (`apply_layout.py`): LOD0 and shadow get the layout (8,084 → 9,862 vertices); LOD1 and shadow are
   projected per chart from LOD0 (4,770 → 5,963); LOD2/LOD3 keep geometry and UVs, and their maps are refilled with
   `lod_repair_claude/scripts/transfer_textures.py` at 512/256.

### Numbers

`texture_quality.py`, LOD0 base colour:

| | Installed (2080×1024) | Pass (2048²) |
|---|---|---|
| Atlas (tool) | 49.9 % | **59.6 %** |
| Texels used / equivalent square | 1.06 M / 1,031 px (tool: 1,469, width-based) | **2.50 M / 1,581 px** |
| Body density p50 | 371 | **890** |
| Head-set density p50 | 2,571 (whole 1K set for 2.8 % of the surface) | 1,603 (×1.8 head factor) |
| Spread p90/p10 | 2.56 | 1.05 |
| Islands / fragments | 663 / 10.6 % | 155 / 0.1 % |
| Stretch p90 | 1.95 | 1.06 |
| Meshy source | 2K body + 2K head, 1K sets | 4K body + 4K head, downsampled once |

The head's nominal texel density is 38 % lower than the old separate 1K head set, but its paint is a 4K head-only paint
instead of a 2K paint downsampled to 1K. The close-ups read sharper (wrinkles, brows, lids). If a later pass wants
more, a head factor near 3 would match the old density at about −10 % body density; it needs a new layout and paint
(20 credits).

**Skin** (`skin_check.py`, ramps applied, every tier; face skin without the 12 mm eye sockets; samples kept only on
skin texels; installed → pass):
- Face UV seams: 213 → 74 seam samples. Colour step across a seam (1.5 mm inside each side, mean / p95, sRGB levels):
  A 7.0 / 19.4 → 6.7 / 19.4, B 7.1 / 19.4 → 7.3 / 20.8, C 7.6 / 23.3 → 7.5 / 27.8. The baseline 3 mm apart inside
  islands is 4.5–4.8 (installed 4.9–5.9). Before seam healing the pass had 9.5 mean (A).
- Face against hands: A +13 / +8 / +5 (RGB), B +11 / +7 / +6, C +13 / +11 / +10. The installed were +6 / +3 / +7.
  The face samples lit cheeks, forehead and nose; the hands carry more AO.
- Face skin mean (A): installed 206 / 147 / 115 (repainted pale skin), pass 236 / 144 / 109 (the head masters' warm tone).
- Tier regions on skin: 5.7 % of face-skin samples get some hair ramp (mask > 0.1) at the hair, brow and moustache
  edges (installed 1.7 %, which had the mask on the lips). Hands: 0.04 %. The skin itself is in no region.
- The installed face mask problems are gone: lips and chin are skin, and the moustache and eyebrows are hair.

**Tier colours** (`tier_tone.py`, ramps applied, same surface points where both masks agree):
- robe: all tiers within 0.2 levels; cape within 1.3;
- beard: A +11.5 R, B +4.6, C +8.7 (the hair region also holds the darker scalp hair, so the beard part maps a little
  brighter); 14 % of the installed beard mask (lips, chin) is now skin.

**Eyes**: installed eye paint, centred pupils and blue irises, as the HD head views.

**LOD1 against LOD0** (`lod1_check.py`): colour error mean 3.9 → 1.2, p99 64.8 → 21.4. Far-LOD colour means within
6 levels (LOD2 110.5 / 78.9 / 31.9 → 104.9 / 76.3 / 31.1).

### Checks

- `glb_diff.py`: OK, only UVs, vertex splits and images differ.
- `check_winding.py`: 0 inverted closed parts. `flat_shading_check.py`: flat 0.00.
- `detached_parts_audit.py`: identical before and after (`review/detached_{before,after}.json`).
- Installed 2026-11-01 with `flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py
  export/mm7_m274.glb --world mm7`. Every cooked texture `uri` exists (12/12).
- `mm6_mm7_mm8_actor_models_build_every_binding`: pass (647 descriptors on 185 models). No regression names this
  model; `mm6_sorcerer_*` is MM6's `mm6_sor1`.
- Viewer [review/viewer/](http://127.0.0.1:8912/level_generation/creatures/mm7_m274_texpass_claude/review/viewer/):
  installed and pass per tier. `run_creature_review.py check`: 54 switches, no console errors. The "Face close-up"
  and "Eyes close-up" focuses replace the template's shoulders and feet presets. The staff attachment is not shown.
- Sheets (identical cameras, every tier, installed | pass):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front, face 3/4, head 3/4, head front) and
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png) (front, back, 3/4, skirt and hands).

### Drift and limits

- The skin is warmer and more saturated than the installed pale repaint (the head masters' tone).
- The robe is smoother than the installed mottled cloth. A few darker fold streaks on the front skirt follow the
  installed robe's broad shading.
- The upper back's gold mantle is larger than the installed one, as on the HD back master.
- The hair/skin edge is softened by the 1024 mask (see the 5.7 % above).
- A thin texture seam remains on the nose bridge, at installed level.
- Not done: an in-game run, the Android cook.

### Rebuild

```sh
P=level_generation/creatures/mm7_m274_texpass_claude
python3 -I $P/scripts/compose.py $P/textures/m274_tp
python3 -I $P/scripts/closeup_fix.py $P/textures/m274_tp $P/textures/m274_tp3 moustache=flat   # see the sections below
python3 -I $P/scripts/apply_layout.py $P/work/before_texpass/mm7_m274.glb $P/work/uv_fine.npz \
    $P/textures/m274_tp3 $P/work/nomoustache/pre_tp3.glb   # input: the pre-pass GLB (its LOD0 is the layout's mesh)
python3 -I $P/scripts/remove_moustache.py $P/work/nomoustache/pre_tp3.glb $P/textures/m274_tp3_eyes.json \
    $P/export/mm7_m274.glb
python3 -I $P/scripts/glb_diff_removal.py $P/work/nomoustache/pre_tp3.glb $P/export/mm7_m274.glb
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $P/export/mm7_m274.glb
flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py $P/export/mm7_m274.glb --world mm7
```

Inputs: `work/lod0_before.npz` (`dump_lod0.py`), `work/approved_fine_*` (`resample_approved.py`),
`work/texel_xyz2048.npy` and `work/islands.npy` (`texel_maps.py`),
`textures/m274_tp_ao_2k.png` (`bake_ao.py`). Viewer: `viewer_variants.py <glb> <tag>`, `viewer_manifest.py`;
sheets: `pair_sheet.py`. Measures: `layout_quality.py`, `skin_check.py`, `tier_tone.py`, `lod1_check.py`.

**Rollback:** `flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py
level_generation/creatures/mm7_m274_texpass_claude/work/before_texpass/mm7_m274.glb --world mm7`. That file is the
pre-pass installed GLB with the gait clips.

## Close-up fixes (2026-11-01)

User close-up review (tier B Wizard, front head close-up):
- the moustache read as two dark sausages with a bare skin bump between them;
- a pale lower-lip/chin patch sat inside the beard like a hole;
- on other MM7 models, eyes showed shattered, blocky paint at close range.

`scripts/closeup_fix.py` runs after `compose.py`: `textures/m274_tp_*` in, `textures/m274_tp2_*` out (installed).
Everything is painted from the texels' rest-pose positions (`work/texel_xyz2048.npy`), so every triangle agrees and no
paint edge follows a triangle line. Only images and the region mask changed. `glb_diff.py` OK, winding 0, flat 0.00,
atlas unchanged (59.6 %), LOD1 error 1.2 mean.

- **Moustache**: the moustache piece is its own mesh component (107 triangles under the nose, centre bump
  included). All of it is now hair in the hair region (B, the beard ramp), so A/B/C colour it ginger / dark grey /
  white:
  - strands run outward and down along rays from a point under the nose tip (wavy, broken along their length);
  - brightness is rank-mapped onto the beard's distribution near the mouth (L p10/50/90 0.135 / 0.209 / 0.280),
    with a lighter shadow on the underside;
  - the upper lip under it (visible between its lower edge and the mouth) is moustache hair too, so it reads as one
    mass that meets the beard at both mouth corners;
  - the hair fades at 30 % onto the skin just under the nose.
- **Mouth**: the mesh has a closed mouth: the moustache box, then the lower lip's upward slope (y 1.4355–1.4445 m),
  a crease, the chin.
  - A small lower lip in lip colour (188 texels), |x| < 9–12 mm, shaded by AO.
  - A thin dark mouth line (130 texels) between the lower lip and the moustache hair; the faces hidden behind the
    moustache are hair or dark, none pale.
  - The bare chin and lower-lip front, plus the old patch's feathered rim (it showed as an orange outline on B), are
    beard: 843 texels of strands fanning down, feathered over 1.5–4 texels into the painted beard and added to the
    hair region.
  - The 1024 mask edit averages only covered texels, so island edges are not half-masked (orange cracks on B in an
    intermediate build).
- **Eyes**: the carried-over installed eye paint showed a dark block and a split iris on the character's right eye
  at close range. Each eyeball (its own component) is now painted procedurally in eye-local coordinates:
  - sphere fitted (R 9.8 mm; centres x ∓0.017, y 1.488, z 0.115); axis from the centre through the visible cap,
    blended with straight ahead;
  - off-white sclera darkening to the edges, and a blue-teal iris (angular radius 0.50 rad) with radial streaks and a
    darker limbal ring;
  - a round pupil (0.17 rad), the upper lid's shadow on the top of the eyeball and a small soft highlight;
  - the skin within 3 mm of each eyeball (lid rims, corners: about 270 texels per eye) takes up to 50 % lid shadow.
- Skin seams (`skin_check.py`, first install → close-up fixes): A 6.7 → 6.4, B 7.3 → 7.0, C 7.5 → 7.2 (mean levels);
  face-skin samples touched by a tier region 5.7 % (unchanged).

Checks: installed with the shared lock (12/12 cooked textures present); `mm6_mm7_mm8_actor_models_build_every_binding`
pass (647 descriptors on 185 models); viewer check 81 switches, no console errors.

Viewer: tiers `before` (installed before the pass), `pass` (first install) and `final`. Close-up focuses: "Mouth
close-up" (arms) and "Eyes close-up" (feet). Sheet [review/closeup_sheet.png](review/closeup_sheet.png): every tier,
first install | close-up fixes; columns mouth front, mouth 3/4, eyes front, eyes 3/4, face. Shots are in
`review/shots/m274_<tier>_{pass,final}_{mf,mq,ef,eq,ff}.png`.

Rollback to the first install: `work/before_closeup_mm7_m274.glb` (install it with the same flock command).

Limits:
- The moustache's procedural strands are cleaner than the Meshy beard.
- A faint brownish lid shadow from the paint stays above the right eye.

## Moustache geometry removed (2026-11-01)

User request: remove the moustache geometry and keep only the face surface under it.

**Investigation** (scratch copy, LOD0 only, `review/shots/m274_{a,b}_scratch_*`):
- The moustache is a separate shell. It sits on the face along 23 open edges, and it is its own connected component
  in LOD0 (107 triangles), LOD1 (23) and LOD2 (4); LOD3 has none. Each shadow mesh mirrors its LOD.
- The face under it is intact except for one small opening: a 5-vertex loop, 5 × 6 × 5 mm in LOD0 and 7 × 7 × 5 mm in
  LOD1, at the philtrum. It showed as magenta/dark shards in the scratch close-ups. LOD2/LOD3 have no opening.
- The mouth line and the small lower lip read without the box from the front, 3/4 and side.

**Removal** (`scripts/remove_moustache.py`, after `apply_layout.py`):
- The moustache component is dropped from every LOD and shadow mesh, found per mesh by connectivity.
- The opening is closed by a fan of 3 triangles over the loop's own vertices, wound like the surrounding faces. The
  fill corners copy those vertices' normal, joints and weights. Their UVs are a front projection into a 48-px
  hole-fill patch of free atlas space, painted to match.
- LOD1 UVs are projected again per chart from the new LOD0; 25 LOD1 triangles near the mouth and eyes changed.
- LOD2/LOD3 keep their UVs, and their maps are transferred again from the new LOD0.
- Vertex buffers are rebuilt from the kept corners: LOD0 9,862 → 9,722 vertices, 8,228 → 8,124 triangles
  (−107 +3); LOD1 4,113 → 4,093 (−23 +3); LOD2 2,057 → 2,053.
- `glb_diff_removal.py`: OK. Nodes, skin, inverse binds, every clip, materials and variants are unchanged, and so are
  position, normal, joints and weights of every kept corner. The fill reuses existing vertex positions. UVs changed
  only on the LOD0 eyeballs (135 triangles) and on the 25 LOD1 triangles above. The base build passes `glb_diff.py`
  against the pre-pass GLB.

**Eyes in their own patches:** at a true close-up even the procedural eyes were blocky (about 22 × 22 texels per
eyeball at the head density) and showed white sclera shards past the low-poly lids.
- Each LOD0 eyeball now maps (planar along its axis) into its own 64-px patch of free atlas space
  (`work/nomoustache/patches.json`).
- `closeup_fix.py` paints each patch with the same procedural eye, and the sclera now darkens to the lid colour
  towards the cap's edge.
- The patches' robe/cape mask channels are cleared: `compose.py` had padded the robe channel into that free space,
  and the first fill showed purple.

**Paint** (`closeup_fix.py moustache=flat|bare`):
- *flat* (installed): a flat painted moustache on the exposed upper lip, in the hair region, so each tier colours it.
  Strands run outward and down from under the nose, with the beard's brightness. It is dense down to the mouth line
  and out to the corners, where it meets the beard, with a ragged, thinning feathered edge under the nose. The thin
  dark mouth line and the small lower lip are kept.
- *bare* (viewer only): clean upper-lip skin (the cheek skin tone, AO-shaded, fine pore noise), with the same mouth line
  and lip. GLB: `work/nomoustache/nm_bare.glb`.

**Gates** (installed flat version):
- `check_winding.py` 0 inverted; `flat_shading_check.py` flat 0.00.
- Texture quality: atlas 59.7 %, 148 islands, fragments 0.1 %.
- LOD1 against LOD0: colour error mean 1.2, p99 20.8.
- Openings near the mouth: none in any LOD. The only open edges nearby are the eyeballs' own cap rims (y 1.478), as
  before.
- `detached_parts_audit.py`: same flagged parts as before (the two braids). One component fewer; the head part has
  1,506 triangles.
- LOD switch (viewer entries `flatlod1..3` draw LOD1–3 in place of LOD0): LOD0 → LOD1 shows the same flat moustache,
  closed mouth and eyes; LOD2/LOD3 have no hole at the mouth.
- Floor audit (Mage A/B/C) unchanged: stand −0.7..−0.6, walk −1.4..0, dead 0.0, ok.
- Installed under the flock, 12/12 cooked textures; `mm6_mm7_mm8_actor_models_build_every_binding` pass;
  viewer check 216 switches, no console errors.

**Viewer:** tiers `final` (moustache geometry, the previous install), `flat` (installed) and `bare` (viewer only),
plus `flatlod1..3`. The close-up focuses aim at the posed head (`scripts/posed_point.py`: in Standing the head sits
about 17 cm back and 4 cm up from its rest position): "Mouth close-up" (arms), "Eyes close-up" (feet).

**Sheet:** [review/moustache_removed_sheet.png](review/moustache_removed_sheet.png). Every tier, rows `final` (before),
`flat` and `bare`. Columns: mouth front, mouth 3/4, mouth side, eyes, face. Shots are in
`review/shots/m274_<tier>_{final,flat,bare}_{mf,mq,ms,mb,ff}.png`.

**Rollback** to the moustache-geometry install: `work/nomoustache/rollback_installed_closeup.glb` (same flock install
command).

**Limits:**
- The flat moustache is softer than the Meshy beard: the upper lip under the old box is crumpled geometry seen at
  grazing angles.
- At the closest zoom a few ginger flecks show through partly masked edge texels on tiers B and C.

