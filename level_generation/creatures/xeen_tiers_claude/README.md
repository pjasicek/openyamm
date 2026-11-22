# Xeen colour tiers on reused models (lane S)

Xeen's reused monster families get their own colour tiers on the installed 3D models they already used as stand-ins.
Nothing new is modelled: a tier is one more `KHR_materials_variants` skin whose materials copy an existing tier's
materials with recoloured region ramps (the engine contract in
[CLAUDE_CREATURE_TEXTURES.md](../CLAUDE_CREATURE_TEXTURES.md), "Region mask and ramps"). Mesh, clips, LODs, images,
mask and attachments stay as they are. A family can only change the colours its source model's region mask covers.

## Route

1. **Learn the regions.** `preview_tiers.py <source glb> <out.png> --mask` rasterises the LOD0 body from four sides with
   every skin through its ramps, plus a mask view (region 0 red, 1 green, 2 blue, 3 yellow).
2. **Look at the sprites.** `xeen_monster_images.json` maps every Xeen monster row to its sprite image (Clouds:
   `reference/mm4_5_world_of_xeen/unpacked/sprites/xeen/NNN.mon/frame_0000.png`, Darkside: `sprites/dark/`). Pick a
   tier colour from the sprite (roughly 1.3x the sprite's mean, since sprites carry baked shading). Xeen draws one
   sprite with no palette swaps, so rows that share a sprite get designed variations.
3. **Spec.** `spec_<family>.json`: `{"_model": note, "variants": {"<skin>": {"from": "<source skin>", "_follows":
   note, "regions": {"<i>": {"mid": "#rrggbb"}}}}}`. `mid` makes the region's average shown colour that sRGB colour
   (every ramp stop is scaled by its luminance relative to the mean luminance the region's texels show through the
   source ramp), so the shading survives. `contrast` (power on that ratio, below 1 flattens) and `lift` (blends the
   ratio towards 1, for a source tier whose dark stops are black) adjust it. The older `hue`/`sat`/`val` and `rgb`
   rules remain (the goblins use `hue`).
4. **Build and preview.** `xeen_tiers.py assets_source/worlds/<w>/models/<stem>.glb export/xeen_<stem>.glb
   spec_<family>.json`, then `preview_tiers.py export/xeen_<stem>.glb <png> <skins...>`.
5. **Install.** `check_winding.py` (0 inverted), `python3 tools/install_model.py export/xeen_<stem>.glb --world xeen`.
6. **Bind.** `rebind.py worlds/xeen/models/xeen_<stem>.glb "Xeen X A=<skin>" ... --note "<line>"` (keeps every other
   field of the binding). Bosses take their `look` tier's skin (exception: the Diamond and Onyx golems, below).
7. **Check.** `build-xeen/game/openyamm --world xeen --headless-validate-actor-models` (0 refused), then in game:
   `make_tour.py <tour.yml> <capture dir> --close-dialog <name>=<id>,<id> ...` and
   `tools/run_game.sh --isolated <name> --binary build-xeen/game/openyamm --world xeen --map xeen_xd21.blv
   --position -2560 320 0 --yaw-radians 1.5708 --pitch-degrees -8 --set debug.actor_models=true
   --set debug.immortal=true --set debug.menu_input_tour_path=<tour> --warmup 3 --seconds 110`.
   XD-21 now opens with an entry text: `--close-dialog` presses Escape first, otherwise actors stay paused. Archers,
   casters and wizards move off the spawn point; spawn them `friendly` (a hand-written tour) to see them.

**Body regions (decision D-10, 2026-11-20).** Where the source model's mask misses the body, `add_region.py <in.glb>
<out.glb> body_<family>.json` adds one more mask channel to the copy (classified per LOD atlas from the base colour by
HSV boxes, existing channels excluded; the base colour's filled gutters pad it) and a ramp for it on every material:
the listed Xeen skins get their colour (`mid`, optional `shadow`/`highlight` hues for the dark and light stops,
`contrast`, `lift`), every other skin a ramp fitted to the base colour, so it keeps its look (fit error 0.5–3.5 of 255
mean). Rebuild order: `xeen_tiers.py` (source → tiers) → `add_region.py` once per new channel → for the Lava Golem
`lava_cracks.py` (crevice masks per LOD atlas) and `claude_shared/emission.py` per LOD material → winding → install.
Rule for later families (D-10): a cloth-only tier only when its regions cover about a quarter of the front silhouette,
the tiers differ clearly at combat distance and the unchanged colour matches the sprite; golems, elementals, slimes and
skeletons always tier the body.

**Attachments.** A binding's attachment without its own `skin` follows the body's skin name and falls back to variant
0 when it lacks it. Every attachment of these families is either one material for all tiers (orc and ratman swords,
bow, arrow, knight sword, sorcerer staff, zombie forearm) or carries a ramp whose mask is empty on the item (goblin
sword, dwarf axe, ogre sword, cleric staff, skeleton sword), so variant 0 looks the same and no attachment needed
new skins.

## Families (2026-11-20)

Native = the colour of that row's own Xeen sprite; design = a variation where Xeen has no sprite or shares one.
All rows were seen in game (XD-21, `build-xeen`) on 2026-11-20 unless noted; the D-10 body regions (golems, ogres,
werewolves, orcs) were seen there the same day (`s2-d10` run).

### Orcs and orc warband: `xeen_m246.glb` (from MM7 goblin `mm7_m246`) and `xeen_gob2.glb`

Regions: 0 vest, 1 leggings and sleeves, 2 skin (D-10, `body_orcs.json`: the MM7 goblin's green skin to the Xeen
orc's tan, Xeen 6's skin x1.3, one shade darker per tier: a #a26a3c, b #9a5e38, c #8e5a34, d #84522e, e #7a4a2a).
Gold armour and boots are fixed.

| Skin | Rows | Follows | Colours (vest / legs) |
| --- | --- | --- | --- |
| xorc_a | Orc A | native, Xeen 6 (teal tunic) | #4a9ea2 / #33767c |
| xorc_b | Orc Archer B | design (no sprite) | tan #9a6a3e / olive #4c5a2a |
| xorc_c | Orc Guard C, Drum-Master | native, Darkside 40 (brown vest, green trousers) | #7a5432 / #3a5e22 |
| xorc_d | Orc Elite (warband A) | native, Darkside 40 (white fur trim, green) | #b0aca2 / #1a5a0e |
| xorc_e | Orc Captain (warband C), Shaalth | design (the sprite's red loincloth) | #a8180e / #2c2a2a |
| xgob_e | Orc Shaman (warband B), on `xeen_gob2.glb` | native skin of Darkside 43 | skin #8a5a34 |

The Orc Shaman stays on the MM6 goblin shaman for its cast clip; `xgob_e` was added to `spec_goblins.json` and
`xeen_gob2.glb` rebuilt (the goblin skins are byte-identical materials).

### Mad dwarves: `xeen_dwa1.glb` (from `mm6_dwa1`)

Regions: 0 tunic, 1 trousers.

| Skin | Rows | Follows | Colours (tunic / trousers) |
| --- | --- | --- | --- |
| xdwa_a | Mad Dwarf A | native, Xeen 7 | teal #2e7078 / blue #0c62a8 |
| xdwa_b | Clan Sergeant B | design (same sprite) | rust #8a4a26 / teal #2a6a70 |
| xdwa_c | Clan Guard C, Clan King | design from Xeen 7/75 (the green cape) | green #1e7a14 / blue #0a4a8a |

### Ogres: `xeen_ogr.glb` (from `mm6_ogr`)

Region 0 the horns and wrist spikes (`lift` 0.55: the MM6 ramp's dark stops are black); D-10 added 1 the light
armour plates and 2 the orange cloth (loincloth, leg wraps, chest straps) (`body_ogres_1.json`, `body_ogres_2.json`).
Skin kept.

| Skin | Rows | Follows | Horns / armour / cloth |
| --- | --- | --- | --- |
| xogr_a | Ogre A | design (Xeen 32 has no horns) | ivory #d0c4a0 / silver #b4b6bc / rust #a85a28 |
| xogr_b | Ogre Brute B | design | dark iron #5a5a5e / dark iron #55575c / red-brown #6a2a1e |
| xogr_c | Ogre Chief C, Ogre Chieftain, Graalg | native, Darkside 42 (gold horns, blue armour, gold) | #d4b818 / blue #2848c8 / gold #d0a420 |

### Outlaws: `xeen_thf.glb` (from `mm6_thf`)

Region 0: the hooded cloak.

| Skin | Rows | Follows | Cloak |
| --- | --- | --- | --- |
| xthf_a | Rogue A | native colour, Darkside 54 (blue suit) | #2a3a9a |
| xthf_b | Thief B | design from Darkside 54 (black vest) | charcoal #3a3a3e |
| xthf_c | Master Thief C, Robber Boss | native, Xeen 80 Robber / Robber Boss (purple cloak) | #5a1890 |
| xthf_d | The Master Thief (boss, session 4) | design: its own boss skin, a dark oxblood cloak | #561216 |

### Evil rangers: `xeen_arc1.glb` (from `mm6_arc1`)

Region 0: sleeves and shorts.

| Skin | Rows | Follows | Colour |
| --- | --- | --- | --- |
| xarc_a | Evil Archer A | native, Xeen 43 (brown leather) | #986138 |
| xarc_b | Evil Ranger B | native, Xeen 35 (purple cloak, magenta trousers) | #8a149a |
| xarc_c | Elite Ranger C | design (the ranger's teal tunic) | #2a6a72 |

### Darkside sprites: `xeen_sprite.glb` (own model, `spec_sprites.json`)

Body regions 0 skin, 1 hair, 2 dress; the wing material's region 0 is the membrane, set with `by_material` (added to
`xeen_tiers.py` in session 3). `sprite_d` Gorgon Sprite (Dark Sprite A, Darkside image 53: bronze, black hair, green,
violet wings); `sprite_e` Elder Gorgon Sprite (Dark Sprite B: copper, black, dark wine, ember wings); Dark Sprite C
uses `sprite_c`. Seen in XD-21 (session 3).

### Burlock knights: `xeen_kni.glb` (from `mm6_kni`)

Regions: 0 trims (collar, belt, knee and arm bands), 1 the plate armour (including the helmet plume).

| Skin | Rows | Follows | Trims / armour |
| --- | --- | --- | --- |
| xkni_a | Jouster A | native, Xeen 29 (silver plate, red) | #b81414 / #8a8a90 |
| xkni_b | Yang Knight B | native, Xeen 38 (teal, white plates) | #e4e4e4 / #2a7078 |
| xkni_c | Knight Captain C, Captain Yang | design (darker Yang teal, gold) | #d8a828 / #1a4a52 |
| xkni_d | King's Guard D | native, Xeen 84 (violet, gold) | #e0c020 / #6a1a9a |
| xkni_e | Renegade Jouster (Xeen Renegade A, D-11.2) | design: tarnished, dull brick trims | #6a2a1a / #57544f |
| xkni_f | Renegade Knight (Renegade B) | design: rust-brown trims, blackened plate | #7a4a20 / #3a3a3c |
| xkni_g | Renegade Captain (Renegade C) | design: tarnished gold, near-black plate | #8a6a20 / #262428 |

The renegade skins were added in session 3 (2026-11-20) and seen in XD-21 beside Knight A-C: they read apart from the
King's knights and from the Dark Knights (mm6_kni `kni_a-c`, blue-violet trims).

### Cultists and heretics: `xeen_cle.glb` (from `mm6_cle`)

Regions: 0 robe, 1 leggings and hem/collar trim, 2 cloak. Skin stays (the Mok heretic is blue-skinned).

| Skin | Rows | Follows | Robe / trim / cloak |
| --- | --- | --- | --- |
| xcle_a | Cleric of Yak (Cultist A) | native, Xeen 17 | blue #2a40e0 / #1c2a80 / silver #b4b4ba |
| xcle_b | Yak Priest (Cultist B) | native, Xeen 25 | tan #c69068 / #8a6a3a / silver #b4b4ba |
| xcle_c | Yak Elder (Cultist C), Yak Master | design (priests' gold as cloak) | indigo #2a1e70 / #3a3060 / gold #b08a2a |
| xcle_d | Mok Heretic (Heretic A) | native, Darkside 8 | orange-brown #a8662e / #5a1878 / purple #3a1050 |
| xcle_e | Heretic Priest (Heretic B) | design | rust #902a18 / #aa1a1a / black #26242a |
| xcle_f | Heretic Lord (Heretic C) | design (Mok's red crown) | black #2a2630 / #2a2226 / crimson #b01818 |

### Skeletons: `xeen_ske.glb` (from `mm6_ske`)

Region 0: all bone.

| Skin | Rows | Follows | Bone |
| --- | --- | --- | --- |
| xske_a | Skeleton A | native, Xeen 8 (teal bones) | #4a9aa0 |
| xske_b | Spirit Bones B | design (same sprite): spectral | #b0d4d0 |
| xske_c | Skeleton Lord C | design (the cape colour of Xeen 8) | slate violet #6a5a90 |

### Rotting dead: `xeen_m438.glb` (from MM7 zombie `mm7_m438`)

Region 0: trousers and headband; skin and wounds fixed.

| Skin | Rows | Follows | Rags |
| --- | --- | --- | --- |
| xzom_a | Zombie A | native, Xeen 9 (purple trousers) | #7a28a8 |
| xzom_b | Ghoul B | design after Xeen 27 (green ghoul) | moss #3a5a16 |
| xzom_c | Grave Ghoul C | design | grave brown #5e5040 |

### Bats and night bats: `xeen_bat.glb` (from `mm6_bat`)

Regions: 0 wing membrane, 1 body fur and wing bones (`contrast` 0.6 on the body: its highlights clip otherwise).

| Skin | Rows | Follows | Wings / body |
| --- | --- | --- | --- |
| xbat_a | Giant Bat (Bat A) | native, Xeen 1 (charcoal) | #3a3a3c / #3e3a3c |
| xbat_b | Cave Bat (Bat B) | design | brown #6a4428 / #5a4232 |
| xbat_c | Mine Bat (Bat C) | design | rust-ochre #9a5a14 / dust #5a5450 |
| xbat_d | Bat Queen (Night Bat A) | native, Xeen 16 (brown cape, blue dress) | #5a4028 / #2232a8 |
| xbat_e | Vampire Bat (Night Bat B) | design | purple #4a1460 / black #262028 |
| xbat_f | Beholder Bat (Night Bat C) | native, Darkside 18 (red wings) | #c42020 / #6a1010 |

### Spiders and arachnoids: `xeen_spi1.glb` (from `mm6_spi1`)

Region 0: the whole body; fangs and eyes fixed.

| Skin | Rows | Follows | Colour |
| --- | --- | --- | --- |
| xspi_a | Giant Spider (Spider A) | native, Xeen 4 (dark teal) | #2a6a74 |
| xspi_b | Cave Spider (Spider B) | design | pale grey-brown #8c8270 |
| xspi_c | Huge Spider (Spider C) | design | black-violet #3c2c56 |
| xspi_d | Arachnoid A | native, Darkside 52 | brown #8a6a4c |
| xspi_e | Arachnoid Hunter B | design | rust #8c3a1e |
| xspi_f | Arachnoid Queen C | design (the sprite's purple venom) | #6e2a90 |

### Oozes: `xeen_ooz.glb` (from `mm6_ooz`)

| Skin | Rows | Follows | Colour |
| --- | --- | --- | --- |
| xooz_a | Slime A | native, Xeen 0 | lime #5ad830 |
| xooz_b | Breeder Slime B, Wobbles | native, Xeen 73 | green #1ea814 |
| xooz_c | Sewer Slug C | native, Darkside 48 | blue #1a86d8 |

### Rats: `xeen_rat.glb` (from `mm6_rat`)

Regions: 0 bare skin (face, ears, paws, tail), 1 fur, 2 eyes.

| Skin | Rows | Follows | Skin / fur / eyes |
| --- | --- | --- | --- |
| xrat_a | Sewer Rat A | native, Darkside 47 (black-green, red eyes) | #7a8a30 / #16301a / #e81010 |
| xrat_b | Rooka B | design (same sprite, greener) | #8a9a34 / #2e6a1e / #e81010 |
| xrat_c | Sewer Stalker C | native colours of Darkside 4 (green scales, brown belly) | #a0704a / #3e7a16 / #e8d020 |
| xrat_d | Dire Rat D (11393, D-26) | design: rust-brown, apart from the green tiers | #b08a80 / #5a2e18 / #ff6010 |

`xrat_d` was added in session 3, installed and bound to Xeen Rat D at scale 292.5 against Rat A: the size scales by
the standing sprite's frame scale, and Rat D shares Rat C's `rCtsta`, so this is 1.25x the Giant Rat (rescale if the
row gets its own sprite). Seen in XD-21 beside Rat C.

### Sewer stalkers: `xeen_ratman.glb` (from MM8 `mm8_ratman`)

Region 0: trousers; fur fixed.

| Skin | Rows | Follows | Trousers |
| --- | --- | --- | --- |
| xrtm_a | Rooka A | native colour, Darkside 47 | sewer green #24502a |
| xrtm_b | Sewer Stalker B | native colour, Darkside 4 (brown belly) | #8a5d3e |
| xrtm_c | Stalker Matriarch C, Rooka the Rat Queen | design | royal purple #4e2060 |

### Serpents and cobras: `xeen_cob.glb` (from `mm6_cob`)

Regions: 0 body scales, 1 inner hood and belly, 2 hood markings. The model is a hooded cobra for every row.

| Skin | Rows | Follows | Body / hood / markings |
| --- | --- | --- | --- |
| xcob_a | Giant Snake (Snake A) | native, Xeen 3 | green #2a8a18 / #c8c418 / #e0d830 |
| xcob_b | Viper (Snake B) | design | olive #7a6a2e / #b49464 / #3e2e1e |
| xcob_c | Constrictor (Snake C) | design | moss #3e4c20 / #a88a56 / #dcc894 |
| xcob_d | Guardian Asp (Cobra A) | design (same sprite as Giant Snake) | emerald #0e7040 / #c8b420 / #d8a818 |
| xcob_e | Killer Cobra (Cobra B) | native, Darkside 46 | copper #a8683c / #c8bcac / #ece0c4 |
| xcob_f | King Cobra (Cobra C) | design | black #2a2a2c / gold #d0a828 / #ecc838 |

### Werewolves: `xeen_wwf.glb` (from `mm6_wwf`)

Regions: 0 shorts, 1 pendant gem, 2 the fur (D-10, `body_werewolves.json`; `lift` 0.15–0.2 on the near-black source).

| Skin | Rows | Follows | Rags / gem / fur |
| --- | --- | --- | --- |
| xwwf_a | Wolfman A | native, Xeen 39 (torn white rags, brown fur) | #c8c6be / amber #e0a020 / brown #72492a |
| xwwf_b | Werewolf B | design | brown #6e4a2a / green #20c040 / grey-brown #6a625a |
| xwwf_c | Greater Werewolf C | design | maroon #5e1414 / red #e01818 / silver #a4a6ae |

### Material and elemental golems: `xeen_m254.glb` (from MM7 golem `mm7_m254`)

Regions 0 and 1 are the two interleaved stripe colours of the loincloth and headdress; D-10 added 2, the whole sandy
body (`body_golems.json`; colours about 1.3x the sprites' mid tones, dark and light stops given their own hue). The
Lava Golem's body crevices glow (`lava_cracks.py` masks, `emission.py` colour 1.0,0.12,0.02 strength 2.4, pulse
0.25/3 s, on each LOD's xgol_i material).

| Skin | Rows | Follows | Stripes / body (shadow, mid, highlight) |
| --- | --- | --- | --- |
| xgol_a | Wood Golem (Golem A) | native colour, Xeen 44 | #5e3a1c / #a8743e; wood #4a2a14, #7a5030, #a8743e |
| xgol_b | Stone Golem (Golem B) | native colour, Xeen 55 | #6a6a6a / #d0d0d0; stone #6a6a70, #a4a4a2, #e0e0dc (contrast 1.3) |
| xgol_c | Iron Golem (Golem C) | native colour, Xeen 58 | #38383e / rust #c06010; iron #2c2c30, #4e4c4c, rust #b0682a |
| xgol_d | Diamond Golem (boss) | native colour, Xeen 67 | #e4ecf4 / ice #7ad4e4; #5a9aac, pale #b8dce4, #f0fcff (contrast 1.6) |
| xgol_e | Onyx Golem (boss) | native colour, Darkside 24 | #1e1e20 / #6a6a6e; #1a1a1e, #3a3a3e, #7a7a84 |
| xgol_f | Sand Golem (Elemental A) | native colour, Xeen 37 | #a8704a / #d8a888; #8a5a30, #c08458, #e0b48c |
| xgol_g | Water Golem (Elemental B) | native colour, Xeen 28 | #1e30d0 / #6c98fc; #0a148c, #2a44e8, #80a8ff |
| xgol_h | Cloud Golem (Elemental C) | native colour, Xeen 60 | #d8d8d8 / #a8b4c4; #a0a8b8, #e0e2e6, #f8f8fc |
| xgol_i | Lava Golem (Elemental D) | native colour, Xeen 65 | #1e1414 / lava #d81a0a; #1a0c0a, #3a1c16, #8a2410 + glowing crevices |
| xgol_j | Sky Golem (Elemental E) | design (its Darkside 24 is the Onyx face) | #4c94e0 / #eef4ff; #3a6ab8, #6aa4e8, #eef4ff |

The Diamond and Onyx golems are bosses with `look: C`, but their names are their materials and they have their own
sprites, so they got their own skins instead of the Iron Golem's.

### Wizards: `xeen_sor1.glb` (from `mm6_sor1`)

Region 0: the robe; gold trims, skin and staff fixed.

| Skin | Rows | Follows | Robe |
| --- | --- | --- | --- |
| xsor_a | Wizard A | native, Xeen 42 (violet) | #6a1aa0 |
| xsor_b | Sorcerer B, Valio, Darzog's Clone | native, Xeen 50 (black with red) | #2e2426 (contrast 0.9) |
| xsor_c | Master Wizard C, Baron Darzog, Xenoc | native, Darkside 64 (copper-orange) | #b8661c |

Valio's own Darkside sprite (65) is teal and Xenoc's (64) copper; they follow their `look` tiers as the lane rule says.

Session 5 (D-39): `xsor_d` Cult Acolyte (row 11197; undyed grey-brown wool `#6a6056`) and `xsor_e` Basenji Cult Leader
(row 11198; near-black blue-charcoal `#23262e`, and wolf-grey trim `#8e9094` through a new channel 1, the gold trims,
added by `add_region.py` with `body_wizards.json`; every other skin keeps its gold through the fitted ramp, fit mean
4.0 of 255). Rebuild: `xeen_tiers.py mm6_sor1.glb export/xeen_sor1_tiers.glb spec_wizards.json`, then
`add_region.py export/xeen_sor1_tiers.glb export/xeen_sor1.glb body_wizards.json`. Bound when A2's rows exist.

### Floating mages: `xeen_m426.glb` (from MM7 `mm7_m426`, session 5)

`spec_floating_mages.json`, region 0 the dress and bodice (cape, hair, gold fixed). The stand-in's look (a hovering
sorceress) is not Xeen's floating bearded head (Darkside 35); a model of its own would be new work.

