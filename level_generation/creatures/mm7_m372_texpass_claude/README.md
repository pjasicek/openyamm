# MM7 Peasant Human2 Female texture pass (`mm7_m372`)

Related projects: [mm7_m372_claude](../mm7_m372_claude/README.md) (production, HD masters, region ramps),
[mm7_m372_reduce_claude](../mm7_m372_reduce_claude/README.md) (installed LOD0/LOD1),
[lod_repair_claude](../lod_repair_claude/README.md) (far LODs). The installed file also carries the gait-h14 clips
(Walk2, Jog). This project has its own lease (`mm7:m372-texpass`, token in `work/LEASE.txt`).

## Texture quality pass (2026-11-01)

**Why.** The user reviewed an in-game screenshot of a skin with a pale hood and a blond fringe. Body and head
textures were terrible: blurry, flat, with a blotchy face and hood. The faces had to be seamless in every skin: one
continuous skin tone, with no head/body seam and no mismatched patches. The coordinator later added close-range
fixes found on the other MM7 peasants: procedural eyes, a dark mouth opening and soft nostrils.

**Installed 2026-11-01** (`tools/install_model.py --world mm7` under `output/creature_3d_locks/texpass_install.lock`).

**What changed.** Only UVs (with the vertex splits they need) and images changed. Nodes, skin, inverse binds, every
clip (Standing, Walking, Walk2, Jog, Hit, Death, Dead, Fidget), materials, the six variants, the ramps and the LOD
lists are the installed ones. `glb_diff.py` confirms it ("only UVs, vertex splits and images differ"). `actors.yml` is
untouched.

### Results (`texture_quality.py`, LOD0 base colour)

| | Installed (2080×1024 body \| head atlas) | Pass (2048²) |
|---|---|---|
| Atlas use | 48.9 % of 2080×1024 (1.04 M texels) | **53.0 %** of 2048² (2.22 M texels) |
| Density p10 / p50 / p90 | 292 / 481 / 954 | 1,072 / 1,117 / 1,252 |
| Spread p90/p10 | 3.27 | 1.17 |
| Islands / surface on fragments | 725 / 7.7 % | 191 / 0.1 % |
| Stretch p90 | 1.86 | 1.08 |
| Face / eyes, texels per m | 2,013 / 2,087 (own 1K head set) | **2,308 / 5,000** (procedural eyes on charts of their own) |
| Hands / gown / hood, texels per m | 721 / 302 / 555 | 857 / 655 / 838 |
| LOD1 against LOD0 colour error, mean / p99 | 2.4 / 44.9 | 0.9 / 14.5 |

Map sizes: colour and normal 2048², metal/roughness and region mask 1024² (RGBA), replacing 2080×1024. LOD2 and LOD3
keep 512 and 256 px.

### Route (`scripts/`; the scripts are copied and adapted from `mm8_m480_texpass_claude`)

1. **`dump_lod0.py`** dumps the installed LOD0 to `work/lod0_before.npz`, with the approved head set and each face's
   approved region. `work/face_piece_lod0.npy` holds the production Smart Topology piece of each LOD0 face. It is
   built from the reduce project's `face_piece.npy` by a nearest-centroid vote.
2. **`uv_texpass.py`** (Blender) runs `claude_shared/uv_atlas.py` with the fast packer (`fine=250 steps=0`).
   - The paid layout is `work/uv_v2.npz` (`HEAD_FACTOR=3.5 HEAD_FRONT_Z=0.0`, 53.0 %). The head-set faces in front of
     z = 0 (face, fringe, eyes) are ×3.5; the hidden back of the head under the hood is ×1. Hands ×1.3, hood above
     1.45 m ×1.3.
   - The first layout, `uv_fine` (head ×1.8, 52.0 %; brute force gave 50.7 %), was painted and then dropped. It gave
     the face only 1,290 texels/m, below the installed dedicated head set (2,013). Its paints are kept in
     `meshy/*_v2` but are not used. **Never re-run the UV script**: xatlas packs differently on every run.
