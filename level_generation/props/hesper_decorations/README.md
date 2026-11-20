# Hesper decorations in 3D

3D decoration models for the Hesper world (Starport Reach and the zone 1 interiors): the organic pieces through Meshy,
the hard-surface pieces built in Blender. The interiors' list and counts are in
[INTERIOR_ART.md](../../../design/kreegan_world/zone1/dungeons/INTERIOR_ART.md#3d-decorations). Designs, places and looks: [STARPORT_REACH.md](../../../design/kreegan_world/zone1/STARPORT_REACH.md)
("Decorations", "Chests"); concept sheets `design/kreegan_world/zone1/concepts/z1_05_decorations.png` and
`z1_06_chests.png`.

## Route (organic pieces)

The ground-item route ([playbook](../items_claude/GROUND_ITEM_3D_PLAYBOOK.md)), with the approved concept crop as the
design source instead of an inventory icon:

1. `python3 -I scripts/deco3d.py master <design>`, then `deco3d.py codex meshy/<design>/references_hd/CODEX_BRIEF.md`:
   Codex makes the HD three-quarter master from `concept_crop.png`, or, for a design with no concept (`"concept":
   null`), from its identity text and the style references in its `refs` (copied in as `ref_<n>.png`). Review before
   spending credits.
2. `deco3d.py st-request <design>`, then `tools/run_creature_meshy.sh` submit / poll / download: Meshy Smart Topology,
   untextured, 5 credits a model.
3. `blender --background --python scripts/codex_texture.py -- prep <design>`, `deco3d.py paint-briefs <design>`,
   the three Codex painting sessions, then `codex_texture.py -- bake <design>`: base colour, metallic-roughness and
   normal maps from Codex's paintings.
4. `check_winding.py`, then install as an engine model (`tools/install_model.py --engine`) and bind.

`scripts/codex_texture.py` is a copy of the item route's script (it reads this folder's `designs.json`) with one
addition for the buildings: `repack <design>` between the paintings and the bake. Meshy returns the buildings as
hundreds of small islands, and prep's 1 % margin round each left about 5 % of the texture in use (the first hull-home
bake was blurred); `repack` unwraps with a 0.2 % margin and packs the islands rotated (25 times the texels), and a
design's `texture` (2048 for the buildings) sets the maps' size. The guides and paintings do not depend on the UVs.

## Designs

