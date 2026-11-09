# MM6 Mep / PeasantM3 — review round 3

**Accepted by the user, including the head.** Requested Death speed change is applied: **3.633333 → 1.816667 s**. Staff release is 0.075 s instead of 0.150 s; Dead and all other clips are unchanged. No appearance/geometry/weight changes. **60 / 100 credits; zero this round.**

[HANDOFF](HANDOFF.md#review-round-3-death-timing) contains hashes, unchanged triangle counts, checks and integration ownership. [Death sheet](review/round3/Death.png), [live playback](review/round3/playback_Death.png), [phase/identity receipt](review/round3/timing_identity.json).

Only Death time inputs changed in the GLBs. All 873 baked pose samples are retained at effective 480 Hz; a reversed time transform exactly reconstructs the original document and binary. Authoring Death keys/handles are halved in work/final_lod0–3.blend and export/mm6_mep.blend. The head, skin, sash, grip, materials, staff and corpse pose are preserved.

Required Death floor/stretch checks pass on every LOD (floor penetration 0 mm); bindings print no BAD; viewer passes all 27 tier/clip switches. The full shared runner also flags the deliberately faster Death against its unchanged rotation/acceleration limits: 208 repeated FAIL rows, plus eight pre-existing UNVERIFIED blunt-staff blade-edge rows. These results are retained openly in [the report](review/round3/gates/gates.md); no thresholds or poses were changed. This is a scoped timing delivery, not an unconditional full-runner PASS.

integration/actors.yml is byte-for-byte unchanged. The orchestrator installs the new export/mm6_mep.glb with tools/install_model.py; the staff GLB needs no replacement. Native regression/captures remain orchestrator-owned. No game launch, build, runtime install or commit was performed.

Reproduce only from the preserved review/round3/before/ snapshot: claim the lease, run scripts/round3_death_timing.py through tools/run_creature_blender.sh (--threads 4, one process), then scripts/prepare_review.py and the shared gate/binding/viewer checks. The retime script is idempotent against that snapshot. The gate's Death held interval is scaled to 0.075 s; other gate intent/thresholds are unchanged.

Historical identity, native references, round-2 authoring and skin calibration are preserved in [the prior README](review/round3/before/README.md) and [prior HANDOFF](review/round3/before/HANDOFF.md). Shared files, native/restored sprites, other projects and assets_dev remain untouched.
