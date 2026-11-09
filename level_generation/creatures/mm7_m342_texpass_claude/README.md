# MM7 Peasant Human1 Female (`mm7_m342`) texture pass

Sharper textures only, run as the
[texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) on the installed GLB. Queue and earlier results are in
[texpass_mm678/HANDOFF.md](../claude_shared/texpass_mm678/HANDOFF.md). Mesh, rig, weights, clips (including Walk2/Jog
from the gait pass), materials, the nine variants `m342_aa`..`m342_cc`, region ramps, LOD lists and bindings are the
installed ones.

Related projects:
- [mm7_m342_claude](../mm7_m342_claude/README.md): production (HD masters, head views, ramps);
- [mm7_m342_reduce_claude](../mm7_m342_reduce_claude/README.md): the installed LOD0/LOD1;
- `mm7_m342_gait_h14_claude`: the installed gait clips.

Lease `mm7:m342-texpass` (token in `work/LEASE.txt`).

## Texture quality pass (2026-11-01)

**User review (2026-11-01, in-game MM7 peasant women):** the textures were poor on body and head. Faces showed patches
and seams in different skin tones, and the hair looked flat and smeared. The face must be seamless, with one skin tone
across the face and from head to body, in every skin.

**Cause.**
- The installed atlas was 2080×1024: a 1K body set and a 1K head set. These were 2K Meshy paints downsampled once to 1K.
- Atlas use was 26.8 %, with 863 islands and 8.8 % of the surface on fragments.
- The production compose repainted skin as one albedo times Meshy's clipped shading. Each Voronoi-filled triangle facet
  therefore kept its own brightness, which reads as patches on the face, and the head and body sets met at a seam.
- Meshy had smeared the gold of the earrings over the hair strands by the ears.

**Route (`scripts/`).**
1. **`dump_lod0.py`** dumps the installed LOD0 to `work/lod0_before.npz`, with these extra per-face data:
   - the head-set faces (the right half of the old atlas);
   - connected pieces;
   - the hidden legs under the skirt: 201 faces that all shared one UV point of the petticoat.
2. **`uv_texpass.py`** (Blender, `claude_shared/uv_atlas.py`) lays out one 2048 atlas:
   - densities: head set (face, scalp, 31 hair strands, eyes, mouth) ×1.8, hands ×1.3, hidden legs ×0.3. The legs are
     welded apart from the shoes, so no chart straddles the two.
   - `cut_closed=1`: without it, the belt band collapsed 28 triangles to zero UV area.
   - fast packer sweep, `max_cost=4`.

   **`work/uv_cc4_fine.npz` is the paid layout. Never re-run it.** Hashes are in `work/layout_hashes.txt`. Runs compared:
   `uv_fine` 54.4 % (zero-area belt), `uv_cc_fine` 53.8 %, `uv_cc4_fine` 55.7 %.
3. **Retextures** (`requests/`, `meshy-7`, 4K, `enable_original_uv`, backup account):
   - **Body:** the whole mesh with the four HD masters.
   - **Head:** the head set plus the skin shell above 1.30 m (neck, collar, shoulders as the head views show them),
     with the four close head views.

   Both returns keep the layout: body 55.7 %, 211 islands; head 24.9 % of the same square.
4. **`resample_approved.py`** carries the installed colour, mask and metal/roughness onto the layout at the same surface
   points. **`bake_ao.py`** bakes AO (reach 3.5 cm, 2K).
