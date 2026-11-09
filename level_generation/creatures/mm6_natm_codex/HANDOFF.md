# MM6 PeasantM4 / natm — staged review handoff

Latest: **Review round 6**, following the user-accepted round 4 and completed round 5 recovery revision.
**50/100 Meshy credits total; zero credits this round.**

## Review round 6 (attack smoothing)

The late frame-42–45 pelvis surge caused the jerk: its 30 cm displacement was concentrated into three intervals.
The revised Attack spreads that forward drive into the existing approach using a quintic ease across frames 32–40,
with a small eased tail to frame 43. Leg IK retains the existing foot targets. Spine and arm rotations in the approach
are unchanged; removing the pelvis surge smooths their world-space translation and the spear tip together.

- **Attack: 57/48 = 1.187500 s → 55/48 = 1.145833 s.**
- Two redundant transition intervals are removed. The old round-4 hold at frames 46–52 was already removed in round 5
  and remains absent. Every exported interval after frame 32 contains movement; the lowest-motion interval is the
  single turnaround at 42–43 (0.231 mm maximum joint displacement), followed immediately by recovery.
- The entire round-5 simultaneous spear/shield/body recovery is retained, shifted from **45–57 to 43–55**:
  **12 intervals / 0.250 s**. Maximum world-matrix difference after this time shift is 0.000001087 (float precision).
  Both arms and the body reach the same accepted rest endpoint together.
- Peak acceleration over the drive: **pelvis 256 → 68.818 m/s²; spear tip 256 → 88.856 m/s²**.
  [Velocity comparison](review/round6_velocity.png) and [per-sample linear/angular metrics](review/round6_motion_diagnostic.json)
  include all spine segments, upper arms, forearms, hands and the spear socket at 48 Hz. These extra measurements use
  the shared pose evaluator; the shared runner remains the acceptance authority.
- Fastest aimed spear-tip motion now occurs at **35.5/48 = 0.739583333 s**, 8.202553 m/s and 15.557° from forward.
  Old impact was 43.5/48 = 0.906250 s. **integration/actors.yml changed:** all six melee/ranged impact values across
  A/B/C tiers updated. **Cast is unchanged**, including 0.479166667 s release and Socket_LeftPalm binding.
  Binding SHA256: `67ee3db83a63b8ef623c9c55c825b1e52e5f979a3f40cc534b4e0a259f9d95cb`.
- Geometry, weights, textures, materials, all eight other clips and both prop GLBs remain unchanged. The original body
  binary payload is intact; replacement Attack accessors are appended. Before frame 33, exported poses are identical.
  The existing texture-memory cost and historical accepted qualifications remain in the archived handoffs.

[Attack sheet](review/sheets/Attack.jpg) · [drive/recovery close-ups](review/round6_smoothing.jpg) ·
[viewer](review/viewer/index.html). Front, side and three-quarter renders inspected; other clip sheets remain unchanged.

### Files for integration

Install the new **export/mm6_natm.glb** together with the revised **integration/actors.yml** events.
Prop exports are byte-identical and listed for verification. The near editable source and all four
`work/runtime_lod0.blend`–`runtime_lod3.blend` files contain this Attack.

| File under export/ | Bytes | SHA256 |
|---|---:|---|
| mm6_natm.glb | 16,135,960 | `9b7666a3a0211c47a09584c7fc1ccac6f2c33cea28e719eb887e519e460fb928` |
| mm6_natm_spear.glb | 1,497,884 | `df1c78973c28c0d954ffe4d208422e7c663218527a7683b7848c546bfb259789` |
| mm6_natm_buckler.glb | 3,418,444 | `46f605731fdd1527bf24e5c4772c665d69c4c203b5648785b6bc4fcf6d9e54c9` |
| mm6_natm.blend | 9,329,785 | `6f05595e61e5215c2f7bbdf4083dd30a3f099a5533046ffc552018fe2eb86a28` |

Triangle counts are unchanged (the body has matching dedicated opaque shadow LODs):

| LOD | Body / shadow | Spear | Buckler |
|---|---:|---:|---:|
| 0 | 12170 | 2210 | 1670 |
| 1 | 6372 | 1170 | 858 |
| 2 | 2818 | 272 | 399 |
| 3 | 1240 | 156 | 160 |

### Validation

- [Shared Attack gates](review/round6_attack_gates/gates.md): **PASS**, {'PASS': 970, 'INFO': 32, 'N/A': 8}; all four colour and shadow LODs.
  Runner evaluates 57 bone/mesh samples at 48 Hz, including its float-duration endpoint sample.
- [Dense shaft checks](review/round6_shaft_gates/): **PASS** on every matching LOD, 57 samples each.
  [Probe provenance](review/round6_probe_provenance.json), [matching LOD provenance](review/round6_pairs/provenance.json).
- Worst arm/body penetration **0 mm**; floor penetration **1.516475 mm**; rotation step **24.978480° / 25°**;
  arm angular acceleration **18845.414°/s² / 20000°/s²**. No acceptance threshold was increased.
- [Strict shaft/body diagnostic](review/round6_clearance_diagnostic.json): zero penetration into torso/hips/legs at
  all 56 exact frame samples on all four LODs; minimum separation **9.865210 mm**, excluding the gripping/releasing
  hands. Shared dense prop checks separately include the configured hand contacts (worst 0.385271 mm shaft and
  0.514261 mm buckler penetration, within the existing gates).
- [Binding check](review/bindings_check.txt): exit 0, **no BAD line**, including shadow opacity and normalized weights.
- [Viewer check](review/viewer_check.json): **27 switches**, zero errors/failures. Owned Chrome processes stopped.
- [Payload invariants and hold check](review/round6_motion_diagnostic.json): unchanged original binary prefix,
  geometry/material/image records, both props and eight other clips; only the six expected actor event values changed.

### Reproduction and scope

`review6_motion.py` loads the preserved `work/review_round6_before/` round-5 blends, eases the pelvis drive and solves
legs onto the prior foot targets. `review6_export.py` transplants only the affected channels/samples, shifts the
unchanged recovery two frames earlier, and updates events/duration/grip interval. `review6_probe.py` and
`review6_pairs.py` prepare the unmodified shared runner inputs. `review6_preview.py`, `review6_render.py`,
`review6_sheets.py` and diagnostics update the review package. Intermediate animation: `work/round6_animation.glb`.
The offhand grip window moves from 42–45 to 42–43 with the removed transition intervals; all limits stay unchanged.

No install, assets_dev write, build, game launch or commit. Native integration/captures remain orchestrator-owned.
This is technical completion and agent visual review; the user still judges the revised motion in the viewer.

## Review round 5 (attack hold)

[Preserved round-5 handoff](work/review_round6_before/HANDOFF.md) includes its full timing/recovery implementation,
hashes and validation, and links the accepted round 4 and earlier reviews.

## Texture size (orchestrator, 2026-10-13)

Round 4 rebaked the body maps at 4096x2144 (about 179 MiB uncompressed with mips). The orchestrator halved all four
embedded maps to 2048x1072 (Lanczos) with no visible difference at close range (`export/mm6_natm_4k_backup.glb` keeps
the 4K export); geometry, rig, clips and materials are unchanged.
