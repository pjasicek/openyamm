# Riverside sewer outfall

The original outfall reservation remains at front `[-768,-10528]`, facing the southern bank. Its low vault uses
newly authored Garrote masonry geometry and native-resolution materials. A recessed metal grating identifies the
entrance; every bar and the dark end face dispatch venue `mm5:sw/sewer_out/entrance`, local event 145. The handler
remains a named status-only placeholder. No BLV transfer, NPC, monster or reward is added.

## Terrain and construction

The river and frontage ground lie at Z256. Native frontage tiles are `wtrdrs` shore/transition tiles, not pure-water
tiles; the source water-mask color alone does not establish runtime passability. The dry landing and threshold sit
at Z288, 32 above the river. A 256-wide, 608-long ramp joins the southern bank at Z358 to a wider 320×128 landing.
The bank end clears native terrain by six units. The approach intentionally extends beyond the original small
body reservation; it does not flatten terrain or relocate the source entrance.

The vault has an eight-segment arch, 128 inner radius, 224 outer radius, 160 spring height and 384 depth. Two lower
walls and two buttresses bury their bases beneath the native heightfield. The grating stands 48 units inside the
front; its crossbars and five vertical bars stop ordinary entry into the unimplemented passage. The dark end is
320 units inside. The supported interior floor ends at depth 376, eight units short of the rear closure to avoid
overlapping surfaces. The inactive return marker is `[-768,-10592,288]`, on the outer landing.

Materials reuse the inspected Garrote vocabulary: `t18a01a` masonry, `t18a02a` arch, `t18b01` support stone,
`t32a05b` paving, `gn_mtl03` grating and `solid01` recess. These are existing verified material files; no donor
BModel vertices are copied. [prepare_sewer.py](../prepare_sewer.py) fits the approach against native triangles;
[author_sewer.py](../author_sewer.py) authors the vault, landing and interactive grating.

## Review record

Inspected all three V1 source renders. The rear closure had conspicuous triangle UV restarts; a shared X/Z
projection fixes that in V2. The V2 rear view still showed a black strip where the landing skirt overlapped the
closure. Shortening the hidden threshold by eight units removes the overlap in V3. Repeated V3 front, oblique and
rear views have been inspected; [source evidence](../review/sewer_v3/source_review.json) includes image and OBJ
hashes. All 252 earlier model files remain unchanged.

[review_sewer.py](../review_sewer.py) checks written floor winding/grade/clearance, buried supports, water clearance,
rear separation, grating bindings and inactive return marker. All ten checks pass in the new native build, alongside
existing environment audits. The native map has 255 BModels and 85 handlers, with no actors/spawn records.

[Native review](../review/sewer_v3/native_review.json) records seven actually inspected images: bank, ramp, click,
blocked forward movement, restored view, backward exit and rear river view. Ordinary movement reaches the grating
and stops there; the click shows the named status placeholder. Quicksave/reload restores the same view and a
backward walk returns outside. The native rear has continuous masonry and no black overlap. Decoded before/after
saves preserve map, gold, food, held item, health and inventories. The inspector does not report coordinates or QBits.

The isolated [starting save](../review/playtest/start_sewer.json) matches this revision. This accepts the local
construction/access/placeholder checks; final riverbank composition and whole-map acceptance remain outstanding.
