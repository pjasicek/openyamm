# MM6 Sorcerer — handoff

**Review round 4 texture fix complete. The user accepted the look and motion in round 3.**
Replace both staged runtime GLBs together. Meshy **40/100 credits total; 0 this round**.
No commit, assets_dev write, shared-file edit, build or game launch. Native integration belongs to the orchestrator.

## Review round 4 (texture fix)

The reported lines were texture artifacts. Replaced the fragmented per-LOD rebakes with one shared body/head
atlas at **2080×1024**: base colour, tangent normal, ORM and region mask. Coherent robe UVs use a back seam;
other seams follow garment/piece boundaries and side planes. Every chart has a measured **18 px reserved margin**
(36 px between unrelated chart bounds). All unused pixels are dilated, including the mask. Source filtering is
restricted to its own UV-chart interior so old edge contamination is not transferred into the new atlas.
The same original paint and unchanged tier ramps supply all three colours. Lower LOD UVs refer to the same atlas.
The staff's accepted 1024-square LOD0 maps are shared across its existing consistent UV layout at every LOD.

Robe density is at least the accepted round-two level: upper robe **412.31→415.00 px/m**, lower robe
**312.73→323.70 px/m**. Final atlas has 180 charts. Six raster pixels overlap between neighbouring triangles
sharing mesh vertices; no unrelated chart rectangles overlap. All unused atlas space is padded, not black.
[Material measurements](review/round4/material_checks.json), [layout](review/round4/atlas_layout.json),
[transfer receipt](review/round4/material_transfer.json).

**Geometry and motion are unchanged.** Every exported triangle retains its positions, normals, joint indices and
weights exactly, including all shadow LODs. UV seams can duplicate vertex records without changing any triangle.
Nodes, sockets, inverse bind matrices, animation channels, interpolation and sampler bytes also match round 3.
[Preservation receipt](review/round4/preservation.json). No new paid model or texture generation.

**integration/actors.yml changed: no.** Attack stays 2.5 s / impact **1.220833 s**; Cast stays 2.05 s / impact
**0.7375 s**. Both ranged events use **Socket_Staff_Head**. Tiers, scale 106.121, yaw −1.570796327,
ids 631/632/633 and descriptor shape are unchanged.

| Export | Embedded images before → after | Bytes before → after |
|---|---:|---:|
| Body | 32 → 4 | 17,112,956 → 8,545,332 |
| Staff | 12 → 3 | 2,211,996 → 1,466,436 |
| Combined | **44 → 7** | **19,324,952 → 10,011,768** |

Combined size falls **48.2%**. The body maps are all 2080×1024; staff maps are all 1024×1024.
No per-LOD texture sets or unused images remain in either installable export.

| File | Colour LOD triangles / role | SHA-256 |
|---|---|---|
| [export/mm6_sor1.glb](export/mm6_sor1.glb) | 7753 / 4085 / 1852 / 907 | `39482327ce533cece528bc7f124847c5bf22e46db6bb79d848afb984276f3a88` |
| [export/mm6_sor1_staff.glb](export/mm6_sor1_staff.glb) | 1674 / 720 / 340 / 148 | `cb6c025aa182576ef5081072e6948acc7dfd99f17b7f0e6d46d7d086084eed69` |
| [work/production_master.blend](work/production_master.blend) | Editable LOD0 master | `c1311b1239f02b9949bb1f2ab23843ec0cb51a84af441bdbcb8c1829467b0906` |
| [integration/actors.yml](integration/actors.yml) | Unchanged | `f2b270b9038aa04427a7a1cb627d36d5067f6922211fa4e2b508fcec187f7d27` |

Body has four colour and four matching shadow LODs, one primitive each, 124 joints, maximum eight influences.
Combined body + staff counts remain **9427 / 4805 / 2192 / 1055**. No installed count increased.
[Checksums](export/SHA256SUMS), [current artifact manifest](review/round4/artifact_manifest.json).
Changed files include both exports, `work/production_master.blend`, `work/round4_lod0..3.blend`,
`textures/round4/sor1_{basecolor,normal,orm,mask}.png`, three viewer GLBs/manifest, review sheets and records.
Obsolete round-three intermediate exports are archived under `review/round4/baseline/export/`.

## Verification

- **Shared gate runner:** [50 static checks pass](review/round4/shared_gates/gates.md), bound to these export hashes.
  The local entry calls the shared runner's static functions. No animation gate was rerun: exact geometry/skin/clip
  preservation carries the accepted round-three G4–G6, elbow, wrist, jitter, contact, posture and timing evidence.
  Static config retains the accepted 907/7753 body far-LOD ratio (0.117 cap); no further reduction was authorized.
- **Weights and bindings:** [check_weights](work/round4_weights_check.txt) and
  [check_bindings](work/round4_bindings_check.txt) exit zero, **no BAD line**.
  All body LODs/shadows satisfy the stricter shared weight tolerance 1e-4; materials/shadows pass runtime checks.
- **Visuals:** [eight-view side-by-side](review/round4/eight_view_comparison.jpg) and
  [three tiers](review/round4/tier_comparison.jpg) preserve the accepted appearance; silhouette IoU is 1.0.
  [Robe/collar/hem at native texel scale and 4× mip](review/round4/mip_comparison.png) show no reported coloured
  streaks. The 4× test explicitly downsamples the material maps by four, at the same camera/render size.
  Tiny source-edge hem flecks found in the first close-up were repaired before the final checks.
- **Viewer revision mm6_sor1_codex_review4:** [24 clip/tier switches, zero errors](review/viewer_check.json),
  [skin checks pass](review/round4/browser/skinning_check.json), 14 browser stills including all tiers,
  collar/robe/hem close-ups, Standing, Attack and Cast. Browser/server helpers closed after checks.
  [Hem](review/round4/browser/hem_close.png), [collar](review/round4/browser/collar_c.png),
  [robe](review/round4/browser/robe_close.png), [viewer](review/viewer/index.html).
- Refreshed all-clip sheets: [front](review/final_clips/front_sheet.jpg),
  [side](review/final_clips/left_sheet.jpg), [three-quarter](review/final_clips/three_quarter_sheet.jpg).
  [Runtime audit](work/runtime_audit.json) also confirms read-only source reference hashes match.

## Accepted history and remaining integration

[Round-three handoff](review/round4/baseline/HANDOFF.md) retains the full rig/reduction/timing evidence and previous
hashes. Its pending-art statements are historical: the user subsequently accepted the look and motion.
[Round two](review/round3/baseline/HANDOFF.md), [round one](review/round2/baseline/HANDOFF.md).
Small dark facets around the collar visible in the accepted model remain; this revision does not alter geometry.
The accepted 11.2% combined far LOD, corpse pose and palette choices remain as recorded in round three.

The orchestrator installs these two exports and performs native material/blending/GPU checks and captures.
No descriptor merge is needed for this round. Browser/software rendering does not establish native GPU behaviour.
Workspace lease release is the final handoff operation; no paid job or helper process remains active.