The buildings of the second Starport Reach pass (2026-10-21, after the user's review of the first build: "the houses
just look plain bad, like we are in a sci-fi world, it needs to look the part") are models too: the Ashrunner camp,
the Hesperian encampment round the Lift Head, the scrapyard crane and the forward outpost. The map gives them
invisible collision boxes instead of collision cylinders (`building` in
[build_out1.py](../../projects/hesper_out1/build_out1.py)).

| Design | What | Triangles | Status |
|---|---|---|---|
| `hes_skull_ribs` | Giant Kreegan skull and ribs, half sunk in ash (a landmark) | 6 000 | mesh 5 999; baked, winding clean |
| `hes_founder_statue` | Headless robed founder statue on a cracked plinth | 4 500 | mesh 4 181; baked, winding clean |
| `hes_ashrunner_totem` | Scrap scarecrow with goggles, cape and hanging charms | 3 500 | mesh 3 269; baked, winding clean |
| `hes_creep_pod` | Kreegan creep pod: tendril cage over glowing egg sacs | 3 500 | mesh 3 500; baked, winding clean |
| `hes_kreegan_pod_chest` | Closed Kreegan pod chest | 3 000 | mesh 2 912; baked, winding clean |
| `hes_corpse_colonist` | Drowned Hesperian worker, face hidden (D2, D10; clickable) | 3 500 | mesh 3 500; baked, winding clean |
| `hes_founder_intact` | The founder statue whole and clean (D10) | 4 500 | mesh 4 403; baked, winding clean |
| `hes_salvage_heap` | Heap of scrap, panels, pipes and cable (Lowhold, the scrapyard) | 4 000 | mesh 3 962; baked, winding clean |
| `hes_market_goods` | Sacks, roots, jars, tins and a crate (Lowhold stalls) | 3 500 | mesh 3 500; baked, winding clean |
| `hes_loader_mech` | Dead cargo loader mech with forks (D0) | 6 000 | mesh 5 999; baked, winding clean |
| `hes_resin_rib` | One curved Kreegan resin rib of the scrapyard fence | 3 500 | mesh 3 500; baked, winding clean |
| `hes_ash_hull_home` | Ashrunner home: a gutted crawler-tank hull under tarps  stove pipe (concept z1_03) | 8 000 | mesh 7 143; baking |
| `hes_ash_hull_home_b` | Ashrunner home: an upright cargo-crawler hull section  corrugated porch | 7 000 | mesh 6 777; baking |
| `hes_ash_trader_stall` | The Ashrunner trader's stall (concept z1_03) | 7 000 | mesh 6 999; baking |
| `hes_ash_watchtower` | Ashrunner scrap watchtower (concept z1_09) | 6 000 | mesh 5 510; baking |
| `hes_low_pod_home` | Hesperian home in a landed escape pod (concept z1_03) | 7 000 | mesh 6 808; baking |
| `hes_low_shelter` | Hesperian tarp shelter against an Ancient slab; Venn's camp (concept z1_03) | 5 000 | mesh 5 000; baking |
| `hes_low_palisade` | One straight salvage palisade segment  tiles end to end | 3 000 | mesh 2 738; baking |
| `hes_low_gate` | The palisade gate: two plate towers  a hull-rib lintel  open leaves | 5 000 | mesh 4 888; baking |
| `hes_low_water_still` | The Hesperian water still and basin (the camp's well) | 4 000 | mesh 3 913; baking |
| `hes_salvage_crane` | The Kreegan scrapyard's work crane: Ancient lattice in resin  claw and plate | 6 000 | mesh 5 867; baking |
| `hes_kreegan_outpost` | The forward outpost: resin grown over a white pylon tower (concept z1_03) | 8 000 | mesh 7 580; baking |
| `hes_alarm_pylon` | The outpost's glowing alarm pylon (concept z1_03) | 3 500 | mesh 3 371; baking |
| `hes_glass_tree` | Glass tree: a tree-shaped black-glass fulgurite (the wild "trees" of Starport Reach) | 4 000 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_wire_thicket` | Wire scrub thicket: a dome of black wire stems with rust-red tips | 3 500 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_ash_hoodoo` | Ash-stone pillar: wind-cut layered volcanic stone with a cap rock | 3 000 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_fungus_tree` | Landfall's cultivated fungus tree in a prefab planter ring  a grow-light over it | 4 000 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_fungus_tree_b` | Fungus tree, cluster: three slender stalks with bell caps in a dark planter ring | 4 000 | Landfall dressing (2026-10-21, the user: "atleast 2 variations of the fungus trees") |
| `hes_fungus_tree_c` | Fungus tree, shelf: a thick ribbed trunk wearing tiers of bracket caps, white ring | 4 000 | Landfall dressing (as above) |
| `hes_fungus_planter` | Dark prefab planter box of pale cultivated mushrooms (Main Street) | 3 000 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_fungus_clump` | Knee-high clump of cultivated mushrooms (beds, the ring round the fountain) | 2 500 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_water_condenser` | A settler's water condenser tower beside a house | 3 500 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_hand_cart` | A settler's two-wheeled hand cart with crates | 3 000 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_market_goods_colony` | Landfall's stall goods: ration crates, canisters, fungi, energy cells (replaces hes_market_goods) | 3 500 | Landfall dressing (2026-10-21, the user's second review: "come up with some 3D decorations") |
| `hes_lander_wreck` | The party's wrecked colony lander, from the lander in concept 01 (hes_out1's crash site) | 9 000 | mesh 8 854; repacked, baked at 2048, winding clean |
| `hes_lander_wing` | The lander's torn-off wing (no concept: the wreck's crop and the style sheet) | 4 000 | mesh 3 999; baked, winding clean (front/back views registered at 1.24-1.38: thin end-on silhouettes) |
| `hes_lander_engine` | The lander's torn-off engine nacelle | 3 500 | mesh 3 500; baked, winding clean |
| `hes_collar_node` (and `_off`) | The Scour's collar node: a resin pillar round white-and-gold machinery, four violet-red lenses (concept z2_07; `_off` is the same model with its lenses darkened) | 4 000 | mesh 3 957 |
| `hes_overseer_perch` | The Scour's Overseer perch: a deck on four resin-wrapped ceramic legs, a bone-spike railing (concept z2_07) | 5 000 | mesh 4 885 |
| `hes_derelict_hull_a` | The Scour's derelict swarmship, bow half: a ribbed chitin keel (concept z2_08) | 7 000 | mesh 6 999, repacked, maps at 2048 |
| `hes_derelict_hull_b` | The Scour's derelict swarmship, stern half: a ported hull with five rib spines (concept z2_08) | 7 000 | mesh 6 798, repacked, maps at 2048 |

The baked models are `work/codex_tex/<design>_export.glb` (base colour, metallic-roughness and normal at 1024); compared
with their masters in `review/organic_v1/compare.jpg` and, for the interior five, `review/organic_v2/compare.jpg`. The
first five's painted views registered at 1.00-1.01. The pod chest's orange seams came out fainter than in its master.

## Hard-surface pieces

Built by `scripts/build_hard_surface.py` (Blender, headless) from primitives, textured with the Hesper sets in
`design/kreegan_world/art/` (cube-projected at the BLV/BModel texel density), each material with a normal map derived
from its texture and its own roughness and metallic; lamp glass, the casket's seam and candle flames add a constant
emissive colour. Output `work/hard_surface/<name>.glb`; renders `review/hard_surface_v2/sheet.jpg`. All thirty pass
`check_winding.py` (0 inverted closed parts).

The first build (`review/hard_surface_v1/`) projected every texture as a 1.28 m square, which stretched the non-square
ones (the 4:1 gold trim, the 1:2 wall panels) and spread the trim's dark groove over whole parts. UVs now follow each
texture's native size, and gold parts and beams use seamless strips cut from the trim's gold band and the girder
texture's beam (`STRIPS`).

| Model | Faces | Size (m) | Notes |
|---|---|---|---|
| `hes_pylon` | 56 | 0.64 × 0.64 × 3.54 | Dead landing-light pylon |
| `hes_container` | 18 | 2.42 × 1.24 × 1.29 | Cargo container; its end bands stand 1 cm proud of the ends (flush, they z-fought) |
| `hes_fuel_tank` | 78 | 2.72 × 1.24 × 1.42 | On saddle feet |
| `hes_gantry_segment` | 132 | 4.50 × 0.88 × 1.06 | Toppled lattice section |
| `hes_signpost` | 24 | 1.38 × 0.46 × 2.10 | Ancient glyph signpost, two arms |
| `hes_tablet_plinth` | 24 | 0.90 × 0.90 × 1.35 | Colony log tablet on a stepped plinth |
| `hes_brazier` | 50 | 0.64 × 0.64 × 0.75 | Ashrunner drum brazier (the flame is an effect) |
| `hes_colonial_locker` | 66 | 1.59 × 0.90 × 0.80 | Chest. Second pass: larger, a lid, gold corner posts and seam, a drawn keypad mapped once over its panel (`hckeypad`), a blue status light |
| `hes_ashrunner_crate` | 24 | 1.10 × 0.65 × 0.54 | Chest |
| `hes_glass_shards` | 42 | 0.77 × 1.06 × 1.18 | Cluster of black glass shards |
| `hes_glass_boulder` | 40 | 2.06 × 1.54 × 1.31 | Faceted glass boulder |
| `hes_drone_wreck` | 290 | 1.88 × 1.42 × 1.00 | Second pass: the concept's white-and-gold sphere with a dark lens, broken open, shell plates round it |
| `hes_glass_shards_blue`, `hes_glass_boulder_blue` | 42, 40 | as above | D2: the Glassback Queen's growths (`higlass`) |
| `hes_relay_post` | 88 | 0.70 × 0.70 × 2.41 | Aster's relay post; its crystal glows by its light group |
| `hes_baggage_cart`, `hes_baggage_cart_over` | 98, 104 | 1.52 × 0.79 × 1.02 | Upright and overturned |
| `hes_shelf_rack`, `hes_shelf_rack_tools` | 132, 134 | 1.81 × 0.55 × 2.17 | Boxes; drums, pipes and boxes |
| `hes_luggage_pile` | 150 | 2.14 × 1.54 × 0.53 | Cases and bags |
| `hes_bench` | 42 | 1.92 × 0.51 × 0.99 | Colonial bench |
| `hes_fallen_plates` | 170 | 2.48 × 1.80 × 0.63 | Fallen wall panels and rubble |
| `hes_hanging_lamp` | 80 | 0.44 × 0.44 × 1.43 | Origin at the lamp's foot; the chain's top is its height; glass emissive |
| `hes_lamp_string` | 208 | 6.06 × 0.09 × 0.84 | Cable sagging 0.6 between hooks 6 apart, five lamps |
| `hes_drum` | 74 | 0.60 × 0.62 × 0.90 | The brazier's drum with a lid |
| `hes_bedroll` | 54 | 0.88 × 1.96 × 0.29 | Rug blanket, rolled cloth, pillow |
| `hes_offerings` | 196 | 0.98 × 0.84 × 0.70 | Candles (emissive flames), bowls, a crystal, a post with cloth strips |
| `hes_casket` | 60 | 1.50 × 0.80 × 0.78 | Chest; marble, gold bands, a cyan emissive seam |
| `hes_lectern` | 38 | 0.62 × 0.60 × 1.15 | Reader slab of dark glass |
| `hes_crystal_socket` | 42 | 0.28 × 0.28 × 0.61 | Aster shard socket; glows by its own light |
| `hes_fountain` | 202 | 3.51 × 3.51 × 2.81 | Landfall's fountain: an Ancient purifier, octagonal basin, fluted column, four streams, a crystal |
| `hes_stat_barrel_<colour>`, `hes_stat_barrel_empty` | 112 | 0.74 × 0.75 × 0.99 | MM7's stat barrels as the white colony drum, open: the liquid (red, orange, blue, yellow, green, purple, white; flat colour, a little emissive) in a gold rim and a gauge strip |

### Hangar Nine's lander sockets

`scripts/build_lander_sockets.py` (Blender, headless; it imports `build_hard_surface.py`'s kit) builds the derelict
lander's five sockets for D0 Hangar Nine, three states each, scaled up so they read from the hangar floor:
`hes_sock_<socket>_dead` (empty, unpowered: dark cavity, loose cable ends), `_ready` (the power on: amber lamp) and
`_lit` (the part fitted, glowing cyan, the lamp green), for `cockpit` (a gold cradle on the flight console; the
Pilot's Core, 0.56 m), `coil` (a gold-framed bay; the Ion Coil's rod and rings, 0.9 m), `nav` (the Nav Matrix's glowing
plates), `engine` (the Energy Core's caged cylinder, 1.0 m) and `ring` (the Re-entry Emitter's ring and disc). Their
backs are the plane y = 0 (the hull). Also `hes_light_pylon_off`, the light pylon with an unlit diffuser. All pass
`check_winding.py`; bound in `level_generation/projects/hesper_stage/decorations.yml`.

### The Crown's props (hes_out4)

`scripts/build_crown_props.py` (Blender, headless; it imports `build_hard_surface.py`'s kit) builds the Crown's new
props from [THE_CROWN.md](../../../design/kreegan_world/zone4/THE_CROWN.md) sections 12 and 14 and
[KITS.md](../../../design/kreegan_world/zone4/KITS.md), concepts `z4_03`, `z4_04`, `z4_06`, `z4_08` and `z4_10`. It
adds the zone 4 textures to the kit's tables: `hocannon`, `hntrim`, `hnresin`, `hncapac`, `hnstrip` (K9), `homast`,
`hpbanner` (K10), `hkglyph` (K5) and `hlscorch` (`hlhull` darkened under soft soot blotches, written to
`work/hard_surface/derived/`). A `sweep` helper makes the tapered tubes (resin roots and claws, prongs, stakes, cables,
the arc). The banner and the glyph plate map their texture once over the front (`fit_faces`). Every model's origin
is the centre of its foot and its front faces -y (glTF +z). Faces are Blender polygons, with GLB triangles in brackets.
Renders are in `review/crown_v1/` (`sheet.jpg`, with detail views) and, for the great cannon, `review/crown_v2/`.
All pass `check_winding.py` (0 inverted closed parts, no open parts). Nothing reaches below the ground: the build
snaps a model's lowest point to z 0, so sweeps, sunken rocks and tilted slabs are flattened at the ground
(`ground_clamp`) instead of lifting the whole model (the first build floated the bastion cannon 0.25 m and the pile
0.28 m).

| Model | Faces | Size (m) | Notes |
|---|---|---|---|
| `hes_great_cannon` (rest), `_dark`, `_c1`…`_c5` | 2 564, c5 2 654 (2 908, c5 3 070) | 25.62 × 51.76 × 21.12 (c5 52.62 deep) | The one great cannon on the Crownspire's dome (COMBAT.md "Ion cannons"; `concepts/monsters/ion_cannon.png`, candidate 1). A stepped round base (radius 12) of `hocannon` slabs, a resin course, a gold turning ring and resin roots; a yoke platform 20 m across with two cheeks and gold hubs. The head lies level along -y (glTF +z): a slab-sided octagon 50 m from the breech (12 m behind the origin) to the prong tips (38 m in front), white ceramic (`hoterm`; `hocannon`'s lattice made a mosaic of it) above a resin belly, gold collars, seven bone fins raked back along its spine, four resin cables from the yoke into the breech. **Pivot 12.0 m up on the origin's vertical; the bore's centre 12.0 m up, its glowing face 34.25 m along +z; the prong tips' plane 38.0 m along +z.** Four glow zones, each its own material per zone and level (`HS_gc_<zone>_<level>`; zones `breech`, `pods`, `ring1`…`ring5` from the breech, `muzzle`; levels `dark` dark glass, `dim` violet, `lit` violet-white, `hot` white): the breech core (a round window in gold on each side of the breech), the twin capacitor pods (the breech's upper flanks), five capacitor rings and the muzzle crown (the bore and the inner blades of three prongs). States: `_dark` all dark (powered down, the instant after a shot); rest all dim; `_c1` the breech lit; `_c2` plus the pods; `_c3` plus rings 1–2; `_c4` plus all five rings; `_c5` everything lit, the muzzle white-hot and three jagged arcs between the prong tips (the only geometry that differs). Static: no pitch bone |
| `hes_ion_cannon`, `_dark` | 1 426 (1 600) | 11.66 × 22.56 × 8.62 | Base drum radius 5.0, roots to 6.1 (fits the bastion's 7.2 top). The pivot is 5.6 m up; the barrel is 22.25 m from breech to emitter and points along -y, raised 8°, reaching 17.1 m in front of the origin and 5 m behind it. White ceramic barrel with gold rings on a `hocannon` yoke and turntable; resin roots up the drum and cheeks, resin spikes. Lit: the emitter tip (blue), two barrel seams and the cheek slots glow; dark: dark glass. Static: no `B_Barrel` bone. Superseded by the great cannon (the bastions now carry Crown Sentinel turrets); kept |
| `hes_node_mast`, `_off` | 566, 506 (692, 584) | 2.01 × 2.01 × 12.51 (off 12.40) | Resin foot (radius 0.8) with four claws, a `homast` shaft with gold bands, a gold collar and two bone prongs opening upward, their tips 1.44 apart at 12.4 m. Lit: two jagged emissive strands between the tips (0.8, 0.68, 1.0); off: no arc, dark tips |
| `hes_glyph_plate` | 12 (24) | 6.00 × 0.80 × 9.30 | Resin slab 6 × 0.8 × 9 on a 0.3 stub; the front face carries `hkglyph` once (the square texture stretched 1.5× up the 2:3 face) |
| `hes_grafting_frame` | 650 (858) | 3.90 × 1.54 × 4.25 | Two pointed resin arches, cross ribs, gold apex spikes; a white-gold capacitor cell (glowing middle band) held by four resin claws over a stump; three cables |
| `hes_membrane_banner` | 295 (394) | 2.20 × 0.93 × 4.60 | Bone pole on three gilded claw feet, a bone cross-bar with gold ends, a waving 1.5 × 3.0 membrane in front of the pole with `hpbanner` on both sides, a gilded spear tip and crescent |
| `hes_cable_spool` | 648 (714) | 2.45 × 4.66 × 2.85 | Spool 2.6 across and 1.8 wide, its axis along x: resin flanges with gold rims and wound `hnstrip` cable on two resin A-frames on a cradle slab. The loose end runs 3.3 m along the ground in front (-y), which is most of the 4.66 depth |
| `hes_trophy_pile` | 456 (670) | 2.57 × 2.36 × 1.50 | Broken `hocannon` plates over rubble, a ceramic helmet with a gold brow and dark visor impaled on a bone stake, gold rings |
| `hes_pen_post` | 480 (808) | 1.36 × 0.82 × 2.20 | Resin post with a gold band and gilded cap; a hook arm in front holds a resin chain down to a violet-red emissive collar, and a second chain drapes to the ground on +x |
| `hes_crawler_wreck` | 1 002 (1 196) | 11.05 × 7.37 × 3.62 | Hull 8.7 × 3.4 on its +y track, sagging 3.6° toward the lost -y track. The front (-y) is torn open between x -2.4 and 2.0, with the floor inside 0.2 (front) to 0.4 (back) m up and about 2.6 m clear: the locker stands inside. The inside, roof and nose are scorched (`hlscorch`), with `hlhulltorn` plates round the opening and a broken sensor turret. The thrown track (+x), a fallen wheel and a wall plate lie on the ground; the hull alone is 9 × 4.5 m |
| `hes_fire_bowl_gilded` | 579 (678) | 1.17 × 1.15 × 1.15 | Polished resin bowl (0.92 across) on an hourglass stem, three gilded claws curling over the rim, six gilded rim horns, an emissive ember mound with coals (the flame is the light) |

### The Brood Spires' props (hes_out3)

`scripts/build_brood_props.py` (Blender, headless; it imports `build_hard_surface.py`'s kit) builds the two
hard-surface pieces of [BROOD_SPIRES.md](../../../design/kreegan_world/zone3/BROOD_SPIRES.md) section 14 (KITS.md),
replacing the greybox stand-ins in `level_generation/projects/hesper_out3/standins/` (this folder is read first). It
adds the colony livery (`hhprefab`, the teal and orange stripe) to the kit's materials. Renders:
`review/brood_hard_v1/`. Both pass `check_winding.py`.

| Model | Faces | Size (m) | Notes |
|---|---|---|---|
| `hes_trail_cairn` | 72 | 1.23 × 1.06 × 1.22 | Four white ceramic slabs stacked and turned, a shard on top, chips at the foot, a red-and-gold cloth strip (`hfbanrd`) round the middle with two hanging ends. Twice the design's 0.6 m (the integrator's review: lost on the pale lane) |
| `hes_agflyer_wreck` | 932 | 18.51 × 18.90 × 6.98 | A colony crop flyer (event 20, "Agri-Service 3"), nose at +x: a box cabin in the livery, a dark canopy, the crushed nose in `hlhulltorn`, a spray tank with hazard bands, a high wing with a ducted fan and a nozzle boom, a tail boom with fin and tailplane, skids. Pitched nose down 0.16 rad and listing 0.07 to the right, where the wing is torn at the root; the torn wing and its fan lie beside it (-y). Resin creep lumps over the tail boom, two roots climbing to them from a star of ground roots. The map's three collision boxes (cabin, tail, fallen wing) are measured from these bounds in `build_out3.py` |

## Spending

The user approved Meshy for the first five on 2026-10-20, and for the five interior designs later the same day (25
credits). On 2026-10-20 the user raised the project's Meshy budget to 1000 credits (claim the workspace with `--budget 1000`; it is the lifetime limit). Spent so far: 285 by the receipts in `meshy/creature_3d_progress.json` (2026-10-23).

| Date | Design | Job | Credits |
|---|---|---|---|
| 2026-10-20 | `hes_skull_ribs` | `hes_skull_ribs_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_founder_statue` | `hes_founder_statue_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_ashrunner_totem` | `hes_ashrunner_totem_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_creep_pod` | `hes_creep_pod_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_kreegan_pod_chest` | `hes_kreegan_pod_chest_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_corpse_colonist` | `hes_corpse_colonist_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_founder_intact` | `hes_founder_intact_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_salvage_heap` | `hes_salvage_heap_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_market_goods` | `hes_market_goods_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_loader_mech` | `hes_loader_mech_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-20 | `hes_resin_rib` | `hes_resin_rib_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_ash_hull_home` | `hes_ash_hull_home_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_ash_hull_home_b` | `hes_ash_hull_home_b_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_ash_trader_stall` | `hes_ash_trader_stall_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_ash_watchtower` | `hes_ash_watchtower_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_low_pod_home` | `hes_low_pod_home_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_low_shelter` | `hes_low_shelter_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_low_palisade` | `hes_low_palisade_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_low_gate` | `hes_low_gate_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_low_water_still` | `hes_low_water_still_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_salvage_crane` | `hes_salvage_crane_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_kreegan_outpost` | `hes_kreegan_outpost_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_alarm_pylon` | `hes_alarm_pylon_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_glass_tree` | `hes_glass_tree_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_wire_thicket` | `hes_wire_thicket_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_ash_hoodoo` | `hes_ash_hoodoo_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_fungus_tree` | `hes_fungus_tree_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_fungus_planter` | `hes_fungus_planter_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_fungus_clump` | `hes_fungus_clump_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_water_condenser` | `hes_water_condenser_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_hand_cart` | `hes_hand_cart_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_market_goods_colony` | `hes_market_goods_colony_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_fungus_tree_b` | `hes_fungus_tree_b_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-21 | `hes_fungus_tree_c` | `hes_fungus_tree_c_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-22 | `hes_lander_wreck` | `hes_lander_wreck_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-22 | `hes_lander_wing` | `hes_lander_wing_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-22 | `hes_lander_engine` | `hes_lander_engine_st_v1` (Smart Topology, untextured) | 5 |
| 2026-10-23 | `hes_collar_node` | `hes_collar_node_st_v1` (Smart Topology, untextured; the Scour) | 5 |
| 2026-10-23 | `hes_overseer_perch` | `hes_overseer_perch_st_v1` (Smart Topology, untextured; the Scour) | 5 |
| 2026-10-23 | `hes_derelict_hull_a` | `hes_derelict_hull_a_st_v1` (Smart Topology, untextured; the Scour) | 5 |
| 2026-10-23 | `hes_derelict_hull_b` | `hes_derelict_hull_b_st_v1` (Smart Topology, untextured; the Scour) | 5 |