| Skin | Rows | Dress |
| --- | --- | --- |
| xfm_a | Mystic Mage A | Darkside 35's blue-teal #2c6a8a |
| xfm_b | Magic Mage B | flame orange #c8641c (design) |
| xfm_c | Mega Mage C | deep crimson #7a1420 (design) |
| xfm_d | Floating Adept (D-39, 11203) | pale sea-green #5a9a7a (design) |
| xfm_e | Floating Magus (D-39, 11204) | royal violet #5a2a8a (design) |

A-C rebound and seen in XD-21 (`ingame_s5/s5-floating.png`); D and E wait for A2's rows.

### Gargoyles (Cloudside and Magic Mountain): `xeen_gar.glb` (from `mm6_gar`), 2026-11-20 (session 2)

Region 0: the whole body and wings (eyes and claws fixed), so these are body tiers. Seen in game (XD-21, `s2-gar`).

| Skin | Rows | Follows | Body |
| --- | --- | --- | --- |
| xgar_a | Gargoyle A | native, Xeen 47 (violet) | #6a1aa8 |
| xgar_b | Gargoyle Lord B | design | indigo #3e1a8a |
| xgar_c | Obsidian Gargoyle C | design | black-violet #2a1c36 (contrast 1.3) |
| xgar_d | Mountain Gargoyle A | native, Darkside 21 (magenta-purple) | #781a78 |
| xgar_e | Gargoyle Sentinel B | design | slate plum #5a3a5e |
| xgar_f | Gargoyle Overlord C | design | crimson purple #7a1438 |