3. **Retextures** (`requests/*_v3.json`, `meshy-7`, 4K, `enable_original_uv`, backup account):
   - body: the whole mesh with the four HD masters;
   - head: the bust above 1.25 m (head, hood, beads, shoulders, as the head masters show it) with the four HD head
     views.
4. **`resample_approved.py`** carries the installed colour, mask and metal/roughness to `work/approved_v2_*`.
   **`bake_ao.py`** bakes `textures/m372_tp_ao_v2.png`.
5. **`compose.py`** writes `textures/m372_tp_*`. Unlike the Troll pass, it does **not** carry the approved colour at
   low frequency: the user rejected that look.
   - **Paint.** The head-set pieces (head with neck and chest skin, fringe, eyes, circlet, rim beads) use the head
     paint entirely, so no skin has a crossfade. The gown and hands use the body paint. The hood and the neckline
     beads crossfade from body to head paint over 1.30–1.42 m. The gentle grade follows the recipe.
   - **Skin** (head piece without hair, hands) is one albedo, sRGB (204, 151, 130) from the HD head views' lit skin.
     It is multiplied by:
     - the paint's own luminance detail over a 6 mm low pass computed **in 3D** (voxel grid), so no UV seam shows in
       it. The detail is clamped to 0.8–1.2, or 0.9–1.08 at the lids and nose;
     - a compressed share of the low pass, for form;
     - AO, applied once to all skin.

     Paint that is not skin-coloured keeps no detail: hair painted under the hood, bead green on the neck, dark
     wedges. Lips are red paint in the mouth zone, weighted in 3D (the texture-space blur had left a pale seam line).
   - **Mouth, nose and eyes** (coordinator follow-up):
     - The slit between the lips (inward-facing lip triangles, teeth paint, the interior) is one dark gradient.
     - The downward-facing nostril triangles are one soft 1.5 mm shadow, and the nose has no dark detail spike.
     - The eyes are painted by `eyes.py`.
   - **Ramped regions.** For gown, hood + lining and hair, a luminance quantile curve maps the paint onto the approved
     distribution at the same surface points. That distribution is taken only where the approved mask has the same
     region. RGB is scaled by the luminance ratio, so the **installed ramps hold unchanged**. Before the mapping, the
     gown grain and the hood knit are softened (×0.4 and ×0.5 at 1.5 px). Pale hood paint that the head masters
     projected onto the gown's shoulders is filled from the surrounding gown.
   - **Region mask** is assigned by piece (gown, hood, fringe plus the approved crown faces). Lining is pale paint
     within 1.5 cm (in 3D) of the approved lining faces. Accessory faces keep their approved region.
     - Small green paint patches on the hood (up to 1.5 cm²) are beads and stay unmasked dark green in every skin, as
       the modelled beads do. Larger green smears are hood cloth.
     - Head faces that the installed build gave the hood mask keep it where the head pokes through the hood. The inner
       walls seen through a gap in the left cheek become skin: in the installed skins they showed as a sage or blue
       wedge.
   - **Normal** is the paint's, converted from +y down to glTF +y up. Its tilt is capped at the approved map's p90
     (scale 1.0), halved on skin, and flat on the eyes. **Metal/roughness** is the approved map carried over.
6. **`eyes.py`** writes `textures/m372_final_*` and `work/uv_v2e.npz`.
   - **Frames.** `eyefit.py` fits each eyeball sphere (r 10.7 mm) and its frame, looking straight ahead and 5.7°
     down. The eyeball faces are the shell pieces plus 28 head faces that lie on the sphere.
   - **Charts.** Each eye leaves its five to seven xatlas islands for one azimuthal chart of its own: 90 px at
     5,000 texels/m, about 2.1× the face, placed in the largest free atlas squares. The 3–4× that was asked for does
     not fit: the largest free square is about 95 px.
   - **Paint** is procedural, in eye-local angles, so every triangle agrees:
     - an off-white sclera;
     - a grey-green iris (HD head views) with radial fibres, a darker limbal ring and a round pupil;
     - a small highlight;
     - an almond lid opening (iris radius 20°, opening ±40° × +15.5/−17°) with a dark lash line and a soft lid
       shadow outside it.

     The same function repaints head skin within 3 mm of an eyeball, so z-fighting lid faces and corner shards agree
     with the eyeball beneath them. Shards in front of the eyeball get the lash shadow, and lid parts take skin gloss.
