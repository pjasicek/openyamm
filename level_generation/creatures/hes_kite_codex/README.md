# Hesper Ashkites — R5-2

Rows 10310–10312 (`hes_ashkite`, `hes_spire_kite`, `hes_storm_kite`), staged Hesper only.
2026-10-26: **model, all eight clips, three tiers, LODs, bindings and four-map placement built.**
Audio is blocked by ElevenLabs DNS. Automatic second-melee animation selection needs an engine capability
outside R5 scope. Browser/GPU capture is unavailable in this sandbox; Blender renders and headless coverage are used.
The user accepted the current viewer animation revision (`ashkite_v5_flight_legs`) on 2026-10-26.
This is not marked technically complete while the deliverables above remain open.

## Review

- [A: Ashkite](review/tier_a_sheet.jpg), [B: Spire Kite](review/tier_b_sheet.jpg),
  [C: Storm Kite](review/tier_c_sheet.jpg): 39 v4 overview renders inspected; current Fly/Run leg detail is linked below.
- [Local viewer](review/viewer/index.html): three tiers, eight clips, ordinary and half-speed controls.
  Prepared GLBs bake the runtime ramps for preview only; production shares textures through material variants.
- [Selected concept](../../../design/kreegan_world/concepts/monsters/fam_ashkites.png),
  [five HD masters](references_hd/selected_views_review.png), [HD prompts/hashes](references_hd/generation_runs.json).
- [Runtime gates](review/runtime_gates.json), [corpse contact](review/corpse_gate.json),
  [winding](review/winding_final.log), [LOD comparison](work/hes_ashkite/result.json),
  [family scenario](integration/ashkite_family.yml), [results](review/checks.json).

## Art, geometry and paid jobs

Concept candidate 1 won for its thin long neck, lean body, narrow wings and clearer separation from the ground
beasts and Kreegan flyers. Both candidates and exact prompts remain in `design/kreegan_world/concepts/monsters/`.
Five transparent 1536×1024 landscape masters show A; side views overlap far wings, while front/back/primary establish
four wings. No concept-sheet crop was submitted as a modelling master.

| Meshy job | Task | Credits | Outcome |
|---|---|---:|---|
| body_geometry_v1 | 01a17831-5b64-7210-8e8d-59d83e55b10c | 5 | Preserved; rejected neck bridges/asymmetry, 16,008 triangles. |
| body_geometry_multiview_v2 | 01a17845-e8de-7076-9876-4247a7cb3689 | 20 | Clean neck/body; locally corrected to four wings. |
| body_texture_v3 | 01a1784e-ebd6-72a7-ad7c-2ceae83c6e25 | 10 | Downloaded existing-UV retexture, composed into shared PBR maps. |

**35/100 credits spent; 65 remain.** All jobs succeeded and were downloaded. No uncertain or pending paid job,
no paid animation. Originals and receipts remain in `meshy/`, `requests/` and canonical progress. Do not resubmit.
The stored animation library was checked; humanoid clips do not fit this four-wing animal. Local authoring follows
the flyer route. Multiview geometry was neutralized, repaired and decimated with head protection; rear wings were
made from the clean front membranes, shortened and swept back. Final body: **12,328 triangles**.

## Rig, clips, contact and scale

37 deforming bones plus beak/tail sockets. Four top-view wing chains carry weighted membranes; front/rear beats are
one quarter-cycle apart. Fly/Run hips, knees and feet flex with a delayed tuck/release, slightly offset left/right. Body LOD0 uses at most four influences. Coincident membrane seams share weights. Rest,
opposed-wing, fold and whip stress poses were inspected; 99th-percentile edge stretch stays at or below 1.256.
The largest local ratio is on a 6 mm edge, without a visible tear.

