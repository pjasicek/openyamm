# Review round 1 — proposed playbook notes

- Choose two-handed clips by actual axe trajectory. Great Sword Slash (2) supplies this bull's chamber, weight transfer and follow-through; the previous authored swing is superseded.
- Fixed grips need full palm frames, not just hand positions or a sliding shaft projection. Use right-hand ownership, fixed off-hand IK, anatomical elbow planes and distributed forearm roll on every held clip.
- Do not bake quantized per-frame pole searches. Smooth the carrier and transported elbow-circle angle, then fit smooth contact corrections. Check angular acceleration after export; slowing a discontinuous pole curve does not remove the discontinuity.
- Fit the complete hoof sole plane through ankle/leg IK. Preserve idle body motion. Enforce gait heading in the gate instead of merely reporting it.
- LOD switch pixels measure the culling AABB diagonal. At an 88 px switch this body is about 61 px tall. Keep body and weapon counts strictly decreasing and record exporter removal of zero-area triangles.
- Retest reduction stops after animation changes. Rebake selected geometry and inspect all tier palettes. Correct tiny decimator UV extrapolations in the native mesh rather than weakening atlas validation.
- This local three.js loader retains extra weight attributes but skins four influences by default. The project viewer restores first-four sums and adds the second-four GPU terms. Shared viewer/engine files were not changed.
- Blender's importer creates an unlinked bone-display Icosphere. Exclude it from bounds/vertex comparisons. Imported rest frames can differ, so align native/exported vertices at a shared animated pose.
- Fractional action endpoints are truncated to whole export samples. Publish actual GLB durations in the manifest and retain impacts inside those durations.

These are proposed shared lessons for the orchestrator. No shared playbook, tool or engine file was edited.

## Review round 2

Accepted Attack spatial motion retained; early wind-up shortened by 20%; impact 0.947917 s.
Head/neck curves smoothed; rigid horn weights retained. Death now uses local Two Handed Sword Death:
single backward fall, axe release at 0.18 s, gravity drop and held terminal Dead pose.
Inspect Death at 0.1875, 0.375, 0.75, 1.5 and 2.4 s. Inspect the old Attack 34–39 phase after the timing shift.
Current shared-gate failures and missing head/neck/full-body/axe floor coverage are explicit in HANDOFF.md.
Historical custom gate passes are not evidence for this export. No game checks were run.
