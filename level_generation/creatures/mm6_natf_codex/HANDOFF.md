# MM6 natf — review round 5 handoff

Attack-only correction verified and staged. The accepted slim skirt, appearance and eight other clips are unchanged. **30/100 credits total, zero spent this round.** No installation, game launch, build, shared registry edit or commit. The orchestrator owns native integration.

## Review round 5

### Arm and shoulder correction

The right hand now continues down and across through the slash instead of folding back beneath a raised elbow. The anatomical elbow solve uses a lower, more extended endpoint and minimal humeral rotation. Forearm roll and the associated deformation-helper twist fade toward neutral through the problem interval; the hand retains its neutral wrist relation to the forearm. The transition is smoothed, then projected back onto the anatomical elbow hinge.

At the pose corresponding to original **frame 56**, elbow flexion changes from **112.22° to 46.86°**. Over original frames **48–64**, the shared runner measures peak elbow flexion **117.37° → 66.03°**, forearm roll **82.03° → 10.42°**, and upper-arm roll **18.01° → 7.59°**. Wrist flexion remains neutral. The shoulder keeps its volume in the reviewed close-ups: the fix is in Attack's bone orientation/twist, with existing mesh weights preserved so other clips retain their accepted deformation.

Only the Attack action is changed. Within it, pose edits affect `B_R_UpperArm`, `B_R_Forearm`, `B_R_Hand` and their two twist helpers, smoothly covering old times 0.80–1.70 s. Its other channels, including the moving shield and fitted skirt, are retimed together. No geometry, UV, weight, texture, rig-layout or triangle-count change was made.

### Timing and binding

“30% faster” is implemented as **1.3× speed**, using the viewer's original 48 Hz frame numbering. The strike section retains **1× timing**.

| Phase | Original interval | New interval |
|---|---|---|
| Wind-up, frames 0–27 | 0–0.562500 s | 0–0.432692 s |
| Strike, frames 27–64 | 0.562500–1.333333 s | 0.432692–1.203526 s |
| Recovery, frame 64–end | 1.333333–2.150000 s | 1.203526–1.831731 s |

The 60 Hz export holds the endpoint for another **1.603 ms**, giving a runtime duration of **1.833333 s**. Original frame 56 is now at **1.036859 s**, approximately new viewer frame 50. Phase anchors and duration are updated in the viewer manifest.

**`integration/actors.yml` changed: YES.** All six melee/ranged Attack impact entries across A/B/C change from **0.697916667 s to 0.572916667 s**. This is the freshly measured fastest target-facing blade interval at 48 Hz, with zero shared-gate impact-time error. `gates.json` changes only that same impact intent. Cast timing, scale, stride, run binding, attachments and other actor settings are unchanged.

### Files and hashes

| File | SHA-256 | Triangles L0 / L1 / L2 / L3 |
|---|---|---|
| `export/mm6_natf.glb` | `d575618852d50b157a06362b27d40ca89311af4d83b4b4bf74611be9a2160895` | 11641 / 4699 / 3077 / 2707 |
| `export/mm6_natf_blade.glb` | `656bf58071372eea4f6f27d1e3af22ea386be8198fbe038f0b170dca367a4fcb` | 1142 / 378 / 270 / 144 |
| `export/mm6_natf_shield.glb` | `b2d12e8663945df612f81e383f13bdade374a28860fc1821debb7bb2c965f54c` | 1636 / 642 / 450 / 156 |

Equipped counts remain **14,419 / 5,719 / 3,797 / 3,007**. The blade and shield runtime files match the previous hashes exactly. The rig remains 120 bones.

Editable `export/mm6_natf.blend`: `b4458ac0decf5205d609141fb05d04548f80efad90f94b48b4fede0dad4cb5ef`. Staged `integration/actors.yml`: `d4be7bc8bbc3d6841173c86286ad9b703b7e85b661e840ea27b6a1bbd7539240`.

Changed files include `scripts/round5_attack.py`, `round5_preview.py`, `round5_sheets.py`, `scripts/capture_viewer.mjs`; `work/accepted_master.blend`; final authoring/export files; `export/export_info.json`; `integration/actors.yml`; `gates.json`; the three viewer tier GLBs and `review/viewer/manifest.json`; Attack and combined review sheets; round 5 comparison images/receipts; README, progress and this handoff. Exact file hashes are in `review/final/artifact_hashes.json`.

### Verification and visual evidence

The unmodified shared gate runner reports **7,640 PASS, 144 INFO, 64 N/A**, with no failures or unverified rows, on every clip and all colour/shadow LODs. Attack's right-arm stretch p99 is at most **1.9298×**, maximum **3.7411×**. Right-arm rotation steps remain below **21.04°** and angular acceleration below **12,540°/s²**. Elbow plane, wrist, roll, body contact and all cloth checks pass. No acceptance thresholds were relaxed.

- [Shared gates](review/round5/gates_final/gates.md); current copy in `review/final/all_gates.md`.
- [Shared arm-window measurements](review/round5/arm_window_shared_metrics.json), comparing the same original phase before/after retiming.
- [Before/after arm close-ups](review/round5/arm_comparison.jpg), [Attack sheet](review/final/Attack.jpg), [browser frame-56 equivalent](review/viewer_attack_arm_56.png), [viewer](review/viewer/index.html). Reviewed front, right and three-quarter follow-through poses at original frames 48/56/64 and final browser captures.
- [Preservation](review/round5/preservation.json): eight other clips have **zero sampled transform difference at 48 Hz**; every mesh accessor and embedded texture is identical, equipment files unchanged, and all **59 native PNG hashes** match.
- `review/round5/bindings.txt`: **PASS, no BAD line**.
- Viewer: **27 tier/clip switches**, **18 fresh full normal/quarter-speed playbacks**, no console errors. Receipts in `review/final/viewer_check.json`, `viewer_capture.json` and `review/playback_check.json`.
- [Final verification](review/round5/final_verification.json) binds these results to the final body hash.

The orchestrator should install the body revision through `tools/install_model.py` and merge the six staged Attack impact values. Do not copy GLBs directly into assets_dev. Native game checks were deliberately not run under the batch rules. The workspace lease is released after the final hash audit.

### Retained decisions and history

The round 4 checkpoint is archived at `review/round5/before/HANDOFF.md`. Its slim skirt and user-authorized accepted-look exception for the existing independent LOD UV/texture sets remain unchanged; strict shared-texture batch compliance is not claimed. The historical conservative hem-opening method is likewise unchanged. Earlier source/library provenance, costume adaptation and five-view prompts remain linked from that checkpoint and `references_hd/ADAPTATION.md`.

## Far-LOD texture sizes (orchestrator, 2026-10-13)

LOD1/2/3 texture sets were box-downscaled to 1024/512/256 px (props 512/256/128) (exactly the mip the GPU would sample at those sizes;
LOD0 maps untouched). Backups: `export/*_prelodtex_backup.glb`.