### Snow Beast: `xeen_bf.glb` (from MM9 bigfoot `mm9_bigfoot`, session 5)

`spec_snow_beast.json`: `xbf_a` from the Yeti tier `bf_c`, fur `#b4b4b2`, chest `#76777a`, back `#a2a2a0` (Xeen image
36's neutral grey-white, sprite fur mean 119 grey), blue hands and feet kept; the head keeps the Yeti's own image (open
snarl, blue bands: it has no ramps). Bound to `Xeen Wolf C` with MM9 Bigfoot C's animation and clips (`bind.py`,
`work_snow/bind_snow_beast.yml`), scale 95 (2.15 m: the crouched 140 px sprite at 1.34 units/px is 188). A copy, not a
cross-world binding, because the Xeen world depends on the engine only. Seen in XD-21 beside two Dark Wolves
(`ingame_s5/s5-snow.png`). The descriptor still has the wolf's collision height 160 (A2).

### Earlier: goblins and gremlins

`xeen_gob2.glb` (`spec_goblins.json`): xgob_a teal goblin (Xeen 5), xgob_b purple gremlin (Darkside 26), xgob_c deep
violet, xgob_d magenta, and since 2026-11-20 xgob_e for the Orc Shaman.

## Files

- `xeen_tiers.py`, `preview_tiers.py`, `rebind.py`, `bind.py`, `make_tour.py`: the tools; `flame_ramps.py` recolours
  unmasked materials (fire elemental flames) per skin; `new_mask.py` gives a model without skins an empty mask
  (session 12, the treant); `add_region.py` and
  `lava_cracks.py` for D-10's body regions; `body_*.json` their specs.
