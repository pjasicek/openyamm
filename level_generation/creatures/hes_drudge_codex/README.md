# Hesper Drudges — accepted and complete

Built under [CREATURE_BUILDS](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md) and the
**Integrator answer to the Drudge builder (2026-10-23, openyamm-30)** in
[P1](../../../design/kreegan_world/WORK_PACKAGES/requests/P1.md).
The ruling resolves the earlier source/concept conflict: **retain the shared tail and sculpted harness**.
The harness mask's G channel now uses skin ramps, 15% darker in linear colour than the matching skin ramp.

**Complete and accepted on 2026-10-24**, per
[Integrator answer: Drudges, playback and in game](../../../design/kreegan_world/WORK_PACKAGES/requests/P1.md#integrator-answer-drudges-playback-and-in-game-2026-10-24).
The integrator checked A's Standing, Attack, Running and Death plus every tier (Brute, Hulk, Hatchling, Thrix).
D3, D5, D8 and D9 captures confirm they load and draw with **0 "Actor model load failed"**.
The user-approved chest-slab gap is retained. The earlier scenario failures were intermittent; later sweeps pass.
D15 step 87 is tracked by the separate **Actor sizes** job. No Drudge build work remains.

## Tier colours (2026-10-24)

The user decided that castes and tiers stop sharing one skin. `build_drudges.py` now recolours the skin with
`../claude_shared/kreegan_skin.py` instead of copying the Trooper ramps: A clay, B (Brute) ash grey, C (Hulk) rust,
the Hatchling with A; every tier takes the Trooper A ramp's luminance spread, and the harness stays 15 % darker than
the skin. Thrix's baked skin is pale grey-pink (`BOSS['thrix']`). `rebuild.sh` reran in full (exit 0): every export
has the same geometry, skin, clips and nodes as before, with only the ramps changed (Thrix's baked textures change
too). Gates and verification pass as before, winding 0, viewer 5 models x 22 clips. The only console messages are
404s for `undefined`: the shared viewer asks for clip source images this manifest never had, as before.
Sheet: `review/tier_colours_20261024.jpg`; the previous exports are in `work/before_tiercolours_20261024/`.

## Deliverables

| Row | Binding | Appearance | Relative scale | LOD0 triangles, including additions |
|---|---|---|---:|---:|
| 10000 | Drudge A | Bare violet worker, digging claws | 1.0 | 9,408 |
| 10001 | Drudge Brute | Plum worker; one chipped ivory scrap shoulder with a gold remnant and resin fixing | 1.15 | 9,492 |
| 10002 | Drudge Hulk | Deep red-violet; shoulder plus broken chest slab, dim orange join | 1.3 | 9,600 |
| 10003 | Hatchling | Same young caste body at reduced scale | 0.8 | 9,408 |
| 10263 | Thrix | Untinted grey-violet skin, pale healed graft sockets, short torn umber scarf | 1.0 | 9,492 |

Runtime files: `export/hes_drudge.glb`, `hes_thrix.glb`, `hes_drudge_shoulder.glb`,
`hes_drudge_slabs.glb`, `hes_drudge_scarf.glb`; bindings in [integration/actors.yml](integration/actors.yml).
The body scale is the existing MM6 Demon/Kreegan scale, 104.8623316, multiplied by the table above.
Existing stage picture slots, collision dimensions, tactics and gameplay rows were preserved.
The Hatchling retains the encounter's `hes_brood A` picture slot; Thrix resolves to `hes_thrix`.

The final Hulk assembly is editable in `export/hes_drudge.blend`, with all 22 actions and its two rigid additions.
The scripts are the authoritative sources for every tier, Thrix's detail texture and the rigid geometry.
`work/motion.blend` preserves the fitted motion authoring state.

## Shared-body invariants and art sources

Mandatory source: `../hes_kreegan_claude/export/hes_kreegan.glb`, SHA-256
`38cc3345adbebe78ee535f2430886ee52899270951767a938ede58094eafbc11` (2026-10-24 tier colours: only its skin ramps
changed; geometry, skin, clips and images are identical to the earlier `7057137f…`).
**All LOD0 positions, normals, UVs, weights, indices, 80 joints, bind transforms and the 18 inherited
Carbine_*/Demon_* animations are unchanged**, checked by [scripts/verify.py](scripts/verify.py).
No shared Kreegan project or installed MM6 asset was modified. Its previously reduced 9,408-triangle stopping
point is retained under the frozen-body ruling; no caste-specific body reduction or rebuilding was introduced.

Approved input: [family](../../../design/kreegan_world/concepts/monsters/fam_drudges.png),
[Hatchling/Thrix](../../../design/kreegan_world/concepts/monsters/drudge_extras.png),
[brief](../../../design/kreegan_world/concepts/monsters/CODEX_BRIEF_DRUDGES.md), overridden only by the explicit
body ruling. The existing Kreegan paint/normal/roughness maps remain shared. Hostile tiers use
`KHR_materials_variants` names **hsd_a / hsd_b / hsd_c**, one texture set and mask per LOD; no baked tier colours.
Thrix has a distinct healed-scar albedo pattern and **no variants, region ramps or binding skin override**.
His skin detail does not cut or rebuild the body. The additions have a shared neutral wear/normal/ORM set,
with material factors for ivory, old gold, resin and cloth. Eyes are dim blue; the Hulk's join uses orange
`emissiveFactor`. No emissive textures. The three tiny rigid additions are 84 / 108 / 84 triangles; they
skip further LODs under modelling-guidelines section 7 (already simple), with hard edges on UV seams.

## Motion and measured gates

All inherited clips were sampled at **60 Hz** (half frames). Four fitted local clips were appended:

- **Drudge_Walking:** inherited Demon_Walking, arms spread 14 degrees to clear the thighs, native open claws.
- **Drudge_Running:** local library `mx/standard_run_f8c60f` (Mixamo Standard Run), retargeted with the shared
  source-frame rig route; `run_fit.py` preserves sampled ankle paths, knee planes, heel kick and toe-off.
  No paid action and no synthetic foot trajectory. Final measured binding strides: walk **1.2469 m**, run
  **1.1026 m**; the run cycle is **0.7333 s**.
- **Drudge_Death / Drudge_Dead:** the shared falling death with open claws, clearance correction and a matching
  held corpse. The inherited Demon death remains upright when its old burn effect is absent, so it is retained
  but unbound. The fitted falling death also limits the left wrist twist to 85 degrees.

The original 18 clips remain available. The runtime binds Standing/Attack/Hit/Fidget from Demon_* and the four
fitted clips above. Root floor correction samples the actual exported GLB at **120 Hz**, preserving airborne
phases. Neither inherited movement source appears in `head_bob_claude/jobs.txt`; no head-bob reapplication applies.

Final bound-clip evidence: [validation.json](review/validation.json), [gates_final.json](review/gates_final.json),
[gates_initial.json](review/gates_initial.json), [motion corrections](review/final_motion_corrections.json).
Across the eight bound clips: arm edge stretch p99 **<= 1.966**, hand edge stretch **<= 2.225**,
wrist swing **<= 50.45 degrees**, wrist twist **within +/-85 degrees**; sampled hand-to-body penetration **0**.
New clips' body minimum is **0.003 m**; inherited bound clips stay about **0.0043–0.0046 m** above the floor.
The tightest sampled addition-to-head vertex clearance is **0.00678 m**, during the falling death; no weapon
blades apply. This numeric nearest-point check supplements, and does not replace, the integrator's visual review.
Pelvis step and sole/stride measurements are retained per clip in the JSON. The shared 48-fps angular
step/second-difference probe was also run on all 22 final clips: [jerk measurements](review/jerk_48fps.json).
Fitted walk/run loops close within 0.05 degrees; maximum per-frame angular steps are 12.61 / 20.84 degrees.
These smoothness measurements carry no invented pass threshold; the integrator accepted playback on 2026-10-24.

**Unbound inherited warnings are retained honestly:** Carbine_Attack/Fidget/Death, Demon_Cast_FireBolt and
Demon_Walking have measured contact warnings; Carbine_Running, Demon_Running and Demon_Walk_Native have floor
penetration. The original Carbine death has a large left wrist-twist excursion. These clips are not runtime
bindings for this family; the viewer labels inherited clips as unbound. The shared source was not changed.

## LOD and geometry validation

The local `lodrep/` is the worked Kreegan project's explicit-path adaptation of
`../lod_repair_claude/scripts/repair.py`: same MeshLab collapse, xatlas unwrap, texture transfer, shadow rebuild,
ratio ladder and calibrated switch gates. Before rebuilding, old far baked material references are replaced
with LOD0 source materials; LOD0 and LOD1 geometry stay unchanged. Local changes to the audit launcher only
select the installed Blender binary and exit after background work (this host hangs during PulseAudio shutdown).

Both bodies chose **r30_16**: LOD0/1/2/3 **9,408 / 4,684 / 2,788 / 1,482 triangles**, plus matching shadow LODs.
The smaller r25_12 candidate failed the LOD3 outline gate and was rejected.

| Body | LOD2 outline / colour | LOD3 outline / colour | Result |
|---|---|---|---|
| Drudge | 4.0% / 11.6 | 10.1% / 10.9 | Pass |
| Thrix | 4.0% / 11.4 | 10.1% / 10.8 | Pass |

Full route results and calibration frames: `work/lod_drudge/result.json`, `work/lod_thrix/result.json` and their
`audit_r30_16/` folders. These are offline LOD calibration renders, not final viewer/game acceptance captures.
[Winding log](review/winding.log): **0 inverted closed parts in all five runtime GLBs**. The mandatory body retains
its original double-sided materials; the added closed pieces are single-sided and included in the signed-volume check.
Buffer ranges, finite positions, index bounds, source invariants, variants, clips, attachment nodes and viewer hashes
all pass the focused verification script. No renderer or engine tests/build were added.

## Stage and completed review

Exactly **10000, 10001, 10002, 10003 and 10263** now point to this project's bindings in the shared stage list.
Only their bindings and five required model registrations were changed; a semantic comparison checked every other
row and every other field. Locked staging succeeded: five new model GLBs cooked. [Stage log](review/stage.log).
The historical builder `rebuild_all.sh --scenarios-only` sweep finished: **68 PASS, 2 FAIL, 1 declared WIP-FAIL; exit 1**.
[Summary](review/regression.json), [sweep log](review/scenarios.log). The two failures are D15
`d15_side_paths` step 43 (picked event target has event IDs 0) and `scour_edges` step 22 (Crown return edge
requests source 0 / hes_out4 instead of source 1 / hes_out2). D5 fails its declared WIP movement replay.
The integrator subsequently confirmed the two failures were intermittent and later sweeps pass;
D15 step 87 belongs to the separate Actor sizes job. The original logs remain as historical evidence.
D3, D8, D9, Scour camps,
exits, depot, harvester, tablets, collision and stage dialogue scenarios pass.
The cooked stage contains all five expected [bindings](review/staged_bindings.json).

The standard existing viewer is prepared at [review/viewer/index.html](review/viewer/index.html): **five models,
22 clips each**, source hashes, relative scales, attached geometry and clear bound/unbound clip labels. Only
viewer copies bake ramps for three.js; runtime files keep region variants. No browser/viewer capture was attempted.
The integrator completed the delegated review under CREATURE_BUILDS rule 9 and accepted the build on 2026-10-24.
The reported playback coverage is A's Standing/Attack/Running/Death and every tier; game capture coverage is D3,
D5, D8 and D9. Acceptance is attributed to that report; these checks were not rerun by the builder.

With the repository server running, use the existing wrapper (its actual CLI has no `setup` subcommand):

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_drudge_codex check
python3 tools/run_creature_review.py --project level_generation/creatures/hes_drudge_codex playback
```

On **2026-10-23 the user accepted the appearance shown in the Hulk screenshot**, including the small visible
chest-slab/body gap: “i guess we dont care its small ... otherwise fine i guess.”
[Approval evidence](review/user_acceptance_20261023.png) is bound to viewer revision `hes_drudge_codex_v1`,
Hulk SHA-256 `e23f704f26b5980ce00d97a2e2500bb356bf5b4b971ea1146ddbe7d4fd4d2d41`. The gap is intentionally retained.
The subsequent integrator acceptance above closes the playback and in-game review handoff.

## Reproduction and Meshy jobs for the integrator

**None. 0 / 0 credits, no Meshy calls.** The model, add-ons, motion and scar pattern do not depend on a paid job.
Run `rebuild.sh` through `tools/creature_workspace.py run` with a new active project lease. Set `BLENDER_BIN` to a
working Blender and `LOD_REPAIR_PYTHON` to a Python with pymeshlab, xatlas, numpy, scipy and Pillow. This session used
`/snap/blender/current/blender` (5.2.2 LTS) because the snap launcher cannot start in this sandbox, and the existing
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/98721a52-31e0-41a8-8023-ca6cbaee6d61/scratchpad/mlvenv/bin/python`.
No new dependencies were installed. The rebuild script only writes this project; stage and regression commands
remain separate, under the work package's locks. The source hash assertion stops a rebuild if the shared body changes.

No engine code, installed assets, design specification, Vulkan build, performance run or git staging was changed.