7. **`apply_layout.py`** builds `export/mm7_m372.glb` from the pre-pass installed file:
   - LOD0 and its shadow copy get the new UVs (8,214 → 10,074 vertices);
   - LOD1 and its shadow copy get UVs projected per chart from LOD0 (4,624 → 6,046 vertices);
   - LOD2 and LOD3 keep their geometry and UVs, and their maps are refilled with
     `lod_repair_claude/scripts/transfer_textures.py` at 512 and 256 px.

### Faces seamless in every skin (`skin_seams.py`)

The measurements use engine colour: the ramps are applied as the engine applies them. The installed values are given
for comparison.

| | Installed (all six skins) | Pass (all six skins) |
|---|---|---|
| Face / neck / chest / hands mean sRGB | 228,159,143 / 196–207 (tinted per skin) / 226,165,148 / 223–225 | 192–193,141,122 / 189–192,141,121–123 / 197,146,125 / 197,146,125 |
| Skin across the old head/body split at y 1.42 (bands 1.41–1.42 → 1.42–1.43 → 1.43–1.45) | 232 → 219 → 199 (the neck seam) | 190 → 190 → 187 |
| Colour step across skin UV seams, mean / p95 / max | 10.9 / 36.9 / 103–161 | **4.0 / 15.0** / 88 |
| Face skin with any region mask > 0.02 / p99 ramp change | 7.0–7.4 % / 61–99 | 5.7–5.9 % / 25–33 (hair line and hood edge, about 1 mm) |

The neck no longer changes colour with the skin; in the installed file the hood ramp tinted it. The hood and hair
ramps do not reach the face beyond the hood edge and the hairline. Close-ups of every skin (front and ¾) are in the
sheets.

### Tier colours as the engine shows them (`tier_tone.py`, same surface points)

Only texels in the region before and after are compared.
- Gown: within 0.6 levels in every skin.
- Hood: +1.2 levels.
- Hair: +1.5 to +2.1 levels.
- Luminance sd: gown 10.1 → 9.5, hood 29.5 → 28.9, hair 52.3 → 50.6. The values are in `work/tier_tone.txt`.

### Checks

- `glb_diff.py`: OK. `check_winding.py`: 0 inverted closed parts. `flat_shading_check.py`: flat 0.00.
- The texture URIs of `assets_dev/worlds/mm7/models/mm7_m372.glb` all exist (12 of 12, re-checked after the
  regression).
- Regression: `mm6_mm7_mm8_actor_models_build_every_binding` passes (647 descriptors on 185 models, 0 failed). No case
  names m372.
- Viewer: `tools/run_creature_review.py check`, 96 switches, no console errors. In this project the viewer's `feet`
  focus is a face close-up.

**Viewer:** http://127.0.0.1:8912/level_generation/creatures/mm7_m372_texpass_claude/review/viewer/ (installed and
pass for the six skins).

**Sheets** use identical cameras: face close-up front and ¾, head front and ¾, upper body, hands, whole body ¾, back.
- [review/texpass_sheet_a.png](review/texpass_sheet_a.png): skins AA, AB, AC.
- [review/texpass_sheet_b.png](review/texpass_sheet_b.png): skins BA, BB, BC.
- Close-ups: `review/shots/<skin>_{before,pass}_{cf,cq}.png`.

**Meshy: 40 credits** (backup account, 3,860 → 3,740): body and head on `uv_fine` (20, dropped for face density),
then body and head on `uv_v2` (20).

### Left as is (geometry, out of scope for a texture pass)

- A long sliver of three head triangles (3593, 3594, 3596, edges 16 cm) runs from the right mouth corner to the hood
  as a thin light line. It is present in the installed file.
- A small dark wedge shows on the left cheek. It is the inner walls seen through a gap in the mesh, lit from behind.
  It is now skin-coloured (×1.3) instead of sage or blue.
