# Hesper Overseers — accepted art, final exports staged

The accepted pistol grip, smooth eye-level ranged aim and 10° recoil are retained. Final fitted colour/shadow LODs,
shared winged body and Nobles reuse contract are published; rows **10030–10032, 10102, 10103** use these exports in
the Hesper stage. `stage.py` passes its LOD/shadow/specular-mask rules. All seven animations pass the full-chain
checks (**8,782 PASS, 162 INFO**) and the final far-selection check (**1,727 PASS, 62 INFO**), with no failures or
unverified checks. The scenario sweep passes **94/94**, with zero actor-size or decoration-ID mismatches.
The integrator's desktop smoke exposed missing burn maps. Both exports now include them, and the cooked
`_BURN_ORDER` checks pass. The integrator owns the desktop rerun (see checkpoint).

[Accepted viewer](http://127.0.0.1:8912/level_generation/creatures/hes_overseer_codex/review/viewer/),
[final LOD sheet](review/lods/sheet.jpg), [export/stage validation](review/finish_validation.json).
Viewer revision `overseers_recoil_20261024` retains the user-accepted full-detail models and content hashes.

## Finish checkpoint — 2026-10-24

The integrator's desktop smoke rejected all five rows because the burn bindings had no burn maps. This repair
adds **17 UV-layout maps / 85 materials** to `hes_overseer.glb`; the shared `hes_kreegan_winged.glb` inherits
**8 maps / 40 materials**. Every variant and colour/shadow LOD is covered. The cooked runtime copies have valid
`_BURN_ORDER` on all **40 / 16 primitives**, respectively. The five temporary `death_effect: none` overrides
are removed; all five staged bindings again use burn. `stage.py` exited 0 (two GLBs and 17 burn textures cooked).
The new `--scenarios-only` sweep passes **94/94**, exit 0, no FAIL/WIP-FAIL. The runner now includes
`hesper_stage/item_expansion`, one more scenario than the earlier 93-case sweep.
[Summary](review/burn_scenarios.log); detailed logs: `output/hesper_stage/logs/scenarios_111845_39/`.

[Burn validation](review/burn_validation.json) proves all non-burn geometry, UVs, skinning, clips and appearance
content are unchanged; all six rigid attachment files and `integration/actors.yml` remain byte-identical.
The previous joint/contact gates and user art acceptance therefore remain applicable. The pre-variant build and
attachment split were exercised in `work/burn_pipeline_check/`. No engine changes/builds, assets_dev writes,
Meshy jobs or git staging. **The integrator reruns the desktop smoke; no new desktop launch was attempted here.**
Historical sandbox launch failures remain in [the attempt record](review/desktop_smoke.json).

Accepted input `work/overseer_body_lod0.glb`, SHA-256
`31f62cdde36cb773f24c86344c6e39e5d07e0935e787fec3c6de63f61d0f72b8`, and the seven accepted animations are preserved
exactly at LOD0. Project ownership is returned at this handoff; a resumed session must claim a fresh lease.
Final candidates and rejected reductions are retained under `work/final_lods/`; initial failed gates under
`review/gates_before_contact_lods/`. Do not restart generation or refit the accepted grip/recoil.

## Tier colours (2026-10-24)

The user's caste table (MONSTERS.md "Kreegan skin colours") replaces the shared violet/plum/red-violet skins in
`hes_overseer.glb`: **ov_a indigo, ov_b verdigris, ov_c ember, ov_krav ash grey, ov_ghulkat bronze**.
`scripts/tier_ramps_overseer.py` takes them from `claude_shared/kreegan_skin.py`. It rewrites only the body and head skin
ramps in `textures/overseer_ramps.json`; the head keeps its darker relation to the body. Sash, equipment, weapons and
glow ramps are byte-identical. **`hes_kreegan_winged.glb` is unchanged** (byte-identical; the Nobles pick their own
colours), so `publish_shared.py` must not be rerun. Backups are in `work/before_tiercolours_20261024/`.

Re-run: `materials_preview.py`, `finish_lods.py hes_overseer .55,.30,.16`, `validate_finish.py`, both gate runs and
`viewer_tiers.py` (viewer revision `overseers_tiercolours_20261024`). Compared with the accepted export, geometry, UVs,
skins, nodes, clips and every image are identical. That includes the 4×4 glow burn map, which `embed_burn.py` now
writes itself. Only the 40 body/head skin materials (five tiers × four LODs) changed their ramps. Burn maps: 17, smallest
4×4. The six weapon/kit exports needed no re-finish (content-identical splits; files unchanged). `validate_finish.py`
passes, with 0 inverted closed parts in all eight exports and the five viewer GLBs. Final gates **PASS 8,754 / INFO 160**:
they differ from the archived 08:41 run only by the Maul's LOD3, removed after it. Far gates **PASS 1,727 / INFO 62**,
unchanged. `run_creature_review.py check` passes for every tier and clip (35 switches each, no console errors).

## Returned weapons

| Weapon | Meshy triangles | Fitted triangles | Current attachment |
|---|---:|---:|---|
| Pulse pistol | 3,056 | 1,800 | `export/overseer_pulse_pistol.glb` |
| Collar-control staff | 3,013 | 1,600 | `export/overseer_collar_rod.glb` |
| Arc Maul | 3,173 | 2,449 | `export/overseer_arc_maul.glb` |

The heads and silhouettes come from the integrator's Meshy returns. The pistol handle was widened to the retained
claws; both long weapons share a fitted circular grasp. Maul grip facets were subdivided locally after reduction
so triangle interiors follow the round handle rather than cutting through the palm. UVs and painted appearance
are retained through fitting. Staff/Maul heads are turned toward the measured strike direction.

`work/equipment_meshy.blend` contains the fitted painted equipment. `work/equipment.blend` and the old
`work/*_lod0.glb` weapon stand-ins are historical inputs only; the old blend still supplies the armour material and
retained hip saber/key. The viewer and gate configuration use the new attachments.

Five exact-mesh orthographic guides per weapon supplied Codex paint views. The bake combines base colour,
metallic/roughness, restrained normal detail and region masks. The neutral ceramic, brass, leather and energy regions
share `textures/overseer_ramps.json` across all tiers. Court metal/glow is gilded. Emission uses factors on modeled
cell faces; **no emissive textures**. Browser-only models bake the tier ramps because three.js lacks the engine's
region-ramp support; runtime exports retain the shared textures and `KHR_materials_variants`.

[Paint provenance](textures/weapons/generation_runs.json) retains prompts and image hashes.
[Post-return record](meshy/post_return.json) records reduction, fitted transforms, maps and returned hashes.
Foreground-box registration corrected generated-view framing; raw scale corrections sometimes exceed 5% and are
recorded in `textures/weapons/*/registration.json`. Projection covers 54.4% / 80.3% / 83.8% of pistol/staff/Maul
UV texels respectively; unseen interiors receive darkened nearest-supported colour. Offline CPU renders were
inspected; the current viewer appearance was accepted by the user on 2026-10-24. In-game rendering remains unverified.

## Hands and motion

The retained six claws per hand now use connectivity-derived finger ownership and measured chains. Distal palm
weights no longer follow the forearm. The pistol fit uses small finger bends, a trigger target and a 2.5 mm collision field of the complete weapon.
Fitting checks vertices, edges and triangle interiors against the handle and housing;
actual exported-surface gates remain authoritative. Skin transitions across the armpit and elbow were smoothed,
with four normalized weights per vertex. Original body bind geometry is retained.

Arm motion comes from local `anim_library/humanoid_set/1Hand.glb` and `Armed.glb`, fitted to the retained limb
lengths with elbow-plane selection, wrist limits, distributed twists and smooth recovery. Wings and legs retain
native flying-demon motion. No paid animations were used. The clips are Flight, AttackRanged, AttackMelee, Cast,
Hit, Death and Dead, all prefixed `Overseer_`. All five rows fly, so grounded walk/run checks are inapplicable.

- Flight keeps the pistol lowered (maximum vertical muzzle component -0.778).
- AttackRanged uses the fitted local-library aim with flight-clavicle sway compensation, a 10° upward wrist recoil,
  and quintic raise/lower envelopes baked at 48 Hz. The old source clip's large whole-arm kick is removed.
  Aim holds at 0.35–0.45 s; fire 0.45 s; recoil peak 0.53 s; aim recovered 0.73 s; lower 0.85–1.2 s.
  Actual GLB interpolation at 192 Hz measures **0.062° aim drift**, **9.92° recoil** and
  **17.35 mm** grip travel relative to the shoulder during the firing window.
  [Playback](review/ranged_motion.gif), [pose strip](review/ranged_motion_sheet.png),
  [grip side](review/pistol_grip_side.png), [opposite side](review/pistol_grip_other.png).
- Melee lasts about 2.4 seconds: overhead wind-up, downward smash, then recovery with the staff clear of the body.
  The right hand reaches 0.099 m above the head and the staff head drops 1.11 m after its peak.
- Target-directed contact times: staff **0.864583 s**, Maul **0.843750 s**. Preserve these per-prop timings in future
  bindings; the fastest vertical head movement occurs later in the follow-through.
- Krav's hip saber and Ghulkat's belt key/holstered pistol have short leather belt hangers and their own body-contact checks on every clip.

[Motion probes](review/feedback_motion.json), [source inventory](work/action_sources.json),
[shared gates](review/gates_candidate/gates.md) and [handoff validation](review/feedback_validation.json) retain evidence.
Worst grip gap is **2.95 mm** (3 mm limit); sampled grip penetration is **1.01 mm** (3 mm limit).
Worst prop/body penetration is **0.000 mm** (2 mm limit); arm stretch p99 is
**1.800×** (2× limit). The existing wrist-flexion configuration is 60°;
other joint/contact limits remain unchanged (the fitted LOD ratio exception is documented below). Gates cover seven prop configurations and all seven exported clips.
The user accepted the corrected grip and base motion on 2026-10-24 and requested stronger firing recoil.
The kick was doubled from 5° to 10° and accepted by the user ("ok good accepted"). [Revision checks](review/recoil_revision.json) confirm identical geometry,
skin and grip, and identical poses outside the recoil window; all other clips are unchanged.

## Final geometry and checks

| Row | Viewer variant | Scale | Visible LOD0 triangles |
|---|---|---:|---:|
| 10030 Overseer | ov_a | 1.0 | 13,782 |
| 10031 Overseer Prime | ov_b | 1.1 | 13,782 |
| 10032 Court Overseer | ov_c | 1.15 | 13,782 |
| 10102 Overseer Krav | ov_krav | 1.3 | 14,230 |
| 10103 Overseer Ghulkat | ov_ghulkat | 1.3 | 14,903 |

Scales follow `data/make_monster_tables.py`. Body/shell/sash: 10,382 triangles; retained saber/key with belt hangers: 448/260; holster hanger: 12.
The 16,951-triangle authoring export contains mutually exclusive gear; no live loadout exceeds 15k.
[Validation](review/finish_validation.json) records final hashes, triangle counts, skin/animation parity, UVs,
normal winding and variant/binding checks. All eight exports have zero inverted closed parts or degenerate triangles.

| Model / loadout | LOD0 | LOD1 | LOD2 | Far level |
|---|---:|---:|---:|---:|
| Body + shell + sash | 10,382 | 8,103 | 5,686 | 4,334 |
| A / B / C equipped | 13,782 | 10,650 | 7,545 | 6,033 |
| Krav equipped | 14,230 | 10,902 | 7,687 | 6,119 |
| Ghulkat equipped | 14,903 | 11,402 | 8,130 | 6,692 |
| Pulse pistol | 1,800 | 1,309 | 937 | 851 |
| Collar staff | 1,600 | 1,238 | 922 | 848 |
| Arc Maul | 2,449 | 1,718 | 1,235 | retain LOD2 |
| Hip saber + hanger | 448 | 252 | 142 | 86 |
| Collar key / holster hanger | 260 / 12 | retain | retain | retain |

LOD fitting retains the arm/hand deformation surfaces, sash and weapon contact geometry. Initial uniform
collapse loosened the grips and made the sash non-manifold; those candidates were rejected. The Maul's fourth
level missed the silhouette gate; the 260-triangle key lost its loop under reduction. Both retain their last
useful geometry. This follows the integrator's explicit “fit the LODs, not 50 % ratios” instruction. The numeric
ratio caps are .8/.6/.55 instead of the shared runner's .55/.25/.10; **all joint, contact and deformation limits
are unchanged**. Fitted shadows use the matching colour geometry under separate mesh indices, preserving the
wing membranes, grip contacts and cloth regions. This is denser than the generic shadow merge/reduction route.

The shared MeshLab/xatlas repair functions provide new UVs and baked base/normal/MR/region maps per reduced level,
including RGBA mask channels. [Switch scores](review/lods/scores.tsv) pass in three views at 450/180/72 pixels;
colour LOD0 is unchanged. Worst final arm stretch p99 is 1.806×; grip gap 2.946 mm, penetration 1.013 mm,
prop/body penetration 0, sash penetration 0.812 mm, all within the existing limits.
[Full-chain gates](review/gates_final/gates.md) cover the candidate including the discarded Maul LOD3;
[final far-selection gates](review/gates_far_final/gates.md) verify every clip after retaining Maul LOD2 at distance.
All other runtime geometry is identical between those audits, as recorded by the export validation.

Bindings use the source DemonFly scale 130 times the design scale. Ranged release is at the pistol muzzle at
0.45 s; Ghulkat's ranged collar pulse releases from the Arc Maul during its strike, with the pistol still holstered.
Every caster has `animation.cast`; native burn-away is bound for Death/Dead. Collision sizes, tactics and unrelated
stage rows are unchanged. All changes go through `hesper_stage/monsters.yml`, never installed assets_dev models.

## Reusing the winged Kreegan body (Nobles)

**Published:** `export/hes_kreegan_winged.glb`, mesh node `OV_Assembled`, four colour/shadow levels:
**8,846 / 6,930 / 4,718 / 3,480 triangles**. This is the accepted flying demon's skin, head, native ivory horns,
claws, feet and wings. Plates, belt, sash and weapon geometry are absent at every level. **No tail and no
transplanted ground-Demon harness.** Do not add either when building Nobles.

Reuse the body, head/horns, UVs, shared PBR maps, skin weights, source-frame rest transforms and bone names.
Copy the export into the Nobles project; keep this project and the installed MM6 source unchanged. Its burn
maps now cover every tier and LOD; preserve `extras.openyamm_burn_map` when copying/compacting, and add maps to
any new skinned materials. A runtime burn model also needs the cook's `_BURN_ORDER` attribute. The inherited
body/head maps are identical to the Overseer maps. Add the
Nobles' own skinned shell, crest, cloth, weapons, rank ramps and design scales. Refit their hand poses to their
own weapons and run the shared gates; the included closed grips are specifically fitted to Overseer equipment.

| Rig region | Names / contract |
|---|---|
| Root and trunk | `Rig`, `B_Pelvis`, `B_Spine`, `B_Spine1`, `B_Spine2`, `B_Neck`, `B_Head` |
| Arms | `B_L_*` / `B_R_*`: `Clavicle`, `UpperArm`, `Forearm`, `Hand`; `UpperArmTwist` and `ForearmTwist` helpers retain their current weights |
| Hands | Six three-bone claws per hand: `Finger0` (thumb) through `Finger5`; descendants normally suffix `1`, `2`. The right thumb's exact descendants are `B_R_Finger0.001` and `B_R_Finger0.002`; do not silently rename them |
| Legs | `B_L_*` / `B_R_*`: `Thigh`, `Calf`, `Foot`, `Toe0` |
| Wings | `B_Wing_L_*` / `B_Wing_R_*`: `Root`, `Arm`, `Finger1`, `Finger2`, `Finger3`, `Lead` |
| Overseer-only sockets retained for rig compatibility | `PulsePistol`, `CollarRod`, `ArcMaul`, `HipSaber`, `CollarKey`, `HolsterPistol`, `Socket_Muzzle`, `Socket_Rod`, `Socket_Maul`; no attached meshes in the shared export |

The 83-joint rig retains seven clips: `Overseer_Flight`, `Overseer_AttackRanged`, `Overseer_AttackMelee`,
`Overseer_Cast`, `Overseer_Hit`, `Overseer_Death`, `Overseer_Dead`. Flight supplies standing/walking/running;
Death/Dead are authored for the source demon's burn-away. The source units and facing are unchanged:
Blender −Y / glTF +Z, 1 unit = 1 metre; Overseer base binding scale 130, yaw offset −π/2. Nobles use their
own design scale and action/loadout bindings; do not inherit the Overseers' gun/rod roles automatically.

In this shared body, five `KHR_materials_variants` share one texture set per LOD: `ov_a` violet, `ov_b` plum, `ov_c` red-violet,
`ov_krav` A-derived and `ov_ghulkat` B-derived. Skin lives in mask R; horns, claws and wing membranes preserve
their native colours. Nobles should author their own named ramps from these masks rather than bake tier colours.
The head and body remain separate materials: their luminance ranges differ and the wing material is double-sided;
the common head-atlas merger correctly refuses that combination. This is an intentional runtime material exception.

The Overseer caste export is `export/hes_overseer.glb` (same rig/clips plus skinned plates, belt and rank sash).
Its six external attachment exports contain the accepted Meshy pistol/staff/Maul plus hip saber, collar key and
holster hanger. These caste pieces are not part of the shared anatomy.

## Meshy jobs for the integrator

All three jobs in [job_manifest.json](meshy/job_manifest.json) **SUCCEEDED on backup**, five credits each:
`overseer_pulse_pistol_smart_v1`, `overseer_collar_staff_smart_v1`, `overseer_arc_maul_smart_v1`.
**15 credits spent; no additional jobs, retries or paid retextures requested.** Ready-to-submit is false for each.
Canonical receipts remain in `creature_3d_progress.json`; original returns remain under `meshy/<job>/`.
No Meshy API/tool was called from this sandbox. Job provenance and processing records are complete.

## Reproduction

Use the project lease and `tools/creature_workspace.py run` for every mutation. Current build order:

1. `inspect_bind.py` → `build_base_rig.py` → `fit_hands.py` (retained source and fitted hands).
2. `weapon_texture.py` prep → retained/generated paint views → bake; then `fit_weapons.py`.
3. After the initial attachment split, Blender `weapon_collision.py`; host `fit_meshy_grips.py` (`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`).
4. `build_armour.py` → `prepare_actions.py` → `correct_actions.py` → `assemble.py` → `export_preview.py`.
5. Host `materials_preview.py` (burn maps embedded before tier variants); Blender `probe_feedback_result.py` and `run_preview_gates.py`.
6. Blender `render_weapons.py`, `render_grips.py`, `render_feedback.py`; host `viewer_tiers.py`, `validate_handoff.py`.
7. `finish_lods.py <stem> <ratios>` with a Python containing pymeshlab/xatlas/numpy/scipy/Pillow: body `.55,.30,.16`,
   pistol/staff `.55,.30,.24`, Maul/saber `.55,.30,.16`; key/hanger kept. Uses the shared Kept/lod_repair functions.
   Body exports finish with `embed_burn.py`, baking again for each final UV layout. Head/wing-finger ignition uses
   the shared surface-distance baker; tiny glow strips with one UV burn uniformly at order 128/255. The sash retains
   its original repeating UVs. All five tier materials of a primitive share its map.
8. `publish_shared.py` strips caste geometry at every level and writes the five binding entries;
   `validate_finish.py` verifies runtime exports; the shared compactor preserves burn texture references. `lod_split.py`, `render_lods.py`, `lod_score.py` audit switch images.
9. `run_final_gates.py` through `blender_entry.py` (400-second timeout); `run_far_gates.py` uses the selected far
   review GLBs/config. The latter was needed after retaining the Maul's passing LOD2.
10. Stage under the BUILDER_GUIDE locks; `validate_burn.py` checks the cooked models against the retained
    `work/before_burn_20261024/` baseline. Run `rebuild_all.sh --scenarios-only`, then `scripts/desktop_smoke.py`
    inside the project lease on a host with a working desktop. It takes the engine/stage locks for each map.

Blender entry example (inside the lease guard):

```sh
timeout -k 5s 300s /snap/blender/current/blender --background --factory-startup --disable-autoexec -noaudio \
  --threads 4 --python level_generation/creatures/hes_overseer_codex/scripts/blender_entry.py -- \
  level_generation/creatures/hes_overseer_codex/scripts/assemble.py
```

The local entry avoids the sandbox's audio-shutdown hang. `refine_grips.py` is superseded by the full-surface Meshy
fitter. Historical feedback/weapon checkpoints remain in `work/before_feedback_20261023/` and
`work/before_meshy_weapons_20261023/`. The integrator owns browser captures via `tools/run_creature_review.py`.

Desktop retry (from repository root, inside a fresh project lease):
`python3 level_generation/creatures/hes_overseer_codex/scripts/desktop_smoke.py`.
It discovers the placing maps, launches each minimized through `run_game.sh`, uses the engine/stage locks and
records the exact private run folders. Current nine attempts all failed before graphical map load with
`SDL_Init failed: No available video device`; they do not certify zero actor-model load errors.