| Clip | Seconds | Role |
|---|---:|---|
| Fly | 0.833333 | Standing, walking, fidget; loop closure checked. |
| Run | 0.583333 | Faster flap, loop closure checked. |
| Attack | 0.75 | Back/side wind-up with head raised, whole-body forward bite, impact 0.458333; melee and ranged fallback. |
| Sting | 0.75 | Tail whip, supplied on all tiers as script role `sting`. |
| Cast | 1 | C wings-up Lightning Bolt, release 0.65; four violet-white joint glow sockets. |
| Hit | 0.5 | Recoil. |
| Death | 1.25 | Fall into the fitted corpse pose. |
| Dead | 1 | Folded feet, belly low, four wings spread on the floor. |

Every key and midpoint is measured, including attachments; worst body/edge floor penetration is 0.505 mm in interpolated
Run (0.075 world units at C scale), below the 2.5 cm gate. Attachments remain above the floor. The Dead belly is
2.13 cm above the lowest membrane; distal wing mean heights are 5.2–7.8 cm. Dead body height is 25.8 cm.
Living clips share one fixed 0.282129 m baseline measured across their wing strokes; their per-frame grounding
correction is removed. Fly and Run have zero root-height variation. Attack retains its intentionally authored
10 cm vertical motion, and Death eases the baseline out into the unchanged corpse. No binding `z_offset` is used.
All clips were transferred into the accepted LOD asset with zero joint-matrix difference and unchanged geometry.

There are no native sprites. [Area calibration](review/silhouette_area.json) compares matching spread top silhouettes:
concept area 0.840858 m² at a nominal 2.7 m span, model area 0.998425 m², factor **0.917706**. A raised-wing front
master is not comparable to the animated silhouette, so it was not used. Binding scales are 91.770611, 119.301794,
146.832977 world units per model metre (1:1.3:1.6). Resulting maximum spans are approximately 2.51/3.26/4.02 m.
Area matching takes precedence over forcing the approximate span targets.

Maximum bound heights are A 153.3, B 199.3 and C 296.1 world units (C includes Cast); staged height/radius rows are
154/127, 200/165, 297/202. The Quarry Face's 768-unit clearance comfortably contains the A clips. All roles, look
limits (20° yaw, 12° pitch), stride lengths, run and C cast bindings are explicit.

**Runtime limitation:** `game/fx/WorldFxSystem.cpp` selects one melee clip for both attacks; `secondaryAttack` changes
FX but not the selected melee animation. B still applies its designed secondary attack through monster data,
but currently displays Attack. Sting is exported and mapped for scripts; automatic selection is not claimed.
No engine workaround or actor behaviour was added under this asset-only work package.

## Materials, tier parts and LODs

One shared 2K base colour and 1K normal/metal-roughness/region-mask set; AO is locally baked. Regions are hide,
membrane and underside. `KHR_materials_variants` supplies `kite_a/b/c` colour ramps. C retains rust membranes and
cool ash hide; violet belongs to its edge static. No tier-specific runtime baked base colours or emissive texture.
The small bat route uses one set with 2.5× head UV density, rather than an unnecessary separate head material.
Retexture UV parity: 36,984 corners, zero unmatched or changed UVs (max error 2.98e-8).

B carries four 56-triangle wing-joint spur sets and a 148-triangle venom barb. C adds three 112-triangle neck/head
quill sets. Their final GLBs are in carrying-bone coordinates; separate world-space originals support Blender review.
The 973-triangle edge overlay is displaced 1 mm to avoid coplanar flicker, hidden for A/B, and uses C-only
`emissiveFactor [0.68, 0.48, 0.95]`. Cast sockets use `[225, 200, 255]`. Static parts are already simple, so they
need no separate LOD chain. No burn map is used.

| Level | Body triangles | C total including static edges and all parts |
|---|---:|---:|
| LOD0 | 12,328 | 14,009 |
| LOD1 | 6,163 | 7,844 |
| LOD2 | 3,082 | 4,763 |
| LOD3 | 1,540 | 3,221 |

