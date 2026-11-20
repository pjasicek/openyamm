# MM6 Druidess (dru1), 2026-10-11

Druid / Great Druid / Grand Druid (descriptors Druidess A/B/C, monsters 517/518/519; palettes 722 green / 723 rose /
194 blue), built with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) default route (source-frame rig with
gates, `../mm6_bar1_claude/`, `../mm6_gob2_claude/`) plus the thief's cloak simulation (`../mm6_thf_claude/`).
**Installed and bound** (`assets_dev/worlds/mm6/models/mm6_dru1.glb`, `actors.yml` Druidess A/B/C; opt-in via
`debug.actor_models=true`). Placeholder quality per the playbook's quality bar; user artistic acceptance not recorded.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_dru1.glb` (7.5 MB; 3 variants share every image) |
| Triangles LOD0/1/2/3 | 9,873 / 4,935 / 1,775 / 592 (Smart Topology 15.3k; eyeballs, lash/lip strips and 32 stud beads removed, lid openings capped) |
| Skeleton | 52 `B_*` bones cloned from the humanoid set + forearm/upper-arm twist bones + 15 cloak chains x 4 bones (116 joints, under the 128-joint palette row) + palm sockets |
| Clips (30 fps keys) | Standing (Relax idle), Walking (Relax walk female), Attack (Unarmed cast R buff 2), Cast (0.25 s hold + Unarmed cast dual attack 2), Hit (Unarmed get-hit F1), Death (Relax lay down: kneels, lies face down), Dead, Fidget (Relax drink 1); see [ANIMATION_STUDY.md](ANIMATION_STUDY.md) |
| Events | `attack_melee`/`attack_ranged` impact 0.817 s (right palm), `cast` impact 0.717 s (palms clap; glow between `Socket_Palm_Left/Right`) |
| Scale / stride | 110.4 (native stand 266 px x 0.7 over the 1.686 m standing height incl. the hood); walk 1.25 m per 0.8 s cycle (~170 units/s; speeds 160-200 stay under the run threshold, `run` plays the walk) |
| Textures | body 1K + head 1K (Meshy retextures; face, neck/choker, hair and hood in the head set); one cloth region (cloak + hood) with ramps from palettes 722/723/194; AO in the body base colour (not on the moving cloak); ORM R = specular mask, G = roughness per class |
| Meshy credits | **40 of 100**: Smart Topology 5, auto-rig 5 (joint estimate + weights), body retexture 10, head retexture 10 (10 still reserved-free) |
| Checks | G6 body contacts 0 in every clip; G5 hand stretch <= 2.7x; G4 arm p99 <= 1.7 except the attack apex 2.0 and the prone death's left shoulder 2.3; cloak gate (poke-through / tears) below; viewer 3 tiers x 8 clips clean (`check_viewer.mjs`); regression `mm6_druidess_actor_model_tiers_share_one_size` (suite 30/30); outdoor and indoor 3D-vs-sprite captures in `review/ingame/` |

Viewer: `http://127.0.0.1:8901/level_generation/creatures/mm6_dru1_claude/review/viewer/index.html`
(`python3 -m http.server 8901` from the repository root).

## Replay

1. `references_hd/` (Codex briefs `CODEX_BRIEF_v1_primary.md`, `CODEX_BRIEF_v2_primary_fix.md`, `CODEX_BRIEF.md`;
   v3 primary selected by Claude's gate: hands clear of the cloak; alpha haze removed), `references_head/`.
2. Meshy: `requests/smart_topology_v1.json` -> `examine_parts.py` (`work/st_v1_parts.blend`) -> `step1_clean.py`
   -> `export_clean.py` -> `requests/rig_v1.json` -> `meshy_joints.py`, `source_rest.py` (one-off inputs).
3. `scripts/rebuild.sh` (cleanup -> joints -> rig -> fingers -> retarget [Relax; Unarmed with `PLANT_FROM=Standing`]
   -> twist -> weights -> finger weights -> cloak rig -> reduce -> open fingers -> death/attack arm offsets ->
   narrow stance -> clip timing -> cloak sim -> G4/G6/G5 -> sync clips into the textured master -> cloak gate).
4. Textures (one-off, after the rig): `export_uploads.py` -> `requests/retexture_v1.json` -> `transfer_uv.py`
   (`work/rig_v6.blend`) -> `requests/head_retexture_v1.json` -> `uv_raster.py` HeadUV -> `eye_disc.py` ->
   `eye_caps.py`; `bake_ao.py`.
5. `scripts/build_runtime.sh [--install]` (rasters -> `compose_dru1.py` -> `export_runtime.py` -> prepare -> LODs ->
   shadow fix -> region variants -> head merge -> install), then `viewer_tiers.py`, `update_viewer_manifest.py`.

## What the gates caught (each fixed in the layer where it started)

- **HD masters**: the first primary hung the hands over the cloak (Smart Topology fuses such hands into the cloth);
  one targeted regeneration spread the arms to ~40 deg with the hands clear of the cloak's silhouette.
- **Mesh**: the cloak came back fused to the torso shell; a flood fill from the hem limited to z < 1.40 labels it
  (the join is only at the shoulder tops, 1.40-1.42).
- **Joints (G3)**: the bracers ARE the forearms (no skin under them) and the hands are separate shells: wrist = the
  centre of the hand shell's open wrist ring; elbow from two line fits; ankle height from Meshy (the narrowest boot
  ring sat 4 cm up the shaft).
