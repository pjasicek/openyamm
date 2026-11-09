# MM9 PeasantM1 human townsman (mm9_peasantm1) — 3D actor, 2026-11-01

MM9 `PEASANTM1.abc` (the PeasantMale 45-joint skeleton) with its two skins. Every `MONSTERS.txt` row naming the model:
43 Commoner "Peasant Human1 MaleA A" (PEASANTM1A; DAT class `CommonerHumanMaleA`, about 33 placements in the rebuilt maps),
56 Prisoner "Peasant Human2 MaleD A" (PEASANTM1B; no DAT placement found), 296 RailTest (PEASANTM1A, Princess.scr, a test
row). Skins C and D belong to `PeasantM1d.abc` (sibling `mm9_peasantm1d_claude`). Built on Annud's route (`mm9_annud_claude`,
same skeleton and clip library) in one pass: MM9 skeleton and MM9 clips, grafted five-finger hands, a separate head set,
sharp textures from the start. Townsfolk batch, `devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`. Receipts and hashes:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm1.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm1.glb` from `export/mm9_pm1.glb`), variants `pm1_a`, `pm1_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_peasantm1_claude`: `MM9 43 Commoner` (pm1_a), `MM9 56 Prisoner` (pm1_b), `MM9 296 RailTest` (pm1_a); `scale: 100` (MONSTERS Scale 1), `yaw_offset: -1.570796327`, stride walk 1.1 / run 3.0 (`scripts/stride.py`: walk 0.97/1.21 per foot), look `Bip01 Neck, Bip01 Head`, impact 0.5 s (hattack1 `Rattack`, as Forad) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 43 -> 358, 56 -> 375, 296 -> 358 (the stand-ins of `mm9_npc_legacy_replacements.tsv`); tables regenerated (168 rows), descriptors 9043 / 9056 / 9296 |
| Triangles LOD0/1/2/3 | 7,354 / 3,675 / 1,321 / 437 (Smart Topology 15,010; head set 4,163 incl. hands 1,398; body 3,191) |
| Skeleton | PEASANTM1 = PeasantMale, 45 joints, names and rest rotations unchanged, joints translated onto our body (`fit_rig.py`), + 15 MPFB finger bones per side (`graft_hands.py`), driven by MM9's mitten curl (`finger_alias`); whole model mirrored to MM9's true handedness (`mirror_glb.py`, last step, as the sibling M1d) |
| Clips (30 fps, PeasantMale library `source/mm9_lib/pmale.glb`) | Standing stand1 3.0 s, Walking walk3 0.9, Running run 1.03, Fidget fidget1 3.37, Talk conv2 4.37, AttackMelee hattack1 1.03 (impact 0.5), Hit wince1, Death die1, Dead; script clips Cower (cower, loop), Conv4 conv4, Conv5 conv5 (22.2 s), Bow bow; `stand` -> Standing |
| Textures | body 2K colour + 1K normal + 1K ORM, region mask 1K (R jacket, G sleeve, B trousers) + ramps per tier; head + hands set 2K colour + 1K normal/ORM, tier B has its own head colour and normal (deviation below). specular 0, metallic 0 |
| Meshy credits | **35** (Smart Topology 5, body 4K retexture 10, head A 4K retexture 10, head B 4K retexture 10; backup account, no retries) |

## Neck fix r17 (2026-11-02, orchestrator review of r16: straight seam with a tone step, rust patch on B, flat skin "bib") - current

- **Diagnosis**: not geometry. The head and body primitives share 10 boundary positions with identical normals (0 deg),
  and both export smooth (`flat_shading_check` 0.00). The neck/shirt shell continues below head_split.py's level cut
  (z 0.62) into the body set, where the body paint had (a) collar-olive texels, inside the jacket region mask, so
  tier B drew them rust, and (b) pale chest skin (248/160/121 against the neck's ~205/137/98): the hard-edged "bib".
  r16's fix_neck.py also worked on detected collar paint only, inside a hard zone, which left a straight tone step.
- **Body side** `scripts/fix_seam.py` (replaces fix_chest.py): the body faces of the head shell's welded part (167
  triangles, all of the flange and the chest skin in the shirt opening; only the cream shirt texels keep their paint)
  take the low-frequency colour of the nearest head-set neck texel plus 60 % of their own fine detail; their R/G/B
  mask channels are zeroed and a fourth region (mask A) carries them: tier A ramp = the repainted flange, tier B ramp =
  the same scaled to tier B's neck tone (fit 0.7 / 0.6 levels mean).
- **Head side** `scripts/fix_neck.py` r17: the whole lower neck's low-frequency colour moves to the tier's skin
  (smooth ramp from 1.56 m to 1.52 m, detail kept), a faint collar shadow only; the beard is excluded only where it is
  dark, skin-hued and on the jaw underside (dark olive/rust collar paint had been taken for beard).
- Chain unchanged otherwise: `scripts/head_paint.sh` then `build_runtime_pm1.sh --install` (BLEND `work/eyes_v6.blend`).
  Rollback of r16: `work/rollback_r16/`. Meshy 0 credits, no Codex.
- Before/after (read): `review/sheet_neckfix.png` (both tiers: front, 3/4, party view 22 deg above, neck close-ups
  right and left; r16 vs r17) and `review/sheet_neckfix_viewer.png` (viewer head shots, front and 3/4).
- Checks r17: gates identical to r16 (arm/hand, jitter, detached 0, flat 0, winding 0, texture numbers); floor ok;
  viewer check 26 switches 0 failed; binding test `mm9_actor_models_build_every_binding` **PASS**, 182 descriptors on
  75 models (`review/gates/regression_binding_neckfix.txt`; a first run caught the Kira sibling mid-install).
- Left: faint light chart lines on the neck in tight close-ups (UV seams of the head set), and pale vein-like body
  paint detail on the chest skin in the shirt opening of tier A from the front.

## Face fix r16 (2026-11-01 evening, user: "looks like he has 2 eyebrows? and like weird eye area?")

Causes: (1) Meshy carved a recessed flat plate round both eyes, outlined by a step at the brows and temples; lit from
above it read as a light goggle whose lower rim looked like a second pair of brows, whatever the paint (checked with a
flat normal map and with the repainted albedo); (2) the head retexture painted that plate as a flat tan band with a hard
outline, narrow slit eyes, and on B red-rimmed dark sockets; (3) under the jaw, the body set's chest skin in the shirt
opening was much paler (median 248/160/121 against the neck's 182/122/87), so the head set's level neck cut showed as a
flat panel with hard edges, and collar-coloured seam lines remained on the neck.
Fixes, 0 Meshy credits, one Codex run:
- **Geometry** `scripts/eye_relax.py` (positions only; UVs, weights, topology unchanged, so the paid paints stay valid):
  one ellipse over both eyes (7.8 x 5 cm, nose bridge held), biharmonic fill with two fixed rings, strength 0.9, 3000
  steps (max move 16 mm, mean 5.4 mm) on `work/texpass_head.blend` -> `work/eyes_v6.blend` (replaces `eye_fill.py`'s
  `eyes_v1.blend`; a harmonic fill left a flat plane that caught the light). Clay `review/face_clay_v6.png`.
- **Eye-area repaint**: `render_face.py` (unlit front orthographic render of the head) -> Codex
  (`scripts/codex_face.sh`, brief `references_face/CODEX_BRIEF.md`): eye area only, one brow pair, open eyes from the
  approved head references. A's eyes came back 35 px high: `warp_eyes.py` moves them onto the mesh's eyes;
  `lid_lift.py` lifts the painted socket shadow under A's brows (`references_face/out_face_a_final.png`, B used as
  returned). `project_face.py` projects them onto the head set (front z-buffer, window |x| < 10.5 cm, height
  1.612-1.700 m, facing ramp), normal map flattened there.
- **Neck/chest**: `fix_neck.py` mask normalised by island coverage (no collar-coloured chart lines) and a soft collar
  shadow; `fix_chest.py` grades the chest skin in the shirt opening to the neck's lowest band.
- Chain: `scripts/head_paint.sh` (fix_neck -> fix_brow -> project_face -> fix_chest), then
  `TOKEN=<lease> BLEND=work/eyes_v6.blend scripts/build_runtime_pm1.sh --install`.
- Before/after (read): `review/sheet_facefix_blender.png` (both tiers: front at eye level, 3/4, party view 22 deg
  above, eye close-up; r7 rollback vs r16), `review/sheet_facefix_viewer.png` (viewer head shots, front, 3/4, profile),
  `review/neck_facefix.png`. Rollback of the r7 install: `work/rollback_r7/` (source GLB, export, head maps, viewer GLBs).
- Gates on r16 (`review/gates/`): identical to r7 (body and clips unchanged): hands clear except Conv5 L 1.9 cm/15 frames,
  jitter flags as listed under Checks, detached 0, flat 0, winding 0, floor ok, head atlas 33.0 % / stretch 1.25.
  Regression `actors --world mm9` (`review/gates/regression_actors_facefix.txt`): passed 191, failed 2 = `out05` (known)
  and `mm9_actor_models_build_every_binding` on `MM9 36 Commoner`, the PeasantF5 sibling's binding written before its
  tables were regenerated; re-run once its descriptor existed: **PASS**, 181 descriptors on 74 models, 0 failed
  (`review/gates/regression_binding_facefix.txt`). Viewer check 26 switches, 0 failed (r16).
- Left: from the viewer's raised head camera tier A's upper lids still read a little lighter than the brow ridge
  (lighting on the relaxed lids, no outline); a small stretched texel triangle at B's outer eye corner; one rust wedge
  on B's neck side and a thin olive line on A's neck under the hair, visible only in neck close-ups.

## Script clips (which MM9 scripts play what)
DAT `CommonerHumanMaleA` objects run NPCbase.scr / Retainer.scr (BaseRun.inc `LoopAnim Cower`), NPC214.scr (conv2, conv4,
conv5, stand), Leffery.scr (conv2, stand, `PlayAnim Bow`, `LoopAnim Aware`), and NPC131/194/88/416/414/427/49/90,
shopkeeper/npcshopkeeper (empty anim parameter), spieslikeus.scr: no animation. `Aware` and `stand` are not in the
PeasantMale library (Standing plays stand1, `stand` is bound to Standing). Princess.scr (row 296) names none.

## Route (scripts/, one project folder)
0. **MM9 sources**: `convert_abc_model.py` (system python with `claude_shared/gltf_venv` site-packages on `PYTHONPATH`),
   renders `ref_renders.py` -> `references_hd/mm9_views_{a,b}.png`, `mm9_head_views_{a,b}.png`, `mm9_skin_x4_{a,b}.png`.
1. **HD masters** (Codex via `codex_slot.sh`, `scripts/codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`):
   five tier A views in MM9's bind pose (arms 35 deg down), 1536x1024. Head turnarounds `scripts/codex_head.sh a|b`:
   `references_head/` (A) and `references_head_b/` (B, a different man painted on the same head silhouette).
2. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
3. **Fit + weights** `fit_rig.py` (`fit_config.json`; two changes for this body: the pelvis is not depth-fitted, the
   open jacket hem moved it 10.7 cm back, and `hip_half_width` 0.25 keeps the hanging hands out of the hip width;
   X-ray `review/xray_v1.png`), `reduce_uv.py` (decimation only; its Smart UVs are replaced in step 5).
4. **Hands** `graft_hands.py` (`graft_pm1.json`): no paint exists yet, so the skin/cloth classes come from the hand
   bone weights (`classes_from_weights`, new opt-in); five-finger MPFB hands, 15 finger bones per side.
   **Head split** `head_split.py` (`head_pm1.json`): part 0 (head + neck + shirt shell) cut at z 0.62 within 22 cm.
5. **UVs** `texpass_uv.py` (body 59.1 %, head/hand faces 0.35x in the upload) and `texpass_head_uv.py`. **Never re-run
   either**: the paid paints belong to `work/texpass_uv.blend` / `work/texpass_head.blend`.
6. **Paint**: body 4K retexture -> `bake_ao_texpass.py`, `compose_texpass.py` (no skin class on the body), gentle grade
   (`grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`); hands
   `bake_hands.py` + `compose_headhand.py --ref-head --hand-gain 1.18` for both head jobs; tier B's hand squares are
   copied from A (MM9 B's hands are the same pixels).
7. **Head fixes** (no new paint; superseded for the eyes by "Face fix r16" above): `eye_fill.py` (shell vertices behind Meshy's eyeball cups moved onto the cup
   surface; the cups are dropped at export with the hidden inner hair shell, `export_fix.drop_parts` [2, 5, 8]: from a
   camera at or above eye level the eyes read as closed before) -> `work/eyes_v1.blend`; `fix_neck.py` (the lowest
   neck faces inside the collar were painted collar colour, olive/rust: recoloured to the tier's skin with a collar
   shadow, gutters refilled); `fix_brow.py` (the flat tan band between eyes and brows moved 60 % toward the forehead
   tone, detail kept). Sheets `review/eyes_fill_compare.png`, `review/neck_fix.png`, `review/brow_fix.png`.
8. **Tiers** `tiers_pm1.py` -> `textures/pm1_region_mask.png`, `textures/pm1_ramps.json`: R jacket, G sleeve past 55 % of
   the upper arm (B's short sleeve cap stays jacket), B trousers. Ramps: A fitted to our paint (jacket, sleeve) or to
   MM9's trouser knit x1.3 (the paint's trousers came out near-white); B from MM9 B's own pixels by luminance quantile
   at the gain mapping MM9 A onto our paint. Tier B head image: `tier_head.py`.
9. **Runtime** `TOKEN=<lease> BLEND=work/eyes_v1.blend scripts/build_runtime_pm1.sh [--install]` (repo root): export,
   clips, `hand_rest.py` per `hand_rest_pm1.txt`, prepare, LODs, shadow fix, region variants, tier head, extras, floor
   fix, mirror, winding. Texture-only changes: `scripts/retier.sh <revision>` (project folder). Viewer:
   `viewer_tiers.py`, `make_viewer_manifest.py`. Binding: `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock
   level_generation/creatures/mm9_peasantm1_claude/scripts/bind_under_lock.sh`. Gates: `scripts/gates.sh`.

## Hands on the body (arm and hand gate)
MM9's hands rest on MM9's thin hips and chest; on this fuller body with an open, flared jacket they sank 9-17 cm into
the hem and thighs (Talk, Conv4, Conv5) and the chest (Bow). Tried: `arm_clear.py` (Annud's route) cleared them but
jittered (upper arm +2 deg/f over MM9 in Talk/Conv4, +27 in Conv5); `hand_rest.py --max-push 0.05` left hands 6 cm
inside; slower filters on Talk/Conv4 doubled the shoulder excess. Kept: the full smooth push (`hand_rest_pm1.txt`), Bow
pushed 45 deg below horizontal (a horizontal push carried the hand to the face). Strips `review/talk_raw.png` (before),
`review/talk_r3.png` (after).

## Checks (final build r7, `review/gates/`; the mirror does not change any number: `review/gates_pre_mirror/` identical)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only`, 48 fps, every clip | hands 0 frames over 1 cm in every clip except **Conv5 L 1.9 cm, 15 of 1065 frames**; forearms up to 3.5 cm (Talk 2.3, Conv4 3.3, Bow 3.5, Conv5 3.0) and **Fidget 5.7 / 6.0 cm** (MM9's look-at-the-hand gesture: the sleeve passes behind the open jacket flap, `review/fidget_raw.png`); finger stretch p99 <= 1.32, max 2.39; 19 joints per hand |
| `jitter_gate.py` vs MM9's untouched clips | hand acceleration and angular velocity equal MM9's in every clip. **6 flags**: Conv5 L upper arm +3.44 deg/f at frame 848 (limit 1.0; during MM9's own fastest swing), Bow R +2.12 deg/f, Talk R +1.17 and Conv4 R +1.19 deg/f (skin +3.1 mm/f2), all from the hand-rest push; Walking and Death flag only the shoulder-skin p95 (7.6 / 8.9 mm/f2) with identical maxima, the vertex-split artefact Annud's and Forad's passes report |
| `detached_parts_audit.py` | **0 detached**, 14 components |
| `flat_shading_check.py` | 0.00 flat on both materials |
| `texture_quality.py` LOD0 | body atlas **59.1 %**, density p10/p50/p90 1414/1461/1499, spread 1.06, fragments 0.2 %, stretch p90 1.09; head set 33.0 % of the 2K image (head square 0.8 x 0.8 plus hand squares; the dropped inner hair shell left its charts unused), spread 1.89 (hands half as dense by design), fragments 1.9 %, stretch 1.22 |
| `bone_length_audit.py` | 1 of 12: L Thigh 12.2-13.6 cm (Cower/Conv5). MM9's own library reads 2 of 12, thighs 9.7-12.9 cm (`source/mm9_lib/pmale.glb`) |
| `check_winding.py` | 0 inverted |
| `floor_audit.py --world mm9` | MM9 43 Commoner and MM9 56 Prisoner ok (stand 0, walk -0.0..+0.0, dead 0) |
| Viewer `run_creature_review.py check` | 26 switches, 0 failed, 0 console errors (r7) |
| Regression `--world mm9 actors` (final install) | **passed 192, failed 1** (the known `out05` MM8 case); `mm9_actor_models_build_every_binding` **PASS** (168 descriptors on 69 models, 0 failed). `review/gates/regression_actors_final.txt` |

## Deviations and open points
- **Tier B head image.** MM9's PEASANTM1B paints another man on the same head (blond bowl cut, clean-shaven, heavy
  jaw); a ramp cannot remove a beard, so the head material has a B copy with its own colour and normal from a second
  head retexture (10 credits). The body stays one shared set with region mask and ramps, as the rule asks.
- **Trousers** take MM9's knit colour in both tiers (region B); the B skin's knee tears are not reproduced.
- **Eyes**: the reference face squints with a half-smile; from the viewer's head camera (above eye level) the lids
  still cover much of the eye. The brow/lid band is softened, not gone (`review/brow_fix.png`).
- **Neck**: faint chart lines remain where the recoloured collar flange meets the neck, and thin body slivers at the
  collar show jacket colour (olive on A, rust on B) in tight neck close-ups (`review/neck_fix.png`).
- **Boots** are taller than MM9's (the HD master's design); the hood/collar is Meshy's reading of MM9's shawl collar.
- Handedness: mirrored to MM9's true handedness. `references_hd/mm9_views_*.png` are renders of the raw conversion
  (the mirror image), so left/right details in `review/sheet_mm9_vs_ours.png` appear swapped.