The required LOD repair workflow was copied into this project and run without editing its shared source. The
25%/12.5% far ladder passes: switch silhouette errors 1.7%, 4.7%, 7.5%; colour errors 7.0, 7.5, 5.0.
**Recorded guideline deviation:** LOD1 carries up to six influences on 188 vertices; its fifth/sixth contributions
preserve the decimated membranes (largest weight beyond the first four 0.06195). The engine supports eight.
Other body LODs use at most four; rigid attachments use one. All nine staged GLBs report zero inverted closed parts.

## Placement and source changes

| Map | Placement | Preserved/replaced |
|---|---|---|
| Scour/out2 | Two five-A flocks on opposite Great Pit spoil rims; groups 150/151, indices 108–117. | Added 10; original 108 actors retained. |
| D3 Quarry Outpost | Two four-A flocks at Quarry Face, centres (2000,-2300), (3100,-2300), Z -1536; groups 150/151. | Added 8 at indices 59–66; original 59 retained. |
| Brood Spires/out3 | Four four-kite A/B spur flocks plus two four-kite mixed egg-field spire flocks. | Replaced 8 Sentinel/Heavy Sentinel actors (10055/10056), added 16 more; 24 kites, 89 total actors. |
| Crown/out4 | Four C each over B2 and G7 grafting yards; groups 150/151, indices 48–55. | Added 8; original 48 retained; clear of cannon range and test emplacement. |

All placements are direct actors, with their own Picture names; no encounter slots were changed. Existing `kites`
relations govern party/wild-beast hostility and Kreegan neutrality. The out3 family scenario keeps a flock beside
Overseer Prime active for 30 seconds: neither side loses HP or acquires an aim target. It also spawns all three rows
indoors with no actor model-load failure.

Changes live in each map's author/build source. D3's count gates now expect 67; its walkability test uses `last`
for its explicitly spawned Drudge. Out3's events 151/152 and generated regression now describe kite clearance,
preserve saved QBits 100501/100502, and omit the turret-specific autonote 10203. The historical
`brood_turrets.yml` filename stays registered in the shared queue; no turret shield assumption remains.
Abandoned plinth decorations remain. No hand edits to generated Lua, no terrain edits, no minimap or lighting
rebake for actor placement. Crown relief checks pass with zero findings; height range remains 32–5920.

## Audio and validation limits

Ten owned jobs in `design/kreegan_world/audio/jobs.yml`: six two-take sources (attack, wince, death, fidget, sting,
C cast) plus four C voice derivatives at -1.5 semitones. Planned cost 520 ElevenLabs credits, IDs 60160–60169.
Mono, 70 Hz high-pass, peak-window target -9 dB (-11 for fidget), maximum boost 10 dB. Thin shrieks, leather claps,
rattling hiss and crackling C screech. The final wrapper retry still fails before the first HTTP connection:
`URLError: [Errno -3] Temporary failure in name resolution`. [Retry evidence](review/audio_final.log).
Zero receipts, WAVs or picks; no `audio.yml` hooks were added. Native BBat descriptor sounds remain inherited in
staging until real voices exist. Audio failure did not block model, placement or staging.

`python3 tools/run_creature_review.py --project ... check` failed with **Chrome did not start**.
The minimized native launcher failed with **SDL_Init failed: No available video device** before any screenshot.
See [browser evidence](review/viewer_check.log), [desktop evidence](review/desktop_game.log).
Four prepared [map tours](review/tours/) remain ready. R5's authorized fallback was used: all three tiers/eight
clips rendered in background CPU Blender and inspected, plus staged headless scenarios. Browser playback at
normal/half speed, native appearance, cast bloom and map screenshots are unverified.

