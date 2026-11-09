# Hesper Lancers and the Forgemaster

**Build complete. Lancers A–C, Forgemaster art and the corrected slam are accepted by the integrator.**
Acceptance: “the Forgemaster's slam (2026-10-24)” in
[requests/P2.md](../../../design/kreegan_world/WORK_PACKAGES/requests/P2.md).
The user retains the last word on the slam's weight; in-game capture follows in D8's next integrator capture round.
No build work remains unless the user requests more. Keep the numeric slam gate.

The Forge now has a recessed orange-core Thunder Maul, broad articulated hull plates from chest to knees,
front and rear, three overlapping shoulder lames per side, heavier forearms/shins and orange seams.
The black banded haft has gold collars; ivory plates carry rust, painted rivets and normal-map relief.
The rear apron divides around the required native tail. Its rigid panels use the Harrower strip simulation,
then measured hinge/contact fitting; they do not stretch like rubber. The broad strapped bib replaces the small
old chest underplate. Skin under removed plates is restored; the original concealed chest ornament stays culled.

## Heavy maul animation

The accepted RPG `2HandAxeAttack1` windup is retained. Its missing downward segment is replaced by an explicit
maul trajectory, with both hands fitted to the haft, a forward torso drive, dropped knees, planted feet and tail
clearance. The apron and shoulder hinges are fitted to the new Attack. Geometry and weights are unchanged.
The named local Mixamo downward / RPG axe-air / sword-air alternatives were probed; no Meshy job was needed.

The attack lasts **3.5 seconds**: **impact 1.75 s**, **0.25 s weight hold**, then **1.5 s recovery** to the accepted
guard. Melee and ranged event bindings use the measured impact; Cast remains **0.87 s**. Both hands remain on the
shaft. The runtime hold moves the head only 2 mm; the final arm/hand/maul pose matches the accepted guard within
0.22° and 0.02 mm. The largest attack twist step is **9.93° per 60 Hz sample**, below the existing 15° limit.
See `review/forge_heavy_attack_selection.json`, `forge_slam_fit.json`, `forge_slam_skin_fit.json` and
`forge_runtime_twist_continuity.json`.

The new numeric slam gate is included in the **nine-role report** and independently checked on the runtime GLBs.
At impact, the head centre is **0.380 m high**, below both wrists (**1.012 / 1.177 m**) and both knees
(**0.503 / 0.421 m**), **1.593 m in front of the pelvis**. Its lowest surface is **1.61 cm above the floor**.
The head reaches its lowest point **exactly at impact**. See `forge_slam_gate.json` and `forge_slam_runtime_gate.json`.

## Preserved source and bindings

The read-only source is `../hes_kreegan_claude/export/hes_kreegan.glb`, SHA-256
`38cc3345adbebe78ee535f2430886ee52899270951767a938ede58094eafbc11` (2026-10-24 tier colours: only its skin ramps
changed; geometry, skin, clips and images are identical to the earlier `7057137f…`).
The Forge author's body geometry and named weights are exactly unchanged from the previous master
(`review/forge_concept_preservation.json`). Native tail, sculpted harness, skeleton names and source Demon/Carbine
clips remain. All nine Forge roles remain; Attack alone changes. The other eight roles are byte-identical in the raw export.
The thick rear hull has 4 cm of settling allowance during Death; the final runtime solver grounds the corpse.

`integration/actors.yml` binds rows **10020–10022 and 10110**. Lancer scale remains `104.8623316`, Forge
`157.2934974` (×1.5). Stage height/radius stay **327/60** for the Forge; tactics and other gameplay data are unchanged.
Lancers retain their two-hand ready idle, armour, twin-barrel B and gilded/grafted C. Their four runtime export
hashes match the accepted 2026-10-24 files. Optional lance-coil colour polish was not applied.

## Runtime assets

Triangle counts exclude shadows:

| File | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| `hes_lancer.glb` | 10,466 | 5,156 | 4,499 | 2,268 |
| `hes_ion_lance.glb` | 604 | 388 | 140 | 61 |
| `hes_ion_lance_twin.glb` | 992 | 610 | 223 | 111 |
| `hes_lancer_graft.glb` | 132 | 132 | 132 | 132 |
| `hes_forgemaster.glb` | 11,453 | 5,443 | 4,710 | 2,525 |
| `hes_thunder_maul.glb` | 2,456 | 1,482 | 542 | 126 |

