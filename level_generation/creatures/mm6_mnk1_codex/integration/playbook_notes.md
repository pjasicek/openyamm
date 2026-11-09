# BMonk production lessons for the orchestrator

Shared playbooks were read only. These are proposed notes, not edits to those playbooks.

- A label such as “unarmed fighter” does not establish the native attack. BMonk uses dual-palm elemental attacks;
  inspect native frames and merged monster data before selecting local clips.
- Meshy produced six fingers and a malformed left hand. A corrected five-digit right hand was mirrored, then both
  finger chains were fitted by connectivity; a generic humanoid rig alone did not resolve the anatomy.
- Distinguish the narrow anatomical wrist from the hidden shell stump under a broad sleeve. Label-based nearest
  Meshy weights tied the cuff to the wrong segment. Explicit piece ownership plus fitted rings was necessary.
- A central waist constraint must also be spatially limited; applying it to every vertex at waist height can pin a
  lowered cuff to the pelvis. Shared torso/skirt waist weights prevent the garment opening at the belt.
- The closed robe uses 12 circumferential chains of four fixed-length links. Neighbor-spacing and posed-vertex floor
  feedback were needed in addition to individual chain lengths; independent chains can open fan-shaped gaps.
- Cloth and boot corrections had half-frame keys at 30 fps. Export at 60 fps with doubled key times preserves them;
  exporting every integer frame at 30 fps discarded the corrective samples.
- Normalize quaternion signs before linear component interpolation. A sign flip can produce a violent half-frame
  roll despite identical integer-frame rotations. Recreate Dead from the complete final Death pose rather than
  overwriting only its endpoint keys while retaining stale intermediate keys.
- A smooth hand rotation must stay synchronized with its sleeve-clearance path. Slowing the palm alone created
  intersections. Giving only fast authored unfold intervals more time preserved the known-clear full pose path;
  the original handoff used 2.433333 s; review round 1 instead keeps the hands covered and restores a 2 s fall.
- Retexture omitted two tiny belt-knot triangles. Preserve the animated mesh, transfer the other 9377 faces with
  sub-micrometre corner error, then explicitly project the two missing triangles into the neighboring belt chart.
  Record their identities; do not add a generic relaxed nearest-face UV fallback.
- Palette brightness must not be normalized against unrelated bright cloth projection outliers. The final cloth
  ramp range uses native colours and the shared cloth luminance's 0.5–95 percentiles; 99.5 made nearly all cloth black.
- The shared LOD builder deliberately permits eight influences after collapse. Validate the actual runtime contract:
  review round 1 uses up to eight at LOD0 and reduced LODs, with normalized sums and identical bind space.

## Review round 1

- A covered monk idle needs real hand containment and matching forearm levels. Test skin vertices against actual opaque sleeve triangles from multiple elevations, then confirm the exported GLB and close-up cameras.
- Broad outer cuffs need an inner wrist lining so palms do not appear detached when released. Keep cloth texel density consistent; a locally high-contrast patch may still be mostly flat, so inspect the selected patch before repeating it.
- Blending a fixed tuck quaternion with a moving source quaternion can switch shortest arcs near 180 degrees. Blend fixed endpoint poses during entry/return and trace the actual exported motion. Preserve release timing and check the complete clearance path.