**Initial production validation (before the flight/bite follow-up below):** restage passed;
**109/109 regression scenarios passed**; family scenario **34/34 steps passed**.
Actor sizes: 22 maps, 1235 actors, zero mismatches. Decoration IDs: 22 maps, 3433 decorations, zero mismatches.
All 13 gated BLVs pass the serial walkability audit (18 examined; existing non-gated findings remain).
All four body LODs pass every clip at keys and midpoints with all eight skin-weight slots, including LOD1's six.
See [all-LOD gates](review/lod_clip_gates.json), [checks.json](review/checks.json),
[placement coordinates](review/placements.json) and [final hashes](review/artifact_manifest.json).
Suite logs: `output/hesper_stage/logs/scenarios_152144_268/`. The first integrated
suite exposed D3's stale spawned-actor index, which was fixed and passed its focused retry. It also found an
unrelated D4 walkability test still pointing to a newly placed Kennel Hound; that other map was not edited here
and its test now passes in the final shared-stage run.
The design audit has zero findings; its report was redirected here to preserve design sources.

## Viewer follow-up (2026-10-26)

The reported startup error came from a missing `review/viewer/feedback/user_feedback.json`. It now exists, and
`viewer_export.py` initializes it without overwriting saved findings. Copied humanoid labels, camera targets,
reference captions and feedback filenames now describe Ashkites. JavaScript syntax, all referenced local files,
model hashes and preservation of existing findings were checked. The browser wrapper still cannot start Chrome;
interactive playback remains unverified here. Refresh the viewer to load the corrected page.

## Flight and bite follow-up (2026-10-26, v4 checkpoint)

The user's Fly frames 15–25 exposed per-frame lowest-vertex grounding: when a wing passed below zero, the entire
body rose. The old Fly root moved 0.189786 m vertically; Run moved 0.282129 m. One shared living baseline now
clears the full flight envelope without frame-dependent snapping. Fly and Run root travel is **zero**, including
viewer frames 15–25 at 48 fps in all three exported tiers. Wing rotations are unchanged. Death eases the baseline
out, and the final corpse is unchanged within 0.00001 m. The dimensions above include the revised envelope.

The requested bite now leans backward and sideways with the head up (source frames 6–8), then drives the whole
body forward into contact at frame 11: **0.458333 s / viewer frame 22 at 48 fps**. Root travel from the coiled
pose to impact is 0.48 m forward; the beak rises for the wind-up and reaches in front for the strike. Follow-through
is at frame 13 and recovery at frame 18. All three melee/ranged fallback impact bindings match the contact time.
The viewer exposes Ready, Wind-up, Coiled, Bite, Follow-through and Recover anchors. Revision: `ashkite_v4_flight_bite`.

[Flight half-speed preview](review/fly_half_speed.gif), [bite half-speed preview](review/attack_half_speed.gif),
[full flight sequence](review/flight_motion_sheet.jpg), [full bite sequence](review/bite_motion_sheet.jpg).
All 40 sequence frames and 39 refreshed tier renders were inspected. Geometry, UVs, skinning, materials and LODs
are unchanged; non-Attack joint rotations match exactly. Every clip/LOD floor gate and Fly/Run closure passes.
[Measured correction](review/flight_fix.json), [bite movement](review/attack_motion.json),
[three-tier viewer check](review/viewer_motion_check.json), [clip merge](review/animation_merge.json).

The four owned maps were rebuilt with height/radius 154/127, 200/165 and 297/202; placement counts and terrain
were preserved. Crown relief still reports zero findings. Restage passes, as do actor sizes (22 maps, 1253 actors, zero mismatches), decoration IDs
(3433, zero mismatches), and the D3 walkability gate (zero findings). The 21 owned-map scenarios and family scenario
all abort on their first new-game/map-load step with `free(): invalid pointer` in the current game binary.
The unchanged Starport Reach arrival scenario reproduces it; GDB is blocked by `ptrace: Operation not permitted`.
The cause was unestablished at that checkpoint. The v5 retry below now passes with the current binary. Prior 109/109 results above belong
to the pre-motion-revision checkpoint. [Current logs](review/flight_bite_checks/) and `review/checks.json` preserve
the failed runs and successful static checks. Browser automation again reports `Chrome did not start`; the rendered sequences and numeric
GLB evaluation supply the review evidence, without claiming native GPU playback.

