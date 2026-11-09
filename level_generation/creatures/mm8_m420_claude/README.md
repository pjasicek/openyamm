# MM8 Pirate Mage — m420

Claude humanoid-playbook production for the Regnan Sorcerer, Battlemage and Archmage (monster ids 16–18),
and Pirate Seer, Magi and Wizard (187–189). All six share this rigged body and gold cobra staff.
The right lower leg is a wooden peg; the left leg retains its striped stocking and buckled shoe.
Both hands have individually fitted fingers. The long coat, gold trim, white shirt, red sash and forked beard
follow the native sprites and the selected generated references.

## Delivery

- `work/pirate_mage_final.blend`: packed editable master with all nine animations on a 120 Hz export timeline.
- `export/mm8_m420.glb`: body, six native material variants, colour and shadow LODs.
- `export/mm8_m420_staff.glb`: rigid cobra-staff attachment, fitted to the right fist.
- `review/viewer/`: shared browser review controls, six palette previews and all nine motion roles.
- `review/palette_review.jpg`, `review/final_playback_grid.jpg`, `review/lod_review.jpg`: review sheets.
- `export/install_receipt.json`: authoritative source/runtime hashes. The installed body and staff live under
  `assets_source/worlds/mm8/models/` and are cooked into `assets_dev/worlds/mm8/models/`.

The current revision is **m420_coat_skin_v8**. The browser URL is
<http://127.0.0.1:8420/level_generation/creatures/mm8_m420_claude/review/viewer/>.
If needed, serve the repository root with `python3 -m http.server 8420 --bind 127.0.0.1`.
The viewer bakes the same palette-ramp rule used by the engine; runtime materials share base maps and region masks.

Body triangles: **12,008 / 6,082 / 3,128 / 1,644**. Staff: **1,800 / 900 / 450 / 224**.
The rig has 58 bones, including four twist helpers, Staff and Socket_Staff; exported vertices have at most four
influences. Body and head each have a 1K PBR set, merged into a padded 2080×1024 runtime atlas. The staff has a 1K set.
ORM channels are specular mask, roughness and zero metallic. `prepare_actor_glb.py` converts the Meshy normal maps
to the runtime glTF convention. The peg keeps its 160 triangles at every LOD because reduction crossed its UV
seams and sampled adjacent coat islands. This small budget exception preserves the defining leg and its material.

## Native identity and materials

| Descriptor family | Ids | Palette ids | Coat / hair |
| --- | --- | --- | --- |
| Pirate Mage Male A–C | 16–18 | 421 / 422 / 423 | Green/brown, blue/grey, burgundy/blond |
| Wimpy Pirate Mage Male A–C | 187–189 | 649 / 650 / 651 | Burgundy/blue, purple/orange, green/blond |

`native/inventory.json` records source frames, descriptor data and hashes. The source BMP's embedded palette is not
this creature's base palette; references were rendered with ACT 421 before generation. `textures/pirate_mage_ramps.json`
uses the changing native coat/hair palette entries, weighted by actual standing-frame pixel counts. Gold, skin,
shirt, sash, breeches, stocking, shoe and wood retain their own material colours. Stray projected collar and shirt
colour on the head/neck and beard was corrected during texture composition.

## Motion and fitting

Standing 3 s; Walking 1 s; Running 0.733333 s; Attack and Cast 1.75 s; Hit 0.633333 s; Fidget 1.4 s;
Death 1.3 s; Dead holds the final fall for 0.1 s. Local humanoid-set and Mixamo sources were selected before modelling
and are recorded in `motion_selection.json`. No paid animation actions were purchased and no raw library clips
are installed. Attack and Cast use the selected dual-hand source: both arms draw back and extend forward together, with the
right fist gripping the cobra staff and the left palm open. One continuous whole-body source timeline coordinates the channel
and release from the start. Shoulder-relative wrist paths are smoothed before fitting; the shoe and peg support the weight shift.
The release cue is **1.25 s**, matching the native attack duration. Gameplay recovery, stats, spell choices and AI
remain unchanged. Both ranged attack and spell casting charge and release through `Socket_Staff` at the cobra head.

The source animation rest frames are retained while joint positions, fingers and weights are fitted to this mesh.
The peg is rigid to the right calf. Garment islands, cuffs and coat tails have explicit weights. Forearm twist helpers distribute wrist roll;
the coat shoulder roots follow the upper arms without counter-twist. The running grip is displaced outward to clear the coat. The cast uses the dual-hand source with whole-body channeling and shoulder-relative arm reach. Its elbow remains low,
with one continuous wrist-roll solve and exact matching to Standing at both endpoints.
The fidget turns the staff across the waist as in the native animation. The fall retains the staff in the fist and
places both body and equipment above the floor.

