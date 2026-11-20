# MM8 Ogre Warrior (m440) — triangle reduction trial

Staged candidate, **not installed or artistically accepted**. Follows the texture-aware, no-retexture route in
[the retopology playbook](../RETOPOLOGY_PLAYBOOK.md). Source project: [mm8_m440_claude](../mm8_m440_claude/README.md).
No Meshy jobs or credits. Original game sources/runtime models remain unchanged.

[Interactive installed/candidate comparison](http://127.0.0.1:8912/level_generation/creatures/mm8_m440_reduce_codex/review/viewer/)
· [matching close-ups](review/comparison.png)
· [normal-speed samples](review/playback-normal.jpg)
· [half-speed samples](review/playback-half.jpg).

| Triangle count | Installed | Candidate |
|---|---:|---:|
| Body, source LOD0 | 18,752 | 17,626 |
| Body + club, source LOD0 | 20,139 | 19,013 |
| Body + club, runtime LOD0 including cook back faces | 20,953 | 19,783 |
| Body, source LOD1 / LOD2 / LOD3 | 10,649 / 6,400 / 4,238 | unchanged |

The safe trial saves 1,170 runtime triangles (5.6%) at LOD0. The existing contact-preserving lower LODs and club
are retained. This preserves the source project's recorded LOD exception. No frame-rate gain is claimed.

## Selection and preservation

Texture-aware MeshLab collapse, with exact UV/weight-aware source welding and per-component surface-interpolated
weights. Four skin influences, matching the installed source; only 27 new vertices needed limiting. Head (9,449
triangles), both hands, sole patches, small hardware and fitted torso patches are protected: 13,760 faces retain
their original positions and corner UVs. Material maps, three colour variants, all eight clips, skeleton, sockets,
coarser colour/shadow levels and club are retained. Full-detail shadow geometry follows the new LOD0.

The first aggressive ladder (90/82/76%) failed deformation limits. The gentler 94/92/90% pass found that 92% still
exceeded both limits (p99 4.53 mm, max 23.03 mm). Those exploratory measurements used eight influence interpolation;
the final 94% candidate was rechecked with the installed four-influence budget. Its p99 is **3.59 mm**, maximum
**18.56 mm**, against limits 4.46/22.32 mm. Minimum silhouette IoU **0.9963**, mean textured SSIM **0.9962**;
1,430 open edges in both source and candidate. Earlier results remain in `work/aggressive_ladder.json` and
`work/eight_weights_ladder.json`; only `work/selection.json` identifies the final candidate.

A nearest-sample texture-drift heuristic flags 11 changed faces above 40/255, mainly on fine chainmail plus one
strap (p99 14.8). Matched back/chest close-ups show no obvious new blotch or pattern break; this remains an artistic
review note, not a claim of exact texture sampling preservation.

## Verification and files

- [Shared gates](review/gates/gates.md): final candidate, every clip and shipped colour/shadow level.
- [Preservation assertions](review/preservation.json): animations and texture payloads byte-identical; skeleton,
  materials, lower-LOD geometry and protected face positions/UVs unchanged. Candidate has only one skin-weight set.
- [Viewer check](review/viewer_check.json): six models (three tiers, before/after), 48 clip switches, no errors.
- [Playback](review/playback/playback.json): all eight clips at normal and half speed, videos plus timed captures.
- Runtime source candidate: [export/mm8_m440.glb](export/mm8_m440.glb).
- Editable reduction candidates: [work/ladder.blend](work/ladder.blend), object `Cand_94`; `Body` is the source.
- Geometry cook preview: `export/mm8_m440_geometry_preview.glb` (embedded source textures; not an installed cook).
- Rollback snapshots: `work/mm8_m440{,_club}_{source,runtime}_pre_reduce.glb`, plus `work/master_pre_reduce.blend`.

Claim identity `mm8:m440` through `tools/run_creature_workspace.sh` before writing. Reproduction scripts are local:
`init_source.py`, `dump_mesh.py`, `decimate_tex.py` with `work/keep_fitted.npy`, `run_ladder.py`, `export_pick.py`,
`swap_lod0.py` with `REA_KEEP_LODS=1`, `check_preservation.py`, `assemble_review.py`, `viewer_variants.py`,
`run_gates.py`. The retained original project is the authoring/texture source; this branch is a reduction trial.

No install, native-game capture, Android/Vulkan testing or GPU performance measurement was performed.
Per playbook step 5, artistic review precedes installation and the actor regression. Add the reduction ledger row
only when installed or rolled back.
