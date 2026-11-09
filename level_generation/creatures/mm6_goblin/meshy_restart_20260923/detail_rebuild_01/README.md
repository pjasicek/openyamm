# Goblin detail simplification — 2026-09-24

**Current result: a complete 10,577-triangle static review candidate, excluding the sword.**
This is a geometry/normal-map test, not a production-ready or rigged character.

## Open these files

- [Source / low geometry / baked export comparison](comparison.jpg)
- [Face comparison](face_comparison.jpg)
- [Clean editable Blender scene, with packed maps](goblin_simplified_10577.blend)
- [GLB with embedded maps](goblin_simplified_10577.glb)
- [Actual reimport render](export_front.png)
- [Rear view](final_back.png), [quarter view](final_quarter.png)

## What changed

| Part | Triangles |
| --- | ---: |
| Body, head, hands, feet and fused armor | 8,799 |
| Previously rebuilt skirt and belt | 1,392 |
| Pouch | 318 |
| Two upper-back plates | 68 |
| **Total** | **10,577** |

The twelve separate back rivets previously used 1,200 triangles. They now contribute to the plate normal bake,
with no separate rivet geometry in this export. The pouch was reduced from its clean 2,880-triangle component;
the earlier spatial pouch extraction also contained a disconnected slice of the right hand, which was removed.

The body uses weighted collapse decimation, retaining more geometry in the head after the first uniform
reduction made its silhouette too angular. Large spikes, the jaw, mouth opening and visible teeth remain
geometric. Shallow armor relief is largely represented by the dense-source normal bake; this does not mean
that every fused rivet was individually detached and rebuilt. The final body uses the unsmoothed source;
a first-pass gorget smoothing experiment was superseded by the weighted body reduction.

The head/mouth were reduced together. This is not a newly authored tooth row, mouth interior or facial rig.

## Maps and checks

- Shared 2048² tangent normal atlas for body, pouch and back plates.
- Existing 2048² skirt/belt normal atlas retained.
- UVs on every mesh; sampled raster masks show no overlaps between body/pouch/plate atlas regions.
- Major bake misses were reduced using a region-sized projection cage. Some local projection defects remain.
- Clean GLB reimport measured **10,577 triangles** and was rendered and visually inspected.
- An export initially used stale packed pixels. The image was unpacked, reloaded from the final bake and repacked.
  The embedded body normal image now matches the final bake pixel-for-pixel.
- Measurements: [final report](final_report.json), [reimport check](export_verification.json),
  [embedded texture check](texture_export_verification.json).

## Remaining work before production acceptance

1. Clean the remaining projection marks at the left shin rim, jewelry and thin armor edges. These are visible in
   the review images and are not claimed as finished texture work.
2. Correct the source's extra left-ear jewelry and tidy the mouth/ear details where needed.
3. Test joint deformation and repair topology around shoulders, elbows, wrists, hips and knees as needed.
   A successful static bake does not establish that collapse-decimated topology will animate well.
4. Produce authentic color and roughness textures; these current renders deliberately use neutral clay.
5. Add the separate sword, rig/weights and original-action animation checks. No sword is included in the count above.

Original models and earlier trials are preserved. No Meshy credits, Quad Remesher solver job or engine changes
were involved. Runtime skeletal skinning and normal-map support remain separate engine work.

## Resume and permissions

Use the clean `goblin_simplified_10577.blend` as the review asset. `goblin_low_detail_test.blend` is an earlier
working checkpoint containing diagnostics; it is not the final export. Scripts in `scripts/` document the
iterations and depend on the named working scenes, so they are not a standalone turnkey pipeline.

The user authorized routine Blender work without repeated confirmations. Write scripts in the permitted
workspace or /tmp separately, then invoke the already approved helper command on its own:
`python3 /tmp/openyamm_review_meshy_animations.py SCRIPT.py`.
Do not bundle heredoc/script creation into the elevated command. The `/snap/bin/blender` launch prefix is also
saved. Actual sandbox/client approval rules still apply; do not claim that chat authorization disables them.
