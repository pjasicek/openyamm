# Proposed playbook notes (orchestrator to review; no shared playbook edited)

- The squat dwarf's shirt, shoulder yoke and nape are close together. Bind the yoke/studs to the actual supporting shell;
  nearest-surface weights can accidentally bind a shoulder stud to the beard. Give each small stud one coherent weight blend.
- Short tunics need an inner-trouser overlap that follows the outer hem. Trim genuinely hidden upper trousers, taper
  the overlap inward and transfer nearby hem weights there. On this model the source Death's wide legs also needed
  reduction to 40% of their local motion from Standing; re-fit the corpse to the floor afterwards.
- An open hem invalidates a generic nearest-face signed-distance test: exposed trousers can be classified as poking
  out by several centimetres while no surfaces cross. This project uses two-way triangle/edge crossing at 48 Hz and
  requires zero crossings on every clip; keep the rejected diagnostic explicitly labelled.
- Smart UV Project can produce overlapping head charts. The whole-body Meshy return supplied an overlap-free
  alternative; two omitted triangles kept independent original islands. Repack only the head and reproject all maps,
  converting tangent normal bases. Final strict overlap is zero on both atlases, with no collapsed islands.
- Local whole-body retexture UV transfer was accurate below 0.7 micrometres. Preserve the full upload bounds for fitting
  a head subset to a whole-body return; use head-only bounds only with a head-only return.
- The source frame, thumb/finger connectivity and a fixed grip solve remain necessary on a broad hand. Left fingers
  at 45% source curl give a relaxed hand and avoid source-relative rotation spikes. Final hand edge maximum is 2.818×.
- With the real modelled axe, a 60° attachment roll gives a signed cutting-edge lead of +0.941 at 0.71875 s.
  Recheck the final exported samples: the earlier Blender pilot selected 0.739583 s, one 48 Hz interval later.
- Review round 1 corrects the earlier exporter diagnosis: reduced LODs have WEIGHTS_1 as well as WEIGHTS_0.
  A partial WEIGHTS_0 sum below one is valid. The local normalizer and validator missed the second set and caused
  the rejection; this is not evidence of a shared-exporter bug. Normalize all influence sets jointly after all
  body/head/shadow merging and splitting, immediately before writing the final runtime GLB. Validate every final
  primitive with a strict <1e-4 combined-sum error and bind the report to that file's SHA-256. Current max: 1.22935e-7.
- Workbench's fake specular highlight ignores actual roughness maps. Disable it for neutral colour review and use
  PBR prop closeups to judge metal. Native renderer material review remains an orchestration gate.
- Viewer source-pose anchors may deliberately have no native image (measured impact). Hide the native image then;
  otherwise continuous playback repeatedly requests `undefined`, a failure missed by checks at clip time zero.

- Round 2: a global lowest-point floor check cannot prove that both soles are level. Select actual bind-space
  sole contact patches, measure each plane and heel/toe heights after export, and solve each ankle with leg IK.
  This dwarf needed bounded leg extension (max 3.30%) to reach flat targets while keeping existing hip/body keys.
- Anatomical elbow hinges come from the cloned source frames, not the tiny kink in a fitted A-pose. That kink
  produced misleading off-plane numbers. With source-frame calibration, Attack/Fidget needed upper-arm roll
  correction; preserve the forearm's world matrix, rebake the helper and recheck G4–G6 and interpolated joint paths.
- Keep the orchestrator's existing `animation.cast: Attack` alias when reinstalling this non-caster. The unchanged
  project actor snippet predates that integration correction; round 2 requires only the body GLB replacement.

- Round 3: `animation.cast` is now explicit in the project snippet as well as installed entries. Run the shared
  `check_bindings.py` against staged descriptors; it validates all referenced project exports before installation.
- Grounding a run by the mesh's global minimum does not constrain airborne frames. Measure the lowest actual sole
  through the entire cycle and report contact percentage. Short legs need a lower root path and explicit foot targets.
- A flat foot throughout a walk can still shuffle. Measure individual heel/toe lift and mid-swing knee flexion.
  The dwarf now has 9.4 cm clearance and 56–57° knees; 120 Hz IK sampling holds flat support under interpolation.
- Match support travel to the runtime gait phase: `stride_length` is multiplied by 1.55 when running. The accepted
  0.89 m descriptor therefore needs 1.3795 m run travel, not an independently estimated stride.
- A connected tunic needs coherent central panels and smooth side-strip blends. Add whole-panel edge stretch to
  the gate, keep covered cuffs/studs on the host weights, and check real crossings after changing either legs or cloth.
