# Dark Grove Skyroad access: source and construction requirements

The retained source interaction is A3 `(14,7)` → Skyroad A3, map 91 `(13,8)`. Its reverse record is map 91
`(13,7)` → A3 `(14,7)`. [The extracted records](natural_site_sources.json) retain both routes separately; neither
is active in this environment milestone. The original prompt describes a rope passing through a ceiling.

## Artwork verification

The object at this location uses sprite 28. Inspected the extracted `sprites/dark/028.obj/frame_0000.png`: it shows
a small thatched hut, not a freestanding rope. The same source sprite is also placed at Falista and Nibbler. This
explains the source's generic hut/ceiling language; the selected recreation mapping deliberately interprets the
creature contacts as natural clearings and the Skyroad contact as an exposed climbing landmark.

This is the direct sprite number, not number plus one. ScummVM's
[Xeen map loader](https://raw.githubusercontent.com/scummvm/scummvm/master/engines/mm/xeen/map.cpp) selects the
object archive and formats the stored sprite number directly as the object filename. A3 uses the Darkside object
archive. The unrelated `xeen/028.obj` barrel and adjacent Darkside object images do not describe this contact.
The source code was used only to verify resource selection; none is copied into OpenYAMM.

## Retained geometry intent

The accepted mapping calls for a rope and anchoring rock/tree structure, with clear ground access and no new house.
The original compact reservation is centered at `[-2304,11520]`, with south-facing front `[-2304,11232]`; central
ground is Z704. Ground 704 units west is Z688 and 704 units east is Z704. Preserve the existing off-road Dark Grove
relationship and fit the anchor to the actual terrain without adding a lane or flattening a house pad.

The final composition must explain both ends of the rope. A pole or dangling segment with an unexplained cut top
does not establish sky access. Resolve a visible upper anchor or a deliberate canopy/cloud termination, inspect
the full silhouette and player-height approach, and retain a separate inactive ground return marker. The full
Skyroad map and actual climbing/transfer are deferred. Reserve local event 151 for the visible rope/contact surface;
its named unavailable feedback must leave the party on valid ground.

The native map checkpoint is tracked below; these source findings alone do not certify a completed landmark or functioning destination.

## Working canopy-access study

[author_skyrope.py](../author_skyrope.py) now creates an isolated original climbing rig: stranded rope, loose ground
coil, knotted upper wrap and timber brace lashed to a native `tree12` trunk within its canopy. It uses existing
`t06c11`/`t06a10` materials and independently generated geometry. The tree retains its native 1024-unit artwork
height. This is an exposed climbing contact leading toward the deferred upper route; no full Skyroad geometry is
introduced. The body is still only a study and is not included in the active map source/export.

The first isolated render ignored the preview PNG's alpha and showed an opaque rectangle; fixed its material to
use the existing RGBA alpha. The next views exposed a disconnected-looking brace and floating lower coil. Lowered
the brace to a visible trunk lashing and fitted the coil to the study ground. Inspected repeated approach, side
and upper-knot views in [V3 source evidence](../review/skyrope_study_v3/source_review.json).

Next, fit the rig at its original map reservation, add its native tree/context explicitly, bind the visible rope
and coil to event 151, retain a clear inactive ground return, and review native movement/clicks and the silhouette
from multiple directions. The study's flat ground and local render do not establish any of those native checks.

## Authored map source

The rig now occupies its original Dark Grove site in the main source scene. `prepare_skyrope.py` preserves the
source route and inactive return `[-2176,11104,704]`, uses one inert native tree12 and reserves the southern approach.
`native_scenery.py` owns shared explicit-site descriptor/art resolution for this tree and the two clearings.
Two original BModels contain the brace/lashing and clickable rope/coil. Event 151 belongs only to the latter.

The coil's full local support patch is flat at Z704. Inspected main-scene approach, side and upper-knot renders
with the actual heightfield and native alpha tree in [the source review](../review/skyrope_v1/source_review.json).
All prior 255 OBJ hashes remain unchanged. Native export, quantized geometry audit and local runtime review are complete; see below.

## Native checkpoint

[Native review](../review/skyrope_v1/native_review.json) contains inspected front/side silhouettes, ordinary ground
approach, actual rope click, F9/F10 reload and withdrawal. The 994 exported contact faces retain event 151; the coil
is one unit above native ground and no face degenerates after coordinate quantization. The supporting tree is inert.
A dimension error in the new review script was corrected and the audit repeated without changing native geometry.

The real click displays `Dark Grove Skyroad rope: not implemented yet.` and leaves the party on this map. Decoded
pre-click/save fields retain map, gold, food, held item and party health/inventory. This is the ground contact only;
upper-map geometry, climbing/travel and complete regional scenery remain outside this local acceptance.
