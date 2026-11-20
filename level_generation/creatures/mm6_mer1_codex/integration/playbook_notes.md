# Round 3 notes for the orchestrator

- Preserve dense head/hands outside the clothing reduction and rebake; dedicated sets avoid reprojection drift.
- Native luminance rank mapping amplified subtle skin noise. Linear exposure preserves generated skin detail.
- Apparent armpit/waist tears were partly exaggerated tangent normals, confirmed by equal source/export poses
  and a normal-disabled render. Positive-hemisphere, low-amplitude garment normals remove those visual flaps.
- Four-influence weight fitting over retained clips clears shoulder stretch without adding geometry patches.
- A folded robe hem violates the shared containment check's planar-opening assumption: see
  ../review/round3/cloth_findings.json. Do not silently waive this or count a virtual cap as real cloth.
- No shared checker/playbook change was made in this production project. Dedicated shoulder-volume and
  hem-vertex acceleration checks remain unavailable in the current shared runner.
