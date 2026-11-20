# MM9 PeasantF1, the older human townswoman in a hood (mm9_peasantf1) — 3D actor, 2026-11-01/02

MM9 `PEASANTF1.abc` (476 triangles) with skins `PEASANTF1B` and `PEASANTF1A`. `MONSTERS.txt` rows on this model: 29 Commoner
"Peasant Human1 FemaleA A" (F1b) and 33 Shopkeeper "Peasant Human1 FemaleC A" (F1a); no other row names PeasantF1. DAT classes
`CommonerHumanFemaleA` (row 29, 11 objects: Guberland, Lindisfarne, Sturmford City, Thjorgard City, Thronheim, Thronheim City, Yorwick,
Guberland City) and `ShopkeeperHumanFemaleA` (row 33, 2: BankOrb.scr in Thronheim City, shopkeeper.scr in Thjorgard City); the rebuilt maps
carry 10 + 3 actors with the stand-ins 349 / 355 (`scripts/dat_objects.py "^(CommonerHumanFemaleA|ShopkeeperHumanFemaleA)$"`).
Second human-female townsfolk body after PeasantF8: MM9's human female skeleton (73 joints, `FHP *`, bind identical to PeasantF8's) and the
`peasantfemale` clip library, on the approved MM9 humanoid route (MM9 skeleton and clips, never Mixamo). Scripts copied from
`mm9_peasantf8_claude` and adapted; the new ones are named `*_pf1.py`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf1.glb` (`tools/install_model.py --world mm9`), identical to `export/mm9_peasantf1.glb`; variants `pf1_b`, `pf1_a` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf1_claude` (`scripts/bind_actors.py`, under the flock): `MM9 29 Commoner` (pf1_b), `MM9 33 Shopkeeper` (pf1_a); scale 100, `yaw_offset` -1.570796327, stride walk 1.0 / run 1.6 (`scripts/stride.py`: walk 1.01-1.03 m, run 0.99-1.27 m), look Neck + Head |
| Descriptors | rows 29, 33 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 349, 355 = the stand-ins the maps use), tables regenerated: ids 9029, 9033 |
| Triangles LOD0/1/2/3 | 14,474 / 7,105 / 2,556 / 885. LOD0: head + eyes + teeth 3,612, hood 1,150, blouse/bodice/sleeves 2,598, skirt 1,358, skirt lining 1,426, legs 760, arms + hands 3,570 |
| Skeleton | 108 joints: MM9's 73 + 30 finger bones (MPFB hands) + 5 half-joint helpers |
| Clips (30 fps) | Standing `stand1`, Walking `Walk`, Running `run`, Fidget `Fidget4`, Talk `Conv2`, Conv1, Conv3, Hit `Wince1`, Death `Die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal and ORM 1K, region mask 1K (R bodice, G skirt + lining, A tier-A embroidery); head + hood colour 1K per tier (2), head normal and ORM 1K shared. 8 images |
| Meshy credits | **35 / 60**: Smart Topology 5, body retexture 4K 10, head retextures 4K B 10 and A 10 (backup account, 3560 -> 3510 seen before the last job), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf1_claude/review/viewer/ revision `r23-20261102` (eye area, ear plate), tiers `pf1_b`, `pf1_a` (the pre-fix r12 build: `review/viewer_before/`; r21 in `work/rollback_r21/viewer/`; r22 GLBs in `work/vtest/r22_*.glb`) |

## Clips

Same set and reasons as PeasantF8 (README there): NPCbase.scr -> `Converse` (conv1-3) and BaseRun `LoopAnim Cower`; retainer.scr,
shopkeeper.scr, BankOrb.scr (bank orb quest) and NPC244.scr (Bikki Yrsadotir's voice and prize) play no animation. Bound: standing, walking,
run, fidget, hit, dying, dead; attack_melee/attack_ranged play Fidget (the library has no attack); script clips `talk`/`conv2` Talk, `conv1`,
`conv3`, `cower`, `stand`. Not carried: Fidget3, Yawn, Wash, Washfidget, wipe, wipefidget, Wince2, Die2, cowerstart, cowerend
(`ALL=1 scripts/pf_roles.py` writes them if wanted). Retarget: `scripts/clips_pf.py` unchanged from PF8 (soft offset line).

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256` (run with `PYTHONPATH=<gltf_venv site-packages>` for pygltflib + system yaml);
   `source/mm9_lib` copied from PF8 (the same library). Renders of MM9's model with both skins (`ref_renders.py`) -> `references_hd/mm9_*`.