Scale **119.387352** maps the measured 1.683595 m standing body to **201 native pixels**, excluding the staff.
All six bindings use explicit equal scale. Runtime strides are 1.768 m walking and 3.991 m running, measured on
planted shoe/peg surfaces rather than the virtual right foot; `work/physical_stride.json` retains the contact samples.
Head look is limited to 30° yaw and 15° pitch.

## Verification

The original authored sweep has no staff/body or head/shoulder triangle intersections and keeps the lowest support
at 2 mm. The revised Attack/Cast exports also pass a fresh 120 Hz intersection/floor sweep. The exported 48 Hz sweep also has no intersections; its minimum floor clearance is 0.57 mm during running.
Maximum Blender/export surface discrepancy is 0.598 mm between samples and 0.0074 mm at integer source frames.
Finger-edge stretch remains below the playbook threshold. Source-versus-fitted rotation diagnostics are retained
in `review/export_physics.log`; the current cast measurements are in `review/dual_cast/motion.json`.

UV raster overlap is two pixels (0.002%) on the body and 0.21% on the head, within boundary tolerance. Neither atlas has
degenerate UV triangles. Meshy omitted one narrow lapel face and shifted one nearby corner by 0.058 mm. The rigged
geometry is retained and that face extends its adjacent UV chart coherently. No degenerate exported geometry or
inverted closed components were found. All six palettes and nine clips passed the browser checker (54 combinations).
Actual playback covered the eight distinct motions at normal and half speed; Cast shares Attack. Face and grip
close-ups cover all six palettes. The viewer disables stale skinned frustum bounds so switching from Dead to a head
close-up cannot hide the head; this is a browser-preview correction only.

The development build and the focused Pirate Mage regression passed, including a run with MM6 active and no native
sprite metadata supplied to the binding. The regression verifies six distinct palettes on one shared asset, equal
scale, all clips, head-look and staff nodes, the casting release contract, and unchanged actor simulation state.
The original production MM8 actor suite passed **33 of 34** cases. The only failure is the unrelated Triton binding/simulation
case; see `review/mm8_regression_final.log`. The Pirate Mage case passes in both the MM8 suite and the focused
MM6 cross-world run.

Eight native OpenGL runs on the NVIDIA GPU captured 176 frames: all six palettes as models and original sprites
in both `oute3.odm` and `6d19.blv`, with identical cameras and spawn offsets. Autonomous movement varies their
poses and distances between captures. `review/ingame/native_comparisons.jpg` compares their appearance;
`death_review.jpg` shows fall, floor contact and the ordinary loot-bag transition. Full frames, tours, GPU log
excerpts and run receipts are alongside them. The sprite-only fixture preloads the six original frame families
for these MM6 maps; missing HUD artwork in that fixture is unrelated to the creature.

Source bitmap/palette hashes and all installed artifact hashes were rechecked unchanged. Concurrent builds
replaced the normal executable during one launch, so subsequent captures and the final suite used a hash-verified
copy of the development binary; `review/ingame/native_binary.json` records it. These minimized-window captures
verify rendering and behavior, not GPU performance.

## Cast revision — 2026-10-18

User feedback requested a Sorcerer comparison and reported an elbow/shoulder inconsistency at viewer frames 62–75.
The old clip turned the torso/clavicle about 31° in one 48 Hz frame before release. Its constrained arm then held
the shoulder high. The revised clip uses the accepted Sorcerer casting gesture rather than its two-handed attack;
the Pirate Mage keeps the native one-handed staff release.

Shoulder-frame motion is now at most 1.54° per 48 Hz frame. In the reported 62–75 range, the staff upper arm and
forearm move less than 0.70° per frame. The fitted wrist stays below 47° bend and 87° roll. Both endpoints match
Standing world matrices within 0.00001. Release remains 1.25 s; actor bindings and gameplay timing are unchanged.

`review/cast_revision/before_after.jpg` and `after/` show the repaired region; `sorcerer_reference/` retains the
reference comparison. `motion.json`, `physics120.json`, `validation.log`, `export_preservation.json`, final browser
playback and native capture receipts document the checks. No additional Meshy credits were spent.