- At head distance the eyes read a little wider than the installed ones: the lid geometry opens wider than the HD
  views.

### Face follow-up (2026-11-01, installed)

The coordinator reviewed the pass's face close-ups (`review/shots_pass1/*_pass_c?.png`) and asked for five fixes. No
Meshy jobs; the lease was re-claimed for this.

1. **Lips** (`compose.py`). The paint drew bright lipstick with a hard outline. They are now:
   - a muted rose, `LIP_TONE` sRGB (192, 124, 114), only a little darker than the skin (204, 151, 130);
   - an upper lip ×0.88;
   - the skin's own detail and AO;
   - a 0.9 mm soft edge into the skin, taken in 3D, with no outline.

   The HD head views themselves have red lips; the coordinator asked for the muted natural colour.
2. **Mouth slit** (`compose.py`, `fix_mesh.py`). It is now a narrow dark-rose line and not black. The line is a smooth
   curve fitted through the mouth opening and the lip corners, painted on the front of the lips (σ 0.7 mm, rose
   ×0.42), so the triangle edges do not draw it. The inward-facing faces between the lips are a mid lip shadow (rose
   ×0.8, their lighting darkens them). The mouth opening itself (27 boundary edges) is closed by a fill painted rose
   ×0.55, sRGB (147, 94, 86). Through that opening the inside of the head had shown as black and pale shards.
3. **Nostrils** (`compose.py`). They are two small soft shadows (σ 1.3 mm, ×0.65) at the centres of the nostrils'
   downward faces. Between the nose and the lip there is no paint smudge and little AO. The nose and mouth zones are
   centred on the face midline (x −7.2 mm: the head sits off x = 0).
4. **Mesh** (`fix_mesh.py`, clean local fixes; LOD0, LOD1 and both shadow copies).
   - **Spike:** a fan of three triangles (LOD0 3593, 3594, 3596; LOD1 1410–1412) shared one vertex pulled 16 cm down
     to the hood. It is removed, and the small triangle its other corners leave open is filled.
   - **Cheek wedge:** it was a five-edge hole in the left cheek. It is filled with three triangles.
   - **Fills** copy their loop vertices' positions, normals, joints and weights, so they skin like their neighbours.
     They are ear-clipped in the loop's plane, with a centroid fan for the zig-zag part of the mouth loop, and wound
     against their neighbours.
   - **Fill charts:** each fill gets a small planar chart in free atlas space, since its neighbours lie on several
     charts. Skin fills take the surrounding skin colour at the loop.
   - **Triangle counts:** LOD0 8,546 → 8,574, LOD1 4,272 → 4,285. Every kept triangle keeps its corner positions,
     normals, joints and weights (`fix_mesh.py` check). `glb_diff.py` on the build before `fix_mesh.py` reports only
     UVs, vertex splits and images.
5. **Eyes** (`eyes.py`). The painted lid opening's upper edge is lowered to 11° (lower lid 15°), so the lid colour
   and lash line on the eyeball cover the iris top as in the HD views. No geometry changed.

**Checks:**
- Winding: 0 inverted. Flat shading: 0.00.
- Installed under the lock; 12 of 12 cooked textures present.
- `mm6_mm7_mm8_actor_models_build_every_binding` passes.
- Viewer check: 96 switches, no errors.
- Skin across UV seams: mean 3.5, p95 12.7. Face 195, chest 197, hands 197, the same in all six skins.
- Tier colours unchanged from the first pass.

**Close-ups:**
- [review/face_followup_sheet.png](review/face_followup_sheet.png): six skins, pass 1 against follow-up, front and ¾.
- Before: `review/shots_pass1/<skin>_pass_{cf,cq}.png`. After: `review/shots/<skin>_pass_{cf,cq}.png`. Installed
  originals: `review/shots/<skin>_before_{cf,cq}.png`.

**Rollback** to pass 1: `work/before_texpass/mm7_m372_pass1_installed.glb`.

### Round 3: robe and face (2026-11-01, installed)

