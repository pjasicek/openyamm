# HANDOFF — MM6 Mep / PeasantM3

## Review round 3 (death timing)

**User accepted the creature, including the head.** The only asset change is the requested **2x faster Death**: **3.633333 → 1.816667 seconds**. Staff release follows the same pose phase, **0.150 → 0.075 seconds**. Dead remains 1.000000 s and unchanged. Other clips, textures, geometry, skin weights, final corpse pose and staff drop trajectory are preserved.

The GLB keeps every one of its **873 baked Death pose samples**, halving only timestamps (effective 240 → 480 Hz); constant channels retain their endpoints and interpolation. This avoids pose drift from re-interpolation or sample removal. Reversing that time transform reproduces the complete original GLB document and binary exactly. All tier viewers and animation-bearing intermediate GLBs receive the same change. Death keys/handles in all four authoring LOD blends and the packed master are time-scaled by 0.5. [Identity receipt](review/round3/timing_identity.json).

**integration/actors.yml changed: NO** (byte-for-byte identical). Runtime uses the embedded Death duration; no binding speed override or event changes are needed. The shared gate config's held-staff interval changes only from 0.150 to 0.075 s. No Meshy work: **60 / 100 credits total, zero this round**. No triangle reduction, other art changes, runtime installation, game launch, build or commit.

### Files, hashes and counts

The orchestrator needs the updated body GLB; staff bytes and actors.yml are unchanged. The packed blend is updated editable source. All four files are 0644. [Full changed-file receipts](review/round3/changed_files.json).

| File | Bytes | SHA-256 |
|---|---:|---|
| [export/mm6_mep.glb](export/mm6_mep.glb) | 17,010,812 | `e3f6688d1e22f2d68656370fdc560c740bd65c5f34ad093e742a855348fd3875` |
| [export/mm6_mep_staff.glb](export/mm6_mep_staff.glb) | 3,659,932 | `2c428fcf83d06f22097acf827a297c7e7e1e14d6ef85162394fccc134d016c3d` |
| [export/mm6_mep.blend](export/mm6_mep.blend) | 7,033,744 | `6e85bc9e906296b9b180ac15c211cc853ded3d32895edaccff6f0567bff78031` |
| [integration/actors.yml](integration/actors.yml) | 3,191 | `89f920ec8b23ba538d8d040c8714239c072c1e6fae07f1af7015178a23fdfc1a` |

| LOD | Body colour | Body shadow | Staff |
|---:|---:|---:|---:|
| 0 | 10,066 | 10,066 | 1,616 |
| 1 | 4,494 | 4,494 | 528 |
| 2 | 3,594 | 3,594 | 352 |
| 3 | 3,494 | 3,494 | 160 |

### Required checks

**Death floor/stretch, bindings and viewer: PASS.** The shared runner checks every colour/shadow LOD. [Shared raw report](review/round3/gates/gates.md), [scope summary](review/round3/validation.json), [bindings: no BAD](review/round3/bindings_check.log), [viewer: 27 switches, zero errors](review/round3/viewer_check.log).

| Shared Death metric | Worst | Limit | Result |
|---|---:|---:|---|
| floor_penetration_mm | 0.000000 | 2.0 | PASS |
| arm_stretch_p99 | 1.633601 | 2.0 | PASS |
| arm_stretch_max | 2.738851 | 4.5 | PASS |
| hand_stretch_p99 | 1.594129 | 4.5 | PASS |
| hand_stretch_max | 2.171514 | 4.5 | PASS |
| cloth_penetration_mm | 1.079891 | 2.0 | PASS |

The full unmodified shared report is **FAIL: 7,466 PASS, 208 FAIL, eight UNVERIFIED, 148 INFO, 64 N/A**. All 208 FAIL rows are Death time-based speed checks: rotation steps reach **34.514226°** versus 25°, and angular acceleration reaches **30,842.757498°/s²** versus 20,000. These are 26 skeleton results repeated across eight LODs, and result from the expressly requested 2x playback. They are outside this round's floor/stretch check scope. No threshold was relaxed or accepted pose altered to make these rows pass. The eight prior blunt-staff blade-edge rows remain UNVERIFIED. Full technical status is therefore still not an unconditional PASS.

### Review and next owner

[Death front/side/quarter phases](review/round3/Death.png) · [normal and half-speed playback](review/round3/playback_Death.png) · [staff drop / final corpse comparison](review/round3/round3_death_timing.png) · [viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_mep_codex/review/viewer/).

Static phase images retain the exact accepted poses with halved time labels; live viewer captures were regenerated for Death and Dead. All other accepted imagery remains valid by the complete binary identity comparison. The previous revision is preserved in review/round3/before/.

The orchestrator owns installation through tools/install_model.py and native playback/regression checks. Workspace lease is released at handoff; no owned Blender/Chrome process remains.

## Previous reviews

Round-2 delivery and head/sash work: [archived HANDOFF](review/round3/before/HANDOFF.md). Its artistic-acceptance status is superseded by the user's acceptance above. Round-1 history remains linked from that document.

## Far-LOD texture sizes (orchestrator, 2026-10-13)

LOD1/2/3 texture sets were box-downscaled to 1024/512/256 px (props 512/256/128) (exactly the mip the GPU would sample at those sizes;
LOD0 maps untouched). Backups: `export/*_prelodtex_backup.glb`.
