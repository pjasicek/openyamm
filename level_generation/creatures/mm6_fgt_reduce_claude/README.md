# MM6 Leather Fighter (`fgt`, FighterLeath A/B/C: Thug / Ruffian / Brigand) reduction (2026-10-14)

User: "tris reduction 3D playbook - do leather fighter". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_fgt.glb` (9,305 tris, one merged body+head atlas material, three variants, four influences;
project `../mm6_fgt_claude/`) and its held `mm6_fgt_mace.glb` (2,232). Scripts copied from `../mm6_figc_reduce_claude/`.
No Meshy credits. Limits for the 1.699 m height: p99 5.10 mm, max 25.49 mm.

## Body: per-region budgets

A uniform cut and the usual head + hands protection both failed: head (2,745 faces) and five-finger gloves
(1,254 each) are 56 % of the mesh, so protecting them left the studded leather to absorb the whole cut (boots pointed,
sleeve fringes jagged; `hh`, `p60`, `p75` in `work/`). `decimate_tex.py` gained `REA_GROUPS` / `REA_GROUP_RATIOS`
(each labelled group decimated on its own, label 0 takes the rest of the ladder budget) and a per-face `group` array
in its output. Regions: `scripts/region_faces.py` (dominant bone weight) and connected components of the welded mesh.

| config | triangles | p99 / max mm | IoU | finding |
|---|---:|---|---|---|
| source | 9,305 | | | |
| g1: head 60 %, gloves 45 %, body ladder | 6,215 / 5,815 | 3.2 / 19.6, 4.3 / 25.4 | 0.994 / 0.989 | lips collapse to a lump (clay), strip ends taper below ~85 % body |
| g2: head 50 %, gloves 35 % | 5,693 / 5,283 | 3.6 / 19.6, 4.5 / 25.4 | | face worse |
| g3: face + eyes kept, hair/gloves 45 % | 7,007 | 3.2 / 19.6 | 0.996 | face matches; crease at the hair edge (clay) |
| g4: face 80 % | 6,839 / 6,719 | | | lips soften |
| g5: g3 + small pieces (<= 80 faces: skirt strips, buttons, ring, caps) kept, hair 60 % | 7,027 / 6,879 / 6,733 | | | straight strip ends; belt tongue still pointy |
| **g6: g5 + both belt bands and the sheath strap kept, rest 70 %** | **6,871** | 4.4 / 25.4 | 0.988 | **pick** |
| g6 at 65 % rest | 6,747 | 5.2 / 21.4 | 0.985 | fails p99 |

Pick `g6r73` (`work/keep_g6.npy`, `work/groups2.npy`, ratios gloves 0.45 / hair 0.6): face/neck skin (1,810) and eyes
(131) kept exactly, 17 skirt strips, buttons, belt ring/buckle bits, copper caps, belt bands and sheath strap kept
exactly (1,612), gloves 2,508 -> 1,128, hair 776 -> 465, the remaining torso/arm/leg/boot/scarf/pauldron shells
2,468 -> ~1,730. Texture drift (`texture_drift.py r73`): one face above 40 (41, front of the left thigh), p99 10.7;
no lock round.

## Mace

Parts (connected components): grip wrap 188, pommel 236, shaft 428, ball 620, ten spikes x 76.
- The plain prop ladder (`prop_ladder.py`) auto-picked r35 (780), but the ball turned lumpy (radius 48-56 mm on the
  source's exact 54 mm sphere) and the collar above the grip got a ragged edge.
- **Pick `m3` (974)**: grip wrap kept exactly (the fist is fitted to it), pommel 35 %, shaft 60 % (clean collar),
  ball 40 % then projected back onto the exact sphere (`scripts/mace_snap_ball.py`, ball-group vertices only; a
  radius threshold also caught the spike bases and the shaft top), spikes at the 200-face floor. Normals transferred.
  LOD1 (1,116) is dropped as no longer coarser; LODs 974 / 400 / 132.
- Grip gate (`scripts/grip_gate_posed.py`, mace at the posed `Mace` joint from its inverse bind matrix, every 2nd
  frame of Attack/Standing/Walking/Running/Hit/Fidget): glove vertices inside/at the handle scale with the glove's
  vertex count (0.57-0.60 of the source's), nearest 2.5 mm vs 1.7 mm from the axis. Renders
  `review/props/grip_sheet.png` (rows source, reduced; Standing and mid-Attack): same grip.

## Result (installed 2026-10-14, user accepted)

`export/mm6_fgt.glb` (= `mm6_fgt_g6r73.glb`): LODs 6,871 / 3,435 / 1,227 / 385 (installed 9,305 / 4,651 / 1,664 /
530), shadow LODs rebuilt, variants carried to every primitive. `export/mm6_fgt_mace.glb` (= `mm6_fgt_mace_m3.glb`):
974 / 400 / 132. LOD0 with the mace 11,537 -> 7,845 (-32 %).
Review: `review/faces/s4.png` + `s4_clay.png` (belt, whole, back, face; rows installed, g5r73, g6r75, g6r73),
`review/faces/s2_face_front*.png` (face configs), `review/props/mace_close3.png` (head and grip, source vs m3),
`review/props/grip_sheet.png`, `review/ladder_sheet.png`. Viewer `review/viewer/` (body only, installed vs pick per
variant; `check_viewer.mjs` 48 switches, no console errors). Other candidates are in `work/candidates/`.

Installed with `tools/install_model.py export/mm6_fgt.glb --world mm6` and the same for the mace (runtime copies
with back faces culled). The `actors` suite's `mm6_thug_actor_model_tiers_and_mace` passes; the other failures are
the guard, mage, ooze and DWI cases unrelated to this model. Lease released. Rollback (install these): `work/mm6_fgt_source_pre_reduce.glb`, `work/mm6_fgt_mace_source_pre_reduce.glb`.