- **Binding plan (map placement is the orchestrator's)**: the rebuilt maps still spawn the legacy stand-in 358 for
  `CommonerHumanMaleA` through `transcode_mm9_dat_to_odm.py` / `mm9_npc_legacy_replacements.tsv`; switching rows 43/56/296
  to descriptors 9043/9056/9296 is the batch-wide transcoder change after the batch (not done here, per the brief).

## Sheets (viewer shots unless noted; read)
`review/sheet_mm9_vs_ours.png` (MM9 raw-conversion renders vs ours, both tiers), `review/sheet_tiers.png`,
`review/sheet_heads.png` (faces, profiles, hands), `review/sheet_faces_closeup.png`, `review/sheet_talk_feet.png` (Talk both tiers, boots in Walking), `review/sheet_clips_1.png` and
`review/sheet_clips_2.png` (every clip at 20/50/80 %, tier A), Blender close-ups `review/neck_fix.png`,
`review/brow_fix.png`, `review/eyes_fill_compare.png`, `review/fringe.png`, `review/fidget_raw.png`, `review/talk_r3.png`.

## Not checked
In game (no map spawns these descriptors yet); LOD1-3 and shadow meshes by eye; motion at normal speed in the viewer
(strips and gates only); tier B clips beyond Standing/Talk; footsteps, sounds; Android cook.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_peasantm1_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm1_reduce_claude/before/`.


**See-through linings added post-install on 2026-11-05 by `level_generation/creatures/mm9_peasantm1_lining_claude/`** (brief `devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md`; LOD0 6,236 -> 7,641, faces appended to the reduced mesh). A rebuild from this project must re-run the reduction and then the lining pass. Rollback source: `level_generation/creatures/mm9_peasantm1_lining_claude/before/`.
