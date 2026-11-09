# Hesper Gloamers (R5-3)

The three tiers are exported and staged, with all nine clips, four LODs, the elder's swelling throat sac, and
placements in all five assigned maps. All unblocked production work is finished. **Custom audio is blocked by
ElevenLabs DNS**. Native GPU tours, Blender/viewer review and headless checks are complete.
The user accepted the reduced model and corrected colours: “OK good accepted” (2026-10-26).

**Triangle reduction (2026-10-26): 11,342 → 9,070 body triangles (20.03%).** The texture-aware ladder
selected 80%; the 70% and 60% steps failed motion/silhouette gates. Teeth, pores and sole contact faces are kept;
the dense head and fingers have separate gentle budgets. All maps, ramps, clips and fitted lower LODs are preserved.
The full-detail shadow is rebuilt. The unchanged LOD1 is 62% of the new LOD0, intentionally retaining its fitted
weights and UVs; LOD transitions still pass. No paid jobs were needed. [Reduction record](reduction_20261026/review/results.json),
[close-ups](reduction_20261026/review/close_tex.jpg), [clay comparison](reduction_20261026/review/close_clay.jpg).
The viewer includes **Before reduction (11,342 tris)** beside the three current tiers.

**Colour correction (2026-10-26):** the user rejected the chalk-white viewer appearance. The composer now
retains the returned warm grey-pink skin and broad crease shading, with matched body/head medians. A/B share
the warmer hide; C retains its darker stone-grey tier. The same correction reaches all four LODs and the sac.
Viewer lighting and pore emission are unchanged. [Correction evidence](review/colour_fix/results.json);
[before](review/shots/before_a_standing.png), [A](review/shots/colour_a_standing.png),
[B](review/shots/colour_b_standing.png), [C](review/shots/colour_c_standing.png).
The older Blender sheets, playback and map gallery below predate this colour correction. Their motion/placement
evidence remains historical; use the current viewer and `reduction_20261026/review/native/` for the current model.

Canonical state: [creature_3d_progress.json](creature_3d_progress.json). Final checks:
[review/regression/results.json](review/regression/results.json). Task: `R5_GLOAMERS.md` and `R5_COMMON.md` under
`design/kreegan_world/WORK_PACKAGES/prompts/`; design: `NEW_FAMILIES.md` section 4. No engine or `assets_dev` changes.

## Review and deliverables

