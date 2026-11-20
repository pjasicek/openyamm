# MM6 Harpy (`hrp`, BHarpy A/B/C) reduction (2026-10-14)

User: "do harpy". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed
`assets_source/worlds/mm6/models/mm6_hrp.glb` (13,534 tris: body 6,474, head 3,314, wings 3,746; three texture sets,
three variants, four influences at full detail; from `../mm6_hrp_claude/`, already reduced once there in v3).
Started with `REA_PROTECT_HEAD=1 ../reduce_installed.sh hrp Body "MM6 Harpy"`; limits for the 2.267 m height:
p99 6.8 mm, max 34.0 mm. No Meshy credits.

## Harpy-specific changes
- **Two-sided sheets.** 183 faces have a reversed copy on the same positions (176 wing membrane, 6 body, 1 head).
  `import_source.py`'s weld merges each pair into one face (13,534 -> 13,351), which would leave those spots open from
  behind. `scripts/find_doubles.py` records the pairs from the unwelded import (`work/doubles.npy`), the ladder keeps
  those faces exactly, and `export_cand.py` (`REA_DOUBLES`) adds the reversed copies back (183 of 183).
- **Head kept** (`Head` weights, 2,791 faces); keep set `work/keep_a.npy` (head + doubles).
- **One drift-lock round** (`work/keep_b.npy`, 3,312 faces): r70 had 162 cm2 of drifted texture around the hips and
  tail feathers; after the lock 34 cm2.
- `texture_drift.py` now samples each material's own base colour (`work/basecolor_<k>.png`, material k at u + 2k).
  `scripts/flip_check.py` (inverted faces against the source) and `scripts/open_edges.py` (new open-edge loops)
  found nothing on any step: the open edges match the source's 15 loops.
- The max error (~43 mm) is the folded wings in Death (frames 30-42) at every step, 80 % included: the folded layers
  pair with the wrong layer in the surface distance. The renders of Death frame 42 match.
- A black spot on one wing feather in the clay renders of the first r70 was a sharp crease under the cavity shading
  (it faced the camera, normals valid, not visible textured); it is gone after the lock round.

## Ladder

| config | step | triangles | p99 / max mm | IoU | drift > 40 | |
|---|---|---:|---|---|---|---|
| source | | 13,534 | | | | |
| head + doubles kept | 80 % | 10,679 | 3.9 / 42.0 | 0.990 | | max only (wing fold) |
| head + doubles kept | 70 % | 9,345 | 5.2 / 44.9 | 0.984 | 162 cm2 | |
| head + doubles kept | 60 % | 8,009 | 6.9 / 43.8 | 0.975 | 210 cm2 | |
| **+ drift lock** | **70 %** | **9,345 (+183 copies)** | 5.4 / 44.9 | 0.982 | 34 cm2 | **pick** |
| + drift lock | 60 % | 8,009 | 7.5 / 43.6 | 0.971 | 83 cm2 | p99 over |

## Result
`export/mm6_hrp.glb` (= `mm6_hrp_br70.glb`): LODs 9,528 / 4,669 / 1,678 / 556 (installed 13,534 / 6,673 / 2,402 /
796); body 3,516, head 3,130, wings 2,882; variants carried to all 10 LOD/shadow primitives; sockets and clips
unchanged. Review: `review/sheet_a.png` (+ `_clay`; installed, r70, r60 before the lock), `review/sheet_b.png`
(installed, r70, pick; installed vs pick in Death 42 and Attack 30). Viewer `review/viewer/` (installed / pick per
variant, every clip; `check_viewer.mjs` 54 switches, no console errors).

## Installed (2026-10-14)

User: "accepted". Previous source backed up to `work/mm6_hrp_source_pre_reduce.glb` (rollback: install that file),
`tools/install_model.py export/mm6_hrp.glb --world mm6` (the runtime copy equals the source: its materials already
carry the back-face flag). Lease released.
