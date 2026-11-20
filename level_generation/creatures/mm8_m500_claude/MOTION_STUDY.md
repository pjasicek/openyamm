# Water Elemental m500 motion and identity

Native authority: ../mm7_mm8_packed_outline/session_mm8_04/mm8_m500/references (original pixel sheets).
Selected body masters and provenance: references_hd/. Head texture masters: references_head/.
Observed anatomy: solid blue scaled fish-serpent, two webbed hands, fish lips and yellow eyes,
one median cranial/dorsal crest, back sail, dorsal tail fins and a vertical caudal fan. No equipment.
Five hand digits and flat continuous ventral scutes are reconstruction interpretations; native detail is limited.
The solid-body route applies despite the elemental name: source frames have no transparent effect shell.

| Role | Native seconds | Authored intent |
|---|---:|---|
| Standing | .125 held | restrained breathing over grounded open coil, 3-second loop |
| Walk | 1.125 | tail wave propagates back, upright trunk remains steady |
| Running | no separate source | faster adapted tail wave |
| Attack | 1.0 | open arms rise outward, chest/head draw back, mouth release at about .5 s, recover |
| Cast | same native attack source | distinct two-palm charge/thrust, cast socket at hands |
| Hit | .75 | head and upper trunk recoil backward, arms flare up then settle |
| Fidget | .75 | small alternating hand/forearm movements, planted lower body |
| Death | .625 | backward arch, head folds down toward tail; no dissolve |
| Dead | .125 held | terminal inverted-U trunk and solid coiled corpse |

The unused_d_2 original side sheet confirms the backward arch and tail contact in depth; active death uses view 0.
Original frame holds and descriptor data are recorded in work/native_timing.json.
Caster comparison: owned humanoid UnarmedCastDualAttack2 has a clear anticipation and two-palm thrust;
use that choreography for Cast with a locally fitted serpent rig, not its humanoid legs or root motion.
UnarmedCastDualAOE2 has an overhead jump and is rejected for this grounded creature.
Source pose samples are in review/source_motion; these are contact-sheet reviews, not playback evidence.

Pilots: grounded Walk and demanding Cast/Attack. Check fixed bone lengths, tail upright frames, fin roots,
webbed-hand flexion and palm orientation. Review all clips at normal/slow speed after export.
Install only descriptors 76/77/78. A/C share palette 501; B uses 502; native scale differs for each.
Delivery also reaches runtime LODs, material masks/ramps, cast/attack event sockets, one family regression,
and indoor/outdoor same-camera native comparisons. Preserve native sprites and unrelated bindings.