5. **`compose.py`** builds `textures/m342_tp_*` (details in its docstring):
   - **Paint.** 4K is downsampled once to 2K. The head paint covers the hair pieces and the shell above the neck,
     crossfaded on the shell over 1.33–1.43 m. Shell texels where either paint is not skin keep the body paint: the head
     views have no straps.
   - **Classes** per texel by piece and colour (production rules): dress, linen, brass, leather, hair, eye/mouth detail
     pieces, earring, legs, skin.
   - **Hair fixes.** Gold earring paint, pale specks and the unpainted crown on the strands are filled from the
     surrounding hair, keeping their luminance detail (86k texels). Hair paint Meshy projected onto the nape, and the
     painted gold of the unmodelled left earring on the cheek, are filled from the skin (11k texels). The hidden legs
     keep the installed flat stocking colour.
   - **Grade.** The recipe's gentle grade (local 0.3, contrast 1.06, saturation 1.15, AO ×0.5).
   - **One skin tone.** A low-frequency skin colour field is computed per welded vertex in 3D and interpolated per texel.
     It is continuous across UV seams, the head/body crossfade and the hand shells. The 2.5 cm Gaussian sets luminance
     and the 1.2 cm Gaussian sets hue. Only skin-hue texels feed it, so lips and brows do not tint the skin around them.
     Skin is multiplied by the installed skin colour (213, 149, 121) over this field; the remaining fine hue deviation is
     halved (lips excluded). The paint keeps its shading detail and AO.
   - **Seam blend.** Across every skin UV seam (345 edges), each side moves halfway to the other and fades into its own
     chart over 5 texels.
   - **Ramp regions.** Dress and hair, plus the linen, leather and brass classes, take per-channel quantile curves onto
     the installed distribution. The installed ramps therefore stay unchanged.
   - **Maps.** Region mask (R dress, G hair) and metal/roughness (the production specular and roughness table) are 1K,
     built from the new classes. The normal map is the paints' normal (+y flipped to glTF), at full strength like the
     installed build.
6. **`apply_layout.py`** builds the runtime GLB from the installed file:
   - LOD0 and its shadow copy take the new UVs, with vertices split at the seams (8,871 → 10,280).
   - LOD1 and its shadow copy take UVs per chart projected from LOD0 (5,106 → 6,135).
   - LOD2 and LOD3 keep their geometry and UVs; `lod_repair_claude` `transfer_textures` refills their maps at 512/256.

| `texture_quality.py`, LOD0 | Installed | Pass |
|---|---|---|
| Texture | 2080×1024 (body \| head) | 2048² |
| Atlas use | 26.8 % | **55.7 %** |
| Equivalent square | 1,077 px | 1,529 px |
| Density p50 (texels per creature size) | 424 | 980 |
| Median texels per cm: head / body | 4.9 / 3.0 | **10.4 / 5.8** |
| Islands / fragment surface | 863 / 8.8 % | 211 / 0.2 % |
| Stretch p90 | 1.87 | 1.13 |

The density spread is 5.9 by design: hidden legs ×0.3, head ×1.8. Map sizes: colour and normal 2048²; mask and
metal/roughness 1024².

**Checks.**
- **Skin as the engine shows it** (`face_tone.py`, `review/face_tone.json`; ramps applied, nine skins, same surface
  points):
  - Across every LOD0 edge of the face and neck, the colour step 2 mm apart is compared with the step inside one
    triangle. Interior edges: ratio 1.15 → **0.99** in every skin, so the faceted patches are gone. UV seams: ratio 1.38
    → 1.23–1.32; the median step is 1.6 dE across against 1.9 within. The remaining mean comes from seams running along
    the brows and the lip line.
  - Chroma difference (a\*b\*) between the face patches: max 4.0. The neck, crossfade and chest differ by 0.9.
  - Hair or dress ramp on face and neck skin: 0 (a 0.028 strap feather on the shoulders).
- **Tier colours:** the dress and hair means of all nine skins match the installed ones within 1 level
  (`tier_tone.py`). Luminance sd is +1–3 % from the new detail.
- **Eyes:** pupils are centred and the blue-grey irises intact, matching `references_hd`/`references_head`. They are
  sharper than installed, where the eyes were smeared facets.
- **Geometry and data:**
  - `glb_diff.py`: only UVs, vertex splits and images differ.
  - `check_winding.py`: 0 inverted.
  - `flat_shading_check.py`: 0.00.
  - `lod1_check.py`: LOD1 against LOD0 colour error is mean 3.6 → 1.5 and p99 103 → 26.
- **Viewer:** `check` passes 144 switches with 0 errors.
- **Install and regressions:** installed with `flock output/creature_3d_locks/texpass_install.lock
  tools/install_model.py export/mm7_m342.glb --world mm7`. All 12 cooked texture URIs are present. The build succeeds,
  and `mm6_mm7_mm8_actor_models_build_every_binding` passes (647 descriptors, 0 failed). No regression case names this
  model. Not done: an in-game look.