Assembled Forge LOD0 is **13,909 triangles**, below the 15k ceiling. The maul's near LOD retains bevel/frame
boundaries. Body LOD2 is denser than successive halving to preserve horns and the layered armour silhouette.
The prescribed repair ladder first passes at **.45/.25**: LOD2 outline/colour **5.3%/11.3**, LOD3 **9.0%/10.9**.
Thresholds are unchanged. See `work/lodrep_hes_forgemaster/result.json` and its rendered audits.

The release/twist fixes and the new slam change animation channels only. `forge_slam_lod_equivalence.json`
proves that only 291 Attack channels changed in this revision. `forge_release_lod_equivalence.json` and
`forge_twist_lod_equivalence.json` prove identical geometry, weights, UVs, materials, texture bytes, nodes and
Standing samples, so those LOD audits remain valid. The resulting near/far arrays and all animation samples match,
except the four documented Death/Dead pelvis/maul translation channels used by the runtime floor solver.

The Forge has its own **2K base / 1K normal, metallic-roughness and region-mask** shell maps in
`textures/forge_armour_*`, plus `forge_ramps.json`. Body maps and region ramps remain shared. Tiers use
`KHR_materials_variants`; orange emission is `emissiveFactor [1, .20, .015]`, with a dark base and no emissive texture.
Review GLBs bake region colours only for the local three.js viewer. No raw animation-library clips are distributed.

## Verification and review

All **nine authoring roles** pass the complete arm/hand, shell-stretch/leak, armour-contact, head and floor gates.
Maxima: arm p99 **2.0435×**, hand **4.1517×**, wrist **59°**, shell p99/max **1.028×/1.029×**, armour contact **0.29 cm**
(limit 0.30 cm). `review/forge_gate_acceptance.json` binds these reports to `work/forge_complete.blend`.
The G6 sweep uses half-frame samples; apron edges remain rigid to within 0.019%.

Final runtime validation passes finite values, four normalized weights, key ordering, sockets, clip sets,
shared tier textures, reduced skin stretch and equipped floor bounds between keys. All nine Forge roles have
**zero exported maul/body-shell intersections at 60 Hz**, excluding intentional grip surfaces. The held Dead pose
matches the end of Death. Winding is **0 inverted closed parts** across all runtime/raw/viewer GLBs; attachment
atlas checks pass. Evidence is in `review/runtime_validation.json`, `runtime_equipment_contacts.json`,
`forge_far_preservation.json`, `forge_floor_runtime.json`, `lod_atlas_check.json` and `winding.txt`.

Restaged successfully; only the Forgemaster body/shell GLB was recooked. All six cooked source hashes match the
exports (`review/staging_strike.json`). The prescribed **`rebuild_all.sh --scenarios-only` passed 93/93**, exit 0,
under shared stage/engine locks; logs: `output/hesper_stage/logs/scenarios_085959_5`.

The integrator accepted the previous **D8 desktop smoke** and requested no repeat for this animation-only change.
Its original evidence remains in `review/desktop_concept_20261024/`. New in-game capture belongs to the integrator.

The viewer is ready at `review/viewer/index.html`: **3 × 8 Lancer clips + 9 Forge clips**. Static checks pass hashes,
durations, imports and JavaScript syntax (`review/viewer_static_validation.json`). The integrator accepted
viewer playback from 0.3–3.2 s: high windup, over the top, floor impact at 1.75 s, hold and slow lift
([review frames](review/integrator_slam_20261024.jpg)). User acceptance of the final weight is not yet recorded.
Offline poses under
`review/forge_concept_Forge_Attack_52.5_side.png`, `forge_concept_Forge_Attack_52.5_quarter.png` and
`forge_concept_Forge_Attack_84_side.png` show the final impact and recovery; their skin/harness uses authoring
materials, while the viewer/native capture uses the runtime region colours.

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_lancer_codex --tier forgemaster check
python3 tools/run_creature_review.py --project level_generation/creatures/hes_lancer_codex --tier forgemaster --token <lease> playback
```

## Tier colours (2026-10-24)

The user gave each Kreegan caste its own skins (design `MONSTERS.md`, "Kreegan skin colours"). `scripts/tier_ramps_lancer.py`
rewrites only the skin ramp (mask R) in `lancer_ramps.json` and `forge_ramps.json` from `claude_shared/kreegan_skin.py`:
lancer_a **bronze olive** `#7d7240`, lancer_b **teal** `#3f7a78`, lancer_c **charcoal** `#3a3433`, Forgemaster
**soot** `#2e2a28` (sRGB at 70 % of the ramp; the two dark skins lift their highlights). Harness, plate, gold and
glow ramps and emission are unchanged; the Forgemaster keeps its forge-orange glow `[1, .20, .015]`.