1. **HD masters** (`references_hd/`, brief `CODEX_BRIEF.md`, two Codex runs): skin B (the placed Commoner), 1536x1024, `clean_alpha.py`
   halo removal. Head turnarounds for both women (`references_head/`, one run; face A with its white linen hood).
2. **Smart Topology** 15k: one fused shell for head, hood, bodice and skirt; separate bare arms, legs, eyes, teeth, lacing pieces.
3. **`seg_pf1.py`**: the fused shell split by multi-seed Dijkstra with a crease cost (head, hood, dress), the skirt below 1.04 m.
   **`assemble_pf1.py`**: mirrored at the midline as one shell, cut once along a slanted neck plane (head/body seam a clean line), split by
   label; eyes, teeth on the head; lacing on the dress; the short sleeve turned 8.2 deg onto MM9's arm direction (Meshy swung the arms
   forward); Meshy's bare arms replaced by a straightened MPFB female arm (`hand_mpfb.py REACH=2.2 UPPER=2 STRAIGHT=1`: upper-arm stub
   inside the sleeve, clamped to 4 cm radius, forearm, five-finger hand, 175 mm hand); legs cut below the knee; dress and legs reduced with
   the part borders held; skirt lining 4 mm in with a hem rim.
4. **`uv_pf.py`** (never re-run: the paid paints belong to `work/uv.npz`): body one 2K square (arms 1.4x, legs 0.5x, lining 0.3x); head set =
   head + hood (face 1.7x). The hood is painted with the face, so the fringe/hood edge is one paint (no material seam at the hairline).
5. **Paint**: body retexture 4K from the four body masters; head retextures 4K for faces B and A. `compose_pf.py`, AO
   `texpass_bake_ao.py` + `pad_ao.py`, `finish_pf.py` (gentle grade), `sym_paint.py` per head, **`head_fix_pf1.py`** (below),
   **`tiers_pf1.py`** (below).
6. **`tweak_pf1.py`** (after the paint, UVs unchanged): midline valley pull and sliver snap (PF8), Meshy's human ears clamped into the skull
   beside the hood (they poked out pink), the mouth closed (Meshy modelled a slit into a cavity with teeth pieces: the cavity comes
   forward flush, the teeth go 15 mm back), the chin's facets smoothed. Part seams (shared positions) never move.
7. `rig.sh` (weights: PF8's plus MPFB upper-arm weights to UpperArm, the elbow helper on the bare arm, and one averaged weight set at every
   part seam of the split shell) -> `build_runtime.sh [--install]` (floor lift tolerance 12 cm, see Checks).
   **One command**: `scripts/rebuild.sh <viewer rev> [--install]` (finish -> tiers -> finish -> tweak -> rig -> runtime -> viewer).

### Head paint fixes (`head_fix_pf1.py`, per tier)
Meshy painted broad crimson lips round a pale open-mouth band, a dark smudge under the lower lip, the reference's orange bodice straps and
jagged collar cream on the neck, red eyelid rims and very white sclera. Fixes: mouth-zone texels that are lip-red or dark off the sculpted
lips -> the surrounding skin; lips and the closed cavity -> one rose lip surface with a lip line at the slit height; the neck of the head
set -> skin down to the seam (the body's standing collar carries the collar, its top is the clean neck cut); reddish texels within 16 mm of
each eye 70 % toward skin; sclera 15 % darker and the eyeball's upper third shaded (lid shadow); grey specks round the pressed-in ears
filled from neighbours.

### Tiers (`tiers_pf1.py`)
Skins differ in the bodice (B rust-orange laced, A black with gold vine embroidery), the skirt (B maroon, A olive-brown), the hood (B ochre,
A white) and the face (B a woman of ~55 with grey-brown hair, A an older white-haired woman). One body paint with ramps fitted to MM9's
texels: R bodice (lacing left out), G skirt (apron left out, lining at the bottom of the ramp). **Embroidery**: MM9's skin A projected onto
our bodice (`project_mm9_skin.py`: nearest point on MM9's bind mesh, the skin x4 sampled bilinearly), its gold texels the fourth mask
channel; tier A's ramp gold (MM9's gold texels x0.72), tier B's the bodice ramp (plain cloth). Heads: one 1K colour per tier (face, hair and
hood), bound per tier by `KHR_materials_variants`. Base fixes: dark lining, collar orange spot and skin teeth -> cream, apron's ragged red
hem blobs closed into the apron.

## Face fix (orchestrator review, 2026-11-02)