**Sheets** (review-viewer shots, identical cameras; installed above texture pass for each skin; head front, ¾, left,
back, shoulders, whole body): `review/texpass_sheet_{a,b,c}.png` (outfits A/B/C, three tiers each). Viewer:
`review/viewer/` (revision `texpass-20261101-r1`, ids `m342_<skin>_before` / `m342_<skin>_tp`).

**Drift and limits.**
- The face now follows the head views: darker, defined brows, red lips and lined eyes, where the installed face was
  pale and soft.
- The modelled right earring (a small gold drop) reads brighter yellow at the same brass tone. The unmodelled left
  earring is no longer painted on the cheek.
- The pale sheen on the crown is a lighting effect on the flat top of the hair cap and is the same as installed.
- Brows are paint on skin, not ramps, so they stay brown on the blonde, white and grey tiers, as installed.

**Meshy: 20 credits** (body and head retexture, 10 each, backup account).

Rebuild (no paid step):

```sh
P=level_generation/creatures/mm7_m342_texpass_claude
python3 $P/scripts/resample_approved.py $P/work/uv_cc4_fine.npz $P/work/approved_fine 2048 1024
tools/run_creature_blender.sh --token <lease> $P/scripts/bake_ao.py $P/work/uv_cc4_fine.npz $P/textures/m342_tp_ao_2k.png 0.035 2048
(cd $P && python3 scripts/compose.py textures/m342_tp)
python3 $P/scripts/apply_layout.py <installed or work/before_texpass/mm7_m342.glb> $P/work/uv_cc4_fine.npz $P/textures/m342_tp $P/export/mm7_m342.glb
python3 $P/scripts/glb_diff.py <that input> $P/export/mm7_m342.glb
(cd $P && python3 scripts/face_tone.py work/before_texpass/mm7_m342.glb export/mm7_m342.glb review/face_tone.json)
python3 $P/scripts/viewer_variants.py $P/export/mm7_m342.glb tp && python3 $P/scripts/viewer_manifest.py texpass-20261101-r1 m342_aa_tp before=installed tp="texture pass"
```

If a later layer changes the installed GLB (clips, nodes), run `apply_layout.py` on the new installed file; it refuses
an input whose LOD0 differs from `work/lod0_before.npz`.

Rollback: `flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py
level_generation/creatures/mm7_m342_texpass_claude/work/before_texpass/mm7_m342.glb --world mm7`.

## Close-up fixes and dress shape (2026-11-01)

User review of the installed pass (the same close-up issues as the Elf Female `mm7_m322`), in two jobs.

### A. Face close-ups

**Eyes.** At close range they looked shattered and blocky. The Meshy layout had cut each eyeball into 3–4 charts of
about 1,000 texels, and each chart painted its own piece of iris; pale and orange shards sat in the lower lids and
corners. The installed pupils also pointed 10–18° outward.
- `face_geom.py` fits each eyeball sphere (right r 11.3 mm, left 11.6 mm) and finds its lid opening: the eyeball
  surface in front of the skin shell, seen from the front, 15 × 9 mm. The forward axis points at the opening's centre,
  9–12° outward of +z, so the pupil sits centred in the opening as in the HD front head view.
- `uv_eyes.py` makes `work/uv_eyes.npz`: the paid layout with only the two eyeballs re-charted, each as **one disc**.
  The projection is azimuthal around the axis, linear to 46°, with the hidden back compressed ×0.2. The discs sit in the
  largest free circles of the atlas.
  - Visible-cap density: 1.05 → **3.5 px/mm** (×3.3). 4× did not fit a second disc.
  - Texels per eye: about 1,000 → 5,000.
  - No seam crosses the visible eye. The few folded triangles at the back share colours, because colour is a function of
    direction.
- `face_paint.py` paints the eyes from geometry (angle to the axis, azimuth around it):
  - **sclera:** off-white, darkening toward the corners;
  - **iris:** blue-grey (22°), warm collarette, radial fibres, dark limbal ring;
  - **pupil:** round black pupil (7.5°);
  - **highlight:** a small soft one;
  - **material:** flat normal, specular 0.45, roughness 0.3.
