# Original transition-edge treatment — reference1264

User accepted the current master direction, then requested restoration of the dark transition treatment visible in
`test_img/1264.png`. The accepted materials stay fixed. The v5 edge pass is complete, baked at 256px, and reviewed in connected layouts and native game captures.
See [the comparison gallery](../review.html) and [final review record](../reports/review_v5.json).

[Original/current comparison](original_vs_current.png): native nearest enlargement, filtered enlargement, current
composite. Inspected the complete original9-road,12-grass/dirt and12-rock/dirt sheets as well.

## Findings

- Roads have an actual painted dark contact rim in the opaque source pixels, especially along the lower/outside
  edge and around end stones. Filtering softens it but does not create it. Stones near the perimeter are drawn to
  end at the road boundary. The current masked master sometimes cuts through a stone, losing its shaded outer side.
- Grass edges have a subtler uneven dark-green/brown fringe and local softness. It varies with the painted clumps;
  it is not a uniform black outline. The current binary-derived mask preserves a silhouette and thin antialiasing,
  but not this edge colour/relief information. Differences in overall texture scale also affect the comparison.
- Rock/dirt has irregular speckled edges, but the strong dark rock texture makes a separate contact rim less clear.
  It should not inherit the road's shadow strength automatically.

The composer currently uses linear-light dirt/foreground interpolation from coverage alone. Thresholding the AI
coverage at128 and applying a narrow signed-distance antialias band intentionally excludes shading. Those masks
are still useful for material ownership, but they do not reconstruct all the original boundary appearance.

## Follow-up treatment

Keep coverage and edge appearance separate. Preserve the existing shared coverage contract; add a narrow, tinted,
variable-strength boundary-shading layer and locally softer coverage where the source supports it. A road also
needs edge stones/grout to terminate naturally instead of merely outlining clipped stones. Use original tiles as
references for this local detail; preserve the master material away from the boundary.

Pilot a road straight plus turn/endcap and a grass straight plus corner. Review each in its connected layout and
the saved overview before processing the other members. Judge the band at256px; broad blur would lose crispness,
and a constant black stroke would exaggerate it. Width/strength remain to be tuned visually rather than asserted
as measured source values here.

Any added shading or edge-colour layer must obey matching tile-border profiles, just like coverage. Recheck final
RGB joins and four-tile corners after baking; equal coverage alone cannot guarantee shaded composites match.
The final output remains opaque256px RGB, so this authoring layer needs no additional runtime texture fetch or
shader pass. Water remains excluded.

## Implemented authoring workflow

`raw/v1/` contains separate imagegen colour edits; `prompts/v1/` and the JSON beside each raw image retain exact
prompts, references and original generated-image paths. Road and grass edits use the v4 composite as target and
the native128px tile as a boundary-style reference. The rock pilot's two-reference requests failed twice with
HTTP500; its simpler single-target edit succeeded. Rejected art and service retry details are in `feedback.json`.

`bake_edges.py` extracts only the local AI RGB change into a separate linear-light delta layer. For roads/grass,
the coverage-derived support is full through10 authoring pixels and fades smoothly to zero by24px. Rock uses a
narrower6..16px band and65% strength. These are edit-support widths, not a uniformly painted shadow width.
The actual irregular fringe, stone sides and mineral details come from imagegen. Protected material interiors
must remain byte-identical to v4. Coverage masks remain `masks/connected_v4/`; no new runtime alpha is introduced.

Equivalent boundary sides share the mean AI RGB delta for their axis/material topology. The first8 authoring
pixels use mirrored common profiles, approaching each tile's own detail through a further24px. Pure-material
edges and corners receive no edge delta. This extends the existing mask/material seam contract to the painted
appearance, including the support of512-to256 Lanczos downsampling.

`layers/<version>/*.npz` preserve signed linear RGB deltas separately from material coverage;
`*_band.png` preserve edit-support masks, and `shared_profiles.npz` preserves common boundary appearance.
The engine only receives baked RGB PNGs. `runtime/<version>/` and `../composites/<version>/` keep versioned exports.

```sh
python3 level_generation/terrain/mm6_new_sorpigal_transitions/edge_treatment/bake_edges.py --version v5
python3 level_generation/terrain/mm6_new_sorpigal_transitions/check_composites.py --version v5 --runtime-dir level_generation/terrain/mm6_new_sorpigal_transitions/edge_treatment/runtime/v5
```

`--pilot` permits missing AI edits for intermediate review only. Final baking requires all33.
`--publish-runtime` copies the reviewed candidate into the project's prepared runtime overlay, never production assets.
The final game trial uses a frozen executable, because unrelated workspace builds can change during generation.