This round comes from the user's review of the installed follow-up. The robe bulged on her right hip in Standing, and
the face was still wrong at close range. No Meshy jobs were run, and the lease was re-claimed for this round.

**A. Robe bulge (animation only; `scripts/dress_fix.py`, copied from `mm7_m342_texpass_claude`, 6° arms).**
- **Diagnosis:**
  - **Rest mesh:** fine; the robe falls straight in the HD masters' A-line.
  - **Chains:** fine.
  - **Clip:** the cause is the cloth simulation in Standing, and in Fidget and Hit, which start from it. The hands
    hang on the rest skirt surface, so `robe_sim.py` pushed the side chains out of the hand and forearm capsules:
    up to 8 cm in Standing and 11 cm in Fidget.
  - **Walking clips:** keep the rest width (the walk retarget has the arms abducted).
- **Fix** (as m342; Standing, Fidget and Hit only):
  - Both upper arms are abducted 6° about the chest's forward axis.
  - Every robe chain point standing more than 1 cm outside the simulation's rest bell is pulled back. The leg capsules
    keep the push they need.
  - Walking, Walk2, Jog, Death and Dead are unchanged.
  - `glb_diff.py` reports only UVs, vertex splits, images and the allowed rotations (Robe_*, both upper arms in those
    three clips).
- **Gates** (`scripts/skirt_gates.py`, every other key of every clip). Robe stretch limit: production p99 ≤ 1.38,
  Death 4.25.