Re-run: `runtime.py variants` (Lancer, twin) from the existing `work/*_lods.glb`; the Forge's `prepare` and
`build_near_lods.py` from the post-slam `export/hes_forgemaster_lod0.glb` (the old `work/hes_forgemaster_lods.glb`
predated the slam), then `variants`; far LODs by `lodrep/repair_glb.py` at the accepted steps
(`LODREP_LADDER=0.47:0.25` Lancer, `0.45:0.25` Forge; the lower Forge steps failed on LOD2 outline, which ramps do
not change) in `work/lodrep_tiercol_*`, with identical scores (Lancer LOD2/3 4.6/8.8, 9.2/9.7; Forge 5.3/11.3,
9.0/10.9); `runtime.py finish`, `bindings.py` (unchanged), both equipment gates (reports byte-identical) and
`finish_lancer_runtime_checks.py` (slam gate, runtime validation, atlas check, viewer, winding: all pass, 0 inverted).
Every export keeps its geometry, skins, nodes, clips and images; only skin ramps changed. `hes_lancer`, the ion
lance and the twin also pick up the current forge-orange glow of their unused `forgemaster` variant (they predated
`glow_variants.py`'s 10-24 change). Graft and maul are byte-identical. `forge_slam_runtime_gate.py` now accepts
those three files when their meshes, indices and clips equal the strike baseline. Previous exports, viewer and
review JSON: `work/before_tiercolours_20261024/`.

## Rebuild from the measured master

Use a project lease with `tools/creature_workspace.py`; Blender scripts run through
`tools/run_creature_blender.sh --token <lease> <full project script path>`. Other writers run through
`creature_workspace.py run --project <project> --token <lease> -- ...`.

- Current Forge master: **`work/forge_complete.blend`**. The accepted pre-strike master, exports, reports and LOD
  inputs are archived in `work/before_strike_20261024/`. The animation driver is `forge_slam.py`, followed by
  `forge_slam_skin.py`. Seed `forge_contact_fit.blend` from that result and fit Attack with `forge_contact_fit.py`
  (`--resume Attack`, then `--smooth Attack`); the selected result is copied to `forge_final_clearance.blend`.
  `forge_revision_gates.py` runs all nine roles and adds the physical slam gate before `finish_forge.py` accepts it.
- For this animation-only revision, `forge_slam_rebase.py` proves raw geometry/material/other-animation equality
  against the archived baseline and transfers only Attack into the existing near/far GLBs. It requires those
  original LOD inputs and deliberately rejects a second application. The far geometry audits remain valid.
- `finish_forge.py` asserts all nine gate reports and exports the master at 60 Hz. Alternatively export an already
  accepted master with `export_lancer.py <absolute master> forge`. Run `runtime.py prepare hes_forgemaster`, Blender
  `build_near_lods.py hes_forgemaster`, then `runtime.py variants hes_forgemaster`.
- Far repair: archive a previous `work/lodrep_hes_forgemaster` when source geometry changes. Run
  `MODEL=hes_forgemaster python3 scripts/repair_lancer.py build <r2> <r3>`, Blender
  `lodrep/lod_render.py <absolute audit directory> installed,<step>`, then `repair_lancer.py score` with the same
  MODEL. Use the prescribed ladder and stop at the first pass; never reuse success for changed geometry.
- Finish with `runtime.py finish hes_forgemaster`, `bindings.py`, Blender
  `runtime_equipment_gate.py hes_forgemaster` (copy its result to `review/runtime_equipment_contacts_forge_review.json`), and
  `finish_lancer_runtime_checks.py`. The latter also rebuilds and statically checks the viewer.
- Lancer master remains `work/lancer_complete.blend`, with `finish_cuirass_outline.py` as its revision driver.
  Do not rerun Lancer export stages for a Forge-only change.
- Re-read the stage manifest, run `stage.py` under its exclusive lock, then `rebuild_all.sh --scenarios-only`.
  Native runs use `tools/run_game.sh`, holding shared stage/engine locks; no full map rebuild is needed.

## Meshy jobs for the integrator

**None. Cap 0, spent 0.** All geometry and animation fitting is local. No jobs are submitted or queued.
No engine/Vulkan work, source-project edits, `assets_dev` installation or git staging.