The installed revision passed focused Pirate Mage regressions with MM8 and MM6 active (1/1 each), all 54 viewer
palette/clip combinations and four Attack/Cast playback runs at normal/half speed. Four final NVIDIA OpenGL
runs captured 60 frames across all six palettes indoors and outdoors; selected sequences are in
`review/cast_revision/ingame/cast_review.jpg`. Run receipts and GPU/capture logs are preserved beside the frames.
The other seven animations, geometry, skin and materials are preserved exactly; their prior visual evidence remains
applicable. The full actor suite, Android/Vulkan builds and performance benchmarks were not repeated for this revision.

## Two-handed cast trial — 2026-10-18

The user selected the recommended compact dual-hand gesture after comparing local source previews. The source's
near-straight elbows needed a stable downward bend direction and 94% maximum arm reach on this fitted body.
Wrist trajectories are smoothed with a 42 ms Gaussian window before IK. The staff follows a wrist-safe direction
near upright; its palm roll is chosen continuously over the clip. Left fingers open from their fitted pose.
Deep source crouching is reduced to a small weight shift over the planted shoe and wooden peg.

The revised clip lasts 1.75 s and retains the 1.25 s gameplay release. Both endpoint world poses match Standing.
Right wrist bend stays below 39 degrees and roll below 39 degrees; the left wrist is limited to 55/90 degrees.
The export passes 120 Hz staff/body and head/shoulder contact checks, 48 Hz all-role checks, surface parity and G5
hand stretch (right 2.11x, left 1.80x). Physical support remains within 5.4 mm (shoe) and 9.1 mm (peg) of the floor.
The browser passed all 54 palette/clip combinations and four normal/half-speed Attack/Cast playback runs.
`review/dual_cast_v5/viewer_shots/release.png` shows the forward release; `motion.json`, `physics120.json`,
`support.json`, `endpoints.json`, `export_preservation.json` and `validation.log` record the measured checks.

Only Attack/Cast samplers change in the body and six palette previews. The seven other clips, mesh/LOD geometry,
skins, nodes and material/image payloads are preserved exactly. The prior Sorcerer-style revision and its scripts
are retained in `review/dual_cast/baseline/`. No new generation or Meshy credits were needed.

The installed revision passed focused Pirate Mage regressions in MM8 and MM6 (1/1 each). Four native
NVIDIA OpenGL runs captured 60 frames across both palette groups indoors and outdoors. The dual-arm
gesture, staff grip, ground support and staff-head spell effects were inspected. Captures, run receipts
and GPU logs are in `review/dual_cast_v5/ingame/`; `cast_review.jpg` collects representative frames.
These minimized-window runs do not measure performance. No engine rebuild or full actor-suite rerun
was needed for this animation-only revision; Android/Vulkan checks were not repeated.

## Continuous wind-up correction — 2026-10-18

The user identified a pause at Attack frames 29–36 (48 fps). The preparation blend ended at 0.60 s, before
the source gesture began at 0.75 s. Extending that blend through 1.0 s overlaps the motions and removes the hold.
The same correction applies to Cast. Release remains at 1.25 s and the full clip lasts 1.75 s.

`review/dual_cast_v6/windup.json` compares the previous master, corrected master and delivered export. Both hands
previously had stationary frames; the export now moves at least 11.14 mm left and 1.63 mm right per frame
through the reported interval. `verify_cast_windup.py` asserts that every step exceeds 0.5 mm.
`review/dual_cast_v6/viewer_shots/windup.jpg` shows frames 24–48. Normal/half-speed Attack/Cast, side/back arm
close-ups, 54 palette/clip combinations, contact/support, exact endpoints, surface parity and G5 passed.
Two current NVIDIA OpenGL runs supplied 30 indoor/outdoor frames; focused MM8 and MM6 regressions passed 1/1 each.
Native captures, GPU/run receipts and representative frames are in `review/dual_cast_v6/ingame/`.
The v5 master, source scripts, body exports and review evidence are preserved in `review/dual_cast_v5/`.
No new generation, engine build, full actor-suite rerun, Android/Vulkan build or performance check was needed.

## Whole-body channel and release — 2026-10-18

The user identified that the first 36 frames still left the body and legs static. The arm-only lead-in was the
cause: source time remained zero for 0.75 s. The current revision removes that delay and runs the complete source
gesture on one smooth timeline. A slower gathering phase lowers the hips, bends the knees and turns the chest;
the body rises and drives forward with the hands into release. Recovery returns the complete body to Standing.
Source body rotations are retained at 50% and pelvis travel at 30% to fit this stance and wooden peg.
The timeline reaches source time 0.5 at the unchanged 1.25 s release, then finishes at 1.75 s.

