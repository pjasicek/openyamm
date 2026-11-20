# MM9 PeasantDM4 dwarf townsman with cap and red beard (mm9_peasantdm4) — 3D actor, 2026-11-02

Variants/townsfolk batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`, `TOWNSFOLK_BRIEF.md`). The only MM9 `MONSTERS.txt`
row naming `PeasantDM4.abc` is **10 Town** "Peasant Dwarf MaleB A", skin PEASANTDM4A, DAT class `TownDwarfMaleA` (11 placed
objects, legacy stand-in 325). Skin PEASANTDM4B is used by no row and is not built (no tiers). Status log:
`devdocs/mm9_rework/overnight/status/townsfolk_peasantdm4.md`. Lease identity `mm9:peasantdm4`.

## Decision: a new body, not a variant
- Skeleton: PEASANTDM4's 41-joint bind equals PEASANTDM1's, PEASANTDM2's and the `peasantmaledwarf` library's exactly
  (`scripts/cmp_skel.py`: max translation and rotation difference 0).
- Mesh: `scripts/rigid_cmp.py` (translation ICP of MM9's DM4 mesh onto DM1/DM2/DM3, after the orchestrator's meshcmp): the
  best rigid shift is under 1 cm and leaves the torso at p50 2.8-2.9 cm, p90 5.2-5.5 cm, 82-88 % of points over 1.5 cm
  from DM1/DM2 (PeasantM2d's 2.6 cm was a pure offset; this is not). Renders `review/sheet_mm9_dm4_vs_dm1_dm2.png`: an own
  design (skullcap with a silver knot medallion, copper-red hair over the ears and a full red beard, laced vest over a
  linen shirt, puffed elbow sleeves, flared tunic skirt). So the full MM9 humanoid route with DM1/DM2's retarget, linings
  and fixes. (DM3 is close to DM1/DM4; another agent builds it as a variant.)

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantdm4.glb` (`tools/install_model.py --world mm9` from `export/mm9_pdm4.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantdm4_claude`: `MM9 10 Town`; scale 100, `yaw_offset -1.570796327`, stride walk 0.4 / run 0.7 (DM1/DM2's: same skeleton and clips), look `Bip01 Neck, Bip01 Head`, impact 0.966 s (hattack1); no `skin` (one material set) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 10 -> 325; tables regenerated |
| Triangles LOD0/1/2/3 | 12,933 / 6,442 / 2,315 / 768 (Smart Topology 14,519 -> 7,609 reduced; + MPFB hands 2 x 700; + linings and the cap's inner lining; shadow meshes drop the one-texel linings) |
| Clips (30 fps, `source/mm9_lib/pmaledwarf.glb`) | Standing stand, Walking walk, Running run, Fidget Fidget1, Fidget2, Talk conv1, AttackMelee hattack1 (impact 0.966), Hit wince, Death die1, Dead, Cower cower (loop), RubBeard Rub_beard, X x |
| Textures | body 2K colour + 1K normal/ORM (one material, no region mask); head + hands set 2K colour + 1K normal/ORM (cap, hair, beard, face, MPFB hands); specular 0, metallic 0 |
| Meshy credits | **25 / 50**: Smart Topology 5 (backup 2975 before), body 4K retexture 10 (2970 before), head 4K retexture 10 (2960 before); no retries |

## Clips the rows play
`scripts/dat_objects.py TownDwarfMale`: `TownDwarfMaleA` 2 objects without a script and 5 with only a voice in ScriptParams
(NPCbase.scr -> BaseRun.inc `LoopAnim Cower`), 3 x NPC7.scr (Hjarrand the fixer at the refinery: `PlayAnim Rub_Beard`,
`PlayAnim x`; BaseWander markers), 1 x `scripts\randverretainer.scr` (`LoopAnim sitting`: no such clip in PEASANTMALEDWARF,
so not carried). `TownDwarfMaleB` (1 object) is row 11 = PeasantDM3, not this body. Roles: `scripts/dwarf_roles.py` (DM1's,
default set changed to these; `--all` still writes the library).

## Route (scripts/, repo root unless noted; DM2's chain copied, changes marked NEW)
0. `convert_sources.sh` (both skins + the library), `ref_renders.py` -> `review/mm9/`, sheets `references_hd/mm9_views_a.png`,
   `mm9_head_views_a.png`, `mm9_skin_x4_a.png`.
1. HD masters (Codex via `codex_slot.sh`; `codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`): 00 = the FIRST run-1
   return (arms 20 deg below horizontal as MM9; Codex's own correction had them horizontal, kept in `raw_codex/`), halos
   removed by `clean_alpha.py` on all five. Head turnaround `codex_head.sh` (brief `references_head/CODEX_BRIEF.md`: calm
   warm face, no ears, nothing in hair or beard). Hashes in `creature_3d_progress.json`.
2. Meshy Smart Topology 15k from `00_three_quarter.png`.
3. `fit_rig.py` + `fit_config.json` (arms within 2 % of MM9), X-ray `review/xray_v1.png`; `reduce_uv.py` (14,519 -> 7,609);
   `graft_hands.py graft_pdm4.json` (`hand_len` 0.205 m: Meshy's hands 0.195/0.181 m, MM9 0.21 m); `loose_parts.py` (a
   3-vertex stray); `head_split.py head_pdm4.json` (cap, hair, beard and face are one head set, `review/head_split_close.png`).
4. NEW `head_shift.py`: Meshy put the separate head shell and cap 1.3 cm off the midline (eye cups at x -0.041/+0.0135, no
   yaw): shifted +1.35 cm. `eye_fill.py 7,10`, `loose_parts.py` drops the eyeball cups, `fill_holes.py`; `eye_relax.py` 0.4
   (DM2's frame options; the eye plate only, nose bridge held fixed; before the UV pass so the paint lies on the final face;
   nose and mouth untouched) -> `work/eyes_relax.blend`.
5. UVs `uv_pass.sh` (body 55.2 %, head 58.0 %). **Never re-run** (the paid paints belong to `work/texpass_head.blend`).
6. Paint: `bake_ao_texpass.py`, `compose_texpass.py`; NEW `ao_fix.py` (isolated black AO specks filled and the AO floored at
   0.5: whole outward cloth islands baked 0.1-0.3, e.g. the top of the right puffed sleeve under the hair, and the grade turned
   them into dark stains) -> gentle grade on `pdm4_tp_ao_2k_fixed.png`; NEW `blotch_fix3d.py 0.72` (Meshy's darker patches on
   the ochre cloth lifted by surface neighbourhood, about 2 vs 10 cm; `blotch_fix.py`, an image-space first try, is
   superseded). `bake_hands.py ... middleage_caucasian_male/...`; `compose_headhand.py pdm4_tp ... --ref-head --ref-lum-min 135`;
   `head_paint.sh` = NEW `emblem_project.py` (the cap's silver knot: Meshy painted the medallion as a cap-coloured blob; the
   knot is cut from `references_head/01_front.png` and front-projected onto it, `emblem_overlay.py`, z-buffered, the normal
   map flattened under the knot only) -> `hand_clean.py` (`HAND_REF` 196,121,94 = the paint's forehead) -> `pad_head.py`.
7. Geometry on the painted master (positions/faces/weights only; **`scripts/geom_chain.sh`** replays all of it): NEW
   `cap_normals.py` (26 cap faces facing inward above the band) -> `work/cap_fix.blend` -> NEW `cap_reshape.py 0.02 0.2`
   (below) -> `sleeve_tuck.py 0.7 0.004 1` -> `cuff_trim.py 0.01 L=-0.015,R=-0.015` (NEW per-side cut: a toothed single-sided
   sleeve flap hung below each wrist) -> `linings.sh` (neck cap; collar, boots as DM2; NEW elbow rims of the puffed outer
   sleeves (`max_edges` 19, before the wrist band); wrist band with own-paint 0.5 mm twins of the inner-layer faces instead of
   DM2's `skip_inner` (which left the bottom wall of the trimmed cuff unlined) and NEW `pick_rgb` shaded linen for the cuff
   lining (the darkest texel read as a black ring round the wrist from the front); NEW skirt hem and skirt belt rims on the
   `Bone*` skirt bones; NEW `cap_lining.py`, the cap shell 3 mm inward flipped; NEW `rim_lining.py min_lum=0.06`; region
   labels from NEW `lining_regions.py`, not used at runtime) -> NEW `head_rigid.py` -> NEW `stub_cap.py` (two-sided caps on the
   hand stubs' open forearm ends; after NEW `body_reweight.py`, below) -> NEW `twin_patch.py` (own-paint flipped twins 0.5 mm behind the faces within 5 cm of
   points where the see-through gate met folds from behind: the +x shoulder top and upper back, both skirt sides at the hips,
   the boots' turned-down cuff undersides; 263 faces; the mirrored left-shoulder points made that side worse and were
   dropped) -> **`work/rigid_v3.blend`** (build default).
8. Runtime `TOKEN=<lease> scripts/build_runtime_pdm4.sh [--install]` (memory-capped): export -> `clips_mm9.py` (soft line,
   DM1's `source_offset`) -> NEW `finger_pose.py` (Kira's, adapted: the dwarf mitten has two segments, so the distal direction
   is Finger11's own axis, sign taken at bind) -> NEW three `arm_clear.py --exact` passes with a NEW `--smooth-keys` Gaussian
   (Talk 4; RubBeard, Fidget 14; Running, AttackMelee 8 with a 7 cm margin) -> `hand_rest.py` per `hand_rest_pdm4.txt`
   (RubBeard rests on the beard: `Ponytail,Bone03` surfaces) -> prepare -> LODs -> shadow LODs -> extras -> `floor_fix.py`
   (`floor_ops.txt`) -> `mirror_glb.py` -> winding. Viewer: `review/viewer/` (`make_viewer_manifest.py`; http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm4_claude/review/viewer/). Binding:
   `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_peasantdm4_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.

## Cap (NEW `cap_reshape.py`, coordinator review 2026-11-02)
Ours read as a round domed metal helmet with a band; MM9's is a tall, flat-topped soft skullcap with the medallion on the
front. Overlaying MM9's head outline (front and side, aligned at the floor: `review/cap_overlay_before.png`) put MM9's crown
2 cm higher with a flat top and slightly tapered sides. `cap_reshape.py` moves only the crown's vertices above the band (per
azimuth: the band is tilted, front lower): a Taubin-smoothed copy of the cap stands for the dome, every vertex moves along its
ray from the band centre onto a frustum r = R0 - 0.2 h with a horizontal flat top 2 cm above the old crown, keeping its
distance ratio to the smooth dome (Meshy's folds), eased in over 1.2 cm above the band. UVs are untouched, so the paint and the
projected medallion follow. Before/after: `review/cap_overlay_before.png`, `review/cap_overlay_s1.png` (MM9 outline in red),
`review/sheet_cap_before_after.png`. No Meshy job.

## Chest and collar weights (NEW `body_reweight.py` + `under_beard_paint.py`; user review 2026-11-02, Talk: "weirdly twists his
clothing? like on breast/collarbones")
Cause: fit_rig.py gave body cloth near the beard the weights of MM9's head-only bones: Bip01 Ponytail1 (22 % on the upper
chest; Talk swings it 49 deg), Bone03 and Head (44 % on the collar), and the upper-arm shares ran to the sternum (17 % each).
The vest top and collar were dragged with the beard and the arms. PeasantDM2's chest has no Ponytail share and its arm share
fades medially. `body_reweight.py` (geometry chain, after head_rigid.py): on every body vertex the Ponytail1/Bone03/Head shares
go to Neck (above 0.33 m Blender rest) / Spine2 (below 0.27) / mixed; above the belly the UpperArm share fades to 0 toward the
midline (|x| 0.17 -> 0.07 m) and the Clavicle share (0.08 -> 0.02 m), the rest to Spine2/Neck. 804 vertices changed.
`scripts/chest_shear.py` (upper chest/collar vertices vs Spine2-rigid, p95 over frames) before -> after (final r14): Talk 5.64 ->
2.15 cm, X 7.38 -> 4.02, AttackMelee 8.49 -> 6.39, RubBeard 5.32 -> 3.57, Death 6.36 -> 4.87, Dead 5.07 -> 2.09, Fidget 4.21 -> 2.82.
Meshy had painted the beard onto the shirt/vest under it; those faces no longer swing with the beard, so they showed as an
orange patch at the collar when the head turned (Talk 77): `under_beard_paint.py` (after the grade, before the build; reads
`*_prebeard.png`) repaints those texels (seeds: clear beard orange inside a 3D window under the beard, grown through connected
beard-like texels, plus orange flecks nearby and Meshy's featureless smooth paint connected to the patch) as real cloth: each
texel takes the class (linen shirt, navy collar band with its gold knots, ochre vest) of its nearest clear cloth in 3D and is
cloned from the purest, most detailed window of that class elsewhere on the atlas (mirrored tiling), scaled to that class's
local shading; the UV gutters round it are padded (orange bled into the mips). A first smooth fill read as a blue-and-yellow
smudge (coordinator review). Before/after: `review/sheet_under_beard_a.png` (Talk 77, X 63), `_b.png` (AttackMelee 27,
RubBeard 45), front and 3/4. The neck cap under the beard then showed through the
collar gap when the head turned (head 27 px in Hit): head-set faces within 6 cm of the neck base got own-paint twins
(`twin_patch.py ... heads=1` in `geom_chain.sh` -> `work/rigid_v3n.blend`, the build default; LOD0 12,933). Sheets: `review/sheet_talk_chest_before_after_a.png`
(Talk 33/77/100, front and 3/4), `_b.png` (AttackMelee 27, X 63), `review/talkfix_neck_r13.png`, `review/under_beard_cmp.png`.

## Rigid head (NEW `head_rigid.py`)
fit_rig.py weighted the one-shell head by the nearest MM9 bone: Bone03 (MM9's chin; turned 24-38 deg against the head in
AttackMelee and Hit), Bip01 Ponytail1 (MM9's hair; 49 deg in Talk), Neck, Spine2 and some clavicle. Every head-set vertex
now carries Head only above z 0.34 (the chin and everything above: lips, jaw, cheeks, hair and cap); between 0.26 and 0.34
the beard's and hair's ends on the chest keep a smoothstep share of Neck/Spine2. Bone03, Ponytail1 and clavicle shares go to
Head (`scripts/head_weights.py` before/after).

## Arms (gates)
MM9's thin-body clips drove the left forearm into this fuller body (exact test): RubBeard 5.1 cm into the chest side, the hand
4 cm into the beard; Running 2.5 cm (skirt ring); AttackMelee 3.3 and Fidget 1.6 (sleeve flare at the belt); Talk 2.4-3.8.
`arm_clear.py`'s own neighbour falloff (its `--sigma` is not used) jumped between keys with different correction axes and
failed the jitter gate (20-37 deg/f); Gaussian-smoothed corrections pass it. NOTE: `jitter_gate.py` on the mirrored export
must take the mirrored reference (`work/mm9_pdm4_clips_mirrored.glb`); numbers are identical to the unmirrored pair.

## Checks (final build; `review/gates/`)
Installed build r15 sha256 d07208ac9f2e... (`work/st_r15.glb`; mesh and clips identical to r14, `glb_diff.py`: 0.000 mm, only the body base colour changed = `export/mm9_pdm4.glb` = `assets_source/worlds/mm9/models/mm9_peasantdm4.glb`; cap reshaped, see-through pass, chest weights).

| Gate | Result |
|---|---|
| See-through (`see_through_gate.py`, every 2nd 30 fps frame of all 13 clips + Running 12/15, 8 azimuths x level / 20 deg down, 3 mm px; `review/gates/see_through_r11.json`) | worst background px per zone, r9 (first install) -> **r11**: torso 97 -> **9**, right sleeve 146 -> **9**, left sleeve 18 -> **17** (Talk 2.6 s from behind-left, a crack on the left shoulder top; <= 11 in every other clip), boots 14/18 -> **11/12** (single slivers at the cuff rims), head 28 -> **18** (Hit; 9-18 in every clip: slivers along the reshaped cap's silhouette edges, where the 3 mm inner cap lining slips past the outer shell at the sharp top corners), collar 0, trousers 0. Tried and dropped: mirrored left-shoulder twins (left sleeve 73 px) and an unflipped under-patch on the left shoulder crack (28 px) |
| See-through after the chest fix (r14, `review/gates/see_through_r14.json`) | torso 10, right sleeve 10, left sleeve 17 (Talk), boots 11/12, head 16 (Talk), collar 8 (X, collar slivers: the collar no longer follows the head), trousers 0 |
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps) | hands 0 frames over 1 cm in every clip, both sides (worst 0.2 cm, AttackMelee); forearms <= 1.0 cm (Running L 1.0, RubBeard 0.3: the stub caps' centre vertices inside the sleeve); before the arm passes RubBeard forearm 5.1 cm / hand 4.0 cm, AttackMelee 3.3, Talk 3.8, Running 2.5, Fidget 1.6. Finger stretch p99 <= 1.18, max 1.5; wrist max 81.6 deg (RubBeard, MM9's); 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's clips, mirrored like the export) | **0 fails** (sigma-3 falloff version: 5 fails, 20-37 deg/f) |
| Sleeve poke (`sleeve_poke_gate.py`) | rest 0 mm both sides; 0 in 12 of 13 clips; Death R 27.4 mm on 1 vertex, 9 frames: checked at that frame (`review/poke_check_death.png`), wrist skin just past the lined cuff, nothing through the cloth |
| Floor (`floor_audit.py --world mm9 --match 'MM9 10 Town'`) | ok: stand 0.0, walk -0.1..+1.6, living -0.7, dead -0.0 world units |
| Winding / bones / flat | 0 inverted closed parts; 12 checked, 0 stretching; flat 0.00 on both materials |
| Detached (`detached_parts_audit.py`) | one part: the left MPFB hand, worst 1.1 cm (Walking 0), flagged in 168/671 poses: the tucked stub floats inside the sleeve (bind gap 0; no visible gap in close-ups, `review/wrist_L.png`) |
| Texture quality (`texture_quality.py`) | body atlas **54.6 %** (target 55: 0.4 short after the cuff trims; 55.2 % laid out), fragments 2.5 % (the twin patches' duplicated UVs), stretch p90 1.07 (density spread meaningless: linings sit on one texel); head + hands set 40.9 % of 2K (head square + hand squares, as DM1 41.4 / DM2 42.2), spread 2.05 (hands half density by design), fragments 1.5 %, stretch 1.33 (the reshaped cap crown) |
| LOD0/1/2/3 | 12,933 / 6,442 / 2,315 / 768 triangles (ceiling 15k) |
| Viewer (`run_creature_review.py check`) | r15-20261102: 13 switches, 0 failed, 0 console errors |
| Binding regression `mm9_actor_models_build_every_binding` | **PASS** (232 descriptors on 102 models, 0 failed; `review/gates/regression_binding.log`) |

## Faces (pre-screen, VARIANTS_BRIEF face rules)
`scripts/face_sheet.sh` (MM9 bind vs ours Standing and Talk 2 s, Workbench studio light; ORTHO 0.22): front, 3/4, right and
left TRUE profiles, low 3/4 from below the chin, party view 22 deg above (front and 3/4) and their 128 px simulations;
`review/eyes_r4.png` (eyes front / party / 3/4, nose from below); `review/faces_eevee_r9.png` (EEVEE with the GLB's normal
maps: front, 3/4, both sides, eyes, mouth; Standing and Talk). The viewer wrapper's `head` focus misframes this rig (empty
shots, as DM2), so lit faces are judged on the EEVEE renders; `review/shots/body_q34.png` is the viewer's own body shot.
- Eyes open with green irises from party height (calm, a little narrower than MM9's); one ginger brow each; no lower-lid
  crescent, no eye-plate band (DM2's `eye_relax` at 0.4 on the eye plate only, before the paint).
- Nose: one pair of nostrils, clean underside (low view); the paint sits on the modelled nose (Meshy painted the head on our
  mesh). Nose and mouth geometry untouched (Wyrde lesson).
- Mouth: one closed lip line under the moustache, on the geometry's lips; no second lip, no pink plate.
- Chin/profile: the full beard is the chin line in both profiles; no receding chin or under-chin slab.
- Ears: none visible, hair falls over them as in MM9 (none modelled or painted; no beads or ties anywhere: the briefs said so).
- Beard and hair: wavy strands, no net pattern on skin. Cap: the silver knot projected from the head master (`references_face/
  emblem_preview.png`); Meshy had painted a cap-coloured blob there.
- Rigid head: everything above the chin moves with Head (Talk 2 s row: no shear of lips or beard).

## Binding plan (map placement)
`TownDwarfMaleA` objects are placed with legacy id 325 by `transcode_mm9_dat_to_odm.py`; they should place the new row-10
descriptor. Per the brief that switch is the orchestrator's (one change for every row). No transcoder or map change here.

## Deviations and open points
- **Wrist bands**: MM9 and the masters wear a thin dark leather band at each wrist; the paint had it on a toothed sleeve flap
  past the cuff (single-sided, background behind it), which `cuff_trim.py` (-1.5 cm both sides, per-side option NEW) removed:
  the cream undersleeve now ends in a clean cuff lined in shaded linen (the first, darkest-texel lining read as a dark stub
  round the wrist in the front T-pose: `review/wrists_front_r10.png`). The cuffs stay wider than the wrist (MM9's hug it).
- **Cap**: reshaped to MM9's tall flat-topped cap (`review/sheet_cap_before_after.png`); its top is wrinkled (Meshy's folds kept);
  a small dark speck in the paint near the left top corner; slivers at its silhouette edges (see-through above).
- **Sleeve paint**: faint darker patches remain on the back of the puffed sleeves after the AO fix and the lift
  (`review/sheet_blotch_before_after.png`); MM9's sleeves are even.
- **Running/AttackMelee left arm** is turned out by up to 26-29 deg (smoothed) to clear the fuller belly and skirt; it reads
  natural in `review/strips_q34_sheet.png`, but differs from MM9's swing.
- **RubBeard**: the hand rubs the outside of the beard (2.8 cm forward of MM9's place); the beard is far thicker than MM9's.
- `sitting` (randverretainer.scr) has no clip in the dwarf library; that one object plays Standing.
- Hands 0.205 m (MM9 0.21) in the face tone; body fuller than MM9's (Meshy from the master).
- Not looked at in game (map placement still uses the legacy stand-in); LOD1-3 and shadow meshes not looked at; motion judged
  on strips, close-ups and gates, not watched at speed; sounds; Android cook.

User artistic acceptance: not recorded.

## Sheets read
`review/sheet_mm9_dm4_vs_dm1_dm2.png`, `review/masters/sheet_masters.png`, `review/masters/faces_masters.png`,
`review/head_masters/sheet.png`, `review/xray_v1.png`, `review/head_split_close.png`, `review/clay_face_relax.png`,
`review/sheet_mm9_vs_ours.png` (MM9 vs ours r9, five views), `review/sheet_face_r4z.png` (face pre-screen with profiles, low
3/4, party view, 128 px), `review/eyes_r4.png`, `review/faces_eevee_r9.png`, `review/cap_emblem.png`,
`references_face/emblem_preview.png`, `review/strips_q34_sheet.png` (every clip at 15/50/85 %),
`review/sheet_blotch_before_after.png`, `review/st_sleeves_r8.png`, `review/st_sleeveR_r6.png`, `review/st_shoulder.png`,
`review/poke_check_death.png`, `review/wrist_L.png`, `review/gates/st_r4_worst.png`, `review/gates/st_r6_sleeveR.png`,
`review/cap_overlay_before.png`, `review/cap_overlay_s1.png`, `review/sheet_cap_before_after.png`, `review/wrists_front_r10.png`,
`review/gates/st_r12q_head.png`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdm4_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdm4_reduce_claude/before/`.