- **Clips (G1)**: the Unarmed casts and hit stand in a boxing crouch. `retarget.py PLANT_FROM` keeps the Standing
  pelvis and legs and turns the upper body by a constant yaw (source chest at frame 0 onto our Standing chest) minus
  the source pelvis's later yaw (copying the source pelvis turn left the chest 45-60 deg sideways and whipped the
  cloak). `clip_timing_dru.py` blends Standing into and out of the source so the boxing guard never shows.
- **Fingers (G5)**: the source clips curl the fingers into fists and a cup grip: 6.8x knuckle stretch. She casts with
  open palms: every finger key keeps 25 % of the source (`fingers_relax.py`): <= 2.7x.
- **Weights (G4)**: Meshy gave the forearms/bracers up to 27 % thigh weight (the A-pose hands hang beside the hips:
  12-43x when kneeling or casting) and the shoulder tops 36-49 % head weight (the hood rests there): limbs stripped
  of the other limb's weight, head weight faded out lateral of the neck. The lats under the armpit carry 88-96 %
  upper-arm weight; stripping it made a hard seam (6-10x), diffusing the weights over the armpit skin (8 passes)
  brought the clips to p99 1.2-1.7. The attack's raised arm stood vertical (4x armpit); the native frames hold it
  diagonally: tilted 25 deg out (`arm_offset.py`, negative angle for a raised arm).
- **Contacts (G6)**: at the kneel the right hand sank 5 cm into the raised left knee (shorter thigh than the
  source): 30 deg outward arm offset over the kneel.
- **Cloak**: chain points were too sparse at the back (the trailing boot bulged between 13-deg chains): denser chains
  across the back (10 deg) within the joint budget, wider leg and heel capsules; the hit's forward bend lifted the cloak
  in the chest frame (lying logic now death-only); prone death drapes the cloak over her back (chest-frame target
  lowered toward the floor, radial collisions) instead of spreading it on the floor under her.
