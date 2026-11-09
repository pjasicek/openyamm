# MM6 PeasantF3 — Cutpurse / Bounty Hunter / Assassin

User accepted the creature otherwise; **review round 3 Death timing is complete**.
Death is now **2.144444444 s**, previously 2.979166667 s. Frames 100–143 at 48 fps run 1.5× faster,
then the whole result runs 1.25× faster. All poses, other clips, mesh and textures are preserved.
[HANDOFF.md](HANDOFF.md) contains current hashes, triangle counts and integration notes. Meshy: **55/100 credits**.

## Current delivery

- [Body](export/mm6_mfp.glb), unchanged [knife](export/mm6_mfp_knife.glb), [packed authoring](export/mm6_mfp.blend).
- [Descriptors](integration/actors.yml) are byte-identical; [orchestrator regression notes](integration/regression.md).
- [Round-3 review](review/round3/README.md), [shared gates](review/round3/shared_gates/gates.md), [manifest](export/manifest.json).
- Editable checkpoints: work/round3/lod0.blend through lod3.blend. Canonical maps: work/round2/textures/.

## Unattended decisions and reproduction

Retime existing dense GLB samples directly, retaining their pose values and all existing binary payload.
Add an interpolated speed-change key to sparse tracks so their original path is also retained. Keep the exact
fractional endpoint (102.933333 frames at 48 fps), instead of rounding and altering the requested duration.
The corpse endpoint and all seven other clips match exactly. Float32 interpolation position difference is below 0.000361 mm.
No events belong to Death, so actors.yml needs no change. No geometry, UV, texture or reduction work this round.

Claim a fresh workspace lease before writes. One background Blender process with four threads.
Round-3 scripts: round3_retime.py (from accepted round-2 snapshots), round3_authoring.py (Death action only),
round3_review.py (shared sampler/checkers and viewer capture), round3_finalize.py (records).
Do not rerun the historical round-2 full exporter over the timing-only delivery.

The accepted round-2 production and its decisions are preserved in [the prior README](work/round3/before/README.md)
and [review evidence](review/round2/README.md). Historical round-2 LOD viewer assets keep the old timing for provenance.
Body counts: 10183 / 5513 / 2278 / 1235; knife: 2344 / 1289 / 543 / 303. Shared 5152×4096 atlas is unchanged.

Sibling mm6_mfp/, shared tools, runtime assets and engine remain read-only. No game/build/install/commit.
Orchestrator installs the revised body with tools/install_model.py and runs game checks. Knife/descriptors need no update.
