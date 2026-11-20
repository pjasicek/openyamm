# natm production lessons

- Check the native death direction from the whole sequence. The first forward-collapse choice was wrong; the selected source is Mixamo's backward death.
- Keep the humanoid source frames and fit measured anatomy. Elbow pole continuity and actual angular acceleration matter more than a clip's name.
- Align gait to the visible sole, not just Foot-to-Toe0 joint direction. natm needed a 16-degree correction on each side.
- A forearm buckler's upper strap must stay below the elbow; the initial strap crossed the bending joint. Validate straps along with the shell.
- Select the entire simplified grip cylinder, including both end rings. Cutting one ring out of the audit region falsely produced 90 mm hand gaps.
- Measure the cupped palm's actual contact-surface normal. The open-hand plane differed from the closed palm's local contact patch.
- Test leg-in-panel volume and panel-in-skin triangle interiors. Either direction alone missed the falling rear panel's overlap.
- Per-row unconstrained contact pushes caused cloth jitter and were rejected. Fit a coherent panel-normal clearance, then a small targeted bidirectional fall correction.
- Preserve clear gaps between distant feathers with a rebaked alpha cutout. Dedicated shadow LODs must remain OPAQUE; use an opaque proxy even when the colour feathers use MASK.
- Recheck skin after far-LOD rebaking/downsampling. Restoring the near skin luminance distribution preserved native mean and highlights on every tier/LOD.
- Shared audit sampling needs float32 endpoint de-duplication; a 40 ns final interval falsely became the fastest weapon motion. A one-frame held clip also needs a third, midpoint sample to measure zero acceleration.
- The shared runner measures raw hand roll against the source hinge frame. Keep that measurement and separately measure the wrist against its actual distal forearm twist frame; do not move the elbow landmark to the helper's head.
- Decorative feather floor contact needs a separate visual gate: skin/feet/props can clear the floor while rigid cape strands pass below it. Review round 1 fixes it with feather-owner deformation helpers and validates every solid-body vertex in a shared-runner Death/Dead floor probe.

Review round 1: keep helper children under their original bone owner for upper-body layering. Copy deformation using both source and helper inverse rest frames; their edit-mode frames can differ. Repack shared UVs with dilated margins, retain pixel density, and report decoded texel area separately from compressed GLB bytes.

Review round 2: counter-rotate the head in world space during torso wind-up. Keep neck/head bind offsets and remove constant translation/scale channels from the export. Blend collar skin smoothly into the neck without clavicle influence at the throat. Use the existing shared edge-stretch selectors for a separate neck probe; do not invent a replacement gate suite. The shared runner still needs explicit head-facing and Cast-palm targets.

Measure the casting palm on the final skin surface, not an inherited socket offset. Forearm shields need checks after wrist presentation changes at every LOD. High-pass colour detail from isolated UV charts can leave triangular skin patches; use coherent object-space grain for the uniform albedo, with small facial features preserved. Round 2 deliberately removes the old native lighting contrasts and records the raw-native percentile mismatch in HANDOFF.md.
