# Falista and Nibbler: native scenery clearings

Both source contacts now own 16 authored native-sprite placements and two placeholder venues in the 45-site
inventory. Their native placements, ordinary access, clicks and save/reload are locally reviewed. No actors or reward behavior are added. [NATURAL_SITES.md](NATURAL_SITES.md) preserves their
original identities and deferred quest rules.

[The plan view](../review/clearing_proposal.png) shows actual terrain contours, native sprite half-width envelopes,
open approaches and Nibbler's empty future growing ground. [Placement data](../review/clearing_proposal.json) records
all 16 proposed anchors, original map usage, bitmap/palette sources, native scaling, collision bounds and distances
from roads, other assemblies, existing scenery and travel bounds. The larger crowns frame the small original
interaction reservations; they are individually grounded rather than sharing a flattened pad.

## Distinct settings

- Falista: three unevenly placed trees frame an open resting site on the southern slope. A flowered broken stump
  (`plant43`) is the proposed sanctuary placeholder; two small flower pockets, white understory and one low rock
  connect it to the grove. Preserve the future rescued-unicorn contact with no occupant or restoration effect yet.
- Nibbler: an open-branched western tree, shorter eastern crown and taller rear tree frame the natural shelter.
  The ivy-covered stump (`plant46`) is the proposed clearing placeholder, with two low rocks and sparse flowers.
  The approach runs west of the reserved growing ground. No productive melons, quest item or reward is present.

Both groups use `tree11`, `tree12` and `tree13` at native scale. The first two have 1024-unit visual heights and
512-unit half-widths; the shorter tree has a 512-unit visual height and 256-unit half-width. All have much smaller
16-unit collision radii. Treat the plotted circles as conservative view envelopes, not solid tree collision.
The stump sprites are 128×128 at scale one with radius 16 and descriptor height 24; their actual clickable screen
area must be checked at walking distance. Do not assume the descriptor height describes the entire visible stump.

The catalogue records `plant43` once and `plant46` twice in Ravenshore. The tree family appears in Ravenshore,
Garrote Gorge and Murmurwoods. These are local woodland details consistent with the linked decoration calibration;
their use does not imply importing Murmurwoods-wide forest density into this region.

## Fit and next implementation requirements

All proposed anchors lie on grass within the travel bounds. The nearest other assembly is over 9,332 units away
for Falista and 3,507 for Nibbler; the closest proposed Nibbler accent remains 736 units from a road segment. Falista's
tree bases range from Z80 to Z264, so real player-height views must establish canopy layering and root contact.
Nibbler's current nearest existing scenery is thousands of units away; the local group does not resolve the broader
countryside composition by itself.

The first draft diagram placed Nibbler's approach through the future crop plot. Shifted the proposed approach west
and inspected the repeated diagram. [Review evidence](../review/clearing_proposal_review.json) records that correction
and the inspected native art. This checks the plan and source sprites only, not native rendering or interaction.

Implementation must explicitly own these additional native decorations and their site/venue bindings. Keep all 698
baseline decoration identities represented exactly once. Use the reserved local events 149 and 150 for the two
stumps, retaining occupant identities as future semantic records. A native-only clearing must not be reported as
missing simply because it has no house BModel, or reported complete merely because its sprite records exist.
Export, inspect the actual scenes, walk each approach, click the stump and verify placeholder-only behavior.

Regenerate the proposal with `prepare_clearing_proposal.py`, then `render_clearing_proposal.py`. These commands write
review data only; active placements are owned by `prepare_clearings.py` and the shared `native_scenery.py` resolver.

## Authored implementation checkpoint

[prepare_clearings.py](../prepare_clearings.py) owns the placements, canonical sprite/descriptor provenance, site
ownership, contact venues and empty-space reservations. [prepare_scenery.py](../prepare_scenery.py) validates their
fixed anchors against native ground, other assemblies, roads, arrivals, colliders, canopy spacing and each site's
approach/crop area. All 16 pass. Existing baseline scenery remains accounted for, and all 255 BModel OBJ files are
unchanged. The author records these two native-only assemblies explicitly without inventing invisible house faces.

The draft confused catalogue zero-based runtime IDs with table row numbers. Canonical-name checks against the
current table caught this before native export; corrected proposal metadata and preserved its earlier version in
`review/clearings_v1/`. The correct runtime IDs include `tree11:460`, `tree12:463`, `tree13:466`, `plant43:618` and
`plant46:621`. Their table row numbers are one larger. The two stumps dispatch secondary events 149/150 with the
named source venue labels. Future resident records remain semantic data; no NPC rows are instantiated.

[review_clearings.py](../review_clearings.py) checks actual written descriptor IDs, positions, flags, events and
reserved spaces. The clearing checkpoint has 44 assemblies and 255 BModels. Native evidence below establishes
local appearance and interaction; broader terrain/contextual acceptance remains pending.

Source-art cross-check: both contacts use Darkside object sprite 28, the same small hut marker as the Skyroad
contact. [The source verification](SKYROPE.md) records that fact. These natural clearings follow the accepted new
composition mapping; their open settings are an intentional reinterpretation of the original interaction marker.

## Native clearing checkpoint

The native readback rejected one pre-existing flower in Falista's reserved approach. The fitter now checks the
whole approach/crop reservations and moves only that flower about 64 units, retaining its original identity.
The repeated native build passes both site audits. Actual player-height approach, click, reload, withdrawal and
side-group views are inspected in [the native review](../review/clearings_v1/native_review.json). Both stumps
display the named local placeholder. Save inspection preserves map, gold, food, held item and party health/inventory.

This approves local placement and interaction, not the surrounding terrain. Falista's adjacent black void edge
is visibly unfinished and must be repeated after the world-rim pass; Nibbler's wider fort/road context also remains
part of regional composition review. No residents, crops, rewards, rescue or quest behavior were implemented.
