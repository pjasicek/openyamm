# Sven Svenssen (`mm9_sven.glb`): see-through linings, 2026-11-05 (candidate, not installed)

Brief: [LINING_BRIEF_20261105.md](../../../devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md) (user decision 2026-11-05:
line the four worst bodies of the 2026-11-02 sweep). Lease `mm9lining:sven` (owner sven-lining-20261105; `mm9:sven` and
`mm9reduce:sven` were free; released at the end). Source: the installed `assets_source/worlds/mm9/models/mm9_sven.glb` (sha256 3e303710a1f4…),
copied to `before/` (rollback). `../mm9_sven_claude/` and `../mm9_sven_reduce_claude/` were only read. No Meshy, no repaint,
no engine/game edits or builds, nothing installed.

**Candidate: `export/mm9_sven.glb`** (sha256 fe2393c1f5ad…; `export/mm9_sven.glb.twins.json` is a sidecar for the gates, not
for install). Rebuild: `scripts/build.sh` (project folder).

## What was added (faces only)
Built at the GLB level by `scripts/glb_lining.py` from the installed file: new vertices and triangles are appended to the
primitives they line; every existing vertex, UV, normal, weight, image, material, clip, skin and node is byte-identical
(`scripts/prefix_check.py`, `scripts/same_clips.py`), and the four shadow meshes are untouched (no lining triangles in them).
Every lining vertex copies the raw JOINTS_0/WEIGHTS_0 of the outer vertex it lines; cap centres take the mean of their loop's
top four joints. The same rules run on each existing LOD1-3 mesh (its own geometry), so no LOD is rebuilt.

| Opening (sweep zone) | Cause | Lining | LOD0 tris |
|---|---|---|---:|
| coat skirt / hem (torso 2,529) | the vest's single-sided skirt (one 43-edge open hem, skirt bones Bone10/18/22); its inside showed from the side, below and on the corpse | band of vest faces below y 1.16 m lined 3 mm inside (fold-aware offset direction; capped at 40 % of the distance to the vest's own cloth), rim strip on the hem, fan cap at the cut (inside the torso above the belt, Spine1-weighted, above the trousers' open top at 1.03 m); one dark texel of the skirt's own red paint (0.098/0.004/0.016) | 367 |
| bracer wrist rings (sleeves 118 / 99) | cuff_trim's cut ring, 2 cm round the hand stub, open into the arm tube | plug from the rim loop: strip to a ring 2 mm inside, tube 3 cm up the forearm axis following the measured wall, fan cap (the stub's open end is 7.4 cm in, so the cap crosses only its inside); one black texel of the bracer's steel pattern | 230 |
| hair (head 77, and the 'torso' pixels of the Spine-weighted hair) | the hair shell's underside along its free edges and where the curtains hang off the shoulders/back | own-UV twins 1.5 mm under 629 hair faces: every face whose underside the gate saw in >= 10 hole pixels (`review/gates_hitlog/`, installed GLB, every clip) plus a 1.5 cm band along the shell's open loops; the underside reads as hair | 629 |
| side braids | open strips | own-UV twins of both braids (73 + 77), 1 mm | 150 |
| brooches, plaques, buckle (collar 23) | six small open shells on the chest | fan cap of each back rim on a dark texel of its own paint | 79 |

Totals (LOD0 / LOD1 / LOD2 / LOD3): installed 8,405 / 4,202 / 1,508 / 501 -> lined **9,860 (+1,455)** / 5,099 (+897) /
1,695 (+187) / 608 (+107). Body prim 3,244 -> 3,920, head prim 5,161 -> 5,940. More than the brief's "few hundred to about a
thousand": 779 of it is the hair, whose underside the gate saw in every clip; the body alone is +676. LOD2/3 hair takes only
the edge band; the bracer plug is skipped where a coarse LOD tube gave no wall (LOD2 L, LOD3 L); LOD1 R's plug takes the
narrowest found wall for 3 of its 8 ring vertices.