- Lash cards (pieces 20/31) are the dark lash line. The lower rims (21/32) are a soft lid shadow.
- The skin shell within 0.8–2.5 mm of each eyeball (the lid margins, about 800 texels) takes the lid shadow: dark above,
  lighter on the lower margin. No pale shards remain.

**Lips.** A diagnostic build showed that the visible lips are the skin shell, closed over the mouth; the gap is a crease.
The separate lip pieces show only inside the gap.
- Lip pieces 23/24 and the mouth interior (25), which had bright pink back faces, take a dark gradient by depth.
- So do the shell's crease texels (about 1,200) whose smooth normal turns away from the front.
- The pale shards were gloss: the mouth parts carried the eye class (specular 0.9, roughness 0.2), and the shell's
  faceted lips had skin gloss. Mouth parts are now matte (0.05 / 0.95) and the shell's lip texels lip-matte (0.12 / 0.7).
- The outer lip paint is unchanged.

**Nose.** The paint under the tip was already light (luminance ≥ 94; the wedge was shading on the faceted, down-facing
underside).
- Luminance within 16 mm of the nostrils is smoothed in 3D (σ 2.5 mm, floor 0.8 × skin).
- The down-facing underside is lifted by up to ×1.35, so it shades as a soft shadow in line with its neighbours.
- The normal-map tilt there is reduced by 70 %.

**Legs (found on the way).** The hidden legs share one UV point that production meant as the white petticoat ("white
stockings"), but it came out dress green, with no ramp. Every tier, the red, blue and purple dresses included, showed
green shins under the hem in walk and jog. The legs are now the installed linen white (`face_paint.py`).
- With white legs, the LOD1 projection had to respect pieces: some LOD1 skirt-lining and petticoat triangles had taken
  the legs' charts.
- `apply_layout.py` now gives each LOD1 connected part its majority LOD0 piece and lets LOD1 triangles use only charts of
  their own piece.
- LOD1 against LOD0 without the hidden legs: mean 1.7 → 1.7, p99 28.3 → 26.3. With them the sampled p99 is 142: LOD1
  leg triangles nested within 2 mm of the petticoat's green lining, hidden in both LODs.

### B. Dress shape

**Cause.**
- The rest mesh already follows the HD master's A-line. Skirt width by height: 0.39 m at 0.85 m (master 0.37), 0.40 m at
  0.70 m, 0.52 m at 0.50 m, 0.68 m at 0.30 m (master 0.78 near the hem).
- The bulge came from the idle clips. In Standing (and Fidget and Hit, which start from its pose) the hands hang at
  x = ±0.21 m, right on the rest skirt surface.
- The production cloth sim (`../mm7_m342_claude/scripts/robe_sim.py`) pushes every chain point out of the forearm and
  hand capsules (0.045 + 0.012 m) along the chain's outward direction. The side chains therefore stood 8 cm out, and the
  skirt measured 0.56 m at 0.85 m: 1.5× the master, right under the belt.
- The walk had been retargeted with the arms abducted 6° (hands at ±0.24 m) and kept the rest width.

**Fix** (`dress_fix.py`, animation only, so the mesh, UVs, weights, every LOD and every shadow mesh follow).
In Standing, Fidget and Hit:
- Both upper arms are abducted 6° about the chest's forward axis, as in the walk retarget.
- Every robe chain point is pulled back to the sim's own rest-bell target (hung from its posed root, in the pelvis's
  heading) wherever it stands more than 1 cm outside it.
- The sim's leg capsules (LEG_R 1.3, same radius rule) keep the push they need.
- Segments stay rigid, and each bone takes the minimal rotation onto its corrected joint.

Walking, Walk2, Jog, Death and Dead are unchanged. The walking clips were already at the rest width.

| Skirt width at y = 0.85 / 0.70 / 0.50 m | Installed | Fix |
|---|---|---|
| Standing t = 0 | 0.559 / 0.518 / 0.528 | **0.409 / 0.461 / 0.531** |
| Fidget t = 0, Hit t = 0 | 0.528–0.544 / 0.51 / 0.53 | 0.414 / 0.47 / 0.53 |
| Walking (unchanged) | 0.370 / 0.415 / 0.496 | same |

**Gates** (`skirt_gates.py`, every other key of every clip, LOD0 posed with `claude_shared/floor/glb_pose.py`):

