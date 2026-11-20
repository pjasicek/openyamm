# MM6 male peasant v3 (pman) — Claude humanoid project

New Sorpigal villager man (`PeasantM1 A/B/C`, monsters 607–609), rebuilt 2026-10-30 after the user's review: "better
head and mind the shoulders — they can't be dislocated nor slumped", no attack needed. **Installed**:
`assets_dev/worlds/mm6/models/mm6_pman_v3.glb` (source `assets_source/worlds/mm6/models/`), bound in
`assets_dev/worlds/mm6/models/actors.yml` (the previous `mm6_pman_v2.glb` is no longer referenced).

In game: [six tiers at the New Sorpigal test spot](../mm6_pfem_v4_claude/review/ingame/peasants_v5_far.png).
Close-ups: `review/g7_v8/`, shoulders `review/shoulder_v6_sheet.png` (Standing/Walking front, back, side).

[Review viewer](review/viewer/index.html) (http://127.0.0.1:8912/level_generation/creatures/mm6_pman_v3_claude/review/viewer/; tiers A/B/C, every clip; rebuilt by `scripts/viewer_tiers.py` + `scripts/update_viewer_manifest.py`, checked with `tools/run_creature_review.py check`: 18/18 switches, no console errors).

## Triangle reduction (2026-10-30)

`scripts/reduce_head.py` collapses only the crown and back hair (front protected up to 7.5 cm over the eyes, all
round up to 2 cm: front-only let the fringe fall onto the forehead and stretched the ears). His spiky hair barely
collapses: head 7,491 -> 6,818. The same face vertices are passed to `tools/build_actor_lods.py --protect-points`
(new option), so the head may reduce in the far LODs without losing the face (head ratios 0.75/0.5/0.32).
LODs 11,159 / 9,829 / 8,520 / 7,432 (was 11,835 / 10,450 / 9,067 / 7,903). Thinner hair needs a different hair mesh.

## Review 5 (2026-10-30)

User: same graft line and pale skin as the female; a more subtle fidget.
- **Faceted heads (the root of the "clay", smudges and graft lines):** Meshy's GLBs import with their own custom
  split normals, flat per face on the head; Blender keeps them over smooth shading, so the head rendered faceted and
  the normals jumped at the graft. `graft_head_parts.py` clears them on every part.
- **Head skin** carries no normal map any more (`head_skin_normal` 0): the re-baked map still held the facets.
- **Skin colour:** the body skin, the neck fade and the neck spot take the head's own neck colour just above the
  fade (the male's neck is darker than his lit face: 187/131/102 against 216/144/113); the fade covers 4 cm and is
  chosen by distance from the neck axis, not by colour (Meshy's shaded neck side kept a hard edge).
- **Fidget:** Mixamo Weight Shift (9.4 s, posture held) instead of Standing Idle 03 Examine.

## Review 3 (2026-10-30)

User: the neck "completely broken" in some animations. Cause: at the welded seam the body's thin neck stub and the
collar pulled apart when the head turned (look-at, up to 60 deg). Now the head's own neck is extruded 4.7 cm down
inside the tunic (`neck_extend` in `graft.json`, rings below 1.445 m tucked 3 mm under the tunic), the old neck stub
is cut below the collar, there is no weld (`weld: false`), the back collar is pressed lower (`collar.factor` 0.6),
and the neck weights are smoothed (`neck_weights.py`, 5 cm band). The extended faces sample one free UV spot that
`compose_peasant.py` paints with neck skin (`neck_uv`). Head skin keeps 25 % of its normal map (see the female
README). Body retexture `retexture_v6` (the collar mesh changed); the UV copy fits by the arm span (`FIT_SPAN=1`)
when the head is not uploaded. Checked with a 60 deg look-at pose rendered front, back and both sides.

## Review 2 (2026-10-30)

User: grey smudges on the head, shirt texture on the neck, shoulders "again not anatomical ... comical", clothes need
a retexture. Fixes:
- **Shoulders**: the clips, not the rig: Standard Idle / Standard Walk / Examine dropped the clavicles 15-18 deg below
  rest and pushed them 16-27 deg forward (the hunch). `posture_fix.py` holds them near rest (3 deg drop, 6 raise,
  8 forward; chest lean 3, neck 5; Fidget clavicles only), the upper arms keep their world aim. The head sits 1.5 cm
  higher (`nudge`) and the tunic's back collar is pressed down (`collar`), so he has a neck; the head is no longer
  pitched (a pitched cut is not level and cannot be welded).
- **Grey smudges**: the head normal map re-baked for smooth shading (`head_normal_bake.py`, see the female README);
  no baked AO on head skin (10 % of his face texels were under dark AO spots).
- **Neck**: welded seam (`weld_neck.py` in `step1_clean.py`), head neck band faded into flat neck skin; the old
  neck's chest V (painted brown by the retexture) is flat skin from 1.35 m up.
- **Clothes**: retexture `retexture_v4` (front master + clean-cloth prompt), the tunic calmed to one colour x mild
  detail (`calm_garment` 0.85-1.15) and the ramp spread 2.2x about its middle, so the palette tiers read as plain
  cloth instead of a mottle. New auto-rig `rig_v2`.
- Gates (`review/gates_v6.txt`): arm p99 <= 1.20 Standing/Walking, <= 1.67 elsewhere; scale 102.9 (178 units over
  the new 1.730 m).

## What changed

- **Head**: a separate head model from a Codex HD head turnaround (`references_head/`, friendlier, defined face, short
  copper hair), Meshy multi-image (30 cr), grafted with `scripts/graft_head_parts.py` (`graft.json`): scale 0.40
  (7.6 heads), pitch +5°, the old head shell cut 2 cm above the new neck and tapered onto it, the old neck's chest
  faces hidden in the closed tunic deleted (they poked out at the collar), the trousers' waist hidden in the tunic
  deleted (LOD collapse showed it through), decimation sparing everything under the brow line (the colour test took
  his tanned skin for hair and flattened the throat into a ridge).
- **Shoulders**: `joints_sym.py` after `compose_joints.py`: one shoulder distance (0.183 m) and height for both
  sides, clavicle heads 3 cm beside the midline, spine on the torso ring centres. Checked on the Standing and Walking
  upper-body renders: level, not slumped.
- **Clips** (no attack; attack and cast play Standing): Standing Mixamo Standard Idle, Walking Mixamo Standard Walk
  (stride 1.663 m), Hit Standing React Large From Front, Death Dying Backwards (travel halved), Fidget Standing Idle 03
  Examine. Hands at 60 % finger curl.
- **Textures** (`scripts/compose_peasant.py`): body from `meshy/retexture_v2` (v1 was textured before the waist cut),
  skin with the head's albedo, trousers repainted one cream with flat gloss and relief (Meshy blotched them
  grey-green), the hanging hand Meshy projected onto the tunic turned into tunic, the throat's invented-shirt texels
  on the head repainted skin; tunic region with `mm6_pman_claude`'s palette ramps (798/799/800), range refitted.
  The body AO bake now parks the head's stray UVMap coordinates (they baked head occlusion over the body).

## Gates (`review/gates_v5.txt`)

Arm stretch p99 ≤ 1.84 (Fidget), Standing/Walking ≤ 1.40; hand stretch ≤ 3.43x (right thumb); G6 hands ≤ 8 mm into
the tunic side; soles Standing −1.4…−0.7 cm, Walking −0.8…+0.8. `check_winding.py` 0 inverted. Regression
`mm6_pman_actor_models_bind_town_peasants` passes.

## Runtime

LODs 11,835 / 10,359 / 8,881 / 7,640: the head (PM3Head_A) keeps its LOD0 geometry in every LOD (ratios
0.99/0.98/0.97, `creature.json` lod_material_ratios, new `tools/build_actor_lods.py --material-ratios`). Meshy's hair
cards barely decimate, so at the default ratios the decimator collapsed the face instead and the faces went blank in
game from about 400 units. Body ratios 0.7/0.4/0.15. Scale 102.9 keeps the 178-unit standing height.

## Meshy

90 credits: head multi-image 30, auto-rig 5 + 5 (rig_v2), body retexture 10 + 10 (v2 after the waist cut) + 10
(retexture_v4, review 2) + 10 + 10 (retexture_v5/v6, review 3: the collar mesh changed twice).

## Known limits

- Heavy far LODs (7.9k at LOD3) because of the head; thinning the hair in the graft would fix it.
- LOD3 shows small texture patches on the tunic (decimation across fragmented UV seams), only at long range.
