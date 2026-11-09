# Hesper Brood and Sentinel actors

**Sentinel A–C and Throne Turret are textured, verified and staged.**
One shared mesh and texture set, region ramps, factor-only glow and four audited LODs. All 72 scenarios pass.

2026-10-23. Scope: CREATURE_BUILDS.md Brood/machines row: Egg Cluster 10045, Brood Sac 10130,
Ganglion 10131 first; Sentinel 10055, Heavy Sentinel 10056, Crown Sentinel 10057 and Throne Turret 10144 next.
Brood Mother, Bulwark and Ion Cannon belong to the next round.

## Brood production

The user reaffirmed the urgent no-Meshy route: start from
`level_generation/props/hesper_decorations/work/codex_tex/hes_egg_mound_export.glb`.
Its frozen copy and SHA-256 are in `source/`. The Egg Cluster preserves that mound. Brood Sac isolates its largest
complete egg on three resin stalks and bone braces. Ganglion reshapes copies of that egg into a broad magenta nerve
mass, with folds, an open bone plinth and trailing cables. The original source is unchanged.

All three actors use one deform bone, `B_Root`, at the ground plane. Standing pulses over 3 seconds; Hit recoils
for 0.4 seconds; Death deflates over 1.2 seconds; Dead holds the exact final pose for 1 second. The simple bone scale
also compresses the supports during death, as allowed by the requested one-bone route. No locomotion, attack,
equipment or cast action is needed by these three rows. A local library query found humanoid actions unsuitable for
these stationary organic props; the procedural motion follows the non-humanoid playbook.

| Actor | Authored triangles | Reviewed LOD0 | Model height | Binding scale |
|---|---:|---:|---:|---:|
| Egg Cluster | 2,499 | 1,997 | 0.75 m | 100 |
| Brood Sac | 1,050 | 628 | 1.20 m | 100 |
| Ganglion | 3,130 | 1,876 | 1.50 m | 100 |

`review/lod0_reduction_review.png` compares 100/80/60/40 percent. The selected reductions preserve the silhouettes;
the next lower study loses resin tips or visibly facets organic curves. The editable `.blend` masters retain the
authored topology; `select_lod0.py` makes the reviewed runtime reduction and restores its floor/height.

One shared atlas, normal and metal/roughness set serves these related actors, with an RGBA region mask (R tissue,
G resin, B bone; A unused). Every actor selects its own `KHR_materials_variants` material data. The Ganglion's tissue
changes by ramps, without a separately baked runtime base colour. Glow uses only `emissiveFactor` on the organic
surfaces. Small bone/resin swatches support the new plinth and stalk meshes. No emissive texture.

The default 50/25/12.5% far-LOD chain and the full default repair ladder failed the outline gates on these thin structures. LOD1 therefore keeps 80% of the reviewed LOD0; the repair route tries 60/40, 65/45, 70/50 and 75/60% for LOD2/3, preserving the same scoring thresholds. This recorded budget deviation costs fewer than 2,000 triangles even at LOD0 and avoids vanishing supports.

Far LODs use the existing `lod_repair_claude/scripts/repair.py` algorithm and gates. `scripts/repair_lods.py` changes
its installed-source paths to this project, so it writes no shared creature or assets_source files.
`scripts/audit_lods.sh` uses the same split/render/score tools in isolated Blender with four threads. It exits after
successful rendering to avoid the host's PulseAudio shutdown hang. Numerical and visual results belong in `review/`
and `work/lod_repair/`; native/browser capture and user artistic acceptance belong to the integrator.

## Sentinel delivery