## Flight leg follow-up (2026-10-26)

The Fly/Run leg rotations were all constant. Revision `ashkite_v5_flight_legs` adds a wingbeat-delayed tuck/release
at both hips, knees and ankles, with the right leg delayed by 0.08 cycles. Fly spans about 20° at the hip, 16° at
the knee and 14° at the ankle; Run is 20% stronger. Feet move about 4.7 cm fore/aft and 2.6 cm vertically in Fly.
Both loops close; the shared baseline and zero body-height variation are preserved. Attack, the other clips,
geometry, textures, skin weights, LODs and height/radius remain unchanged. All three viewer tiers and the staged
animation tracks were checked against the new source. Exported-leg variation is now a runtime asset gate.

Inspected all 21 updated side frames and 26 Fly/Run foot close-ups:
[leg sequence](review/flight_legs_sheet.jpg), [half-speed leg preview](review/flight_legs_half_speed.gif),
[measurements](review/flight_legs.json). The full Fly preview above is refreshed; the v4 tier overview sheets remain
historical. All clip/LOD floor, loop, corpse and winding checks pass. Restage passes; actor sizes are 23 maps,
1253 actors, zero mismatches. **21/21 owned-map scenarios and 34/34 family steps now pass** with the current game
binary, resolving the previous runtime-verification blocker. No engine changes or builds were made here.
[Current validation logs](review/flight_legs_checks/). Chrome still cannot start, so interactive/browser and native
GPU playback remain unverified; the existing audio and automatic Sting limitations remain.

## Resume

Claim `hesper:ashkite` with `tools/creature_workspace.py`, read canonical progress, and reuse all three downloaded
Meshy tasks. There is no pending model-production step and no new paid model job is needed.

1. Further model revisions should rerun the focused owned-map/family scenarios under shared stage/engine locks.
   The v5 follow-up passes all 21 owned-map scenarios and all 34 family steps. No engine change/build was made here.
2. Once DNS works, take the shared audio claim, reread jobs, then use `tools/run_elevenlabs.sh plan/run/process/review`
   on exactly the ten existing IDs. Listen and record suggested takes. Add 60160–60169 hooks only after processed
   WAVs exist, release the claim, restage and verify sound coverage. User picks remain separate.
3. An explicitly authorized engine task can add automatic secondary-melee clip selection. Wire B to the existing
   Sting and verify the poison impact timing; do not claim this works from `script_clips` alone.
4. When desktop/browser tools work, capture every viewer tier/clip and the four prepared map tours through the
   approved wrappers. Check normal/half-speed playback, native C cast bloom and final map scale.

Own writes must use the workspace lease guard. Shared files need their claim directories and documented stage locks.
To regenerate the present runtime after a local animation change: `animate.py`, `corpse_gate.py`, `export.py`, copy
the eight exported attachments to `work/attachments_raw/`, then `merge_animations.py`, `finalize.py`, `gate.py`, `gate_lods.py`, winding,
`viewer_export.py`. Export overwrites attachments in world-rest coordinates; finalization must follow before staging.
`merge_animations.py` refreshes all eight clips in the accepted `work/hes_ashkite/r25_12.glb` while preserving
geometry, weights, materials and the verified LOD ladder. `fit_corpse.py` is a fitted-pose authoring tool, not a required export step.
Use `/snap/blender/current/blender --background --factory-startup --disable-autoexec --threads 4
--python-exit-code 1 --python <script>` with `timeout -k 5 180`; scripts flush and exit to avoid this host's shutdown hang.
Do not run `install_model.py`, edit `assets_dev`, or build the engine for this package.
