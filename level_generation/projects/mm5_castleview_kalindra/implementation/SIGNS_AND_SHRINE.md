# Original signboards and northern shrine

Status: all four features have native readback and local visual review; shrine passage and representative clicks/reload pass.

| Original source | Label | Center | Local event |
| --- | --- | --- | --- |
| 3 (10,9), sprite 38 | West Tower ← | −8448, 14592 | 3004 |
| 7 (2,13), sprite 38 | No Swimming | 3840, 20736 | 3014 |
| 7 (11,2), sprite 38 | Danger Beware | 17664, 3840 | 3015 |
| 3 (8,14), sprite 37 | Northern shrine | −11520, 22272 | 3003 |

All retain their original centers and source object identities. Signboards face south; the western tower arrow
points geographically west. `prepare_source_signs.py` defines the fits and `author_source_signs.py` creates each
slightly leaning timber post, board, rear brace and metal bolts. Editable MM5-local SVG lettering is rendered to
256×128 PNGs by normal architecture preparation, with provenance recorded alongside the existing wood/metal palette.

`prepare_source_shrine.py` and `author_source_shrine.py` interpret the original open four-column portico using the
existing civic stone palette. Buried individual plinths support circular shafts and a complete flat cap. The central
224-unit passage retains the native ground; no raised platform blocks walking through it. Its original prayer and
level-granting intent remains recorded but deferred. All four features dispatch named status-only placeholders.

Nine [sign study views](../review/source_sign_study_v1/source_review.json) and three
[shrine study views](../review/source_shrine_study_v1/source_review.json) were actually inspected. The
[integrated source review](../review/waymarks_v1/source_review.json) confirms matching study geometry, materials and
sign artwork, plus clear approaches. Six preceding well OBJ headers were normalized to canonical semantic names;
their vertex, UV, face and material data remain unchanged. Exported names no longer depend on Blender's open study scenes.

`review_waymarks.py` checks native sign UV extent, material identities, buried feet, shrine passage and event bindings
during the build. The [native review](../review/waymarks_v1/native_review.json) records readable board faces, supported
columns/cap, ordinary forward shrine passage and named West Tower/shrine status clicks with save/reload. Wide cameras
were outside the configured 512-unit mouse interaction depth; closer repeated captures succeed without source or engine
changes. The first sign capture timed out waiting for follow-up actions during graphical approval; it is not click evidence.
Exposed save values remain unchanged, with the comparison's full-stat/level/QBit limitations retained.
These local studies do not approve the unfinished regional foreground or map rim.