**One shared runtime model for Sentinel A/B/C and Throne Turret:** `export/hes_sentinel.glb`.
The editable, packed snapshot is `export/hes_sentinel.blend`; rig/UV construction checkpoints remain in `work/`.
The [viewer](http://127.0.0.1:8912/level_generation/creatures/hes_sentinel_codex/review/viewer/) has all four row choices
and all five clips. [Tier comparison](review/sentinel_tiers.png) shows the final PBR renders. Viewer copies bake the
ramps only for three.js; the runtime GLB retains one shared texture set per LOD with `KHR_materials_variants`.

| Row | Binding | Skin | Scale | Descriptor height / radius |
|---|---|---|---:|---:|
| 10055 Sentinel | `hes_sentinel` | `sentinel_a` — ivory | 100 | 160 / 99 |
| 10056 Heavy Sentinel | `hes_heavy_sentinel` | `sentinel_b` — scorched | 120 | 192 / 119 |
| 10057 Crown Sentinel | `hes_crown_sentinel` | `sentinel_c` — gilded | 130 | 208 / 129 |
| 10144 Throne Turret | `hes_throne_turret` | `sentinel_c` — gilded | 130 | 208 / 129 |

The mesh is 1.5993 m high with a measured base radius of 0.9821 m. The four project bindings share the export;
Throne retains its separate monster identity and tactics. Only these four stage rows and the shared model source
were changed. Existing post, traverse and firing tactics are preserved.

### Retexture correspondence and materials

`review/sentinel_geometry/retexture_compare.json` verifies a bijection over all 9,747 returned triangles and
29,241 corners. After undoing Meshy's normalization (scale 1.4477131), maximum position error is 0.000000125 m;
maximum UV difference is **0.000061 texel at 2K**, with no corner moving half a texel. The approved geometry, weights
and clips were preserved; returned UVs were assigned by exact face/corner correspondence.

The 2K base colour, 1K normal and packed metal/roughness maps are shared. The padded 1K RGBA region mask uses
**R = ivory armour, G = bronze trim; B/A unused**. Channels are resized separately, avoiding premultiplication by
the unused alpha. Resin stays violet. A ramps reproduce the returned ivory appearance (mean fit error 2.16 / 3.92
8-bit levels for armour / trim); B and C ramps sample their own HD colour studies. Armour is dielectric on A/B and
metallic on C, with separate shared-map trim and resin material slots. `sentinel_material_classes.png` records
5 = armour, 9 = trim, 11 = resin. ORM red remains 1: no AO map was supplied, and this asset does not enable the
engine's optional red-channel specular mask; no occlusion texture or invented AO is attached.

The untouched source normal map measures **−0.999223** under `normal_map_convention.measure`, establishing its
DirectX orientation. Green was inverted before runtime export. The lower score after gutter filling/downsampling
is not used to infer the source convention.

Meshy's return omitted the orange muzzle light. Two recessed, 16-sided emitter cores add **120 triangles** and
follow `B_Recoil`. Their per-tier `emissiveFactor` is orange / amber / gold, with `openyamm_bloom: true` and no
emissive texture. No separate baked runtime tier skins or additional Meshy jobs.

### Rig, aim and gates

`B_Root` holds the base, `B_Head` scans, `B_Barrel` pitches and `B_Recoil` slides the paired barrels. Coupling cables
use at most two normalized influences. Upper, lower and centre muzzle sockets follow recoil. The pitch pivot is
`(0.012, -0.215, 0.910)` in Blender metres; Blender forward is -Y, glTF +Z. Local procedural turret clips follow
`hes_turrets_claude`; the local animation-library query returned unsuitable humanoid ranged motions.

| Clip | Seconds | Motion |
|---|---:|---|
| Standing | 6.0 | ±20-degree head scan, small pitch, fixed base |
| Attack | 0.5 | 0.07 m recoil, 4-degree kick; impact/release at 0.166667 s |
| Hit | 0.4 | Head/barrel reaction and recovery |
| Death | 1.2 | Barrel slump with settling |
| Dead | 1.0 | Exact final Death pose |

Runtime look keeps **−25° to +30° pitch**. The old stand-in's ±8° barrel yaw intersected this base at the lowest aim;
barrel yaw is therefore **0°**, while the whole actor traverses at the existing tactics rate. The 10055 override
was updated to the same limit. `review/sentinel_look_gate.json` passes both pitch extremes with zero barrel/base
intersections; the rejected yaw study is retained in the script and log. The neutral rig approval ("LGTM,
continue", 2026-10-23) remains recorded against its exact hash; final tier appearance awaits the user's review.

`review/sentinel_final_gates.json`: all five clips at 60 Hz on all four LODs, floor contact at the largest scale,
fixed base, normalized weights, actual motion and loop/Death–Dead continuity pass. All 105 animation samplers have
valid key times. The single-sided material exposed an inward 22-triangle component hidden by the neutral double-sided
material; its indices and normals were corrected at LOD0 before rebuilding every LOD. **Final winding: zero inverted
closed parts**, including shadows. The mesh positions, UVs and skinning were unchanged by that repair.

| LOD | Triangles | A outline / colour | B outline / colour | C outline / colour |
|---|---:|---|---|---|
| 0 | 9,867 | — | — | — |
| 1 | 4,910 | 3.4% / 15.0 | 3.4% / 14.9 | 3.4% / 15.1 |
| 2 | 2,783 | 5.7% / 16.3 | 5.7% / 16.1 | 5.7% / 16.5 |
| 3 | 1,449 | 5.7% / 11.1 | 5.7% / 11.0 | 5.7% / 10.7 |

The required `lod_repair_claude/scripts/repair.py` route is adapted only to project paths in
`scripts/repair_sentinel_lods.py`. The first 25/12.5% trial failed LOD2 outline; **30/16% passes**. Gates are unchanged:
LOD2 outline ≤6%, colour ≤max(16, LOD1+3); LOD3 outline ≤13%, colour ≤19.5. Every tier was baked for review and scored
separately (`review/sentinel_tier_lods/result.json`). Far levels have reprojected base/normal/metal-roughness/region
maps, shared across variants. Textured PBR stills of all tiers, Attack and Dead were inspected. Browser playback
and native indoor/outdoor captures remain the integrator's rule-9 review.

## HD references and Meshy records

Five original transparent 1536x1024 masters per colour reference remain under `references_hd/sentinel/`,
`heavy_sentinel/` and `crown_sentinel/`. Each has prompts, output hashes and a contact sheet.
`references_hd/throne_turret/masters.json` aliases Crown colours and the shared geometry job. The integrator's
one-mesh ruling supersedes shape differences in Heavy/Crown colour studies.

## Meshy jobs for the integrator

**Both jobs succeeded on the backup account; nothing remains to submit. 15 credits used / 120 cap.**
No connector changes or Meshy submissions by this worker. Full receipts remain in `creature_3d_progress.json`.
Paths below are relative to this project.

| Job | Type / cost | Exact inputs | Settings | Returned target |
|---|---|---|---|---|
| `sentinel_geometry_v1` | `image-to-3d`, 5 credits | `references_hd/sentinel/00_three_quarter.png` | `meshy-t2`, `smart-topology`, 15000 target triangles, no texture, GLB, no pose mode | `meshy/sentinel_geometry_v1/model_urls_glb.glb` |
| `sentinel_retexture_v1` | `retexture`, 10 credits | `work/sentinel_texture_upload.glb`; `references_hd/sentinel/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png` in that order | `meshy-7`, original UVs, PBR, 2K, GLB | `meshy/sentinel_retexture_v1/model_urls_glb.glb` plus base colour, metallic, normal, roughness and thumbnail |

Task IDs: geometry `01a16934-3cb3-7359-b347-4e2ba1d995bb`; retexture
`01a16957-568b-70a5-ab93-b33ec8da595c`. Exact payloads remain in `requests/`; planned Heavy/Crown geometry requests
are cancelled. Brood used no Meshy credits.

## Sentinel reproduction

Run writers under `tools/creature_workspace.py run` with the active lease. Use the actual
`/snap/blender/current/blender`, four threads, bounded `timeout --kill-after=5s`, `--python-exit-code 1` and the final
`--python-expr 'import sys,os;sys.stdout.flush();sys.stderr.flush();os._exit(0)'` before script arguments. This avoids
the host's audio shutdown hang; failed scripts still need the outer timeout. Never start a second writer under the
same lease while Blender owns its guard.

1. Geometry: `sentinel_geometry.py -- study`, `-- select`, `-- uv selected`; `sentinel_rig.py` creates the accepted
   neutral rig. `adopt_sentinel_texture.py` verifies/assigns returned UVs onto it.
2. `compose_sentinel.py` writes shared maps, masks, material classes and ramps; `finish_sentinel_lod0.py` adds the
   shared PBR slots and emitter cores. Run `fix_sentinel_winding.py` on `export/hes_sentinel_lod0.glb` in place.
3. `sentinel_initial_lods.py` creates 50/25/12.5% levels. `sentinel_materials.py <in> <out>` applies ramps, material
   factors and factor-only emission. Its output is `work/hes_sentinel_initial_coloured.glb`.
4. Refresh `work/lod_repair/originals/hes_sentinel.glb` from that corrected initial coloured export; retain the old
   baseline if it changed. Run `repair_sentinel_lods.py hes_sentinel` with `LOD_REPAIR_PYTHON` pointing to the existing
   numpy/scipy/Pillow/pymeshlab/xatlas environment. Adopt only a passing result into `export/hes_sentinel.glb`.
5. Run `audit_sentinel_final.py`; `viewer_bake.py <runtime> <viewer> sentinel_a|sentinel_b|sentinel_c`; score all three
   with `audit_lods.sh`. Run `sentinel_look_gate.py`, `sentinel_pbr_review.py`, and `save_sentinel_master.py` in Blender.
   The editable export is imported from the verified runtime, so it includes the winding repair.
6. `integration/actors.yml` supplies the four bindings; the package's locked stage.py and scenarios-only run install
   and validate them. Browser checks use `python3 tools/run_creature_review.py --project
   level_generation/creatures/hes_sentinel_codex check` / `playback`, operated by the integrator.

## Reference provenance

The approved `fam_sentinels.png` and `fam_brood.png` are copied under `references_hd/`. Built-in image generation
produced unresized transparent HD masters; prompts, selected/rejected outputs and hashes are recorded per subject.
The Sentinel's first back view was rejected as another profile; its corrective rear elevation hides the forward
barrels and shows the rear spine/cables. `selected_views_review.png` is the review contact sheet only.
The additional Brood HD images predate the urgent source-mesh instruction and remain reference archives;
they do not replace the user's chosen egg-mound source. Unsubmitted Brood geometry requests are removed.

## Reproduction and review

Use this project's active lease token for writes. From repository root:

1. Run `scripts/compose_brood.py` and `scripts/source_parts.py` (the latter through `tools/run_creature_blender.sh`).
2. Run `scripts/build_brood.py`, then `scripts/reduction_study.py` through the Blender wrapper.
3. Run `scripts/select_lod0.py`, then `scripts/initial_lods.py` through the Blender wrapper.
4. Apply `claude_shared/region_variants.py` with each `textures/<name>_ramps.json` to
   `work/hes_<name>_initial_lods.glb`, producing `work/hes_<name>_initial_coloured.glb`.
5. Run `scripts/repair_lods.py hes_egg_cluster hes_brood_sac hes_ganglion` with `LOD_REPAIR_PYTHON` pointing to
   the existing Python environment containing pymeshlab/xatlas/numpy/scipy/Pillow. Adopt only passing results.
6. Run `scripts/audit_brood.py`; retain `review/final_gates.json`, winding and key-time results.

For the current Sentinel viewer, the integrator uses:

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/hes_sentinel_codex check
python3 tools/run_creature_review.py --project level_generation/creatures/hes_sentinel_codex playback
```

The integrator provides browser/native captures under the work package's rule 9. Brood viewer GLBs bake region ramps for
three.js only; their runtime exports retain the shared textures and ramps. The Sentinel viewer now contains the three finished tier appearances and Throne alias. Bindings are stage-only in
`integration/actors.yml`; rows 10045/10130/10131 now use them, with `sprite_only` and the missing `3egg` override removed.
Sentinel rows 10055–10057 and 10144 now use the verified shared model.

## Brood staging record and current delivery status

The orphaned Blender lock was released by the integrator. A fresh bounded LOD render/score audit passed for all
three final Brood exports (`review/lod_resume_20261023/result.json`), and the numeric animation/material gates were
rerun. Rows **10045, 10130 and 10131 are staged**; stage.py cooked exactly three changed GLBs. The scenarios-only
pass completed: **70 passed, 1 failed**. See `review/scenarios_20261023.log` and
`review/staging_20261023.json`. No map or engine builds were run. The Sentinel continuation is documented above: the four rows are now staged; the new regression result is recorded below.

[Brood viewer](http://127.0.0.1:8912/output/creature_reviews/hesper_brood_codex/?v=2)
contains all three actors and Standing/Hit/Death/Dead clips. Its feedback schema is corrected.
User acceptance recorded: "the sacs are fine" (Brood Sac appearance only).

The sole failure in that recorded Brood run was `hesper_d05/relay_spire_climb.yml:136`, step 64: interaction hits face 4390 with no event (event 0). This is a map interaction failure, outside these actor changes; no map fix was attempted. The complete failure log is `review/relay_spire_climb_20261023.log`. All Brood Spires, Brood Pits and Seedship scenarios passed.

| Actor | LOD0 / 1 / 2 / 3 triangles | Far LOD2 outline / colour | Far LOD3 outline / colour |
|---|---|---|---|
| Egg Cluster | 1997 / 1595 / 1295 / 897 | 4.4% / 17.2 | 5.9% / 11.6 |
| Brood Sac | 628 / 502 / 408 / 282 | 4.1% / 14.0 | 6.8% / 9.2 |
| Ganglion | 1876 / 1498 / 1124 / 750 | 3.0% / 13.5 | 3.7% / 8.0 |

The Egg Cluster's colour limit is 17.6 (the repair playbook's LOD1 + 3 rule). All three pass the unchanged
repair thresholds. All four LODs and four clips sampled at 60 Hz: Egg Cluster/Brood Sac floor exactly zero;
Ganglion worst -0.392 world units at a lower LOD (within 2.5-unit tolerance), LOD0 zero. Death/Dead positions match.
Final GLBs: one bone each, twelve valid animation samplers each, zero inverted closed parts, no emissive textures.
Normal-map convention measures +0.673 and requires no inversion. Stills reviewed; normal/slow playback and native
indoor/outdoor captures remain the integrator's work under rule 9. No assets_dev writes or git staging.

## Final Sentinel staging result (2026-10-23)

The locked stage.py run cooked **one changed GLB and 28 textures**, with 308 other models unchanged. All four
staged scales, skins, muzzle sockets and look limits were verified. The scenarios-only regression finished
**72 passed, 0 failed** (`review/sentinel_scenarios_20261023.log`). This supersedes the earlier historical Brood
run's unrelated map failure. `review/sentinel_staging_20261023.json` records the final export hash and staged rows.
The viewer's four selections, clip durations, model hashes, local imports and feedback schema pass static checks.
Browser playback and native visual captures remain with the integrator under rule 9. No engine/map builds,
assets_dev installation, connector changes or git staging were performed.