| Clip | Robe stretch p99 (gate ≤ 1.53, Death 1.70) | Hands inside the skirt | Legs out above the local hem |
|---|---|---|---|
| Standing | 1.34 → **1.21** | 6.0 → **0.0 cm** | 1.3 → 1.3 cm |
| Fidget | 1.38 → 1.22 | 5.4 → 0.0 cm | 1.5 → 1.5 cm |
| Hit | 1.28 → 1.21 | 5.7 → 0.0 cm | 1.2 → 1.2 cm |
| Walking, Walk2, Jog, Death, Dead | unchanged (1.58, 1.61, 1.84, 1.70, 1.37) | 0–0.2 cm | Walking 2.0, Walk2 1.5, **Jog 9.5 cm (pre-existing)** |

Robe stretch over the gate in Walking (1.58), Walk2 (1.61) and Jog (1.84) is pre-existing; production recorded Walking at
1.57. So is the Jog's 9.5 cm leg-through-cloth at the knee lift: those clips are from the gait pass and are untouched.

The lowest point of every clip is unchanged (Standing −0.8 cm, Walking −2.3 cm, Death −1.7 cm, as installed).
Texture: no UV change on the dress, so the dress texel density and stretch are those of the pass.

### Checks and review

- **Diff and data:**
  - `glb_diff.py` against the installed pass: only UVs (eyes, LOD1), vertex splits, images, and the rotations of the 56
    robe and two upper-arm bones in Standing, Fidget and Hit.
  - `check_winding.py`: 0. `flat_shading_check.py`: 0.00.
  - `texture_quality.py`: atlas 55.9 %, 206 islands (each eye one chart).
- **Tier colours:** dress and hair within 1 level in all nine skins.
- **`face_tone.py`:**
  - Interior edge ratio 0.89 in every skin.
  - The mean seam ratio reads 1.38–1.45 because the painted lid shadow and lip crease are real features that the
    face/neck box now contains.
  - No hair or dress ramp on face skin.
- **Floor and regressions:**
  - `floor_audit.py --world mm7 --match 'Peasant Human1 Female*'`: nine bindings, 0 floor problems.
  - `mm6_mm7_mm8_actor_models_build_every_binding`: pass. No case names m342.
- **Viewer:** `check` passes 216 switches with 0 errors (revision `texpass-20261101-r2`, ids `m342_<skin>_{before,tp,fix}`).
  The page gained Face, Eyes, Nose and Mouth close-up focuses. `CLOSEUPS=1 viewer_manifest.py` temporarily maps the
  capture wrapper's body-part focus names to them for shots.
- **Sheets:**
  - `review/followup_closeups_{a,b,c}.png`: close-ups of all nine skins, r1 against r2; eyes, mouth and nose, front and ¾.
  - `review/followup_dress_sheet.png`: HD master views, then r1 and r2 at Standing and mid-walk, front, left and ¾.
  - `review/followup_jog.png`: green shins in r1, white stockings in r2, red tier.
- Not done: an in-game look.

### Build, checks, install

```sh
P=level_generation/creatures/mm7_m342_texpass_claude; cd $P
python3 scripts/uv_eyes.py 3.5                                          # work/uv_eyes.npz (geometry only, no paid step)
python3 scripts/face_paint.py textures/m342_tp textures/m342_tp2         # after compose.py
python3 scripts/apply_layout.py work/before_texpass/mm7_m342.glb work/uv_eyes.npz textures/m342_tp2 work/face_r1.glb
python3 scripts/dress_fix.py work/face_r1.glb export/mm7_m342.glb 6
A="Standing:Robe_*,B_L_UpperArm,B_R_UpperArm Fidget:Robe_*,B_L_UpperArm,B_R_UpperArm Hit:Robe_*,B_L_UpperArm,B_R_UpperArm"
python3 scripts/glb_diff.py work/before_followup/mm7_m342.glb export/mm7_m342.glb $A
python3 scripts/skirt_gates.py work/before_followup/mm7_m342.glb export/mm7_m342.glb
```

Rollback to the first pass: install `work/before_followup/mm7_m342.glb`. Rollback to before any pass: install
`work/before_texpass/mm7_m342.glb`.
