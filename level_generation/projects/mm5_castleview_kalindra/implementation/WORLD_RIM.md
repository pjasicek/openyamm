# Western and southern Xeen rim

Status: V5 passes the repeated native corner/turn/reload views and the islet-facing context view. The corrected
renderer also passes the sampled MM6/MM7/MM8 views and an explicit missing-texture fallback capture.
The normal source/native now includes the 20 reviewed rim models. All 18 readback audits pass, and the integrated
corner/turn/reload/return and river views were inspected. Final regional composition remains open.

The alpha-only experiment is rejected. Its actual walking trace reaches Y=-24,310 over a height-zero floor with
neither flying nor airborne active, beyond the visible land ending at Y=-23,040.
See [movement evidence](../review/landscape_boundaries_v1/void_movement.json).

## Retained source meaning

[The source-cell census](../review/landscape_boundaries_v1/source_void_identity.json) finds 1,113 rendered void cells
inside the original world, all derived from surface 15. Another 3,697 extend beyond the original world boundary.
These are not water cells. `geography.py` explicitly preserves surface 15 as class zero and extends that void outward.

ScummVM's [Xeen surface enum](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/map.h#L154-L162)
identifies surface 15 as space. Its
[ordinary outdoor movement check](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/interface.cpp#L1015-L1043)
rejects entry onto space in the normal surface branch. The separate
[step-effect handler](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/interface.cpp#L697-L733)
distinguishes space from sky/cloud falling. This is a behavioral reference from a reimplementation, not a recorded
original-executable playtest. No external code is copied into OpenYAMM.

## Implementation direction

Preserve the impassable space boundary explicitly. A source-owned traversal restriction at the actual land/space
boundary is justified by that retained surface meaning; a new fall-and-respawn system is not required to reproduce
ordinary access. Do not disguise an arbitrary restriction as a mountain range, move the travel envelope, or place a
barrier through valid shore, water, source destinations or their approaches.

The visual layer must show an actual land edge and descending rock, with a void below. Simply making the height-zero
tile transparent leaves its floor intact. The initial flat green field was subsequently identified as opaque fallback
terrain, not merely lower-sky tint; see the exact pixel/source match below. A cliff skin alone also
does not remove that walkable floor. Resolve both layers together, including the river's termination at the edge.
Preserve the accepted river/Acid Pond planes, inland heights and accessible feature fits.

The isolated V1 prototype has 259 invisible solid faces along the exact land/space contour, plus descending rock.
[Actual native review](../review/rim_geometry_study_v1/native_review.json) records a stop at Y=-23,002.5 before the
Y=-23,040 boundary, a face hit with inward normal, save/reload and return onto visible land. This verifies one
ordinary straight approach only. At the stopped viewpoint the cliff disappears from view into flat lower sky,
so this version fails visual acceptance. The parsed
`collision_volume` mechanism label alone does not establish working collision support. Avoid choosing an engine
extension or invisible mesh solely because it is easy to serialize.

The [V2 source study](../review/rim_geometry_study_v2/source_review.json) adds an exposed rock lip while preserving
all terrain samples and native tile/attribute arrays. Its inland edge is more visible, but the cliff still reads as
stepped slabs and an opening remains at a cap/terrain bend. [Native V2 review](../review/rim_geometry_study_v2/native_review.json)
confirms the approach still blocks, but the lip still disappears from the stopped party viewpoint. This iteration is
also rejected. Correct cap contact against all crossed terrain triangles and revisit the visible profile from the
actual stopped viewpoint before adoption. The shared executable changed externally between captures; each review
records its actual hash, and no controlled binary/performance comparison is claimed.
The V3 cap follows all crossed terrain-triangle edges and adds a narrow exposed ledge beyond the unchanged source
collision boundary. [Its native review](../review/rim_geometry_study_v3/native_review.json) verifies the ledge remains
visible at the stopped ordinary viewpoint and after reload. An airborne hit and movement along a straight edge are
recorded; this is not full corner/flying acceptance.

V4 adds two original spill models across all 21 water-adjacent segments, using Alvar's established `WtrTyl`/FlowDown
surface treatment. [Readback](../review/rim_geometry_study_v4/water_readback.json) verifies 168 untouchable scrolling
faces and downward UV direction. [Actual bank views](../review/rim_geometry_study_v4/native_review.json) still fail:
opaque fallback terrain hides the descending geometry. The field's RGB 128,135,115 exactly matches
`colorFromTextureName("mm5void")`. [Renderer diagnosis](../review/rim_render_fix_v1/diagnosis.json) records the fix:
generate fallback colored triangles only for cells without a valid texture. The isolated release build passes.
[Repeated native views](../review/rim_render_fix_v1/native_review.json) show the cliff/spill and intact sampled MM6
town terrain, MM7 shore and MM8 shore. This is not all-map or controlled GPU-performance coverage. An isolated
deliberately missing `mm5absent` texture also receives its colored fallback in the inspected native screenshot.

[The fast native frame sequence](../review/rim_render_fix_v1/flow_tracking.json) verifies downward water motion:
all 15 adjacent comparisons move down, with static rock unchanged. Frames are 62–82 ms apart. Ordinary PNG captures
were about 1.6 seconds apart and aliased the scrolling pattern; their apparent direction was not reliable evidence.

The first two flying attempts remained grounded. The staged fly-up binding is J, not PageUp.
[The corrected J attempt](../review/rim_geometry_study_v4/flying_review.json) records 24 flying traces, a maximum
foot height near 4,000, and a boundary stop followed by reload/return. Its pre-fix images establish movement only.

The corrected-renderer straight-edge repeat retains the visible ledge. The ordinary convex-corner repeat stops at
both perpendicular faces near (-19,930.5, -23,002.5), but the low ledge nearly vanishes behind the HUD after turning.
V5 widens the dry exposed profile by 176 units while retaining the source collision line, water endpoints and all
terrain arrays. [The repeated native corner views](../review/rim_geometry_study_v5/native_review.json) retain visible
rock above the HUD at the corner and after turning/reloading. The islet-facing view shows the water drop beside the
existing bridge. The main author now consumes the same `world_rim.py` implementation: all 288 previous OBJ hashes
remain unchanged and all 20 added models match V5. [Integration evidence](../review/world_rim_v1/source_review.json)
tracks the source; [integrated native evidence](../review/world_rim_v1/native_review.json) records the completed
rebuild and affected native repeats. Rim sections are landscape groups, outside the small-prop radius census.
The original 288 native models are unchanged; the new 20 match V5 apart from the expected model-index offset.
This is not final regional acceptance.

Required review includes land-to-edge walking, oblique movement along bends, jumping/flying limits, turning back,
save/reload, Falista's approach, the wreck/river edge and the islet crossing. Normal player-height views must establish
the cliff/void appearance; a transparent atlas tile or authoring plan cannot establish completion.
