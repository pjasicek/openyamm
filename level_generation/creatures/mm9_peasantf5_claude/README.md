# MM9 PeasantF5, the human townswoman in a coif (mm9_peasantf5) — 3D actor, 2026-11-01/02

MM9 `PEASANTF5.abc` (73 joints, the human female skeleton of `PEASANTFEMALE`, bind identical to PeasantF8's within 5 mm) with skins
`PEASANTF5B` and `PEASANTF5A`. `MONSTERS.txt` rows on this model: 36 Commoner "Peasant Human2 FemaleA A" (F5b), 34 Shopkeeper
"Peasant Human1 FemaleC B" (F5a), 41 Shopkeeper "Peasant Human2 FemaleC B" (F5a); all three run NPCbase.scr. DAT classes (transcoder rule
role + body + palette): row 36 = `CommonerHuman2FemaleA`, **6 placements** (`scripts/dat_objects.py "Human2Female"`); rows 34 and 41 =
`ShopkeeperHuman1FemaleB` / `ShopkeeperHuman2FemaleB`, **no placement** in the rebuilt maps. (The 8 `ShopkeeperHuman2FemaleA` objects are
row 40, PeasantF3, not this body; the brief's "about 13" counted them.) Built on the approved MM9 humanoid route: MM9 skeleton and the MM9
`peasantfemale` clip library, never Mixamo; the retarget, clip method, skirt rig and floor fix are PeasantF8's (`mm9_peasantf8_claude`).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf5.glb` (`tools/install_model.py --world mm9`), identical to `export/mm9_peasantf5.glb`; variants `pf5_b`, `pf5_a` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantf5_claude`: `MM9 36 Commoner` (pf5_b), `MM9 34 Shopkeeper` (pf5_a), `MM9 41 Shopkeeper` (pf5_a); scale 100, `yaw_offset` -1.570796327, stride walk 1.0 / run 1.6 (same skeleton and clips as F8), look Neck + Head |
| Descriptors | rows 34, 36, 41 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 356, 376, 383: the matching MM6-MM8 human women; row 41 had no legacy replacement row, 383 "Peasant Human2 FemaleC B" is its name match), tables regenerated: ids 9034, 9036, 9041 (`scripts/bind_under_lock.sh` under the flock) |
| Triangles LOD0/1/2/3 | 12,992 / 6,386 / 2,297 / 763. LOD0: head (with eyeballs) 4,372, bodice + blouse + puffed sleeves 1,998, hands 1,464, skirt lining 980, skirt + apron 942, bare arms 898, bracelets 768, legs + shoes 640, coif 568, bodice ornaments 256, buckle 106 |
| Skeleton | 108 joints: MM9's 73 + 30 finger bones (MPFB hands) + 5 half-joint helpers |
| Clips (30 fps, `source/mm9_lib/pfemale.glb`) | Standing `stand1`, Walking `Walk`, Running `run`, Fidget `Fidget4`, Talk `Conv2`, Conv1, Conv3, Hit `Wince1`, Death `Die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal and ORM 1K, region mask 1K (R pinafore, G skirt + lining); head colour 1K per tier (2), head normal (flattened in the hair) and ORM 1K shared |
| Meshy credits | **35 / 60**: Smart Topology 5, body retexture 4K 10, head retextures 4K B 10 and A 10 (backup account, balance 3555 before the first job, 3480 before the last), no retries |
| Codex | 3 runs through `codex_slot.sh`: three-quarter master, four views, eight head views (`references_hd/`, `references_head/`) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf5_claude/review/viewer/ revision `r19-20261102` (softer nostrils), tiers `pf5_b`, `pf5_a` (r17 in `work/rollback_r17/viewer/`, r18 in `work/rollback_r18/`) |

## Clips

Exactly PeasantF8's set (same library, same scripts): NPCbase.scr -> NPCBase.inc `Converse -1` (conv1-3) and BaseRun.inc `LoopAnim Cower`.
The F5 objects' own scripts (NPC92, NPC181, NPC182, Shopkeeper.scr, retainer.scr) have empty ScriptParams and play no animation. Bound: standing,
walking, run, fidget, hit, dying, dead; attacks play Fidget (no attack clip in the library: peasants flee); script clips talk/conv2 (Talk),
conv1, conv3, cower, stand. `scripts/pf_roles.py` / `roles_pf.json` copied from F8 (`ALL=1` writes all 20 library clips).

## Route (`scripts/`, copied from `mm9_peasantf8_claude/scripts`, F5 parts new)

0. **Sources**: `convert_abc_model.py --scale 0.0256` (`source/mm9/pf5a|pf5b`), F8's `source/mm9_lib/pfemale` and `work/hand.npz` (MPFB, CC0)
   copied. `mm9_dump.py`, `mm9_regions.py`. MM9 reference renders `ref_renders.py` -> `work/refs/`, sheets in `references_hd/mm9_*`.
1. **HD masters** (`references_hd/`, brief `CODEX_BRIEF.md`, run 1 the three-quarter, run 2 the four views; skin B, the placed row),
   halos removed by `clean_alpha.py`. **Head turnarounds** (`references_head/`, both faces in one run). Codex drew both profiles facing image
   right (her right side) instead of left: mirrored to `*_02_profile_left.png` (symmetric face and coif) instead of another run.
2. **Smart Topology** 15k from `00_three_quarter_clean.png`: 21 shells (head, coif, bodice with blouse, puffed sleeves and a standing collar,
   two bare-arm shells from inside the sleeves to a bracelet ring at the wrist, two hands, skirt with the apron modelled in, legs, shoes,
   eyeballs, mouth inserts, four brooches and the buckle). `step1_clean.py ... 1.806` (MM9's height, soles to coif peak).
3. **`assemble_pf5.py`**: every shell mirrored from its +x half (Meshy's -x eye was malformed; X0 0.009 puts the midline at 0). The +x
   eyeball kept in the head shell and mirrored (without it the sockets read as sunken slits). Arms: axis from ring centres, the sleeve and
   bare arm pulled to MM9's arm length (scale 0.881) and turned 10.0 deg onto MM9's arm direction; Meshy's hand and the arm's closing cap
   dropped; MPFB hands (170 mm) with a 3.5 cm stub clamped inside the forearm; a **procedural bracelet** fitted per angle round the wrist
   (MM9's skin paints a copper bracelet there) covers the arm/hand joint. Legs: the +x leg and shoe on MM9's foot, cut below the knee.
   Symmetric collapse outside the head; skirt lining 4 mm in with a hem rim. Mouth inserts dropped.
4. **`uv_pf.py`** (never re-run: the paid paints belong to `work/uv_orig.npz`): body square (hands 1.5x, legs 0.5x, lining 0.3x), head square
   (face 1.6x). **`fix_needles.py`**: 14 zero-area lining slivers on the midline had UVs reaching to the atlas corner, crossing other charts;
   Meshy painted their colour along thin lines over the hands and skirt. The faces are dropped (`work/uv.npz`) and their footprint refilled
   from the nearest good texel at 4K (`compose_pf.py`, `pad_ao.py`). Check new layouts for this before uploading.
5. **Paint**: body retexture 4K (four body masters), head retextures 4K B and A. `compose_pf.py`, AO (`texpass_bake_ao.py`, gutters padded),
   gentle grade (`finish_pf.py`), `sym_paint.py` on the heads.
6. **`tiers_pf5.py`** (body tone, mask, ramps): pinafore by hue on the B paint (R), skirt without the apron (G, apron picked by hue: its
   fold shadows are saturated ochre), lining darkened; the coif's orange streaks (skin/hair tones Meshy painted on its inner flaps) to coif
   cream; the shins under the skirt (bare orange skin) to a dark wool stocking; Meshy's own braided bracelet band painted on the last 1.6 cm of
   each forearm (a dark sliver above our bracelet) to the forearm skin. Ramps from MM9's texels picked on skin B by hue and read in both
   skins at the same texels (tier A pinafore limited to A's red cloth: A's embroidered blouse front lies where B has pinafore).
7. **`headmap.py` + `head_fix.py`** (per tier, by 3D position): eyes repainted procedurally on the eyeball cups (sclera, iris in the tier
   colour, pupil, catchlight, a shadowed upper lid and lash over the top of the iris, lower lid), Meshy's red rims toward the skin; the
   bright red mouth cavity to a lip-shadow tone (a dark gap read as an open mouth), lips toned toward the skin; the nose underside lifted; the
   whole crown under the coif, the fringe and the temple strips take the tier's hair colour with the paint's strand detail (no pale band
   at the fringe, no coif-cream cap); the head normal map flattened there (`pf_head_normal_fix.png`).
8. **`tweak_pf.py`** (after the paint, UVs unchanged): midline slivers snapped, hand stub rims on one ring, eyeballs 1.5 mm deeper, and
   (face fix) the mouth, eye creases and nostrils reshaped: see "Face fix".
8b. **Face fix** (orchestrator review 2026-11-02, see below): `view_uvtex.py` flat front renders -> `codex_face.sh` (brief
   `references_face/CODEX_BRIEF.md`) -> `align_face_pf5.py` -> `project_face_pf5.py` -> `textures/pf_head_<t>_face.png`,
   `pf_head_normal_face.png` (finish / tier images prefer them).
9. **`rig.sh`** -> `fit_rig_pf.py` (coif back on Ponytail11/12, head pivot at the skull base) -> **`weights_pf5.py`** -> `build_glb_pf.py` ->
   `clips_pf.py` -> `finger_rest.py` -> `arm_out.py` -> `half_keys.py`. **`build_runtime.sh [--install]`**: prepare, LODs, shadow fix,
   `region_variants.py`, `tier_images.py` (head colour per tier), winding, floor (skirt lift tolerance 0.14), `mirror_glb.py`, winding.
   **`rebuild.sh <rev> [--install]`** replays finish -> tiers -> finish -> tweak -> rig -> runtime -> viewer from the paid paints in ~2 min.
   Gates: `gates.sh`, `skin_poke_gate.py`.

## Face fix (2026-11-02, orchestrator review: "pouting mouth, angry brows, glaring round eyes, dark nostril triangle")

The r13 faces read cross and surprised next to MM9's warmly smiling women. 0 Meshy credits; one Codex run. Rollback of r13 in `work/rollback_r13/`.
- **Mouth geometry** (`tweak_pf.py`, positions only, UVs and weights unchanged): the lips' front surface is compared with a heavily smoothed copy
  (nose and chin outside the box hold it) and every vertex of the mouth column (lips and the cavity behind them) moves back by the lips'
  excess, feathered, at most 6 mm (3.3 mm used): the lips are flush with the face, the slit is a closed line. A first try that pulled the cavity
  forward folded the inner lips into a jagged ring, and a box reaching the nose base flattened the philtrum (both reverted).
- **Eye creases and nostrils** (same script): Meshy's deep lid crease under each brow and the open nostril holes stayed dark under a light from
  above even with clean paint; both Laplacian-smoothed in place (crease at most 3.5 mm, nostrils 2 mm; a first nostril box rounded off the nose
  tip and was narrowed).
- **Codex repaint by landmarks** (PeasantM1/F1 route, `scripts/codex_face.sh`): flat unlit front renders of each head (`view_uvtex.py`,
  `references_face/in_face_<t>.png`) with the HD portraits and MM9's own faces (`mm9_face_<t>.png`) as references; Codex returned a warm
  closed-lip smile, relaxed eyes (the iris under the upper lid), soft level brows, no nostril triangle, B clearly elderly with grey-white hair
  swept back (the grey cap band became hair), A's auburn hair without the light lines. `align_face_pf5.py` moved the mouth onto the input's lip
  line (14 / 20 px) and matched the skin colour; `project_face_pf5.py` projected it onto every front-visible head texel in the window from the
  chin to the top of the coif opening; texels the projection only partly reached (the upper eyeball under the lid, the nose underside, the inner
  lips) take the colour of the nearest well-projected texels in 3D; the nose underside (+30 %) and the lid crease (+15 %) are lifted against the
  key light; all gutters padded; the head normal map flattened in the window.
- Sheets: before `review/sheet_faces_before.png`, after `review/sheet_faces_after.png` (MM9 front / three-quarter / side next to ours front /
  three-quarter / side / party view 22 deg above, both women), flat paint `review/flat_b.png`, eye `review/eye_cmp.png`, mouth geometry
  `review/sheet_mouth2.png` (clay before / after).

## Nose and lip fix (user note, 2026-11-02, r18)

User: "peasantf5 - something wrong on her nose?" (`review/user_notes/nose_fault.png`, tier B front close-up). Same faults as PeasantF1
(see `mm9_peasantf1_claude/README.md`, "Nose and lip fix"), checked against MM9's faces:
- **Nose**: the nose's 9 mm underside faces forward and down at a hard crease; the face-fix projection had filled it with the nearest
  texels (a blotchy brown) and then lifted it +30 % with a mask that did not match it, which drew a pale ring round the nostrils: the dark
  triangular patch with a light ring. The repaint's nose itself fits this geometry (width and height checked against the front z-buffer).
- **Mouth**: the lips were moved back but the slit still opened into Meshy's cavity; its inner lips faced up and down between the lips: a
  lighter band inside the lips and a puckered "O" from below (the same second-lip-layer fault as F1).
- **Chin**: a horizontal facet at the bottom of the chin shows in front close-ups (before and after; geometry, not touched).
- **Neck band**: MM9's PEASANTF5 has a dark patterned standing collar round the neck (`references_hd/mm9_head_views_b.png`); ours is that
  collar, and the skin/collar edge is its top edge. Not a fault.
Changes (0 Meshy credits, no Codex run): `tweak_pf.py` (positions only): the cavity closed as one unfolded surface (Tutte embedding, dome,
groove on the repaint's lip line `MOUTH_SLIT` 1.5334 m), the nose tip and underside smoothed (at most 2 mm), midline fins made degenerate;
`project_face_pf5.py`: no underside lift, the underside repainted as plain skin (a touch lighter than the nose front, the columella lighter
again) with two soft nostrils only on down-facing texels (a first version put a dark dot on the ala's side, seen from 3/4), fin texels from
their neighbours, the head normal map fully flat on the nose and mouth. Run order: `tweak_pf.py ... work/uv_tex2.npz`, `project_face_pf5.py`
per tier (b with `--normal textures/pf_head_normal_fix.png textures/pf_head_normal_face.png`), then `rebuild.sh <rev>`.
Rollback: `work/rollback_r17/` (GLB, head textures, normal, uv_tex2, the two scripts, the r17 viewer).
Sheet (read): `review/sheet_nose_lip_before_after.png` (MM9's face, before r17 / after r18: front close-up, 3/4, 60 deg side (the coif hides a
full profile, as in MM9), party view 22 deg above, both tiers). Shots in `review/shots/nose_before/`, `nose_after/`.
Open: the nose underside still shades darker than the face under a light from above (its geometry faces down); the chin facet.

## Nostrils r19 (orchestrator review, 2026-11-02)

Review of r18: the nostrils still read as a dark brown blotch on the tip from the front (tier B most). `project_face_pf5.py`: nostrils smaller
(ellipses 1.9 x 2.8 mm), a cool shadow (the surrounding skin x0.48, a quarter desaturated) instead of brown, only on down-facing texels; the
columella a little lighter. `tweak_pf.py`: the tip/underside smoothing raised to 10 passes, at most 3.5 mm (`NOSE_TIP_CAP`), which shrinks the
underside facet that shaded dark. Rollback `work/rollback_r18/` (GLB, head textures, normal, viewer) and `work/rollback_r18_*.py`.
Sheet (read): `review/sheet_eyes_nose_r2.png` (MM9's face; r18 / r19: front close-up, 3/4, party view, nose close-up; both tiers): the tip
stays skin coloured from the front and from party height; a soft shadow remains under the tip where the geometry faces down.

## Rig and weights

As F8 (MM9's joints, arms on the turned axis with MM9's lengths, MPFB fingers, head pivot moved to the skull base 1.535 m, analytic skirt
weights over MM9's eight chains with exactly four influences, bodice by spine heights). F5 specifics: the bare arm shells are pure
UpperArm/Forearm by position along the arm (elbow band +-6 cm); the bracelets rigid on the forearm; the **hand stub behind the wrist rigid on
the forearm**, blending to the MPFB weights across +-4 mm at the wrist under the bracelet (with MPFB's wrist weights it poked up to 5.3 mm
through the forearm skin when the wrist bent); the coif rigid on the head with its hanging back on Ponytail11 -> 12; the standing collar is
the bodice shell's top on Neck; brooches take the nearest bodice weights, the buckle one blend. Weights mirror-symmetric.

## Tiers

MM9's skins differ in the pinafore and skirt (B slate teal, A maroon/red) and the **face** (B an older grey-haired woman, A a broad-faced
auburn-haired woman): one body paint with ramps (R pinafore, G skirt + lining), one 1K head colour per tier bound by `KHR_materials_variants`.
Skin A's embroidered blouse front is a pattern the ramps cannot give: tier A keeps the plain gathered blouse (deviation).

## Checks (final GLB, `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps) | **0 frames over 1 cm in every clip, both hands**; hand depth at most 0.2 cm; forearm 0.2 cm except **Cower L 1.4 cm in 1 frame** (under the coif's rigid side flap, see open points); finger stretch max 2.36 (Fidget R) |
| `skin_poke_gate.py` (new, after PeasantM7's sleeve gate: hand stub inside forearm + bracelet, arm top inside the puffed sleeve) | **0.0 mm in every clip**, both sides (28 stub + 17 sleeve candidates per side); before the stub weights: 5.3 mm (Conv3 R, 335 frames) |
| `robe_gate.py` (legs through the skirt) | **0 frames in all 11 clips** (Death 2/45 at 4.6 cm with F8's skirt-lift tolerance 0.08, 1/45 at 0.11, 0 at 0.14) |
| `jitter_gate.py` against the same clips without corrections | 0 fails (no arm corrections: MM9's own arms clear this body) |
| `collapse_gate.py` (30 fps, worst frame per region) | worst: Death waist 80 (exposed 38), Hit waist 66 / armpit R 54, Fidget waist 58 / armpit R 43, Cower elbow L 23, Death armpit 27; neck at most 17, skirt at most 19 (Death); see `review/gates/collapse.txt` |
| `detached_parts_audit.py` | 7 flagged: the shins and shoes (4, free inside the skirt by design, as F8/MM9); the bracelets lift at most 1.8 cm from the body cluster in 7 of 838 poses (Conv3, carried with the arm); the buckle 1.8 cm in 1 pose (Death) |
| `bone_length_audit.py` | 14 checked, 0 stretching |
| `flat_shading_check.py` | 0.00 body, 0.01 head (0.00 before the face fix; the flattened mouth) |
| `check_winding.py` | 0 inverted closed parts (r18 too) |
| `floor_audit.py --world mm9` | 3 bindings ok: stand -0.2, walk -0.1..+1.2, living -0.5, dead 0.0 |
| `texture_quality.py` | body atlas 66.6 %, fragments 0.2 %, stretch p90 1.05, spread 3.38 (hands 1.5x, legs 0.5x, lining 0.3x by design; p50 1,718 px/m); head atlas 65.9 %, spread 1.66 (face 1.6x), stretch p90 1.14, fragments 0.6 % |
| Regression `--world mm9 --headless-run-regression-suite actors` | r19 (with F1 r23): binding PASS (187 descriptors on 80 models), suite 192 passed, 1 known out05 failure. r18 (nose/lip fix): binding PASS (187 descriptors on 80 models, 0 failed), suite 192 passed, 1 known out05 failure. Earlier: `mm9_actor_models_build_every_binding` PASS on the r17 install ( after the face fix; 108 outdoor actors textured, 0 missing); suite 192 passed, 1 failed: `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data" (known; same on the two earlier installs) |
| Viewer `run_creature_review.py check` | 22 switches, 0 failed, 0 console errors |

## Sheets (viewer shots, read by me)

`review/sheet_mm9_vs_ours.png` (MM9 renders vs ours, both tiers: body front/quarter/back, head close-ups, party-height view),
`review/sheet_tiers.png`, `review/strips_b.png`, `review/strips_a.png` (every clip, six frames), `review/sheet_joints_b.png`,
`review/sheet_joints2.png` (shoulders in Conv1/Standing, wrist), `review/sheet_hands2.png`, `review/sheet_r5c.png` (Conv3 arms, Cower,
Death), `review/sheet_cower.png`, `review/sheet_dead.png`, face iterations `review/heads_r2.png` ... `review/heads_r9.png`,
`review/eyes_r6.png` ... `review/eyes_r8.png`, r13 faces `review/faces_final.png`, face fix `review/sheet_faces_before.png` / `review/sheet_faces_after.png`, `review/sheet_asm.png`, `review/sheet_asm2.png` (assembly, wrist, eyes), `review/sheet_raw.png`.

## Deviations and open points

- **Handedness:** `mirror_glb.py` last (raw ABC `L` at -x), as every MM9 humanoid.
- **Faces** (after the face fix): gentle closed-lip smiles, soft brows, B elderly; MM9's women smile broadly with teeth, ours keep the lips
  closed (the 3D mouth is closed). Close up (viewer head camera) the eyes still read a little round: Meshy's lid opening is rounder than the
  painted lids, and the eyeball top shows a slightly stepped edge where the lid paint meets it. The lifted nose underside still shows a light
  shadow under the key light.
- **Bracelets** are our geometry (MM9's is paint on the wrist); a tiny dark notch shows at the bracelet's lower edge up close.
- **Pinafore straps:** a small dark tab where each strap ends on the shoulder (Meshy's paint on a strap corner).
- **Cower:** the left hand/forearm brushes 1.4 cm under the coif's rigid side flap in one frame (MM9's gesture covers the face; the
  coif flap does not swing). Not corrected.
- **Legs** hang free inside the skirt (4 detached parts: shins and shoes, as F8 and MM9). The corpse lies on its stiff hem.
- **Map placement not switched** (orchestrator's step): the rebuilt maps still place 376 for `CommonerHuman2FemaleA`; descriptor 9036 is
  ready for the batch switch (34/41 have no placements).

## For the next bodies (lessons)

- Check a new UV layout for needle charts before the upload (`fix_needles.py` logic: UV edge > 0.15 with 3D area < 1e-5): midline slivers
  of an offset lining reached across the atlas here and cost a repair.
- Meshy's eyeball spheres, kept, fill the sockets but come back painted white with a small iris (staring): repaint them (`head_fix.py`).
- A mouth slit into a painted cavity reads as an open, surprised mouth: tone the cavity to a lip shadow.
- Where a grafted hand meets a bare forearm, keep the hidden stub rigid on the forearm and gate it with `skin_poke_gate.py`.

## What was not checked

- In game (no map spawns these descriptors yet; no spawn tour run).
- Motion at normal speed by eye (strips, gates and stills only); LOD1-3 and shadow meshes by eye; tier A joint close-ups.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf5_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf5_reduce_claude/before/`.
