# Terrain iteration and review policy

## Seam contract

1. **Material repeat:** inspect each master in a 5×5 patch before blaming masks. Matching mask edges cannot repair a
   material that does not wrap. Keep versioned masters and record user-requested replacements; [256px diagnostics](master_edge_diagnostics.json)
   report boundary/internal gradient ratios around 0.52–1.37. These are not proof of seamlessness. If a visible master
   seam blocks final qualification, make a versioned, narrowly repaired derivative with imagegen, preserve its accepted
   interior and review it explicitly. The user explicitly requested replacing dirt v4 after screenshot1263; preserve the older version for comparison.
2. **Shared edge profiles:** choose and review common crossing positions, road widths and detailed coverage profiles
   from native neighboring tiles. [adjacency_constraints.json](adjacency_constraints.json) groups connected compatible
   edges into 22 initial groups. Groups are connectivity constraints, not 22 ready-made mask images. Pure edges can
   use constant coverage; mixed edges need actual reviewed pixel profiles. N/S profiles read left-to-right, E/W
   top-to-bottom: no implicit reversal. Corner endpoints must agree across all four tiles meeting there.
3. **Boundary authority:** lock a common 8-authoring-pixel strip as the initial working convention, with a further
   narrow interior repair zone. Every connected tile must use the same reviewed boundary behavior. An edge repair
   changes the shared profile and all dependent tiles together. Do not independently blur four edges or paste a
   hard strip that creates a second seam inside the tile. Imagegen can repair the interior-to-strip join; mechanical
   enforcement retains the final boundary contract. Strip width is a versioned parameter, not an artistic guarantee.
4. **Material pixels:** use common periodic material boundary strips/consistent samples as well as mask strips.
   Equal masks alone do not imply equal RGB. Preserve continuity of texture features and first-neighbor gradients;
   copying a single row of equal pixels can still produce a visible line.
   Painted edge appearance has the same contract: keep coverage separate from contact shading/fringe/stone endings,
   and propagate a shared appearance profile to every equivalent side before reducing to runtime size. Protect
   accepted master interiors. Do not add a uniform black stroke or blur the whole composite to imitate source bleed.
5. **Downsampling:** build at 512, reduce finished colour composites to 256 with a fixed filter and compatible edge
   extension/guard pixels. Do not let unrelated padding contaminate mixed edges. Recheck the exported 256px tiles:
   passing at 512 is insufficient. Recheck engine-generated mip levels and both directions of oblique viewing.

A single transition tile generally should **not** repeat seamlessly against itself: its opposite sides intentionally
contain different materials. Repeat complete valid layouts; use single-tile repeat only for pure materials and valid
straight-road directions. Test every valid observed join, not arbitrary unrelated tile pairs.


For each iteration:

1. **Pilot:** grass straight plus connected corners/X-corners, rock equivalents, and a road straight plus turn/cap.
   Review silhouettes and shared profiles before spending calls on all 33. The remaining family members inherit the
   reviewed edge contract, while their interiors are separately extracted.
2. **Structural gate:** all 33 masks must be opaque grayscale 512px, correct polarity, source orientation and topology.
   Run `check_masks.py`; matching material coverage at compatible joins must differ by at most 1/255, at both authoring
   and mechanically reduced runtime sizes. Compare in global material weights so different-family white masks cannot
   falsely match. Source conflicts are reported separately. Inspect width, silhouette, islands and narrow necks against
   originals; the automated check cannot validate those semantic interior details.
3. **Flat image gate:** composite all 36 tiles; review all pair/corner cases, then longer legal layouts, with grid off.
   Fail any visible tile-border line, chopped feature, sudden colour jump, halo, widened/narrowed road, corner pinhole,
   or conspicuous repeating band. Check mask and RGB separately. Numeric edge gradients rank suspects but cannot
   override a visual failure or certify a pass.
4. **Engine gate:** native flat fixture, terrain x2, fixed executable/settings/light/time, fixed top-down and low-angle
   cameras facing E/W/N/S, close/medium/far distances, bilinear and the intended anisotropic mode. Check slow camera
   motion for mip/LOD shimmer. Store actual screenshots, camera poses, settings and file hashes. Browser checks alone
   never satisfy this gate. No new geometry or dynamic grass is required to evaluate tile continuity.
5. **Map gate:** rerun all four saved New Sorpigal viewpoints plus representative transition-heavy and corrected-conflict
   locations. Flat terrain catches seams; real slopes reveal stretching/filtering issues. Water remains outside acceptance.
6. **Feedback and retry:** record a case ID, side/corner, mask vs material vs sampling vs map-layout failure, severity,
   screenshot crop, candidate hashes, exact requested change and locked invariants. Send imagegen the failed source/mask,
   neighboring masks, shared profiles and crop. Change one cause at a time. Every edge/material change reruns all dependent
   pairs/corners; changing a shared material reruns the whole family and pure repeats. Keep versions immutable.
7. **Stop rule:** after two unsuccessful targeted retries for the same defect, stop blind regeneration and inspect the
   constraint, source ambiguity, master periodicity or downsample/mipmap path. Do not relax the seamlessness gate to
   finish a batch. Acceptance requires structural, flat-image, engine and map gates plus recorded visual review.

Use [feedback_template.json](feedback_template.json) for each failure. Accepted master selection is retained, but it
is distinct from final composite seam qualification.
