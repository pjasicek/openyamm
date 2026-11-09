# MM6 BMonk — mnk1

**Review round 4: technical batch handoff ready.** [HANDOFF.md](HANDOFF.md) contains current hashes, all gates, before/after counts and integration instructions.

Rebaked and reduced the accepted round-3 body from 12,364 to **7,047 triangles**. Final colour/shadow LODs: **7047 / 3804 / 1690 / 701**. All four LODs pass sleeve/robe containment on every clip at 48 Hz; runtime Standing hands remain completely covered. All nine animation streams, tier ramps and actors.yml are unchanged.

- [Runtime](export/mm6_mnk1.glb): `f9bae7487780316c3ce7ba3563d3047e3c02e7133bf61ca78fa27e02d2d0c554`; 11,322,920 bytes.
- [Eight-view comparison](review/round4/comparison.png), [far LOD comparisons](review/round4/lod_metrics.json), [close-ups](review/round4/closeups.png), [viewer](review/viewer/index.html).
- [Reduction curve](review/round4/reduction_curve.json), [receipt](review/round4/receipt.json), [frozen source](review/round4/before/).
- **20/100 credits total**, zero new this round. No install, shared edit, build, game launch or commit.

Unattended decisions: freeze render triangles before simplification; retain the accepted 116-bone authoring rig and 118-joint export; transfer all four maps into fresh UVs at the same texture sizes; preserve the hollow hood and its existing shared map rather than invent a face. Fit far LODs at 550/220/88 pixels. LOD3 prioritizes outline vertices and lowers only the hidden shoe roof to clear the coarse hem. The 6,800-triangle LOD0 step failed silhouette IoU, so 7,047 is selected. Fine texture sampling changes are recorded transparently: fixed-frame SSIM passes .95, foreground-only SSIM does not; compare the supplied images.

Reproduce under the project lease, one Blender at --threads 4: review4_triangulate.py → review4_tri_reduce.py (REDUCE_RATIO=.57) → review4_bake_pipeline.py → external review4_resolve_bake.py and review4_textures.py. Promote work/review4_rebaked.blend and rebaked maps, then export_runtime.py → package_runtime.py prepare → review4_build_lods.py → review4_merge_lods.py → package_runtime.py final → refresh_manifest.py → validate_glb.py. The selected authoring master is work/animation_finish.blend; do not feed the socket-added export master back into export_runtime.py.

Validation/review: review4_final_gates.py, review4_reduction_render.py (and metrics; LOD_REVIEW=1 for far sizes), review4_render_final.py, review4_browser.py, review4_compose.py. The project-specific cloth gate retains opposite-sleeve containment and the animated local hem rule. Shared gates were still under validation and not marked ready when this round ran.

The orchestrator owns installation, regression and native captures. This reduced revision remains pending artistic acceptance; the round-3 look and motion are retained.

## Gait rework: Walk2 and Run2 (2026-10-21)

The installed Walking was a 0.46 m procedural shuffle (authored 0.57 m/s) that the game, which advances gaits by
distance, played at 3.3–4× wandering and 6.7–8× chasing (it was also bound as the run). Two clips were appended to
the round-4 runtime; the nine existing clips, mesh, LODs and textures are byte-identical.

- **Walk2** (0.8 s loop, measured stride 1.703 m): legs from Mixamo "Walk" (chosen by measured natural speed,
  `work/gait2_sources.json`), the source's own ankle paths relative to its hip centre, heights and lateral offsets
  scaled by the leg ratio, forward travel to the stride; half the source foot roll; pelvis lowered only where a planted
  leg cannot reach (double-support dip ≤ 8 cm); boots held on the floor in the source's contact phases.
- **Run2** (0.667 s loop, measured stride 2.828 m): Mixamo "Standard Run" the same way, heel kick at 45 %, feet kept
  level (a rolled foot lifts the heel out of the back of the robe), pelvis 84–94 % of Standing, 11° lean.
- Both keep the native folded arms (every arm, sleeve, cuff and twist local from Standing frame 0), a level gaze and a
  small hip yaw with a chest counter-turn. The leg-driven robe follows virtual legs (`Cloth_*_Thigh` swings 50 % /
  40 % of the thigh, `Cloth_*_Calf` runs straight from that knee to the real ankle), so it drapes as an A-line; the
  cloth-only floor offsets of `review3_floor.py` keep the hem above the floor.

Gates (`review/gait2/`): `gait_gate.py --set walking=Walk2 --set run=Run2` passes (stride trusted; window 0.89/0.98/1.07
wandering and 0.90/0.99/1.08 chasing for tiers A/B/C; floor ok); sleeve and robe containment 0 invalid vertices on all
four LODs at 48 Hz; G4 arm p99 1.62, G5 hand max 2.48, G6 0, elbows pass; 0 inverted parts. Deviations: Walk2's swing
peak is 5.6 cm (the round-3 rule of 8–12 cm was for the shuffle), and the robe's back panel stretches over long strides
(robe edge stretch max 10.8 against 3.7 for Walking), visible as a flared flat panel in side views.

Reproduce under the lease, one Blender at a time: `gait2_measure_sources.py` (source table), `gait2_author.py`
(writes `work/gait2.blend`), `gait2_export.py`, `python3 scripts/gait2_graft.py export/mm6_mnk1.glb
export/mm6_mnk1_gait2.glb` (refuses unless the re-exported Walking matches the runtime's exactly), then
`gait2_gate_blends.py` + `gait2_gates.py`, `gait2_render.py`. Installed with `tools/install_model.py
export/mm6_mnk1_gait2.glb --world mm6 --name mm6_mnk1.glb`. Bindings (applied by the orchestrator): `walking: Walk2`,
`run: Run2`, `stride_length: 1.7026`, `run_stride_length: 2.8283`. The viewer GLBs carry the new clips; playback
recordings `review/playback/{Walking,Walk2,Run2}-{1,0.5}.webm`, comparison `review/gait2/playback_old_vs_new.png`.
