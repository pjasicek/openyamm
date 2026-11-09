# Lich production notes for the integrator

- Native `lch` is a crowned, armored skeleton with short ochre tatters. The informal “robed caster” label
  should not produce a new full robe, staff or weapon. Descriptors are BLich A/B/C, IDs 568/569/570.
- A full-body Smart Topology made a poor skull. The skeleton reference route worked: one skull-only Smart
  Topology, then a measured graft. Rigid pieces use source-frame B_* joints; no Meshy rig purchase was needed.
- Shoulder tatters must hang from the collarbones. Upper-arm weights swung the left rag 29 mm into the skull
  during the raised dual cast; collarbone weights cleared the contact at 48 Hz. Delete obsolete body neck
  shell P13 after the graft; it appears as an unwanted floating ring in a textured close-up.
- Gate every transition against the source. Short entry/return blends made Fidget and Hit rotate too quickly.
  Fidget gained six-frame entry/return pads. Hit uses four-frame entry, a 13-frame sampled source and five-frame
  return, with 70% arm excursion: 0.733 s total, completing before the native 0.75 s cutoff.
- Keep Cast's skeletal fingers open. This also removed excess inherited finger spin while preserving the palm motion.
- Correct foot clearance between baked keys as well as at keys; quarter-frame clearance removed 5 mm sole dips.
- For imported GLB review bounds, select the skinned `Lich` mesh explicitly. Blender's glTF importer also makes
  hidden custom bone-display meshes; the first object of type MESH can be a unit sphere.
- Native tiers mostly change the bracers and a few small metal accents. One padded region mask and 16-stop
  linear ramps from palettes 763/764/765 are sufficient. Base/head color, normal, material-class and AO maps stay
  shared. ORM red uses the current **specular mask** contract, not the older AO-in-red paragraph.

No shared playbooks or tools were edited. These are proposed notes, not a change to the shared production workflow.