Review of r12: a swollen, sausage-shaped pout (the closed-and-repainted mouth one thick crimson blob), a dark smudge under it, round
staring eyes, tier A middle-aged rather than MM9's white-haired grandmother; also the jagged edge where the collar meets the neck in 3/4
and side views, and the grey speck at the hood edge by each cheek. 0 Meshy credits.
- **Codex head repaint by landmarks** (as PeasantM1's eye repaint): `view_uvtex.py` renders the flat unlit front of each head
  (`references_face/in_face_<t>.png`, 1254 px, centre z 0.6703, 0.26 m wide); `scripts/codex_face.sh` (through `codex_slot.sh`, brief
  `references_face/CODEX_BRIEF.md`) repainted both with the HD head portrait and MM9's face as references: a warm closed-lip smile at a
  normal width and thickness, relaxed smiling eyes, clean chin, rosy cheeks, tier A clearly elderly. `align_face_pf1.py` moves the
  repainted mouth 25 px down onto the geometry's lip line and matches the skin by per-channel gains; `project_face_pf1.py` projects it
  back onto every visible head texel of the face window (|x| < 7 cm, 1.495-1.69 m), all texels of the mouth box (lips, the closed cavity,
  philtrum), normalised edge weights (half-weighted island edges had left the old paint as lines), the nose tip kept, the neck behind
  the jaw line kept; the shared head normal map flattened in the window (Meshy's relief of the old lips and eyes).
- **Geometry** (`tweak_pf1.py`, positions only, UVs unchanged): the chin and lips Laplacian-smoothed (at most 4 mm) down to the jaw;
  **the speck was a hole**: a 4-vertex boundary loop Meshy left beside each cheek (mirrored), closed by moving its vertices to its centre;
  the clamped ear plates' inward faces re-wound; `build_glb_pf.py` replaces normals that cancel on folded faces (94 positions).
- **Collar and neck** (`head_fix_pf1.py`): head faces at the shoulder/neck junction outside the bisected band carried the head material
  in jagged spikes below the neck cut; head texels within 5 mm above the cut plane or outside the neck radius now take the body collar's
  cream, so the collar line is the smooth plane; the neck between jaw and collar is one even skin of the repainted chin's tone.
- Rollback: `work/rollback_r12/` (GLB, head and body textures, uv_tex2, the three scripts as they were).
- Sheet: `review/sheet_faces_before_after.png` (MM9's face; before and after: front, 3/4, side, party view from 22 deg above; both women).

## Nose and lip fix (user note, 2026-11-02, r22)

User: "something wron with her nose + lip? like double textures?" (`review/user_notes/face_nose_lip_double.png`, tier B front close-up;
tier A had the same and worse). Causes, found by rendering the runtime GLB lit, clay (skin albedo only) and flat-textured, and by overlaying
the front z-buffer's shading on the repaint (none of it was the normal map: a flat normal map changed nothing):
- **Nose:** the geometry's nose ends ~6 mm higher than the repaint's (and Meshy's first paint's) and has a 1.6 cm underside facing forward and
  down at a hard crease. Seen from the front that underside is a band across the middle of the painted nose, shaded dark under any light from
  above; the painted tip, alae and nostrils sat below it on the upper lip. The r21 pass also kept Meshy's first paint on the nose's front
  (its ringed nostrils, a paint boundary round the alae). Tier A's repaint had drawn the nose as two ear-like flaps with no tip.
- **Bridge stripe:** a flat facet between the eyes catching the light (hard-edged in clay too), not paint.
- **Thin light line down the nose:** midline "fins", faces lying in the x = 0 plane (coincident mirrored pairs) left by the sliver snap,
  standing out of concave stretches.
- **Lip:** `tweak_pf1.py` had pushed the 6 cm-deep mouth cavity straight forward: its walls piled up folded at the rim and the flat plate
  between the lips shaded lighter, a tongue-like oval inside the lips.

Changes (0 Meshy credits, no Codex run):
- `tweak_pf1.py` (positions only, UVs unchanged): the cavity closed as one **unfolded** surface (Tutte embedding of its positions over the
  opening, the hidden sack included; harmonic depth plus a 2.5 mm dome; a 0.7 mm groove on the repaint's lip line, `MOUTH_SLIT` 1.5525 m);
  the nose tip/underside and the bridge Laplacian-smoothed (at most 2 mm); midline fins made degenerate (apex onto the longest edge, at most
  2.4 mm). Clay before/after of the mouth checked.
- New `scripts/warp_nose_pf1.py`: the repaint's nose fitted to the geometry's in the flat front frame (rows by knots, width x0.74; tier A
  takes tier B's nose, colour-matched by gains on a ring round it). `rebuild.sh` runs it; the projection reads `references_face/out_face_<t>_nose.png`.
- `project_face_pf1.py`: the nose is no longer excluded (one paint over the whole nose); the underside repainted as plain skin albedo with two
  soft nostrils at the geometry's recesses (x +-6.5 mm, 9 mm behind the tip); fin texels take the nearest ordinary texels' colour; the head
  normal map fully flat on the nose and mouth box.
- Ear plates (the ear-area sweep's "pale yellow-orange spot", rows 13-14 of `claude_shared/mm9_overview/ear_sweep_20261102.png`): the head
  texels on the clamped ear plate that carried the hood's orange outline take the plate's own neighbours, the plate toned to the cheek
  (gains held to +-10 %) and shaded x0.9. The remaining outline is the hood's own shards beside the plate (geometry, see open points).
- Rollback: `work/rollback_r21/` (GLB, head textures, normal, uv_tex/uv_tex2, the four scripts, the r21 viewer).
- Sheet (read): `review/sheet_nose_lip_before_after.png` (MM9's face, before r21 / after r22: front close-up, 3/4, side, party view 22 deg
  above, both tiers). Shots in `review/shots/nose_before/`, `nose_after/`.

## Eye area and ear plate (orchestrator review, 2026-11-02, r23)

Review of r22: a pale jagged crescent under each lower lid, a grey speck at the inner end of each brow (both tiers; PeasantM1's eye fault),
the hexagonal outlined patch at the hood edge in 3/4 and side. Causes (lit, skin-only and normal-colour renders): Meshy's lower lid ends in
a scalloped ledge just in front of the eyeball that faces up, so a light from above lit it as a pale band (the repaint's pale lid rim on
it); the brow speck was a spike at each socket's upper inner corner; the ear patch was the clamped ear plate, a flat facet at an angle to
the cheek with the hood's shards round it.
- `tweak_pf1.py` (positions only): the socket corner spikes smoothed (9 mm disk, at most 3 mm); the eyeball's positions below a smooth
  lower-lid curve (5 mm under the ball centre, curving up to the corners) 3 mm back, so the lid's own edge follows that curve; the ear
  plates' head positions Laplacian-smoothed into the cheek (at most 4 mm, held inside the clamp). Tried and dropped (each made it worse):
  smoothing the lid shelf, a biharmonic relax of the lower socket (`eye_relax.py`'s method), laying the ball onto the shell.
- `build_glb_pf.py`: the normals of the lower-lid ledge and the ear plates relaxed toward the surrounding surface's (30 neighbour-averaging
  passes, eased at the zone edge). This is what removes the pale crescent and the hard ear-plate facet.
- `project_face_pf1.py`: socket-pocket texels the projection missed take the nearest projected skin x0.78; the lid band and the up-facing
  ledge toned to at most 90-92 % of the cheek's luminance.
- Rollback of r22: `work/vtest/r22_b.glb`, `r22_a.glb` (viewer GLBs), `work/rollback_r22_tweak_pf1.py`, `work/rollback_r22_build_glb_pf.py`
  (r22's `project_face_pf1.py` is the current one without its "under each eye (r23" block).
- Sheet (read): `review/sheet_eyes_nose_r2.png` (MM9's face; r22 / r23: front close-up, 3/4, party view 22 deg above, lower-lid close-up;
  both tiers). The crescent and the brow specks are gone in the front views, irises clear from party height, no red rims. Left: a small
  pale fleck at the inner corner of one eye; up close the lid edge over the ball is a slightly stepped dark line; tier A's ear plate still
  shows as a faint pinker patch in 3/4 (B's is barely visible).

## Checks (final GLB, `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps) | 0 frames over 1 cm in every clip, both hands; hand depth at most 0.2 cm; finger stretch max 3.3 (Fidget R) |
| `sleeve_poke_pf1.py` (arm stub through the short sleeve, 24 fps; after PeasantM7's gate) | 0 mm in every clip, both sides |
| `robe_gate.py` (legs through the skirt) | 0 frames in all 11 clips (the PF8 lift at 8 cm gave Death 8/45 at 6.2 cm and Dead 25/25 at 4.4 cm; 12 cm passes) |
| `jitter_gate.py` | 0 fails (no arm corrections: MM9's arms clear this body) |
| `detached_parts_audit.py` | 2 flagged: the two legs, by design (MM9 has no thighs; legs hang free inside the skirt, as PF8) |
| `bone_length_audit.py` | 14 checked, 0 stretching |
| `flat_shading_check.py` | 0.00 body, 0.01 head |
| `check_winding.py` | 0 inverted closed parts (r22 too) |
| `floor_audit.py --world mm9` | rows 29 and 33 ok: stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0 |
| `texture_quality.py` | body atlas 66.5 %, fragments 0.0 %, stretch p90 1.05, spread 3.4 (arms 1.4x, legs 0.5x, lining 0.3x by design; p50 1,467 px/m); head atlas 58.5 %, fragments 2.2 %, stretch p90 1.2, spread 1.78 (face 1.7x over the hood) |
| Collapse (`collapse_gate.py`) | worst Hit armpit R 74 / waist 67, Death waist 60 / skirt 31, Fidget armpit R 56 (exposed 42 / 32 / 24 / 32): higher than PF8 (41 / 36); looked at in `review/shots/joints/` and `work/refs/joints1.png`, `joints2.png`: folds under the arm and at the bodice waist in MM9's wince and fall, no tear |
| Regression `--world mm9 --headless-run-regression-suite actors` (final install) | r23 (with F5 r19): binding PASS (187 descriptors on 80 models), suite 192 passed, 1 known out05 failure. r22: `mm9_actor_models_build_every_binding` PASS (187 descriptors on 80 models, 0 failed); suite 192 passed, 1 failed: `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data" (known). r21: PASS, 182 on 75 |
| Viewer `run_creature_review.py check` | 22 switches, 0 failed, 0 console errors |

## Sheets (viewer shots, read by me)

`review/sheet_mm9_vs_ours.png` (MM9 vs ours, both tiers, body front/3-4, head front/side), `review/sheet_tiers.png`, `review/strips_b.png`,
`review/strips_a.png` (every clip, six frames) against `review/strips_mm9.png` (MM9's PEASANTFEMALE mesh with the same library clips),
`review/sheet_faces.png` (face front, 3/4, side, party distance, both tiers), `review/sheet_hands.png`, `review/shots/final/chin_*.png`,
`review/shots/joints/` (Hit/Fidget/Death/Cower/Talk shoulders and arms).

## Deviations and open points

- **Mouth**: Meshy modelled the mouth slightly open with teeth; closed geometrically and repainted (Codex repaint): a warm closed-lip
  smile, not MM9's open smile with teeth (the geometry is closed). From below, the lower lip's inner part reads a little light.
- **Eyes**: lids lowered in paint, but the eyeball geometry is round: B in particular still looks a little wide-eyed in lit close-ups.
- **Age**: A is clearly older (wrinkles, crow's feet, softer skin) but the head shape is Meshy's slimmer face, not MM9's plump grandmother.
- **Embroidery** (tier A): projected from MM9's 256 px skin, so the vines are soft blotchy shapes up close; at game distance gold ornament
  on black as in MM9.
- **Ears**: Meshy's ears are pressed flat under the hood edge; in a 3/4 close-up a flat skin patch shows there.
- **Nose** (r22): one paint, fitted to the geometry; the underside still shades darker than the face under a light from above (its
  geometry faces down), with two painted nostrils. From 3/4 the near nostril reads as a small dark mark at the tip's side.
- **Ear plates** (r23: smoothed, normals relaxed): B's barely visible; A's a faint pinker patch in 3/4.
- **Under the eyes** (r23): crescent and brow specks fixed; a small pale fleck at one inner eye corner remains.
- **Collar**: the body's standing collar ends at the neck cut; a small orange lacing grommet at its V (tier B) is the bodice's top eyelet.
- **Handedness**: `mirror_glb.py` last (raw ABC `L` at -x), as every MM9 humanoid. **Legs** hang free inside the skirt (2 detached parts).
- **Map placement not switched** (orchestrator's step): the rebuilt maps still place 349 / 355; descriptors 9029 / 9033 are ready for the
  batch switch (`mm9_npc_legacy_replacements.tsv` rows 29/33 -> the MM9 ids, or the transcoder emitting the MM9 descriptor).

## What was not checked

- In game (no game run made: the maps do not place these descriptors yet); motion judged from strips, numbers and viewer shots.
- Motion at normal speed by eye (no playback capture); LOD1-3 and shadow meshes by eye; tier A joint close-ups (same mesh and clips as B).

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf1_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf1_reduce_claude/before/`.
