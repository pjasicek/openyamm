# Hesper item ground models

Task: FIX_PROMPTS "Hesper item ground models". Every Hesper item lying on the ground draws a borrowed MM ground model
today (`ground:` in `level_generation/projects/hesper_stage/items.yml`). This project gives each Hesper icon its own,
following [GROUND_ITEMS_3D_PLAN.md](../../../devdocs/GROUND_ITEMS_3D_PLAN.md) and the
[3D ground item playbook](../items_claude/GROUND_ITEM_3D_PLAYBOOK.md).

**Status (2026-10-24): done.** 129 models, one per Hesper icon with an item, installed through the stage: every
staged Hesper icon (92) draws its own model, none a native stand-in. Three items wait for their own icons (below).
Meshy: 73 Smart Topology jobs in five batches, 365 of the approved 405 credits, no retries. Codex: 135 sessions
(4 cloak masters, 131 paint sessions), at most four at once. Results, pipeline and deviations: [Results](#results).

## Classification

`python3 -I scripts/classify.py` writes [classification.json](classification.json) from
`design/kreegan_world/data/items.txt`: one design per icon (the engine binds ground models by icon, so the twelve
colony log tablets share one model and the six written readables another). **148 items, 132 designs** (146 and
130 at the estimate; Vreth's two glaives came later). The table is the final route of each.

Routes as estimated (final counts in [Results](#results)):

| Route | Designs | Meshy | What |
|---|---:|---:|---|
| meshy | 73 | 365 | Smart Topology untextured (5 credits), Codex-painted views baked into PBR (playbook). Melee weapons are hybrids: the Meshy job is the sculpted hilt or head only; blades, hafts and shafts are Blender |
| blender | 35 | 0 | built from components: bows, belts, rings, pendants, canisters, cylinders, crystals, coils (the jewellery and ranged sessions' 2026-10-18 routes) |
| flat | 8 | 0 | the plan's cheaper route: a slab, plate or card in Blender carrying the icon's face (tablets, slates, key card, seal, warrant, two woven implant plates) |
| variant | 11 | 0 | a tier II implant whose silhouette repeats its tier I: that mesh, repainted |
| blocked | 3 | (15) | Escaton's Ship Key 11473, Energy Core 11476, Re-entry Emitter 11477: no icon of their own yet (`needs_art`; their old icons `hes_escatons_thread`, `hes_harvester_core`, `hes_hull_plating` show the earlier designs) |

HD masters: every icon is a downscale of a 1254 px Codex original with true alpha (`design/kreegan_world/art/item_icons/raw`,
the selected run in its generation records), so the playbook's master step is already done for 69 of the 73 Meshy
designs. The four cloaks hang in their icons; a cloak on the ground is a folded heap, so they need one new Codex
master each.

`*` marks an item not staged yet (no map or shop holds it); its model is built and bound all the same.

| Icon | Family | Items | Route | Credits | Note |
|---|---|---|---|---:|---|
| `hes_pulse_pistol` | gun | Pulse Pistol 11000 | meshy | 5 |  |
| `hes_noble_sidearm` | gun | Noble Sidearm 11001* | meshy | 5 |  |
| `hes_ion_carbine` | gun | Ion Carbine 11002 | meshy | 5 |  |
| `hes_lancer_carbine` | gun | Lancer Carbine 11003 | meshy | 5 |  |
| `hes_arc_rifle` | gun | Arc Rifle 11004 | meshy | 5 |  |
| `hes_storm_rifle` | gun | Storm Rifle 11005* | meshy | 5 |  |
| `hes_scatter_lance` | gun | Scatter Lance 11006* | meshy | 5 |  |
| `hes_breaker_lance` | gun | Breaker Lance 11007* | meshy | 5 |  |
| `hes_disruptor_cannon` | gun | Disruptor Cannon 11008 | meshy | 5 |  |
| `hes_founders_repeater` | gun | The Founder's Repeater 11420 | meshy | 5 | colonial ceramic and gold, the one non-Kreegan gun |
| `hes_vibro_knife` | dagger | Vibro Knife 11020 | meshy | 5 | hybrid: Blender blade, Meshy grip |
| `hes_noble_fang` | dagger | Noble Fang 11021* | meshy | 5 | hybrid: Blender blade, Meshy grip |
| `hes_ssekhs_fang` | dagger | Ssekh's Fang 11425 | meshy | 5 | hybrid: Blender blade, Meshy grip |
| `hes_plasma_saber` | sword | Plasma Saber 11022* | meshy | 5 | hybrid: Blender energy blade, Meshy hilt |
| `hes_plasma_longblade` | sword | Plasma Longblade 11023 | meshy | 5 | hybrid: Blender energy blade, Meshy hilt |
| `hes_vhorrax_courtesy` | sword | Vhorrax's Courtesy 11421 | meshy | 5 | hybrid: Blender blade, Meshy hilt |
| `hes_vreths_first_cut` | sword | Vreth's First Cut 11438 | reuse |  | added 2026-10-24: hes_harrower_codex warglaives/ground |
| `hes_vreths_last_cut` | sword | Vreth's Last Cut 11439 | reuse |  | added 2026-10-24: hes_harrower_codex warglaives/ground |
| `hes_arc_maul` | mace | Arc Maul 11024 | meshy | 5 | hybrid: Blender haft, Meshy head |
| `hes_thunder_maul` | mace | Thunder Maul 11025* | meshy | 5 | hybrid: Blender haft, Meshy head |
| `hes_forgemasters_hammer` | mace | The Forgemaster's Hammer 11423 | meshy | 5 | hybrid: Blender haft, Meshy head |
| `hes_phase_axe` | axe | Phase Axe 11026 | meshy | 5 | hybrid: Blender haft, Meshy head |
| `hes_phase_cleaver` | axe | Phase Cleaver 11027 | meshy | 5 | hybrid: Blender haft, Meshy head |
| `hes_mraals_cleaver` | axe | Mraal's Cleaver 11426 | meshy | 5 | hybrid: Blender haft, Meshy head |
| `hes_ion_pike` | spear | Ion Pike 11028 | meshy | 5 | hybrid: Blender shaft, Meshy head |
| `hes_lattice_halberd` | spear | Lattice Halberd 11029* | meshy | 5 | hybrid: Blender shaft, Meshy head |
| `hes_coil_spear` | spear | The Coil Spear 11422 | meshy | 5 | hybrid: Blender shaft, Meshy head |
| `hes_overseers_rod` | staff | Overseer's Rod 11030* | meshy | 5 | hybrid: Blender shaft, Meshy head |
| `hes_lattice_staff` | staff | Lattice Staff 11031* | meshy | 5 | hybrid: Blender shaft, Meshy head |
| `hes_conductors_baton` | staff | The Conductor's Baton 11424 | meshy | 5 | hybrid: Blender shaft, Meshy head |
| `hes_spinebow` | bow | Spinebow 11032* | blender |  | swept limbs and a real string (ranged session route) |
| `hes_noble_recurve` | bow | Noble Recurve 11033* | blender |  | swept limbs and a real string |
| `hes_noblebone_longbow` | bow | Noblebone Longbow 11427 | blender |  | swept limbs and a real string |
| `hes_buckler_emitter` | emitter | Buckler Emitter 11130* | meshy | 5 |  |
| `hes_bastion_emitter` | emitter | Bastion Emitter 11131* | meshy | 5 |  |
| `hes_last_light_of_hesper` | emitter | Last Light of Hesper 11428* | meshy | 5 |  |
| `hes_weave_suit` | body armor | Weave Suit 11100 | meshy | 5 |  |
| `hes_refractor_weave` | body armor | Refractor Weave 11101 | meshy | 5 |  |
| `hes_carapace_mail` | body armor | Carapace Mail 11102 | meshy | 5 |  |
| `hes_black_carapace` | body armor | Black Carapace 11103 | meshy | 5 |  |
| `hes_grafted_plate` | body armor | Grafted Plate 11104 | meshy | 5 |  |
| `hes_bastion_plate` | body armor | Bastion Plate 11105 | meshy | 5 |  |
| `hes_bulwarks_shell` | body armor | Bulwark's Shell 11434 | meshy | 5 |  |
| `hes_rebreather_helm` | helm | Rebreather Helm 11106 | meshy | 5 |  |
| `hes_sensor_helm` | helm | Sensor Helm 11107 | meshy | 5 |  |
| `hes_survey_helm` | helm | Survey Helm 11142 | meshy | 5 |  |
| `hes_grip_gauntlets` | gauntlets | Grip Gauntlets 11108 | meshy | 5 | a pair |
| `hes_power_gauntlets` | gauntlets | Power Gauntlets 11109 | meshy | 5 | a pair |
| `hes_load_gauntlets` | gauntlets | Load Gauntlets 11140 | meshy | 5 | a pair |
| `hes_mag_boots` | boots | Mag Boots 11110 | meshy | 5 | a pair |
| `hes_grav_boots` | boots | Grav Boots 11111 | meshy | 5 | a pair |
| `hes_anchor_boots` | boots | Anchor Boots 11143 | meshy | 5 | a pair |
| `hes_ash_cloak` | cloak | Ash Cloak 11114 | meshy | 5 | a folded heap |
| `hes_refractor_mantle` | cloak | Refractor Mantle 11115 | meshy | 5 | a folded heap |
| `hes_insulator_cloak` | cloak | Insulator Cloak 11144 | meshy | 5 | a folded heap |
| `hes_vreths_mantle` | cloak | Vreth's Mantle 11435 | meshy | 5 | a folded heap |
| `hes_utility_belt` | belt | Utility Belt 11112 | blender |  | strap loop and buckle (jewellery session route) |
| `hes_capacitor_belt` | belt | Capacitor Belt 11113 | blender |  | strap loop with cells |
| `hes_reserve_belt` | belt | Reserve Belt 11141 | blender |  | strap loop with cells |
| `hes_conductor_ring` | ring | Conductor Ring 11120 | blender |  | twisted wire band |
| `hes_induction_ring` | ring | Induction Ring 11122 | blender |  |  |
| `hes_crown_band` | ring | Crown Band 11123 | blender |  |  |
| `hes_stormglass_ring` | ring | Stormglass Ring 11124 | blender |  | two set stones |
| `hes_xiths_sight` | ring | Xith's Sight 11436 | blender |  | large oval setting |
| `hes_lattice_pendant` | amulet | Lattice Pendant 11121 | blender |  | chain and faceted pendant |
| `hes_surveyors_pendant` | amulet | Surveyor's Pendant 11125 | blender |  | chain and diamond frame |
| `hes_nightglass_amulet` | amulet | Nightglass Amulet 11126 | blender |  | chain and teardrop stone |
| `hes_gatekeepers_gorget` | amulet | Gatekeeper's Gorget 11437 | meshy | 5 | a sculpted collar |
| `hes_jammer` | amulet | Jammer 11470 | blender |  | egg pendant on a loop |
| `hes_dermal_1` | implant | Dermal Mesh I 11200 | flat |  | woven square plate, clawed corners |
| `hes_dermal_2` | implant | Dermal Mesh II 11201* | variant of `hes_dermal_1` |  |  |
| `hes_capacitor_1` | implant | Capacitor Node I 11202* | blender |  | lathed lozenge, blue core |
| `hes_capacitor_2` | implant | Capacitor Node II 11203* | variant of `hes_capacitor_1` |  |  |
| `hes_ablative_1` | implant | Ablative Lattice I 11204* | meshy | 5 | cracked rounded plates |
| `hes_ablative_2` | implant | Ablative Lattice II 11205* | meshy | 5 | hexagonal plates: a different silhouette |
| `hes_vital_1` | implant | Vital Graft I 11206* | meshy | 5 | gem in a claw cage |
| `hes_vital_2` | implant | Vital Graft II 11207* | variant of `hes_vital_1` |  |  |
| `hes_optic_1` | implant | Targeting Optic I 11208* | meshy | 5 | lens in a curved housing |
| `hes_optic_2` | implant | Targeting Optic II 11209* | variant of `hes_optic_1` |  |  |
| `hes_reflex_1` | implant | Combat Reflex I 11210* | meshy | 5 | three-armed node |
| `hes_reflex_2` | implant | Combat Reflex II 11211* | variant of `hes_reflex_1` |  |  |
| `hes_damping_1` | implant | Damping Weave I 11212* | flat |  | woven square panel |
| `hes_damping_2` | implant | Damping Weave II 11213 | variant of `hes_damping_1` |  |  |
| `hes_regulator_1` | implant | Shield Regulator I 11214* | blender |  | ring disc, blue core |
| `hes_regulator_2` | implant | Shield Regulator II 11215 | blender |  | open ring disc |
| `hes_damper_1` | implant | Null Damper I 11216* | meshy | 5 | U clamp |
| `hes_damper_2` | implant | Null Damper II 11217* | variant of `hes_damper_1` |  |  |
| `hes_resonator_1` | implant | Lattice Resonator I 11220* | blender |  | triangular frame, purple crystal |
| `hes_resonator_2` | implant | Lattice Resonator II 11221 | variant of `hes_resonator_1` |  |  |
| `hes_resonator_3` | implant | Voice-tuned Resonator 11222* | variant of `hes_resonator_1` |  |  |
| `hes_coupler_1` | implant | Arc Coupler I 11223* | blender |  | zigzag conduit, swept |
| `hes_coupler_2` | implant | Arc Coupler II 11224 | variant of `hes_coupler_1` |  |  |
| `hes_coupler_3` | implant | Voice-tuned Coupler 11225* | variant of `hes_coupler_1` |  |  |
| `hes_trigger_graft` | implant | Trigger Graft 11226* | meshy | 5 | bent clawed arm |
| `hes_striking_lattice` | implant | Striking Lattice 11227 | flat |  | diamond plate with a green stone |
| `hes_reflex_booster` | implant | Reflex Booster 11430* | meshy | 5 | crescent with an orange stone |
| `hes_kreegan_gland` | implant | Kreegan Gland 11431 | meshy | 5 | organic pod |
| `hes_asters_lens` | implant | Aster's Lens 11432 | meshy | 5 | lens in a curled shell |
| `hes_voice_splinter` | implant | Voice Splinter 11433 | meshy | 5 | crystal in a claw |
| `hes_shield_cell` | supply | Shield Cell 11300 | blender |  | canister |
| `hes_shield_burst_cell` | supply | Shield Burst Cell 11301 | blender |  | triple canister |
| `hes_stim` | supply | Stim 11302 | blender |  | injector |
| `hes_emp_grenade` | supply | EMP Grenade 11303 | blender |  | sphere with studs |
| `hes_breach_charge` | supply | Breach Charge 11304 | blender |  | strapped box charge |
| `hes_hesper_ration` | supply | Hesper Ration 11305 | blender |  | wrapped block |
| `hes_kreegan_alloy` | supply | Kreegan Alloy 11350 | meshy | 5 | rough resin-metal chunk |
| `hes_ion_cell` | supply | Ion Cell 11351 | blender |  | canister |
| `hes_engram_shard` | engram | Engram Shard 11330 | blender |  | cut crystal (jewellery session crystals) |
| `hes_engram` | engram | Engram 11331 | meshy | 5 | crystal in a gold claw mount |
| `hes_engram_core` | engram | Engram Core 11332 | meshy | 5 | crystal in a cage |
| `hes_hive_navigation_crystal` | quest | Hive Navigation Crystal 11471* | meshy | 5 | crystal in claws |
| `hes_zod_brood_record` | quest | Zod Brood Record 11472* | meshy | 5 | organic pod |
| `hes_escatons_ship_key` | quest | Escaton's Ship Key 11473* | blocked |  | no icon of its own yet (visual_status needs_art) |
| `hes_ion_coil` | quest | Ion Coil 11474 | blender |  | coil torus |
| `hes_nav_matrix` | quest | Nav Matrix 11475 | blender |  | boxed crystal grid |
| `hes_energy_core` | quest | Energy Core 11476 | blocked |  | no icon of its own yet (visual_status needs_art) |
| `hes_reentry_emitter` | quest | Re-entry Emitter 11477 | blocked |  | no icon of its own yet (visual_status needs_art) |
| `hes_aster_shard_1` | quest | Aster Shard (Starport) 11478 | blender |  | a slab in its icon's outline; its Meshy block (batch 4) went unused |
| `hes_aster_shard_2` | quest | Aster Shard (Brood Pits) 11479 | blender |  | crystal shard |
| `hes_aster_shard_3` | quest | Aster Shard (Seedship) 11480 | blender |  | crescent crystal |
| `hes_aster_shard_4` | quest | Aster Shard (Archive) 11481 | blender |  | crystal shard |
| `hes_thrixs_token` | quest | Vhorrax's Token 11482 | meshy | 5 | carved bone token |
| `hes_ghulkats_collar_key` | quest | Ghulkat's Collar Key 11483 | meshy | 5 | organic two-pronged key |
| `hes_glassback_heart` | quest | Glassback Heart 11485 | meshy | 5 | organic heart |
| `hes_lander_log_core` | quest | Lander Log Core 11486 | blender |  | lathed cylinder |
| `hes_archive_armoury_key` | quest | Archive Armory Key 11487 | flat |  | key card |
| `hes_pilots_core` | quest | Pilot's Core 11489 | blender |  | lathed cylinder |
| `hes_court_seal` | quest | The Court Seal 11510 | flat |  | medallion disc |
| `hes_founders_head` | quest | The Founder's Head 11511 | meshy | 5 | a statue head |
| `hes_colony_log_tablet` | readable | 12 items (11360–11371) | flat |  | tablet slab: twelve tablets share it |
| `hes_data_slate` | readable | 6 items (11372–11377) | flat |  | slate slab: six readables share it |
| `hes_militia_warrant` | readable | Militia Warrant 11488* | flat |  | sealed envelope (letters batch construction) |

## Credit estimate

| Family | Meshy designs | Credits |
|---|---:|---:|
| Energy guns | 10 | 50 |
| Melee hilts and heads (daggers, swords, maces, axes, spears, staves; 3 each) | 18 | 90 |
| Emitters | 3 | 15 |
| Body armor | 7 | 35 |
| Helms, gauntlets, boots (3 each) | 9 | 45 |
| Cloaks | 4 | 20 |
| Gatekeeper's Gorget | 1 | 5 |
| Implants | 11 | 55 |
| Kreegan Alloy, Engram, Engram Core | 3 | 15 |
| Quest items (Hive Navigation Crystal, Zod Brood Record, Glassback Heart, Founder's Head, Ghulkat's Collar Key, Vhorrax's Token, Aster Shard I) | 7 | 35 |
| **Total** | **73** | **365** |
| Retry reserve (about one shape in ten; the earlier item sessions had none) | 8 | 40 |
| **Ceiling to approve** | | **405** |
| Later, once the three blocked items have icons | 3 | 15 |

Meshy precedent: the 2026-10-18 item sessions paid 5 credits per Smart Topology job with no paid retries
(organic 80, sculpture 70, maw 120, polearms 40). Jobs are submitted with `tools/creature_meshy.py`, which falls back to
the backup account.

Codex image sessions (no Meshy): 4 cloak masters; paint passes per the playbook, three sessions for each large design
(weapons, emitters, armor, worn pieces, belts: 57 designs) and one for each small one (one sheet of five views: 62
designs, variants included). About **235 sessions**, at most four at once. The flat designs count among the small ones: their
icons show them at an angle, so their faces are painted straight-on too.

## Results

| Route | Models | Triangles (min-max, mean) |
|---|---:|---|
| Meshy Smart Topology (helms, boots, gauntlets, emitters, armor, cloaks, guns, melee, implants, quest pieces) | 72 | 1,261-3,000, 2,493 |
| Blender components (bows, belts, rings, pendants, canisters, crystals, coils; Aster Shard I, see below) | 36 | 88-2,584, about 1,000 |
| Flat (tablets, slates, key card, seal, warrant, two implant plates) | 8 | 96-828, 358 |
| Tier II implants (Blender variants built as their own shapes; the four Meshy ones on their tier I mesh) | 11 | 194-2,000, about 1,000 |
| Reused (Vreth's two warglaives: hes_harrower_codex `warglaives/ground/`) | 2 | 1,262 |

233,544 triangles in all; 12 MB of cooked GLBs. Review: `review/textured/<icon>_{high,low}.png` per model,
`review/textured_sheet_*.png`, and the desktop captures `review/ingame/` (hes_pickups_test, every staged model in three
groups: `tour_final_{1,2,3}.yml`, `layout_final.json`, `final_*_b.png`). Per model: `ledger.json` (route, export hash,
triangles, registration), `codex_tex/<icon>/bake.json`, `NOTE.md` where it deviates.

### Pipeline (scripts/)

1. `classify.py`: classification.json (one design per icon; the master is the icon's own 1254 px Codex original).
2. `build_hesper.py <icon|all>`: the Blender and flat designs from components, in world units, each face carrying
   a surface class (ceramic, gold, resin, glow, crystal, ...). `meshy_jobs.py batch <n> <icon...>`: Meshy job files
   (submitted by the integrator). `prep_meshy.py <icon>`: a Meshy download welded, rested (`meshy_rest.json`: rotation,
   length, triangle budget, crumb threshold; `assembly` adds the Blender shaft or energy blade of a head or hilt crop),
   class `auto`.
3. `hes_texture.py prep`: unwrap and five tinted orthographic guides plus `CODEX_BRIEF.md`; `run_codex.py`: the paint
   sessions, four at once; `hes_texture.py bake`: the paintings projected (the most head-on view wins,
   `FACING_POWER`), unseen texels from the nearest painted texel on the surface, metallic, roughness and emission
   per class (`auto` resolved per texel from the painted colour), at 1024 and written at 512 (colour, emission) and 256
   (normal, metallic-roughness). An open Meshy shell exports double-sided. `bake_ready.py` bakes whatever is painted.
4. `review.py`, `sheet.py`: clay and textured renders. `install.py`: winding check, `ledger.json` and the stage's
   `level_generation/projects/hesper_stage/item_models.yml` (with `ground_lengths.json` overrides).
5. `stage.py` copies each export to `worlds/hesper/models/item_<icon>.glb` with a cook sidecar (`max_size: 512`,
   `normal_strength: 1`), cooks it with the world's models, binds a staged icon to it in place of its stand-in and runs
   `tools/item_model_shapes.py --assets <stage>` for the bounds.

### Deviations and notes

- **Refused by the image tool** (violence filter): Breach Charge (three views; right = left mirrored, front and back
  from the nearest paint), Pilot's Core (sides = top turned 90 degrees: a lathed part), Lancer Carbine and Storm Rifle
  (all views: the approved icon painting projected from above, mirrored, the gun lying on its icon side). Each has a
  `NOTE.md`.
- **Repainted once:** Coupler III (flat colours), the Noble Recurve and Noblebone Longbow (thicker limbs and bone tips
  after the first review).
- **Turned over:** the Zod Brood Record rested egg side down; its icon painting is projected from below and the bake
  turns it over (`meshy_rest.json` `flip`, `guide_bottom.png`).
- **Aster Shard I:** Meshy made a block with the crystal on its narrow sides; it is a Blender slab in the icon's
  outline with the icon painting from above (5 credits spent, the shape unused).
- **Vreth's First Cut and Last Cut** (11438, 11439) were added after the estimate; the Harrower session's own ground
  glaives are used unchanged (no Meshy, no Codex).
- **Sizes after the desktop check** (`ground_lengths.json`): body armor 80 (from 105-120), emitters 48-58 (from
  62-72).
- **Classes by colour:** Meshy models carry no part classes; gold is a saturated yellow-orange hue, glow a bright
  saturated blue or orange, resin the darkest. Pale bone and resin read lighter than their icons on the Power
  Gauntlets and the Bastion Emitter.
- **Blocked:** Escaton's Ship Key 11473, Energy Core 11476 and Re-entry Emitter 11477 have no icon of their own (in
  the item expansion's art list as a follow-up); their 15 credits are held.
- `projlib.fix_winding` measures a piece's volume over its triangles only, so a correct piece of quads and triangles
  comes out flipped: the bake triangulates first.
- The seven staged items that showed engine icons (Engram, Engram Core, Aster Shard I, Nav Matrix, Shield Cell, Shield
  Burst Cell, EMP Grenade) now show their own.