- [Interactive viewer](http://127.0.0.1:8912/level_generation/creatures/hes_gloamer_codex/review/viewer/): three tiers,
  nine clips, plus the unreduced B comparison. Uses the shared viewer; the portable preview GLBs bake the region ramps for browser display only.
- Latest reduced C playback: [18 recordings / 108 reviewed timed frames](reduction_20261026/review/playback/playback.json),
  covering every clip at normal and half speed. The following original-production galleries are historical.
- [Original Blender sheet](review/final_blender/sheet.jpg), [LOD sheet](review/lod_final_sheet.jpg), and
  [canyon den](review/canyon_den/oblique.png), [interior](review/canyon_den/inside.png).
- Every clip at normal and half speed: [A](review/playback_a/playback.json), [B](review/playback_b/playback.json),
  [C](review/playback_c/playback.json). All 54 recordings' 324 timed frames were inspected in nine sheets.
- Native map captures: [D2](../../projects/hesper_d02/review/gloamers/01-drained_sump.png),
  [D10](../../projects/hesper_d10/review/gloamers/02-vault_den.png),
  [D13](../../projects/hesper_d13/review/gloamers/03-elder_front.png),
  [D15](../../projects/hesper_d15/review/gloamers/01-freight_line.png),
  [Out1](../../projects/hesper_out1/review/gloamers/01-canyon_cave.png). All eleven final images were inspected.
- Runtime body [export/hes_gloamer.glb](export/hes_gloamer.glb); elder attachment
  [export/hes_gloamer_sac.glb](export/hes_gloamer_sac.glb); [bindings](integration/actors.yml).
- Editable reduced body: `reduction_20261026/work/selected.blend`; it retains all nine source actions.
  `work/rig_export.blend` is the pre-reduction body plus the unchanged elder sac. The accepted source and
  textures are also snapshotted under `reduction_20261026/before/` for rollback and comparison.

| Asset | LOD0 | LOD1 | LOD2 | LOD3 |
| --- | ---: | ---: | ---: | ---: |
| Body, head and pores | 9,070 | 5,667 | 2,835 | 1,398 |
| C throat sac | 528 | 264 | 132 | 66 |

The body SHA-256 is `412ed8c1848703025224d7fca6cc687f32539c821ece6a6b0dd5cd0ad65adfb9`;
the sac is `19cbec9f76d561ddcc68091965c6649b428bf55d52a3729604f8be559305d7da`.

## Art, references and paid work

Selected [concept candidate 2](../../../design/kreegan_world/concepts/monsters/fam_gloamers.png): its broad eyeless
cranium, blunt jaw, hunch and ribs read as a separate pale biped. Candidate 1 looked reptilian and approached the
Glassbacks' silhouette. Both originals, exact prompts, hashes and selection reasons are retained in the concept
folder. The brief is [CODEX_BRIEF_GLOAMERS.md](../../../design/kreegan_world/concepts/monsters/CODEX_BRIEF_GLOAMERS.md).

Five 1024×1536 RGBA masters in `references_hd/` and four 1254×1254 head views in `references_head/` preserve
actual generated returns and provenance. The side masters remain slightly oblique; the primary controls geometry.
Hands have four fingers plus a thumb, feet four toes. No weapons or equipment are required.

**30/100 Meshy credits consumed; 70 remain.** All four jobs succeeded on the backup account, are downloaded and
receipted in the state, and must never be submitted again. No paid animation was needed.

| Job | Task id | Credits |
| --- | --- | ---: |
| body_smart_v1 | 01a17834-f7f4-73a5-bcba-a99af7302f8e | 5 |
| joints_v1 | 01a17849-608d-7660-86fe-1ab95b285691 | 5 |
| retexture_body_v1 | 01a1787f-f745-75b7-840b-74f76e4a9513 | 10 |
| retexture_head_v1 | 01a17880-0e34-719f-a367-f09b963689ec | 10 |

The raw 15,998-triangle body exceeded its target and had seven local forearm holes. Local caps, a welded pore
patch, flattening of 40 pore patches and protected reduction corrected it. Upper arms are 1.10× and forearms
2.40× the initial measured lengths, allowing grounded knuckles while keeping both arms clear of the legs.

## Rig, materials and gates

The 57-bone rig uses 52 exact source rest frames, four arm twist bones and `ThroatSac`. The source-frame route
uses mesh-measured joints, connectivity-based fingers and world-rotation retargeting; finger chains were inside
the closed skin within 1.4 mm before protected reduction. Teeth are head-owned. Arm contact is corrected locally
in each affected clip. Do not rerun the twist-weight step on an already processed rig.

The selected local Mutant sources are recorded in [clips.json](clips.json). Standing uses Breathing Idle; Fidget
uses Mutant Idle. Walking, Running, compact Punch, Hit Reaction, Dying and Roaring supply the other motion.
Dead holds the corrected death endpoint. Source playback reviewed 90 mannequin frames; its initial Standing and
Fidget sheet labels are reversed relative to the final role mapping, explicitly recorded in `clips.json`.

C's Cast crops Roaring frames 21–109, adds a short lead/ease, lasts 3.0667 s and releases at 0.7333 s. The unlit
throat sac is attached at `ThroatSac`, grows to 1.30/1.20/1.45 of its resting axes and contracts smoothly. Pores
carry cold yellow-green factor-only emission with the existing pulse/bloom material contract; no emissive texture.
The rigid wide jaw is retained; the roar is expressed by head/body motion and the sac.

Body and separate head maps are shared across A/B/C; region masks and `KHR_materials_variants` ramps change the
pale hide and pore strength. Head merging was a no-op for this three-primitive body/head/pore split: keeping pores
separate is necessary for emission. The 256-pixel sac paint is cropped from the head set, without another Meshy job.

`compose_textures.py` owns the skin grading and shared ramps. `refresh_colours.py` updates the selected runtime
exports and reuses the existing far-LOD unwrap with the shared surface transfer; run it with the existing
`/tmp/lancer_lod_venv/bin/python` (Pillow/NumPy/SciPy/PyMeshLab), under the project lease, after composing maps.
Then run `prepare_viewer.py`, validate and restage. The refresh asserts unchanged geometry/rig/animation bytes.
The pre-reduction authoring blend uses external maps. The selected reduced authoring file contains the
accepted embedded runtime maps; use the reduced export chain in `reduction_20261026/README.md` for geometry updates.

The [reduced runtime contact checks](reduction_20261026/review/contacts.json) repeat all nine clips at 60 Hz
(1,261 poses per body) with zero arm–leg, arm–torso/head, arm–arm or sac–arm intersections. Reduced arm-edge
p99 stretch peaks at 1.799× and hand-edge stretch at 3.401×, within the source-comparison gate. The original
[motion probes](review/motion_final.json) are retained as the pre-reduction baseline. [Source comparison](review/source_motion_comparison.json) reports no quaternion interpolation
flips and world-step/source ratios below 1.77. Final normal/half-speed playback was inspected for abrupt correction.

[Runtime validation](review/runtime_validation.json) passes mesh/skin/animation/material contracts: at most eight
normalized weights, normalized quaternion keys, strict key times, shared tier textures and factor-only glow.
[120 Hz exported floor checks](review/runtime_floor.json) pass B and assembled C: worst penetration 14.865 mm at
base scale, below 20 mm even at 1.15×. Run flight and the brief dying lift are intentional source motion.
All final body/sac LODs have zero inverted closed parts; two tiny four-triangle LOD3 pore pieces were reversed
locally after the shared far-LOD repair. Those fitted colour/shadow LODs remain unchanged. The latest
[LOD check](reduction_20261026/review/lods/scores.tsv) reports LOD2 outline 3.8%, colour 8.2; LOD3 outline 5.0%,
colour 8.3, both within the shared gate. The 72-pixel far hands remain simplified.

## Stage and placement

The slot family is `hes_gloamer A/B/C`, including the A Gloamling and C Gloam Elder names. All eight required
roles, running, stride lengths, measured impact time, head look bounds and C Cast/socket are bound. Base B is
175 game units high, radius 62, scale 107.17157105419; A is 0.8× (140/50), C 1.15× (201/72).
Walk/run strides are 1.94327/1.83484 m; melee impact is 0.2333 s. Rows 10320–10322 use native Ghoul descriptors
for the base descriptor layout. They remain in the existing `wild` faction; no relation or combat-stat change.

| Map | Final packs | Change |
| --- | --- | --- |
| Starport Reach | Five A, canyon cave near D2, group 90 | Added in spawns.yml; no removal; actor indices 74–78 |
| D2 Pumping Station | Five A, deep drained sump, group 8 | Added; hidden until two valves; Queen and earlier actors preserved |
| D10 Colony Archive | Two packs of four B, Flooded Stacks B / vault hall A | Added; earlier actors preserved |
| D13 Deepwell | Two packs of three C, Collapse Route / Deep Vein | Replaced only six drones; slot 3 changed; all eight hounds preserved |
| D15 Undercroft | Four packs of four C in western Freight Line; six of four and one of three in eastern Cut | Replaced all 43 drones; slot 1 changed; all Kreegans preserved |

D13's local basalt Deep Vein side cavern realizes the specified below-tap habitat and keeps the lower elders
beyond Kreegan acquisition distance. D15's cut packs were moved east after the minute test detected Psychic
Shock across walls. All five final minute checks leave the Gloamers near their dens, untargeted, with full HP;
indoor checks also verify the other residents retain full HP. D13/D15 use a distant invisible observer so the
party does not provoke the packs; AI and faction relations stay enabled.

D2's reveal logic saves/reloads correctly and its native floor/ceiling check passes all 25 actors. The outdoor
62-face rock shell has continuous thickness and buried rear walls; all five collision footprints have more than
458 units of roof clearance. Its lighting bake and minimap are regenerated for the final ODM.

Map-local sources, handlers, fixtures, tours and README entries are updated. D13's two obsolete drone-hover calls
were removed; D15's tram note names the pale creatures. Dead drone wrecks/cradles remain architecture. D13's
unshielded actor fixtures now use one fatal hit; D10/D15 isolated pursuit fixtures clear residents before spawning.
No design generator, other creature project, engine build or Git staging was changed.

## Regression and limitations

- Design audit: zero findings. Actor-size audit: 22 maps, 1,253 actors, zero mismatches. Decoration audit: 22 maps,
  3,433 decorations, zero mismatches.
- Required `OPENYAMM_WALKABILITY_WORKERS=1 .../rebuild_all.sh --scenarios-only`: **109 PASS, zero FAIL, exit 0**.
  Logs: `output/hesper_stage/logs/scenarios_160546_3/`. After the final cave-shell revision, all ten standard Out1
  scenarios and its minute check pass again. Both extra D13 timing scenarios pass.
- Three-row spawn scenario passes. Five map-specific minute checks pass, plus D2's native saved-visibility/floor
  assertions. Headless scenarios do not prove native GPU model loading.
- Static walkability: D10/D15 zero findings. D13 retains one existing unreachable 64-high charge shelf. D2 retains
  six step findings and nine initial-water-plane floor findings (four crawlers plus five Gloamlings); the drained
  native floor and runtime checks pass. No allowlist or checker rule was relaxed. The required shared gate passes.
- All five native tours complete on NVIDIA OpenGL 3.3 / Wayland, minimized: eleven final images inspected,
  no actor-model load errors. Pore glow, floor contact, elder sac attachment and final cave lighting are visible.
  Initial launches wrapped in the queue failed SDL initialization; invoking `./tools/run_game.sh` directly works
  while a separate holder retains the shared queue locks. Do not wrap approved launch commands in another shell
  or redirect them. The first D2 wrapper reports early warmup exit because the tour completed its screenshot first.
- Browser check: 27 tier/clip combinations, zero errors. Blender reviewed 18 final clip views and three den views.
  Every clip, including Cast swelling, has normal/half-speed viewer playback; native tours are placement stills,
  not an exhaustive native combat-animation recording.

## Audio and resume

Nine jobs exist in `design/kreegan_world/audio/jobs.yml`: five generated sources with two variants each, plus
four elder derivatives at -2 semitones. Planned generation is 528 ElevenLabs credits. Repeated generation attempts, including the final direct wrapper call,
failed DNS before a download; no matching charge/download is recorded. There are no custom WAVs, picks or hooks.
The staged descriptors temporarily retain borrowed native Ghoul sounds 2500–2503. See
[initial failure](review/audio_network_blocker.json) and [resume failure](review/audio_resume_failure.log), and [final direct retry](review/audio_final_retry.json).

1. Claim this project as `hesper:gloamer`, retaining the 100-credit Meshy budget and all existing receipts.
   **Do not regenerate the model, references, textures or clips.** No Meshy job is pending.
2. Claim shared `audio`, re-read the jobs/ledger and use the authorized `tools/run_elevenlabs.sh` directly.
   Run the five source IDs `gloamer_attack gloamer_wince gloamer_death gloamer_fidget gloam_elder_cast`, then
   process/review those and `gloam_elder_attack gloam_elder_wince gloam_elder_death gloam_elder_fidget`.
   Use AUDIO.md batch-3 loudness; propose picks for the user. Install IDs 60170–60179 only after processed WAVs exist.
3. Restage under the exclusive stage lock, check all three rows, then check the installed voices in a direct native run.
   Keep shared stage/engine locks around the entire run queue.
4. Update this README, the canonical state and the existing Gloamers section in `requests/P5.md`; release claims
   and the creature lease. The current handoff leaves no own map claim or active paid job.

Full technical completion remains false because custom audio is outstanding. Model, maps and visual checks are
complete; remaining work depends on ElevenLabs connectivity, then user art/audio picks.
