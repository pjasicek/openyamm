# MM9 PeasantDM1 dwarf townsman (mm9_peasantdm1) — 3D actor, 2026-11-01

Townsfolk batch, wave 2 (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`). MM9 `MONSTERS.txt` rows naming `PeasantDM1.abc`:
**8 Commoner** "Peasant Dwarf MaleA A", skin PEASANTDM1A, DAT class `CommonerDwarfMaleA` (11 placed objects), and **13 / 14
Shopkeeper** "Peasant Dwarf MaleC B", skin PEASANTDM1B (the two rows are identical), DAT class `ShopkeeperDwarfMaleB` (1 placed,
BankOrb.scr). First body on MM9's **dwarf male townsfolk skeleton** and its `peasantmaledwarf` clip library (PEASANTMALEDWARF.abc,
21 clips); no earlier project had retargeted it (`mm9_dwarf_claude` is the DWARF.abc monster rig, a different skeleton). Route:
the PeasantM7 / PeasantM1 chain (Meshy body fitted to the MM9 skeleton, MM9's own clips, MPFB five-finger hands, separate head
set, sharp textures). Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantdm1.glb` (`tools/install_model.py --world mm9 --name mm9_peasantdm1.glb` from `export/mm9_pdm1.glb`, sha256 366854191073... (r3, ear fix); r2 df992d69796e... kept as `work/mm9_peasantdm1_installed_r2_rollback.glb`), variants `pdm1_a`, `pdm1_b` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantdm1_claude`: `MM9 8 Commoner` (pdm1_a), `MM9 13 Shopkeeper` and `MM9 14 Shopkeeper` (pdm1_b); scale 100 (MONSTERS Scale 1), `yaw_offset -1.570796327`, stride walk 0.4 / run 0.7 (twice the foot's sweep: 0.18-0.21 m walk, 0.35 m run), look `Bip01 Neck, Bip01 Head`, impact 0.966 s (hattack1 `Rattack`) |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 8 -> 322, 13 -> 329, 14 -> 329 (the stand-ins of `mm9_npc_legacy_replacements.tsv`); tables regenerated (173 rows), descriptors 9008 / 9013 / 9014 |
| Triangles LOD0/1/2/3 | 7,586 / 3,791 / 1,363 / 453 (Smart Topology 15,704; head set 3,769 incl. two MPFB hands about 1,400; body 3,817) |
| Skeleton | PEASANTDM1 = the dwarf male townsfolk skeleton, 41 joints: no pelvis (`Bip01 Spine` is the root and carries the thighs), no Spine3, `Bone03` (chin) and `Bip01 Ponytail1` on the head, and a tunic ring `Bone22` with eight hem bones hanging from the **Scene Root**. Names and rest rotations unchanged, joints translated onto our body (`fit_rig.py`), + 15 MPFB finger bones per side driven by MM9's mitten curl (`finger_alias`); whole model mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps, `source/mm9_lib/pmaledwarf.glb`) | Standing stand 1.8 s, Walking walk 1.0, Running run 0.8, Fidget Fidget1, Fidget2, Talk conv1 3.53, AttackMelee hattack1 1.7 (impact 0.966), Hit wince, Death die1, Dead; script clips Cower cower (loop), RubBeard Rub_beard, Rock, Hammer hammer, Dump; `stand` -> Standing |
| Textures | body 2K colour + 1K normal + 1K ORM, region mask 1K (R tunic, G gold trim, B forearm skin) + ramps per tier; head + hands set 2K colour + 1K normal/ORM, tier B has its own head colour and normal (two different men); tier A's ear islands carry tier B's ear paint in A's skin tone (`fix_ear_pdm1.py`); specular 0, metallic 0 |
| Meshy credits | **35 / 60** (Smart Topology 5, body 4K retexture 10, head A 4K retexture 10, head B 4K retexture 10; backup account 3555 -> 3460 shared balance over the session, no retries) |

## Clips the MM9 scripts play
DAT objects (`scripts/dat_objects.py DwarfMale`): `CommonerDwarfMaleA` 6 without a script (row default NPCbase.scr -> npcBase.inc ->
BaseRun.inc `LoopAnim Cower`), NPC109.scr (`stand`, `conv1`, basemelee.inc), ake.scr and shopkeeper.scr (no animation; the
shopkeeper's ScriptParams hold a voice file, not an animation), and two `scripts\DwarvenMiner.scr` miners (`stand`, `rub_beard`,
`rock`, `hammer`, `dump`; the miner attaches `dwarfaxe.abc` to RHand1 while mining). `ShopkeeperDwarfMaleB`: BankOrb.scr (none).
So the core roles plus Fidget2 (MM9's second fidget), Cower and the four miner clips. **The miner's pick prop is not modelled**
(our engine does not run DwarvenMiner.scr; Hammer and Dump play empty-handed).

## For the next dwarf body (PeasantDM2, DM3, DM4; same skeleton and library)
PEASANTDM2 and DM4 have exactly this bind (every joint's translation and rotation equal to the library's); **DM3 differs in
one joint rotation (0.12 in a quaternion component)**: check it before reusing the source offset. Copy from `scripts/`:
- `convert_sources.sh` (converts the model with both skins and **`PEASANTMALEDWARF.abc` -> `source/mm9_lib/pmaledwarf.glb`**);
- `dwarf_roles.py` writes the roles json for `clips_mm9.py`: default = the roles above; **`--all` writes all 21 library clips**
  (adds Push, X, CowerStart, CowerEnd, Npc008, WalkCarry, Guard); pick the subset your DAT objects' scripts play. It sets
  `root_nodes` (Spine, Scene Root, **Bone22**: the tunic ring rides on the pelvis from the Scene Root, so it must take the root
  translation too) and **`source_offset`**: the library's clips hold the pelvis and the tunic ring 0.2214 m above their bind
  place (LithTech's per-animation origin, -0.2304 in `pmaledwarf.model.yml`, is not applied by the converter); without it every
  clip floats 22 cm and Running/Death cannot be grounded by `floor_fix.py`;
- `clips_mm9.py` (the `source_offset` option and the soft offset line), `fit_rig.py` (new `follow` option: `Bone22` takes the
  pelvis move) with `fit_config.json` (centre chain Spine..Head, torso band -0.12..0.25 in the MM9 frame);
- `floor_ops.txt` (`--smooth-loop Walking 0.04`: 0.12 left a 3.8-unit hop, no smoothing failed the jitter gate at 8 mm/f2);
- wrists: if the body wears bare forearms and a wrist band, `cuff_trim.py` + `wrist_band_pdm1.py`
  instead of PeasantM7's `sleeve_tuck.py` (made for real sleeves); `hand_clean.py <prefix>` per head set;
- the rest of the chain is PeasantM7's (`build_runtime_pdm1.sh`, `retier.sh`, gates incl. `sleeve_poke_gate.py`).
Arm and hand gate on the library: only Rub_beard (fingers into the chin, 3.9 cm) and conv1 (1.4 cm, 3 frames) touched this body.

## Route (scripts/, repo root unless noted)
0. **MM9 sources** `convert_sources.sh`; renders `ref_renders.py` -> `review/mm9/`, composed into `references_hd/mm9_views_{a,b}.png`,
   `mm9_head_views_{a,b}.png`, `mm9_skin_x4_{a,b}.png`.
1. **HD masters** (Codex via `codex_slot.sh`; `codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`): skin A, MM9 bind
   pose (arms 20 deg below horizontal), 1536x1024; the first run-1 return had the arms 30 deg down (`references_hd/superseded/`).
   Halo removed by `clean_alpha.py` (raw in `raw_codex/`). Head turnarounds `codex_head.sh a|b` -> `references_head/` (A) and
   `references_head_b/` (B: another dwarf painted on A's head silhouette, studded headband, grey stubble).
2. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
3. **Fit + weights** `fit_rig.py` + `fit_config.json` (X-ray `review/xray_v1.png`), `reduce_uv.py` (decimation only, 15,704 ->
   8,302), **hands** `graft_hands.py graft_pdm1.json` (MPFB macro muscle 0.6 / weight 0.65), **head split** `head_split.py
   head_pdm1.json` (neck cut 0.33 in the MM9 frame; parts 2 head, 4 hair, 7/8 eyeball cups) -> `work/head_v1.blend`.
4. **UVs** `uv_pass.sh` (`texpass_uv.py`: body atlas 54.2 %; `texpass_head_uv.py`: head 59.0 %). **Never re-run**: the paid
   paints belong to `work/texpass_uv.blend` / `work/texpass_head.blend`.
5. **Paint** (project folder): body 4K retexture -> `bake_ao_texpass.py`, `compose_texpass.py pdm1_tp ...`, gentle grade
   (`grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`); `bake_hands.py
   work/texpass_head.blend young_caucasian_male/young_lightskinned_male_diffuse.png`; `compose_headhand.py pdm1_tp|pdm1b_tp
   <head job> ... --ref-head --ref-lum-min 135 --hand-gain 1.0` (new `--ref-lum-min`: the ginger beard passed the reddish skin
   test and turned the hands orange-brown).
6. **Fixes without new paint**: `eye_fill.py` (shell onto the eyeball cups, then `export_fix.drop_parts` 7, 8: the cups poked
   through the lower lids as pale drips) -> `work/eyes_v1.blend`; `fix_neck_pdm1.py` (the neck faces inside the tunic slit were
   painted navy/gold knotwork: skin with a beard shadow); `fix_collar_pdm1.py` (the tunic collar rim painted pink -> navy wool;
   the bare forearms painted near white [255,178,134] -> tier A face skin, mask `textures/pdm1_forearm_skin_mask.png`);
   `wrist_band_pdm1.py` (a dark leather wrist band over both sides of the hand graft seam, as MM9 and the master wear one: the
   jagged cut showed a pale toothed rim and dark notches); `hand_clean.py <prefix>` (PeasantM7's: one clean face-skin colour
   on the hands with the bake's luminance detail only, natural nails); `fix_ear_pdm1.py export/mm9_pdm1.glb` (user note
   2026-11-02, `review/user_notes/ear_wrong_texture.png`, see "Ears and beard edge" below). Order: compose -> fix_neck ->
   hand_clean (A, B) -> fix_collar -> wrist_band -> fix_ear -> tiers. Each fix reads its own backup (`*_preneck`,
   `*_precollar`, `*_preear`), so after a new compose delete the backups before rerunning the chain.
   **Wrists** (user lesson on PeasantM7, "hands sticking through the sleeves"): `cuff_trim.py work/eyes_v1.blend
   work/eyes_trim.blend -0.03` bisects the body's forearm 3 cm before the hand joint (a clean ring) and deletes the toothed
   remnant past it that graft_hands.py had left lying on the MPFB hand (0-5 cm past the joint): in bent wrists those teeth
   stood off the hand as shards, and the sleeve-poke gate read the hand through them (rest 22 / 46 mm). PeasantM7's
   `sleeve_tuck.py` was tried first and dropped: on a bare wrist it took the teeth for a sleeve and shrank the hand's wrist
   by up to 5 cm (`cuff_follow.py`, the teeth reweighted to the hand, did not remove the shards either). The band
   (`wrist_band_pdm1.py`, s -0.04..+0.06 body, -0.04..+0.015 hand) covers the ring.
7. **Tiers** `tiers_pdm1.py work/pdm1_body_tex.glb textures/pdm1_tp_basecolor_graded.png textures/pdm1_tp_material_classes.png`.
8. **Runtime** `TOKEN=<lease> scripts/build_runtime_pdm1.sh` (BLEND default `work/eyes_trim.blend`): export (`export_fix`:
   drop 7, 8 and part 14, a 4-vertex zero-volume sliver at the shin that check_winding reported inverted; fill small holes) ->
   `clips_mm9.py` -> `hand_rest.py` per `hand_rest_pdm1.txt` -> prepare -> LODs -> shadow fix -> region variants -> `tier_head.py`
   (B head image) -> extras -> `floor_fix.py` (`floor_ops.txt`) -> `mirror_glb.py` -> winding. Texture-only: `scripts/retier.sh
   <rev>` (project folder; also writes the viewer GLBs and manifest). Binding: `flock -x
   level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_peasantdm1_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`. Gates: `scripts/gates.sh` (project folder).

## Ears and beard edge (r3, 2026-11-02)
User note: "on his ear some leaked wrong textures". **Cause**: both head turnarounds wear a silver knotwork bead at the
end of each temple braid, exactly where the ear sits; the mesh has no bead, and Meshy's tier A head retexture projected
it onto the ear's own UV islands (white metal with black engraving in the colour, embossed in the normal and the ORM).
Tier B's retexture put its bead on the braid below the ear (it stays there, painted on the jaw) and painted the ears as
skin. The texels were wrong in the paid paint itself (`meshy/head_retexture_tp/`), not from a later pass. **Fix**
(`scripts/fix_ear_pdm1.py`, step 6): the three UV islands lying wholly inside the ear box (94 faces, both ears) take
tier B's paint x the per-channel cheek-skin gain A/B (1.14, 1.35, 1.33), so the ear keeps B's ear shading in A's tone;
tier A's head normal and ORM take B's maps there (tier B's head material shares A's ORM, so B's ear roughness is fixed
too). Same shot: the dark **net along the beard's lower and back edge** (beneath the jaw down to the collar) and the
faint thin lines on the neck were Meshy's paint of the beard edge as thin crossing dark strands on skin (no UV seam runs
there: checked with an unlit UV pass, `scripts/ear_views.py ... uv`). On the neck under the jaw, outside the dense
beard, line texels on skin take the mean of the line-free skin around them with a 6 px soft beard-coloured fringe; the
hair bob's strands are excluded by colour. Tier B has no net (grey stubble). Remaining faint horizontal neck creases
are painted skin folds, kept. Shots: `scripts/ear_views.py` (views rear/lear/rprof/lprof/rback/lback/rneck/lneck/party,
rest pose), sheet `scripts/ear_sheet.py`.

## Tiers
Shared paint = skin A (row 8, 11 of 12 placed objects). Region R tunic (the blue wool by hue, above the hem), G gold trim
(gold texels whose non-gold surroundings are dark, so the linen undersleeves' olive stripes stay out), B forearm skin. Tier B
target per texel = MM9 B's colour at the texel's luminance quantile inside the region x the gain that maps MM9 A onto our paint
(as tiers_pm1.py); B forearm = tier B's face skin. Fit error (8-bit mean / p95): tunic A 2.1/7.0, B 2.2/7.1; trim A 4.5/16.5,
B 7.3/20.9; forearm 0.5/1.1. Leggings, belt, boots and linen are shared (MM9 B is only a little brighter; a dark-texel leggings
mask took the boot cuffs, so it was dropped). **Tier B head**: MM9 paints a different man (dark hair, studded headband, grey
stubble) on the same head, so the head material has a B copy with its own colour and normal from a second head retexture.

## Checks (final build, viewer revision r3-20261102; `review/gates/`)

| Gate | Result |
|---|---|
| Arm and hand gate (`arm_hand_gate.py --outer-only`, every clip, 48 fps) | hands 0 frames over 1 cm in every clip except **Talk L 1.4 cm, 3 frames** (frame 105; `hand_rest.py`'s horizontal cast finds no surface to push from). RubBeard L was 3.9 cm / 68 frames into the chin (fingers rub the painted beard): `hand_rest.py` pushed the hand forward 7 cm, now 0. Forearms 0 in every clip. Finger stretch p99 <= 1.64 (Rock R 1.64), max 3.23 (Rock R). Wrist max 86 deg (Fidget2 R). Five chains per hand (19 joints) |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails**. Running shoulder skin 23 mm/f2 and AttackMelee 2.1 came from the per-key floor pass: `--smooth-loop Running 0.12 --smooth AttackMelee 0.1`; Walking 0.04 (shoulder skin 1.3 mm/f2) |
| Floor (`floor_audit.py --world mm9`) | MM9 8 Commoner, MM9 13 / 14 Shopkeeper ok: stand 0, walk -0.1..+1.7, living -0.6, dead 0.0 world units |
| Ears and beard edge (r3) | `review/sheet_ear_before_after.png` (both tiers, before r2 / after r3: tight ear close-ups both sides, profiles, 3/4 back, jaw-neck line, party view from 22 deg): tier A ears skin with ear shading, no foreign texels from any view; beard net gone on both sides; tier B unchanged apart from the ear ORM. Mesh and clips identical to r2 (`glb_diff.py`: 0.000 mm in every clip; only the three tier A head images changed) |
| Winding (`check_winding.py`) | 0 inverted closed parts (was 1: the shin sliver, dropped) |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching |
| Detached (`detached_parts_audit.py`) | 0 detached in any pose (13 components) |
| Flat shading | 0.00 on both materials |
| Texture quality (`texture_quality.py`) | body atlas **53.4 %** (target 55-60 %, 1.6 short: 54.1 % before the wrist trim deleted the cuff teeth), density p10/p50/p90 1082/1118/1151 (spread 1.06), fragments 0.0 %, stretch p90 1.08; head set 41.4 % of the 2K image (head square plus hand squares), spread 2.68 (hands half density by design), fragments 1.0 %, stretch 1.30 |
| Sleeve poke (`sleeve_poke_gate.py`, PeasantM7's) | rest **0 mm** both sides (was 21.9 / 45.6 mm). 0 in Standing, Walking, Talk, Hit, Death, Cower, Dead (both sides) and on one side in the rest; **not 0 where MM9 flexes the wrist 45-86 deg**: L AttackMelee 68.2 mm (22 of 82 frames, 3 vertices), RubBeard 43.0 (23 f), Fidget 37.0 (28 f), Running 4.9 (4 f); R Running 27.9 (8 f), Fidget2 28.0 (36 f), Rock 13.5 (28 f), Dump 8.9 (85 f), Hammer 1.9. These are 1-10 hand vertices just past the wrist folding back over the forearm ring (the gate's ray is perpendicular to the forearm); the renders of the worst frames (`review/poke_check.png`) show the band and ring clean, no skin through cloth |
| Viewer (`run_creature_review.py check`) | 30 tier/clip switches, 0 failed, 0 console errors (r3-20261102) |
| Regression `--world mm9 --headless-run-regression-suite actors` | r3 install (2026-11-02): **passed 192, failed 1** (the known out05 "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS** (647 descriptors on 185 models and 187 on 80, 0 failed); log `review/gates/regression_actors.log`. r2 install: **passed 192, failed 1** (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS** (647 descriptors on 185 models and 181 on 74, 0 failed). An earlier run failed the binding case on "MM9 57 Commoner" (PeasantHOM1's block landed in actors.yml before its tables, mid-run), not this body |

Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm1_claude/review/viewer/index.html` (tiers pdm1_a, pdm1_b;
`viewer_tiers.py` bakes each tier's body ramps into its own viewer GLB; the head keeps its tier material).
Sheets read: `review/sheet_ear_before_after.png` (r3), `review/sheet_mm9_vs_ours.png` (MM9 raw-conversion renders vs viewer shots, both tiers), `review/sheet_tiers.png`,
`review/sheet_heads.png` (bind and Talk: faces, eyes, mouth, neck; both tiers), `review/sheet_fringe_tiers.png`,
`review/sheet_hands.png` (wrist bands, hands vs forearm, both tiers), `review/poke_check.png` (worst sleeve-poke frames),
`review/sheet_eyes_high.png` (faces from 20 deg above: eyes open, one brow line), `review/strips_a_q34.png` and
`review/strips_a_front.png` (every clip at 15/50/85 %, tier A), `review/strips_b_q34.png` (core clips, tier B), `review/xray_v1.png`, `review/head_split.png`, `review/graft_all.png`.

## Binding plan (map placement)
The rebuilt maps place these townsfolk with the legacy stand-in ids (322 for `CommonerDwarfMaleA`, 329 for
`ShopkeeperDwarfMaleB`) through `transcode_mm9_dat_to_odm.py`, so the new descriptors do not show in game yet. Per the brief
this switch is the orchestrator's, once for every row after the batch: those two DAT classes should place 9008 / 9013. No
transcoder or map change here.

## Deviations and open points
- **Tier B is A's tunic recoloured.** B keeps A's knotwork bands (gold on near-black on B) and A's silver medallion; MM9 B
  has a plain gold edging and a small gold pendant. The front yoke knotwork came out dim navy-on-navy in the paint (not
  MM9's bright gold); sleeve and hem bands are gold.
- **Tier B's braid beads** (from its head turnaround) are painted flat on the jaw below each ear, as the paint put them;
  tier A has none since r3 (its beads were on the ears).
- **Wrist bands** are paint over the trimmed forearm ring and the hand's stub (`wrist_band_pdm1.py`), about 5 cm wide; the
  ring shows as a small step (a cuff edge) over the band. The forearm skin between undersleeve and band is shorter than
  the master's.
- **Hands** are graded to the face skin; the forearm skin is repainted to the same tone (Meshy painted it near white).
- **RubBeard**: the hand stays 7 cm in front of MM9's place (rubbing in front of the beard rather than in it).
- **Talk L 1.4 cm, 3 frames** into the body (above).
- **Hammer / Dump** play without the miner's pick.
- MM9 dwarf townsfolk proportions: our body is fuller (Meshy from the master), hands large (22.7 cm), as the master.
- Not looked at in game (no map spawns these descriptors yet); LOD1-3 and shadow meshes not looked at; motion judged on strips
  and gates, not watched at speed in the viewer; tier B clips beyond Standing/Talk not looked at; sounds; Android cook.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantdm1_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantdm1_reduce_claude/before/`.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_RHand1`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
