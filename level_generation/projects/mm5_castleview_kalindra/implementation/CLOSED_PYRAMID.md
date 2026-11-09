# Closed cross-world pyramid

Status: native local street appearance and real placeholder click/reload reviewed.

The original source is Castleview 29 (26,24), sprite 34: a warm masonry triangular passage. Preserve the recognizable
link as a closed monument in this MM5 slice; it must not travel to MM4 or a missing map.

The planned center (−8304, −4008) is only 210.9 units from the authored town wall, too close for its reserved 512×512
footprint. A bounded 256-unit eastward fit, (−8048, −4008), increases center clearance to 466.1 units. A southern
standing point 576 units from the center has 260 units of solid clearance and 1345 units of sprite-approach clearance.
These are source fit measurements, not final geometry/collision acceptance. Original source coordinates remain attached.
The footprint samples ground at Z=633–640; a fitted buried foundation is needed instead of a floating flat base.

The original sprite and the MM6 `outb3` pyramid material assignments were inspected. Native model 0 `pyramidbase`
uses `egybigb`, `egymedb` and `egywalg1`; the former two are warm masonry and `egymedb` is the candidate for this smaller
monument. No native model geometry is copied. MM8's inspected `t14` village textures are a different material language.

The exact MM6 `egymedb.bmp` is now copied to the MM5-local `mm5pyrst.bmp`, with source/hash provenance in the material
specification. This does not add an MM6 world dependency. `author_pyramid.py` independently creates the tapered stone
volume, triangular recess, sealed stone plug and two metal braces. Its foundation extends to Z=600 below the local
ground; its apex reaches Z=1168. All faces share the named closed-pyramid placeholder.

The [V2 source study](../review/pyramid_study_v2/source_review.json) corrects V1's denser front masonry UVs; front and
sides now share the native 256-pixel texture scale and level courses. All three repeated views were inspected.
The [integrated source audit](../review/camp_pyramid_v1/source_review.json) confirms an exact match to that study and
unchanged preceding model hashes. `review_camp_pyramid.py` checks written foundation burial, height, binding and exact
bitmap provenance. Actual street context, access and a real placeholder click remain required; final style acceptance
is not claimed by source review alone.

[Native review](../review/camp_pyramid_v1/native_review.json) records the street silhouette, grounded foundation,
closed entrance, named click and reload. Exposed non-clock saved fields match and the party stays on this map.
This accepts the local monument; final city and regional composition remain unfinished.