| Clip | Robe stretch p99 | Hands in skirt | Sleeves in skirt | Skirt width at 0.85 / 0.70 / 0.50 m | Legs through |
|---|---|---|---|---|---|
| Standing | 1.18 → 1.14 | 5.0 → **0.0 cm** | 6.5 → 2.6 cm | 0.443 / 0.449 / 0.491 → **0.383 / 0.432 / 0.494** | 6.1 → 6.2 cm (0.7 % of leg vertices, unchanged) |
| Fidget | 1.29 → 1.18 | 5.7 → 0.0 cm | 9.9 → 5.4 cm | 0.441 → 0.371 at 0.85 m | 5.8 → 0.0 cm |
| Hit | 1.29 → 1.16 | 5.7 → 0.0 cm | 9.9 → 7.3 cm | 0.425 → 0.372 at 0.85 m | 5.8 → 0.0 cm |
| Walking, Walk2, Jog, Death, Dead | unchanged (1.30, 1.40, 1.61, 2.27, 1.38) | 0 | Walking clips 10 cm (the measure's cap, unchanged) | Walking 0.368 / 0.408 / 0.454 | Jog 17.4 cm (unchanged) |

  The sleeve figures count the bell sleeves' inner lining beside the skirt. They come down in the fixed clips and are
  identical in the untouched walking clips. Jog's robe stretch over the gate (1.61) and its leg-through-cloth (17 cm)
  are unchanged from the gait pass.
- **Floor:** `floor_audit.py --world mm7 --match 'Peasant Human2 Female*'` reports 9 bindings and 0 problems
  (stand −1.3…−1.2, walk −0.1…+0.5, dead 0.0).

**B. Face (as the accepted m342 face).**
1. **Eyes** (`eyes.py`).
   - The lid-coloured part of the eyeball (the head shell's eye holes are larger than the painted opening) takes:
     - the colour of the skin just around the eye (no darker lid band);
     - the lids' shading normal through the normal map (`scripts/normfix.py`: the engine's derivative tangent frame,
       divided by the cook's ×3 relief lift, tilt capped at 35°). Its sphere normals had shaded it as a hard-edged
       patch.
   - The opening's upper lid covers the iris top. The lash line is dark above; below there is only a subtle lower-lid
     line. Both fade toward the corners, so no dark fleck remains where the lids meet.
   - The sclera darkens to the corners (m342 colours). Skin hugging the eyeball has skin gloss and a soft rim.
2. **Nose** (`compose.py`).
   - The dark blob was shading: the underside's albedo was already near white.
   - The down-facing underside's shading normal is turned toward the front through the normal map, by up to 70 % as
     it faces down. It is blended with the paint's relief, and the gutters are padded.
   - The normal-map relief within 16 mm of the nostrils is cut by 70 %.
   - Two small nostril shadows (σ 1.6 mm, ×0.4) sit 5.5 mm either side of the midline.
3. **Lips and slit.**
   - The slit's colour is a function of the 3D distance to one smooth curve through the opening and the lip corners.
     It has a 1.2 mm core plus σ 0.8 mm and is applied to every face alike (front lip faces, inward faces, the mouth
     fill), so the jagged gap edges fall inside one gradient.
   - The slit is dark rose, ×0.32 of the lip tone; the mouth fill has the same colour.
   - The lower lip's inner shelf is held in shadow (×0.7). One rose is used for both lips: upper ×0.95, lower ×0.88.
   - There is no paint relief on the lips or the slit.
   - **Mouth-corner mark:** the AO had been baked with the spike fan in place, and the paint itself (the upload carried
     the spike) drew its edge as a dark scratch on the right cheek. AO and paint detail are cleared within 7 mm of the
     removed spike. The normals of the spike's former corners are recomputed from the faces that remain
     (`fix_mesh.py`).
4. **Gloss:**
   - Lips are matte (specular 0.12, roughness 0.7).
   - The slit and the mouth fill are 0.05 / 0.95.
   - Eyes are wet only inside the opening.

The viewer now applies the cook's normal relief lift (`viewer_variants.py`, as in game), so close-ups show the game's
relief.

**Checks:**
- Winding: 0. Flat shading: 0.00.
- Installed under the lock; 12 of 12 cooked textures present.
- `mm6_mm7_mm8_actor_models_build_every_binding` passes.
- Viewer `check`: 192 switches, 0 errors (revision `texpass-20261101-r3`, ids `m372_<skin>_{before,pass,r2,r3}`).
- Atlas 53.0 %. Tier colours unchanged.

**Shots:**
- `review/round3_robe_sheet.png`: HD masters, then the follow-up install against round 3. It shows Standing front,
  left, right and ¾, Walk2 mid-step front, left and ¾, and hip close-ups.
- `review/round3_face_sheet.png`: all six skins, follow-up against round 3, face close-up front, ¾ and side.
- Robe shots: `review/shots/robe_{r2,r3}_*.png`. Face shots: `review/shots/<skin>_{r2,r3}_{cf,cq,cs}.png`.

**Left:**
- A slight stair-step remains where the upper lip's inner edge meets the slit. It is geometry, much softer than
  before.
- The nostrils read lightly.
- Slight facets show on the eyeball's lid part at very close range.

**Rollback** to the follow-up: `work/before_texpass/mm7_m372_followup_installed.glb`.

### Rebuild and rollback

```sh
P=level_generation/creatures/mm7_m372_texpass_claude
python3 $P/scripts/compose.py $P/work/uv_v2.npz $P/work/approved_v2 $P/textures/m372_tp_ao_v2.png $P/textures/m372_tp
python3 $P/scripts/eyes.py $P/work/uv_v2.npz $P/textures/m372_tp $P/textures/m372_final
$P/scripts/merge_install.sh             # dress_fix.py, apply_layout.py, fix_mesh.py on work/merge_src_mm7_m372.glb, checks
$P/scripts/merge_install.sh --install   # then install under the shared lock
python3 $P/scripts/viewer_variants.py $P/export/mm7_m372.glb pass && python3 $P/scripts/viewer_manifest.py m372_aa_pass before=installed "pass=texture pass"
$P/scripts/shots_all.sh && python3 $P/scripts/texpass_sheet.py $P/review/texpass_sheet_a.png aa ab ac
```

These commands are run from the repository root (`compose.py` and `eyes.py` take paths relative to it).

If a later layer reinstalls the model without the pass, rebuild with `FRESH=1 merge_install.sh`. Its LOD0 must still
be the pre-pass mesh.

Rollback: install `work/before_texpass/mm7_m372.glb` (sha256 4b05594e…, identical to `work/merge_src_mm7_m372.glb`).