- **Textures**: the removed eyeball shells left holes in the face (dark eyes in the lit close-up): eye caps with a
  painted eye disc in a free corner of the head atlas; Meshy painted the hanging hair onto the neck skin (repainted
  with the chest skin colour x its own fine shading) and the hair near-black olive (repainted native dark brown x its
  strand detail); rest-pose AO put black patches on the moving cloak through the ramp (no AO on cloth, lowest stop
  off the sprite's outline pixels).
- **In game** (`review/ingame/`): skin graded x1.1 read pale grey next to the sprites (now x0.9 and saturation 1.4),
  the rose cloak too light (ramp gain 1.0), the model 5 % tall indoors (scale from the standing, not the walk height),
  the cloak flared like a bell and the feet stood apart (native: feet together, cloak close round the legs): the
  hanging target narrows toward the hem (`CLOAK_NARROW` 0.5) and `narrow_stance.py` turns the thighs in 4.5 deg in
  Standing and the planted clips.

## Review 1 (user, 2026-10-11) and fixes

1. **Eyes not eyes; triangle patches on the skin.** Eyes: the caps carried a painted disc and folded over themselves
   on her concave left lid. Now each lid opening is filled flat (`eye_caps2.py`, smooth shading) and mapped onto the
   same eye of the HD head reference (`eye_uv.py`: iris, pupil, lashes), the lid/brow texels round the eyes are
   re-projected from that reference (`compose_dru1.py`; Meshy painted those small UV islands inconsistently) and the
   lid geometry is relaxed (`eye_smooth_lids.py`). Patches: Meshy's projection left whole faces in other tones
   (cloak/hair/leg occlusion). All body skin is repainted with one saturated skin colour x its own fine shading
   (+-5 %); torso leather is decided by 3D neighbourhood (dark blotches on skin were classed as leather); the skin
   gets a weak AO (the rest-pose bake counted the hanging hair and cloak); the neck is skin by position; the front
   panel stands 8 mm off the legs (`panel_offset.py`: the leg shell poked through at the hips).
2. **Hips sway far too much in the walk.** The Relax female walk rolls the pelvis +-34.5 deg with 12.6 cm lateral
   sway (`motion_probe.py`). `walk_damp.py` keeps 30 % of the pelvis oscillation and 50 % of the sway with the spine
   and thighs holding their world rotations: roll -7.5..+13.2 deg, sway 6.3 cm.
3-7. **Cloak flapping erratically in every action.** Measured: even Standing rang (jerk p95 5.3 cm/frame^2, 23
   velocity reversals per point); hit 58, death 89 peak. Damping 0.985 -> 0.94 and pull 0.05 -> 0.09 per substep,
   trajectories smoothed over time (Gaussian 1.5 frames, 3 in the death), and the simulation now keeps every chain
   bone straight and rigid: the bones had aimed at folded half-segments and overshot (the hem punched 15 cm through
   the floor while she dropped and snapped back). Jerk p95 now 0.02 (standing) to 5.4 (hit) cm/frame^2.
6. **Death: thighs through the cloak.** The lay-down ends with the legs bent sideways while the cloak lies straight
   down her back; `death_legs.py` straightens the legs level behind her (feet pointed) over frames 24-46, as the
   native prone corpse; torso and hands stay on the floor (the legs keep the source's 6 cm sink, under the cloak).

Checks after the fixes: G6 contacts 0 in every clip, G5 hands <= 2.7x, G4 unchanged, cloak gate (walk 53
vertex-frames through the cloth, death worst opening 7.4 cm), viewer 3 tiers x 8 clips clean, regression suite 32/32,
in-game capture `review/ingame/out_3d_r1.png`. Viewer checks: `review/vshots_r1/`, `review/r1b_actions.png`.

## Review 2 (user, 2026-10-11) and fixes

1. **Walk still sways left-right.** The trunk, not only the pelvis: the spine bent against the damped pelvis (chest
   5.6 cm, head 4.7 cm side to side). `walk_damp.py` now keeps 12 % of every trunk bone's oscillation (pelvis and
   three spine bones) and 25 % of the pelvis's lateral offset, with neck, clavicles and thighs holding their world
   rotations: pelvis roll -0.5..+7.8 deg, sway 3.1 cm, chest 0.7 cm, head 1.3 cm.
2. **Triangle patches and lips.** Found layer by layer with lit renders (`map_diag.py`, `neck_diag.py`), a piece-ID
   render and ray casts: (a) the skin repaint kept a +-5 % detail and the AO bake, both computed per UV island, so
   neighbouring faces differed slightly: skin is now one flat colour x AO smoothed in 3D (a function of position
   only); (b) the AO grid had no data for the head-set neck: no skin AO on the neck in either set; (c) creases in
   Meshy's neck geometry (`neck_smooth.py`) and 35 unwelded skin vertices (`weld_skin.py`); (d) the hair shell's
   inner faces cut through the neck (`hair_clear.py`, 8 mm); (e) sub-texel faces sampled neighbouring islands
   (`uv_raster.py` now covers each face's corners, edge midpoints and centroid). The choker is a continuous gold ring
   painted by 3D position (z 1.400-1.416) in both sets. Lips: the mouth is re-projected from the HD head reference
   with its own alignment (painted-lip box on the model onto the reference lips), colour matched on skin-hued pixels.
   Steps (c)-(e) and the eye fixes edit the textured master `work/rig_v6.blend` in place (backups `*_pre_*.blend`);
   regenerating that master from `export_uploads.py` + `transfer_uv.py` must replay `eye_caps2.py`, `eye_uv.py`,
   `eye_smooth_lids.py`, `panel_offset.py`, `weld_skin.py`, `neck_smooth.py`, `hair_clear.py` (HAIR_CLEAR=0.008), then
   both `uv_raster.py` layers.

Checks: G6 0 in every clip, G5 <= 2.7x, cloak gate (walk 24 vertex-frames through the cloth), viewer 3 tiers x 8
clips clean, regression 32/32. Viewer captures `review/vshots_r2/`.

## Review 3 (user, 2026-10-11) and fixes

1. **Belt sways in the walk.** The belt and medallion copied skin weights with 22 % thigh weight; they are rigid now
   (pelvis 0.7, spine 0.3; `belt_rigid.py` on the masters, the same rule in `weights_fix.py`).
2. **Head texture: patches fighting the old paint (user: regenerate if needed).** Replaced instead of patched, by the
   playbook's problem-head route: a head-only Meshy multi-image model from the HD head turnaround
   (`requests/head_model_v1.json`, 30 credits; 31k triangles, clean face whose paint matches its own lips/eyes),
   aligned by ICP on the face (`face_align.py`, median 1.4 mm), our face vertices moved onto its surface (<= 8 mm,
   `face_bake.py`), a new head UV layout with the face at 2.2x texel density, colour by nearest model surface point
   (`face_nearest.py`; the ray-cast bake left shards where the geometries differ) applied as detail over the shared
   skin colour inside a feathered face ellipse, normals from the bake, hair/hood re-baked from the previous head set,
   temples and hairline in hair colour, mouth-corner folds relaxed (`mouth_smooth.py`). The review-1/2 eye and mouth
   patch steps are skipped when the graft exists (`compose_dru1.py BAKED`). Meshy credits: 70 of 100.

## Review 4 (user, 2026-10-11): close-up face artifacts, each traced to its cause

- **Cracks across the cheeks and temples:** the face normals baked in Blender's tangent space did not match the
  tangents the viewer/engine derive, so every UV island border lit as a seam (confirmed by an A/B with a flat face
  normal map). The face shape is in the geometry since the graft, so the face normals are flat now.
- **Shards at the mouth corners / between the lips:** Meshy's lips are slightly parted over a mouth bag whose back faces
  the viewer culls. `mouth_close.py` removes the bag (faces hidden from the front: a ray toward the camera meets the
  face within 6 cm; 107 faces), closes the lip line with a cap (coloured from the head model's lip line by
  `face_nearest.py`) and removes a dangling sliver.
- **Speck under the nose:** two folded back-facing philtrum triangles, relaxed in the same script.
- **Pale chips at the face edge:** a band of flat skin between the shaded face paint and the hair; the face colour now
  reaches the face edge below the eyes, and the temples take the hair colour.
Checks: viewer 3 tiers x 8 clips clean; regression druidess case passes (the suite's one failure is another
session's in-progress ogre case); captures `review/vshots_r4/`.

## Review 5 (user, 2026-10-11): black area above the forehead

Not paint (texture 75-83 brown there) and not a hole: ray casts into the posed Standing head showed it was the hair
shell's curled inner side (56 of 129 front-top hair faces face downward; the material is double-sided, lights come from
above). Fixes on the textured master: `hair_normals.py` gives every hair corner the outward normal of the nearest scalp
point (hair-card normal transfer: the shell shades as one outward surface), `hair_edge.py` pins the open front edge
of the hair onto the scalp (a 7.5 mm gap showed the hood lining), the hood lining gets a luminance floor (Meshy painted
it in deep shadow, the ramp made it near black) and hair is matte (specular 0.08, roughness 0.85; the new normals
caught a highlight). Tried and dropped: hair strands copied onto the scalp by 3D nearest texel (streaky smears), and
flattening the hair lip onto the scalp (`hair_lip.py`; the shell already lies within 2 mm there).

## Review 6 (user, 2026-10-11): hood darker than the cloak, black dots on the cloak (in-game, from behind)

- The hood lives in the head set and was painted ~30 % darker than the cloak (median luminance 0.047 vs 0.066), so the
  shared ramp put it on its darkest stops. Its luminance is now quantile-matched to the cloak's.
- Black dots: the ramp is rank-matched, so the darkest few percent of Meshy's velvet mottle took the sprite's darkest,
  near-black greens. The lowest stops now start at the 18th percentile of the native shades, the ramp's contrast is
  0.7 round its middle stop, and only the finest speckle (below a 1.5 px blur) is damped to 60 %. Tried and dropped:
  a 4 px UV-space damping (exposed island-level tone steps as blocky patches) and a 3D-smoothed cloth field (cloak
  lining and outside averaged into dark clouds). In-game capture `review/ingame/cmp_r6.png` (3D above the sprites).

## Known faults (placeholder quality)

- Shoulders read slightly broader than the sprite's in the front view; the cloak still a little wider at the hem.
- The trailing heel can show through the back hem in two walk frames; while she drops in the death the cloak hem
  still slides a little on the floor (rigid 4-bone chains cannot crumple).
- G4: the prone corpse's left shoulder (arms reaching past the head) p99 2.3 (under the cloak).
- Face: the eyes are a flat textured cap in the lid opening (no eyeball depth); a thin wrinkle line under her left eye
  (painted in the head model); a soft rather than crisp hairline under the hood;
  thin dark slivers along the zigzag front edge of the hair shell at close range.
- The source attack's raise is a one-frame flick to overhead (as authored).