- `spec_*.json`: one per family (git-ignored by the creatures JSON rule, like every creature project's data).
- `export/xeen_*.glb`: the installed exports (sources in `assets_source/worlds/xeen/models/`).
- `check_tour_*.yml`: earlier hand-written check tours.

## Session 5 additions (D-42)

- `xeen_cle.glb`: `xcle_g` for the DD-05 Cult Leader (11223): white vestments `#d6d0c2`, crimson leggings and trim
  `#9a1418` (the heretics' red), gold cloak `#c09a30` (spec_cultists.json); distinct from the Heretic Lord's `xcle_f`
  (black robe, crimson cloak). The heretics' sign is not painted on (no decal; colours only).
- `xeen_witch.glb`: `witch_d` for the Darkside Head Witch (11173): bone-white robe `#bdb6a2` (`spec_witch_head.json`,
  built on the installed witch itself, `work_snow/xeen_witch_installed.glb`); distinct from witch_a-c and the coven.
- Both installed; the rows bind when A2's descriptors exist. A Royal Vampire (11295) tier waits until the vampires get
  their Xeen copy (they still bind the stand-in).
- Vampires: `xeen_m422.glb` (copy of MM7 `mm7_m422`, `spec_vampires.json`; regions 0 coat, 1 cape, 2 hair) adds
  `xvam_d` Royal Vampire (11295, `Xeen Vampire D`): royal purple coat `#4a1a6a`, black cape, silver hair. Vampires A-C
  rebound to the copy with their old skins `m422_a/b/c`.
- A2's D-42 draft bound (`work_snow/bind_d42.yml`): Coven Head Witch (11173) = Xeen Head Witch's binding with `witch_d`,
  Cult Leader (11223) `xcle_g`, Vampire D `xvam_d`, the captives and clerics as drafted. Seen in XD-21
  (`ingame_s5/s5-d42.png`: Royal Vampire, Cult Leader, Cult Acolyte). 294 descriptors on 71 models, 0 refused.

### Dark knights in black and red (D-61, session 9): `xeen_kni.glb`

Built on the installed Xeen copy (`spec_d61_darkknights.json`), so every other knight skin is unchanged. Before this,
the dark knights used MM6's `mm6_kni` `kni_a-c`, which have blue-violet trims.

| Skin | Rows | Trims / plate |
| --- | --- | --- |
| xkni_i | Slayer Knight (Xeen Dark Knight A, 11150), the Voweless Knight 11925 (D-61: on the Slayer look) | #8a1a1a / #48474d gunmetal |
| xkni_j | Death Knight (Dark Knight B, 11151) | #1a181c black / #5a1214 dark red |
| xkni_k | Doom Knight (Dark Knight C, 11152) | #d02424 crimson / #161418 near-black |

Rebound, giving 334 descriptors on 83 models, 0 refused. All three, the Voweless Knight, Sheltem (`xsor_h`) and
Corak were seen in XD-21 (`ingame_s9/s9-sheet.jpg`).

## Session 11 (D-57 Q27)

- `xeen_cle.glb`: `xcle_h` for FD-04's druid Alister (11923, `Xeen Alister`): moss-green robe `#5a7a34`, brown leggings
  and trim `#4a3a28`, bark-brown cloak `#5a4028` (spec_cultists.json; preview `work_s11/cle_h.png`). Bound as Cultist
  A's binding (staff, clips, scale 110). Seen in FD-04's west alcove at (-1040, -768) (`work_s11/shots/sheet.jpg`).
- Scan of every Xeen monster row and placed actor (2026-11-21): all 335 Xeen descriptors are bound; the map_stats spawn
  families all resolve A/B/C; the engine rows placed on Xeen maps (MM7 peasants, Ghost C, Swordsman B, Treants, MM6
  Druidess, Novice Monk, Journeyman Mage) resolve through the MM6/MM7 bindings Xeen depends on.

## Session 12: elementals by their names (2026-11-21)

Each elemental family moved to one Xeen copy, so every tier has its own colour (before, Fire C/D, Whirlwind/Guardian of
Air and Tidal Terror/Guardian of Water shared skins, the air and water pairs in red and orange-brown, and all four earth
rows were `m504_a`). The source skins stay in each copy, so the unchanged rows keep their look. Previews in
`work_s12/elementals/` (`air.png`, `water.png`, `earth.png`, `fire.png`; the fire preview ignores alpha, so
`flame_check2.png` and `fire_bodies.png` show the flames and the core). Design colours: these rows share or lack sprites.
`xeen_tiers.py`'s `mid` rule now also takes `shadow`/`highlight` hues (as `add_region.py`).

### Air: `xeen_aie1.glb` (from `mm6_aie1`, `spec_elem_air.json`)

Region 0: the light wind sheets; 1: the darker streaks.

| Skin | Rows | Sheets / streaks |
| --- | --- | --- |
| aie1_a | Lesser Air Elemental (Elemental E) | unchanged: grey-white / grey-brown |
| aie1_b | Air Elemental (Air Elemental A) | unchanged: warm grey / violet |
| xaie_whirl | Whirlwind (Air Elemental B) | storm grey-blue #7a8ca4 (shadow #445470, pale cyan highlight #b4d4e2) / slate navy #2c3a54 |
| xaie_guard | Sleeper's Guardian of Air (Air Elemental C) | bright silver-white #d2cdb8 (highlight #fffdf2) / gold #a8842c |

### Water: `xeen_m210.glb` (from MM7 `mm7_m210`, `spec_elem_water.json`)

Regions 0 skin, 1 belly, 2 fins and hands.

| Skin | Rows | Skin / belly / fins |
| --- | --- | --- |
| m210_a | Lesser Water Elemental (Elemental F) | unchanged: blue / white / coral |
| m210_b | Water Elemental (Water Elemental A) | unchanged: teal / white / pink |
| xm210_tidal | Tidal Terror (Water Elemental B) | deep navy #1c3070 / blue-grey #8c9cb8 / foam #a8dcec |
| xm210_guard | Sleeper's Guardian of Water (Water Elemental C) | bright sea-green #22b46c / pale #c4dcc8 / gold #d8a838 |

### Earth: `xeen_m504.glb` (from MM8 `mm8_m504`, `spec_elem_earth.json`)

Region 0: the whole rock body (shadow, mid, highlight).

| Skin | Rows | Rock |
| --- | --- | --- |
| xm504_sand | Lesser Earth Elemental (Elemental G) | sandy ochre #5e4224, #96784a, #ccb07c |
| m504_a | Earth Elemental (Earth Elemental A) | unchanged brown |
| xm504_blaster | Earth Blaster (Earth Elemental B) | iron-oxide red-brown #220a05, #4e2216, #8a3c22 |
| xm504_guard | Sleeper's Guardian of Earth (Earth Elemental C) | dark slate with jade faces #101418, #384046, #3ea070 (contrast 1.15) |

### Fire: `xeen_fie1.glb` (from `mm6_fie1`, `spec_elem_fire.json` + `flame_elem_fire.json`)

Region 0 is the body inside the flame cage; the flame, fringe and spark materials carry no region. `flame_ramps.py`
gives them, for the listed skin only, a variant material with the body's constant full mask and one ramp of colour
stops over the texture's own luminance range (2nd-98th percentile); the other skins keep the gold flames.

| Skin | Rows | Core / flames |
| --- | --- | --- |
| fie1_a / fie1_b / fie1_c | Lesser Fire Elemental, Fire Elemental, Fire Blower (Elemental A/B/C) | unchanged: red / green / blue core, gold flames |
| xfie_d | Sleeper's Guardian of Fire (Elemental D) | white-hot gold core #ffd458 (lift 0.3, contrast 0.6) / deep crimson-red flames #960c10-#d83218 with orange tips #ffc070 (the first crimson-violet ramp read magenta in game) |

Rebuild: `xeen_tiers.py` per spec on the installed MM6/MM7/MM8 source; for fire `xeen_tiers.py mm6_fie1.glb
work_s12/elementals/xeen_fie1_tiers.glb spec_elem_fire.json`, then `flame_ramps.py work_s12/elementals/xeen_fie1_tiers.glb
export/xeen_fie1.glb flame_elem_fire.json`. Installed (winding 0 inverted on all four); bound and seen in game in XD-11's
hall (`ingame_s12/`), as are the air, water and earth tiers.

## Session 12: trolls, ninjas, swamp things and hornets by their names (2026-11-21)

The user's rule: a tier whose name implies a colour or element must show it, and differently named siblings must not
look identical. Previews in `work_s12/misc/` (`*_tiers.png`). Installed; bound by the lane.

### Trolls: `xeen_m476.glb` (from MM8 `mm8_m476`)

Region 0 the vest trims; channel 1 the yellow-green skin and fur collar, added by `add_region.py` with
`body_trolls_skin.json` (every other skin keeps its skin through the fitted ramp, fit mean 0.8–1.0 of 255). Rebuild:
`xeen_tiers.py mm8_m476.glb work_s12/misc/m476_tiers.glb spec_trolls.json`, then `add_region.py
work_s12/misc/m476_tiers.glb export/xeen_m476.glb body_trolls_skin.json`. The club's mask is empty on every tier, so it
stays `mm8_m476_club.glb` (variant 0 looks the same).

| Skin | Rows | Follows | Skin / trims |
| --- | --- | --- | --- |
| troll_a | Troll A, Warren Troll A | unchanged | yellow-green / green |
| troll_b | Troll Guard B, Hobstadt's Guard D, Troll Matron, Warren Troll B | unchanged | yellow-green / blue |
| troll_c | Hobstadt (Darkside 56 troll chief: not an ice troll) | unchanged | yellow-green / pink |
| xtrl_a | Ice Troll (Troll C 11072, Warren Troll C 11692) | native colour, Xeen 53 (ice) | frost blue-grey #86a8be (shadow #465c74, light #c4e6f6) / frost white-blue #c4dcec |

### Ninjas: `xeen_mnk1.glb` (from `mm6_mnk1`)

Region 0: robe and hood (rope belt, hands, feet fixed). `spec_ninjas.json`.

| Skin | Rows | Follows | Robe |
| --- | --- | --- | --- |
| mnk1_a | Ninja A, Ninja D | unchanged | brown |
| xmnk_a | Shadow Ninja (Ninja B 11121) | design | near-black charcoal with a cold violet-slate cast #2e2c38 (lift 0.35, contrast 0.85) |
| mnk1_c | Ninja C, Clan Master | unchanged | red |

### Swamp things: `xeen_m479.glb` (from the MM7 treant `mm7_m479`)

The treant has no skins and no mask. `new_mask.py` (session 12) gives the copy three skins whose materials copy the
plain material plus an empty mask per LOD atlas; `add_region.py body_swamp_things.json` then fills channel 0, all the
bark (teeth and green eyes stay out), with `mid` and shadow/highlight hues per tier. The default material is
untouched, so Xeen Stumpy stays on `mm7_m479` as it was. Rebuild: `new_mask.py mm7_m479.glb
work_s12/misc/m479_masked.glb xswt_a xswt_b xswt_c`, then `add_region.py work_s12/misc/m479_masked.glb
export/xeen_m479.glb body_swamp_things.json`.

| Skin | Rows | Follows | Bark (shadow / mid / light) |
| --- | --- | --- | --- |
| xswt_a | Swamp Thing (A 11460) | design after Xeen 34 | wet moss green #142a12 / #3a5a24 / #6e9032 |
| xswt_b | Bog Thing (B 11461) | design | peat brown with olive ridges #241608 / #4a3c20 / #808c2c (contrast 1.15) |
| xswt_c | Marsh Horror (C 11462) | design | murky black-green #08140f / #1a3830 / sickly yellow-green #b4c83c (contrast 1.2) |

### Hornets: `xeen_m556.glb`, `xeen_m556_sword.glb`, `xeen_m556_shield.glb` (from MM8 `mm8_m556`)

Region 0 the eyes and the thorax and leg pads; channel 1 the saturated yellow body (`body_hornets_body.json`, sat above
0.84; the black bands stay black); channel 2 the wing membranes and the body's duller gold transitions
(`body_hornets_wings.json`), which take the smoky ember as a shade between crimson and black. Fit means 4.4 and 4.2 of
255 on the other skins. The equipment's region 0 (shield face, sword guard stones) was green on wasp_a, so the sword
and shield got Xeen copies with `xwsp_a` (`spec_hornets_equipment.json`). Rebuild: `xeen_tiers.py mm8_m556.glb
work_s12/misc/m556_t.glb spec_hornets.json`, `add_region.py ... m556_b.glb body_hornets_body.json`, `add_region.py
work_s12/misc/m556_b.glb export/xeen_m556.glb body_hornets_wings.json`; `xeen_tiers.py` on each attachment.

| Skin | Rows | Follows | Body / wings / eyes and pads |
| --- | --- | --- | --- |
| xwsp_a | Hell Hornet (Hornet A 11350) | design (Darkside 20 is a teal beetle) | deep crimson on black #540c0e (shadow #0c0204, light #c8241a, contrast 1.7) / smoky ember #4a2a22 to #d0561c / ember orange #e8641a |
| wasp_b | Hornet Swarm B | unchanged | yellow / tan / violet |
| wasp_c | Hornet Queen C | unchanged | yellow / tan / pink |

## Session 12: dragons and other tiers by their names (2026-11-21, lane)

The user: a tier's look follows its name (Water Dragon blue, Acid Dragon poison green, Fire Dragon red). The audit of
every Xeen family is in `devdocs/xeen/lanes/S.md` ("Session 12: names and looks"). Seen in XD-11's hall
(`ingame_s12/sheet2.jpg`, `sheet4.jpg`, `guardians_crop.jpg`, `sheet6.jpg`).

### Cloudside dragons: `xeen_cdr1.glb` (installed copy of `mm6_cdr1`, `spec_cloud_dragons.json`)

Regions 0 body and wings, 1 belly strip and spine ridge.

| Skin | Rows | Body / belly |
| --- | --- | --- |
| xcdr_water | Water Dragon (Dragon A) | sea turquoise-blue #1c86a6 / pale aqua #8ad4cc |
| xcdr_acid | Acid Dragon (Dragon B) | poison yellow-green #76b21a / sickly yellow #d6dc2e |
| xcdr_fire | Fire Dragon (Dragon C) | fire red #b01a0e / orange-gold #f09a18 |
| xcdr_frost | Frost Dragon (Dragon D) | ice blue #a6c8e2 (contrast 0.85) / frost white #e2f0f8 |
| xcdr_king | Dragon King (D-57 Q3) | black #2a2628 / gold #d0a020 |
| xcdr_pet | Xeen's Pet (session 7) | leaf green / horn brown |

### Darkside dragons: `xeen_m492.glb` (copy of `mm8_m492`, `spec_dark_dragons.json`)

Regions 0 body scales, 1 edges and spines, 2 wing membranes, 3 horns. The body's ramp is nearly black (mean shown
luminance 0.02), so the pale skins need `contrast` 0.5 and `lift` 0.5 or they speckle.

| Skin | Rows | Body / edges / wings |
| --- | --- | --- |
| xdrg_cloud | Cloud Dragon (Dark Dragon A) | storm grey-white #9aa2b0 / slate #56606e / pale silver-blue #d0dae6 |
| xdrg_green | Green Dragon (Dark Dragon B) | forest green #2a7224 / dark green #1a3a12 / yellow-green #8cb032 |
| xdrg_phase | Phase Dragon (Dark Dragon C) | deep indigo #2e2a7a / violet #7a3ab0 / pale cyan #5ac0d0 |
| xdrg_energy | Energy Dragon (D-57 Q30) | violet-white #ac9ad8 / electric violet #8a3cf0 / white-lilac #e6dcfa |
| m492 | Megadragon | native brown-black, gold wings |

### Undead dragons: `xeen_m616.glb` (copy of `mm8_m616`, `spec_bone_dragons.json`, `texture_skin.py`)

MM8's bone dragon has no region mask and its three skins look the same, so the tiers are recoloured texture copies
(as the mummies): Bone Dragon A `m616_a` (bone white), Undead Dragon B `xbdr_b` (rotting grey-green #86907a), Dragon
Mummy C and Scraps `xbdr_c` (tan wrappings #b08a60, Darkside image 15).

### Binding swaps (no new skins)

- Devil (Demon B) takes MM6's red `demon_c` (its Xeen image 70 is red); the Screamer (Demon C) takes the green `demon_b`.
- Venomous Hydra (Hydra B) takes the green `hyd_c`; the Great Hydra (Hydra C) the many-coloured `hyd_b`.

## Session 13: the review's tunings and the lich tiers (2026-11-21)

Work in `work_s13/` (the session-12 exports and specs are kept there as `*.s12.*`), in-game checks in `ingame_s13/`
(daylight: XD-11's hall, `tour_day*.yml`; dim: XD-21, `tour_dim*.yml`).

- **Hell Hornet** (`xwsp_a` on `xeen_m556`): the body's crimson lifted (`body_hornets_body.json`: mid #540c0e ->
  #66110f, highlight #e0301e, contrast 1.7 -> 1.35), and the wings glow ember red-orange: `claude_shared/emission.py`
  on the three `xwsp_a` materials (one per LOD atlas), mask = wing channel 2 x base luminance plus 0.35 x region 0
  (eyes and pads), colour 1.0, 0.16, 0.02, strength 0.42. Other skins have no emission. Rebuild: `xeen_tiers.py` ->
  `add_region.py` body -> `add_region.py` wings (as session 12) -> the emission masks (script in S.md's session-13 log;
  masks `work_s13/hornet/emis_{9,10,11}.png`) -> `emission.py` three times. Seen: `ingame_s13/hornet_v2.jpg` (day
  above, XD-21 below); before: `ingame_s12/shots6/hornets.png`.
- **Guardian of Air** (`xaie_guard` on `xeen_aie1`): sheets pale gold #d4c290 (shadow #a08030, highlight #fff0c8),
  streaks rich gold #c8920e (shadow #6a4404, highlight #ffd040). An emission try (streaks, 0.4 and 0.12) made it a
  glowing column like a fire elemental and was dropped: the blended wind already reads bright. Seen: `air_v2.jpg`
  (with emission), `air_v3.jpg` (final: at 2,000 the guardian is a clear gold column beside the white Lesser Air and
  the blue Whirlwind; the near and dim frames of that run missed it, it had drifted off).
- **Power Lich and Skeletal Lich** (11284/11285, `Xeen Lich D/E`, D-57 Q30): the Xeen copy `xeen_lch.glb` of
  `mm6_lch` (`spec_liches.json`, `body_liches_bones.json` channel 1, `body_liches_gold.json` channel 2,
  `body_liches_mail.json` channel 3; region 0 the bracers' red parts). Lich A-C stay on `mm6_lch` `lch_a-c`.

| Skin | Rows | Follows | Bones / gold parts / mail / bracers |
| --- | --- | --- | --- |
| xlch_d | Power Lich (Lich D 11284) | Darkside 34 (gunmetal skull, bronze veins, violet eyes) | dark gunmetal #45444c / dark bronze #7a4a22 / violet-black #2a1a3a / violet #6a2aa8, glowing (emission 0.25, 0.06, 0.5 on region 0) |
| xlch_e | Skeletal Lich (Lich E 11285) | Darkside 49 (teal bones, violet hair, orange rags, red sash) | teal #3e9494 / orange rags #d6741a / violet #6a2a9e / red #b01818 |

  Gold channel fit on the other skins: mean 7.6 of 255 (saturated gold; the copy's `lch_a-c` are not bound). Seen:
  `ingame_s13/liches_v2.jpg` (Lich Lord C, Power Lich D, Skeletal Lich E; day and XD-21). In game the mail reads
  grey on D (metal), so D is told by its grey bones and glowing violet bracers, E by teal, violet and orange.

## Session 15 (D91 §1)

- `xeen_sor1.glb`: `xsor_i` for the Elder Druid (11928, `Xeen Elder Druid`: the Winter and Spring Druids): moss-green
  robe `#46583a`, bark-brown trims `#6a4e30`, white hair and beard (preview `work_s15/sor_i.png`). Bound as Picard's
  binding. Rebuild order unchanged: `xeen_tiers.py` → `add_region.py body_wizards.json` → `add_region.py
  body_wizards_hair.json`.