`review/dual_cast/windup.json` compares v6, the corrected master and delivered export. In the first 36 frames,
pelvis travel is 50.93 mm, chest rotation 23.23 degrees, thigh rotation 22.68/21.18 degrees and calf rotation
15.64/20.23 degrees. The prior torso rotation was zero. Pelvis motion is checked at frames 8, 16, 24 and 36;
body/leg rotation steps stay below 7.87 degrees per 48 Hz frame across the clip. Both hands retain continuous motion.
Physical floor clearance remains within 6.1 mm for the shoe and 19.5 mm for the peg throughout the cast.

`viewer_shots/channel.jpg` and `side.jpg` under `review/dual_cast/` show the full-body progression. Front, side,
back, hand and foot views, normal/half-speed playback, 120 Hz contacts/support, exact endpoints, surface parity,
G5, all 54 viewer combinations and 30 frames from two native NVIDIA OpenGL runs passed review. Focused Pirate Mage
regressions passed with MM8 and MM6 active (1/1 each). The v6 masters, scripts, exports and evidence are retained
in `review/dual_cast_v6/`. No new generation or Meshy credits were needed.

## Coat deformation correction — 2026-10-18

Attack frame 44 exposed arm-weight bleed into the chest and mismatched clavicle weights across the collar.
`coat_weights.py` puts the medial coat on pelvis/spine/neck, blends the sleeves smoothly across the shoulder,
and removes upper-arm counter-twist from the coat. It preserves the tails, cuffs, hands, peg and other parts.
All nine animation samplers, including the full-body channel, are identical to v7. LOD topology is unchanged;
regeneration introduced less than 2 micrometres of coordinate roundoff. No textures or Meshy jobs changed.

`review/coat_skin/poses.jpg` contains the reported pose and surrounding frames, including side/back views.
Maximum upper-coat edge stretch at frame 44 dropped from 3.49x to 2.44x; p99 dropped from 2.23x to 1.95x.
The previous G4 arm-only mask missed central coat contamination; the new scope check explicitly rejects
arm/clavicle weights on the medial chest/collar and protects coat tails. G4 samples across all nine roles
remain recorded; some extreme poses exceed the approximate 2x p99 guide and were visually inspected.
The revision passed export parity, contact/support sweeps, G5, endpoint and full-body windup checks, 54 viewer
combinations, normal/half-speed playback, four LOD reviews, two native runs and focused MM8/MM6 regressions.
The v7 master and evidence are retained in `review/coat_skin/baseline/`. The user approved this coat-deformation
correction on 2026-10-18 with “good”.

## Provenance and reproduction

Five selected HD body views, four head views and the isolated staff reference are retained with prompts and receipts.
Meshy jobs cost **45 credits** against the 100-credit project limit: body geometry 5, staff geometry 5, rig 5,
staff retexture 10, body retexture 10 and head retexture 10. All original returns are downloaded and retained.
Reuse their task ids and files; no external job remains pending.

Claim the project with `tools/creature_workspace.py` before writing. Use its guarded runner and
`tools/run_creature_blender.sh --token` for project scripts. The selected animation base is `work/master_settled.blend`.
The original construction is `build_actions.py` → `sync_and_texture.py` → `settle_final.py`.
For the current cast, run `author_dual_cast.py` → `finish_cast_revision.py`. Authoring applies `coat_weights.py`
to the retained source master before saving; export rebuilds all colour/shadow LOD skins and viewer palettes.
The skin-only repair is reproduced with `finish_coat_skin.py` from the retained v7 baseline. Run
`verify_coat_skin.py` to check repair scope and identical animation samplers. The old sampler-only
`update_cast_exports.py` predates this skin correction and is no longer part of the selected pipeline.
`compose_pirate_mage.py` creates
material maps and native ramps. Export through `export_final_lods.py`, then `finalize_exports.py` and
`audit_exports.py`; the finalizer preserves the peg, prepares shadow LODs, attaches palette variants, splits the staff
and merges head materials. `viewer_tiers.py` creates browser-only palette previews. Install unprocessed final exports
with `tools/install_model.py`. Runtime bindings are in `assets_dev/worlds/mm8/models/actors.yml`.

Technical completion and agent visual review are separate from user artistic approval. Android/Vulkan builds and
performance benchmarks are outside this asset-validation run. Original sprites and unrelated bindings are preserved.