## Gates (installed -> lined; `review/gates_before/` = installed, `review/gates_final/` = candidate)
| Gate | Result |
|---|---|
| See-through (`scripts/see_through_gate.py`, DM2's gate + options, every clip, step 4, 16 views, 4 mm px; installed run reproduces the sweep exactly) | torso **2,529 -> 12**, sleeve R **118 -> 0**, sleeve L **99 -> 16** (Cower, a sliver at the raised arm's shoulder under the fur), head **77 -> 16**, collar **23 -> 0**, trousers L 11 -> 0, none 1 -> 1; no zone worse |
| Lining poke, visual (same run, `ref=` installed: lining nearest where the installed mesh's first surface along the ray is a front face) | outside the silhouette 0 px in every clip; flagged px per clip 12-49, Death 135 (`review/gates_final/see_through_POKE_*.png`). Read at full size against textured diffs (`review/final/z_death_skirt.png`, `z_bracerL.png`): these are the linings' 1-3 mm silhouette fringes where a lifted skirt flap or the bracer interior is seen from inside, and the bracer cap hiding the stub deep inside the opening; no lining shows through outer cloth |
| Lining poke, vertex (`scripts/lining_gate.py`, 10 fps, each twin vs its own vertex's 2-ring cloth) | at rest every twin inside; in poses up to 2.9 mm out on 7 of 131 skirt twins (Death/Running/Cower, folds at the hem corners) and 1.3 mm on 9 hair twins. A twin past its own cloth faces inward and is culled from outside; the visual check above is the deciding one |
| Arm and hand (`--outer-only --exact`) | identical to installed except Talk L forearm 0.3 -> 0.0 cm |
| Jitter | 0 fails (shoulder-skin values move by <= 0.07 mm/f2 as lining vertices join the sample) |
| Sleeve/bracer poke | identical to installed (0 mm, every clip) |
| Detached parts | 0 detached (38 components; the extra "root lift" notes are the lining twin components, as DM2/Hanndl) |
| UV escape (`claude_shared/reduction_uv_audit.py`) | **LOD0 0 escaping** (body 3,920, head 5,940 faces); body LOD1-3 equal to installed; head LOD1/2/3 171/163/125 vs installed 134/150/112: every added escape is an own-UV twin of an installed face that already escapes |
| Winding (`check_winding.py`) | 0 inverted closed parts |
| LOD heights / floor contact (`scripts/lod_heights.py`, every clip key, all four LODs) | lowest and highest point identical to installed (largest difference 0.000 mm) |
| Bones, clips | 12 checked, 0 stretching; SAME CLIPS/SKIN/NODES/MATERIALS/IMAGES |
| Informational | flat shading body 0.01 (the planar caps); texture_quality body density p10 0 (one-texel faces, as DM2/Hanndl); collapse gate face-frames 20,958 -> 25,926 over all clips (+24 %: the 3 mm rim strips and plug rings count as collapsing faces) |

## Sheets read (full size)
- `review/sheet_full_and_sweep.png` (installed | lined | difference: black same, yellow former hole, magenta other change):
  front, back, both sides, party view, face 3/4 and the sweep's worst view of every zone. Front/back/sides: only former holes
  change.
- `review/sheet_closeups.png`: hem below/side/back/front, both bracer openings (AttackMelee 8), collar and necklace, hair
  edges (Talk 28), skirt flaps of the corpse (Death 28), face.
- Face diff `review/final/face.png` and `face_34.png`: black (one closed hole pixel at the hair edge).
- Diagnostics: `review/diag/` (installed holes textured, texel crops), `review/diff_l4/` (the y_cut 1.045 candidate).

## What to look at
The corpse from the feet (`review/final/sweep_torso_death.png`): the coat tail on the floor and the lifted front flaps now
show dark red cloth instead of the floor/background. The bracer openings read as dark cups round the wrist
(`review/final/z_bracerL.png`, `z_bracerR.png`). The hair's underside at the shoulders reads as hair (`z_hair_back.png`).

## Not checked
Not looked at in game or in the creature viewer (no binding regression, per the brief); LOD1-3 and their new linings not
rendered (numbers only); motion at speed; Android cook. The skirt lining's small vertex pokes in poses were judged by the
visual gate, not rendered per frame in close-up.
