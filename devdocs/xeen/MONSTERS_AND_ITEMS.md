# Xeen: monsters, density and treasure

Proposal, 2026-11-12; revised 2026-11-14 for the user's decisions after the three reviews (README, "Decisions of
2026-11-14"; `reviews/`): the combat review's per-map table is adopted (MAPS §0), the over-wide families are split,
treasure follows the MM6–MM8 table, training caps as proposed. Part of the [Xeen world design](README.md). The decoded
source tables and the full conversion reasoning are in `research/XEEN_SYSTEMS.md` (all 184 original monsters from
`raw/dark/xeen.mon` and `dark.mon`, the item system, classes, skills and spells). This file states what the world uses.

## 1. Conversion rules

Xeen's monsters have far less HP and far more damage than MM6–MM8's, and Darkside's experience is about seven times
Cloudside's, so **no Xeen number is carried over**. Each monster gets a level from its role and region, and the rest
follows the curve that nearly every row of `monster_data.txt` follows:

| Field | Rule |
| --- | --- |
| Level | By role and region (MAPS.md), checked against the MM6–MM8 monster of the same role. **A family spans at most 2.5× from A to C and at most 25 levels; a Xeen group whose monsters lie further apart becomes two or three families.** On a map that must be cleared, A-tier ≈ the arriving party's level and C-tier ≤ 2× it; bosses 2–3×; trap maps exempt. **Ordinary families stop at level 100; named bosses at 125** (MM6–MM8's highest row) |
| HP, XP | HP = L²/10 + 3L; XP = L(L+10). Bosses ×2–4 HP |
| AC, damage | Per-level medians of `devdocs/mm9_rework/BALANCE_PLAN.md` §7.1; golems, knights and dragons +25–50 % AC, casters and swarms −30 % |
| Whole-party attacks | Become area monster spells (Fireball, Ice Blast, Dragon Breath …) or `missile_blast` (`devdocs/MONSTER_MODIFIERS.md`); dragons and big casters only |
| Special attacks | The `Bonus` column's conditions (poison, disease, insane, sleep, paralyse, aging, stone, eradicate …); all exist |
| Damage types | Fire → Fire, electricity → Air, cold → Water, poison/acid → Body, energy → Energy, magic → Mind/Spirit spells |
| Resistances | From the level base; Xeen 100 → immune; Xeen's "energy" → Light |
| Behaviour | Bosses and signature monsters get `modifiers.yml` entries (frenzy, blink, charge, kite) and actor scripts where the source has a trick (breeder slimes split, Lord Xeen immune to all but the Slayer Sword, the Megadragon). **Every boss has its own monster_data row with its HP multiplier and treasure; scene `hp` is not read** (as MM6–MM8's Goblin King and Lord Markham's guards) |

## 2. Monster families

66 families, each A/B/C like MM6–MM8 (Goblin / Goblin Shaman / Goblin King). Levels are the A/B/C levels; named bosses
after the semicolon. "Reuse" names an installed model to recolour into tiers (the colour-tier route of
`level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`); "New" needs a new 3D creature. A split family shares its
parent's model with other colour tiers. The first stat rows (HP, AC, damage, XP, resistances, comparables) are in
`research/XEEN_SYSTEMS.md` §2.2; where a level below differs, this file wins.

| Family | A / B / C (levels) | Where | Model |
| --- | --- | --- | --- |
| Goblins (Cloudside) | Goblin 4 / Gremlin 6 / Gremlin Guard 10 | Witch Tower, X1 | Reuse `mm6_gob2` |
| Gremlins (Darkside) | Gremlin 14 / Gremlin Saboteur 18 / Gremlin Guard 22; Gettlewaithe 24 | D1, Gremlin Court | Reuse `mm6_gob2` |
| Orcs | Orc 5 / Orc Archer 7 / Orc Guard 10; Drum-Master 12 | X1, Orc Caves, X7 south | Reuse an MM9 half-orc or **new** tusked orc |
| Orc warband | Orc Elite 16 / Orc Shaman 20 / Orc Captain 26; Shaalth 30 | Temple of Bark | as Orcs |
| Mad dwarves | Mad Dwarf 7 / Clan Sergeant 10 / Clan Guard 12; Clan King 18 | Dwarf mines | Reuse `mm6_dwa1` |
| Ogres | 18 / 22 / 30; Graalg | X2 (crossings only), X4, D2 | Reuse `mm6_ogr` |
| Trolls | 18 / 28 / 38 (Ice Troll tier); Hobstadt 42 | X5, Troll Holes | Reuse MM7/MM8 trolls |
| Giants and cyclopes | Cyclops 36 / Giant 50 / Elder Giant 62 | X5 corner, D5 | Reuse MM8 cyclops, MM9 giant |
| Minotaurs and gorgons | 38 / 45 / 55 | Lost Souls | Reuse MM8 minotaur (gorgon = bronze tier) |
| Barbarians | Barbarian 14 / Sardaj Warrior 20 / Barbarian Chief 28; Yog | X5, D1, X6 | Reuse `mm6_bar1` |
| Outlaws | Rogue 12 / Thief 18 / Master Thief 30 | Rivercity, Southern Tower | Reuse `mm6_thf` |
| Ninjas | 22 / 30 / 40 | Ninja Pagoda | Reuse a monk tier, or **new** |
| Evil rangers | 8 / 12 / 18 | X2 camps | Reuse `mm6_arc1` |
| Burlock knights | Jouster 14 / Yang Knight 20 / Knight Captain 26; King's Guard 40 (Castle Burlock only), Captain Yang | X4, Castle Burlock, Rivercity | Reuse `mm6_kni`, `mm6_gua` |
| Dark knights | Slayer 45 / Death 55 / Doom Knight 75 | Northern Tower | Reuse `mm6_kni` (black/red tiers) |
| Witches | Wicked Witch 10 / Witch 14 / Head Witch row 20 | Witch Tower | **New** (pointed-hat witch) or MM9 hag |
| Coven | Witch 32 / Coven Witch 40 / Coven Mother 50 | Lakeside | as Witches |
| Sorceresses | 30 / 40 / 55; Morgana | Rivercity, Sandcaster | **New** female caster |
| Wizards | 36 / 45 / 60; Valio, Darzog 55 (+clones), Xenoc 60 | X6, Darzog's Tower, Sandcaster | Reuse `mm6_sor1` |
| Floating mages | Mystic 45 / Magic 55 / Mega Mage 70 | Eastern Tower | Reuse MM7 hovering warlock |
| Cultists | Cleric of Yak 14 / Yak Priest 20 / Yak Elder 28; Yak Master 35 | Temple of Yak | Reuse `mm6_cle` |
| Heretics | Mok Heretic 25 / Heretic Priest 35 / Heretic Lord 45 | Western Tower | as Cultists |
| Madmen | Insane Beggar 4 / Mad Fool 8 | Rivercity, Castle Burlock | Reuse peasants |
| Skeletons | 6 / 12 / 16 | X1 dead forest, Yak | Reuse `mm6_ske` |
| Rotting dead | Zombie 8 / Ghoul 12 / Grave Ghoul 18 (Mummy 30 joins the Pyramid mummies' A tier as Tomb Mummy) | X1, X3, Tomb | Reuse MM7 zombie, MM9 mummy |
| Spirits | Polter-Fool 18 / Tomb Guard 26 / Tomb Terror 40 (Ghost Rider) | Winterkill, Tomb | Reuse `mm6_gst`, MM9 ghost |
| Pyramid mummies | Tomb Mummy 42 / Pyramid Guard 52 / Royal Mummy 65; Ghost Mummy 62 and Phase Mummy 72 (tiers D, E, D-57) | Great Pyramid, Southern Sphinx | `xeen_mummy` (Xeen copy, D-44) with new tiers |
| Liches | 35 / 50 / 65; Sandro 65; Power Lich and Skeletal Lich as ordinary tiers D and E (D-57) | Necropolis, Kalindra dungeon, finale | Reuse `mm6_lch` with own skins (no MM9) |
| Vampires | Gnome Vampire 32 / Vampire 40 / Vampire Lord 50; Count Draco 45, Count Blackfang 70 | Nightshadow, Blackfang | Reuse MM8/MM9 vampires |
| Bats | Giant Bat 3 / Cave Bat 6 / Mine Bat 9 | Mines | Reuse `mm6_bat` |
| Night bats | Bat Queen 10 / Vampire Bat 14 / Beholder Bat 20 | Nightshadow, Ellinger, Gem Mines | Reuse `mm6_bat` |
| Spiders | 5 / 10 / 14 | Mines | Reuse `mm6_spi1` |
| Arachnoids | Arachnoid 14 / Arachnoid Hunter 18 / Arachnoid Queen 24 | D1 Dark Grove | Reuse `mm6_spi1` |
| Swarms | Doom Bug 2 / Insect Swarm 4 / Stingers 6 | Vertigo, Witch Tower | **New** swarm (particle cloud) |
| Hornets | Hell Hornet 35 / Hornet Swarm 42 / Hornet Queen 50 | D3 Aging Forest | as Swarms |
| Giant crawlers | Scorpion 16 / Electrapede 20 / Lava Roach 26 | X6, D1 | **New** (one arthropod rig, three meshes) |
| Mantis ants | Mantis Ant 22 / Mantis Warrior 30 / Mantis Queen 38 | D3 | as Giant crawlers |
| Oozes | Slime 2 / Breeder Slime 4 / Sewer Slug 6 | Vertigo, sewers | Reuse `mm6_ooz` |
| Rats | Sewer Rat 3 / Rooka 6 / Sewer Stalker 9 | Vertigo, Castleview sewers | Reuse `mm6_rat` |
| Sewer stalkers | Rooka 18 / Sewer Stalker 25 / Stalker Matriarch 35 | Sandcaster, Necropolis sewers | Reuse `mm6_rat` |
| Wolves and cats | Dark Wolf 16 / Sabertooth 22 / Snow Beast 28 | D2, X5 | Reuse MM8/MM9 wolf, MM9 bigfoot; **new** sabertooth |
| Werewolves | 20 / 30 / 40 | Castle Basenji | Reuse `mm6_wwf` |
| Burrowers | Tiger Mole 6 / Rock Mole 9 / Tunnel Mole 12 | Mines | **New** (mole) |
| Sand burrowers | Sand Worm 30 / Armadillo 38 / Great Worm 45 | X6, D3 | **New** (worm, armadillo) |
| Toads | Giant Toad 5 / Bog Toad 8 / Swamp Toad 11 | X1 Toad Meadow, X3 | **New** toad |
| Swamp things | Swamp Thing 20 / Bog Thing 26 / Marsh Horror 32 | X3 | From the MM7 treant |
| Octopods | Octopod 50 / Great Octopod 60 / Kraken 70 | D4 lake (trap) | **New** octopod |
| Serpents | Giant Snake 5 / Viper 8 / Constrictor 12 | X1 | Reuse `mm6_cob` |
| Cobras | Guardian Asp 30 / Killer Cobra 38 / King Cobra 45 | Asp, D3 | Reuse `mm6_cob` |
| Snake men | 16 / 20 / 26 | Asp Undercroft | Reuse MM8 serpentmen |
| Great lizards | Iguanasaurus 42 / Great Iguanasaurus 50 / Ancient Iguanasaurus 55 | D5 | Reuse MM6 lizard |
| Harpies | 14 / 18 / 24 | X8 | Reuse `mm6_hrp` |
| Sprites | Medusa Sprite 10 / Killer Sprite 14 / Sprite Queen 18; Sharla | X2, D2 | **New** small winged fey |
| Gargoyles | 16 / 22 / 28 (Cloudside); Magic Mountain tiers 30 / 38 / 45 | X4, D4 | Reuse `mm6_gar` |
| Great birds | Vulture Roc 30 / Roc 38 / Griffin 48 | X9, D4, D5, D6 | Reuse MM7 roc and griffin |
| Eyes | Floating 40 / Terrible 50 / Gamma Gazer 65 | D6 | Reuse `mm6_bh`, MM9 eye |
| Material golems | Wood 18 / Stone 26 / Iron 40; Diamond 50; Onyx Sentry 62, Onyx Warden 72 (D-57); Onyx 85 | Golem Dungeon, Newcastle, Darkstone | Reuse MM7 golem with material skins |
| Elemental golems | Sand 22 / Water 28 / Cloud 50; Lava 55, Sky 75 | X6, Cave of Illusion, sky maps | Reuse MM7 golem with an elemental shader |
| Magic constructs | Flying Feet 18 / Guardian 24 / Carnage Hand 35; Xeen's Guard 60 | Tower of High Magic, Darzog, Castle Xeen | **New**: the most Xeen-specific monsters |
| Robots | Patrol 50 / Annihilator 62 / Autobot 75 | Castle Alamar, Alamar Depths (FD-01), Dungeon of Death (FD-04) | Reuse `mm6_rob1` |
| Elementals | Lesser X Elemental 55 / X Elemental 62 / the source's names on the 70s (Fire Blower, Whirlwind, Earth Blaster, Tidal Terror) / Sleeper's Guardian of X 75; one family of rows per element (D-58) | Planes, D6 | Reuse MM6 air, MM7 water and earth elementals with tier skins (D-47, D-58) |
| Demons | Demon 42 / Devil 50 / Screamer 58; Barkman 60, Lord Xeen 85 | Volcano Cave, Castle Xeen, Temple of Bark | Reuse MM6 demons, MM9 greater demon |
| Clouds dragons | Water 60 / Acid 66 / Fire 75; Frost 85, Xeen's Pet 75, Dragon King 110 | X2 lake, X7, Dragon Cave | Reuse `mm6_cdr1`; the Dragon King on `xeen_cdr1` with his own skin (D-57) |
| Darkside dragons | Cloud 70 / Green 80 / Phase 90; Energy Dragon and **Megadragon 125** as named rows | D7, Great Pyramid | Reuse MM8 dragon |
| Hydras | 45 / 55 / 65 | X7 | Reuse `mm6_hyd` |
| Undead dragons | Bone 45 / Undead 55 / Dragon Mummy 65; Scraps 70 | Kalindra dungeon | Reuse MM8 bone dragon |

The splits and re-levellings follow `reviews/COMBAT_AND_PROGRESSION.md` §6.1 and the sheets' bands (MAPS §1–2). Rows
the review did not name but whose old levels broke the 2.5× rule or a sheet's band (Mad dwarves, Cultists, Snake men,
Great lizards, Gargoyles, Material golems, Elemental golems, Robots, Elementals, Demons, Pyramid mummies, Vampires,
Undead dragons, Sprites, Evil rangers, Burlock knights) are set here to the per-map table; Heretics, Arachnoids and Mantis
ants are new splits with invented B/C names.

About 52 families reuse an installed model with new colour tiers. **New models, in priority order:** magic constructs
(Flying Feet, Guardian, Carnage Hand, Xeen's Guard), witch, sprite, swarm, arthropod rig (scorpion, electrapede,
mantis), toad, octopod, sabertooth, burrowers (mole, worm, armadillo), female caster, optionally an orc and a ninja.
That is 10–13 new creature projects through the standard creature-to-3D route.

## 3. Density

| Space | Target | Basis |
| --- | --- | --- |
| Surface ODM | 45–70 spawn markers, hostiles at load by map role (below), 3 families per map at the map's d-level. Groups as in the per-map table (MAPS §0: 2–4, X1's orcs 3–5). Monsters form 3–8 **encounter areas** of 6–30 cells of 4,096 (a valley, a wood, a river bank) with markers 500–1,500 apart inside, and leave at least a third of the land cells without monsters in two or three large quiet quarters. No more than 3 areas of a single cell (camps, a lair) | MM7/MM8 medians (MM6's 200+ is too grindy); `reviews/SCALE_AND_DENSITY.md` §5 |
| Town maps | None inside the town buffer; the first fight 2,000–6,000 from each arrival | MAP_CRAFT §6.1 |
| Sky maps | 50–60 hostiles, all placed (no respawning spawns), on islands and causeways | MM9 open-air practice; MAPS §0 |
| Planes | 30 each | Small by design; MAPS §0 |
| Dungeons | S 15–30, M 45–75 (XD-03 and XD-05 40, as built), L set pieces 70–80 plus bosses (shipped L 120–180; WORLD_DESIGN §6); 1.2–2.5 per sector, uneven | Measured MM7/MM8 bands, `reviews/SCALE_AND_DENSITY.md` §1–2; MAPS §0 |
| Whole world | **≈ 4,200 monsters** on a first visit: outdoors ≈ 1,640, sky and planes 280, dungeons ≈ 2,270. **Party kill XP ≈ 6.35M** (MM7 5.0M) | MM7 ≈ 4,470, MM8 ≈ 4,130. Re-count after each act's builds with `output/xeen_review/combat/proposed.py` or its successor; a built act over its share by more than 15 % is trimmed |

**Hostiles at load by map role**, from the adopted per-map table: start pocket 130 (X1); hubs 135 with none inside the
town buffer (X2, D1); town maps of the middle 135 (X3, X4, D2, D3); wilderness 110–135 (X5, X6 135, D4 120, D5 110);
trap and endgame 90–110, few and strong (X7, D6). Each ±15 %. The scale review's heavier role bands (hubs 160–220,
wilderness 140–185) match the shipped maps better but would raise the experience budget; they are not used unless the
budget is re-run (HANDOFF, "Not reconciled").

Respawn: MM6–MM8 rules (outdoor spawn points refill after the map's reset period; placed bosses do not).

Placement rules that keep Xeen recognisable (research §2.2): Vertigo's pests, the orc outposts to burn, the dwarf mines'
spiders and mad dwarves, Witch Tower goblins, Rivercity's beggars and robbers, Winterkill's three ghost waves,
Nightshadow's bats, the Golem Dungeon's material ladder, the Tower of High Magic's flying feet, Darzog's carnage hands,
Castleview's gremlins, the troll holes, Bark's orcs, the four towers' themes, Blackfang's vampires, Alamar's robots, the
Skyroads' cloud dragons.

## 4. Treasure

### 4.1 Treasure levels

Treasure level from monster level on MM6–MM8's own drop curve: 1–12 → 1, 13–22 → 2, 23–34 → 3, 35–49 → 4, 50–74 → 5,
75+ → 6 (median drop levels of the shipped rows: L1 10, L2 18, L3 29, L4 39, L5 60, L6 80). Chests at the map's level;
one boss hoard per dungeon one step up. Map `Tres` (map_stats) as in MAPS §0: X1 and its dungeons 1, X2 1, X3/X4/D1 2,
Act II dungeons 2–3, X5/X6/D2/D3 3, Act IV 3–4, Act V 5, Act VI and the optional content 6. Lock/Trap 0 → 4 → 10 → 20
(calibration). Gold per experience at MM7's ratio (BALANCE_PLAN §3.3, before MM9's ×2.2); quest gold about 0.4M over
the campaign.

**Gems as a second currency.** The source pays talking skulls, the dragon tax, gemsmiths and guild fees in gems. Add
gems (MM6–MM8 already have gem items) to the random loot at all levels and let those vendors take them. This is the
cheapest way to keep a strong Xeen flavour; gem payment is required engine work (PRODUCTION E13).

### 4.2 Items

**The user's decision of 2026-11-20 (DECISIONS U-1):** no new equipment items. Random loot and shops use the MM6–MM8
engine items only (the world adds no random_items rows). Artifacts and relics, the tiara copy and the gemsmith gear
reuse MM6–MM8 item skins: each row's `like` is an engine artifact, relic or special item of the same slot and skill
where one fits, whose picture, paper-doll art and ground model it wears, with its Xeen name, id, effects and a
description adapted from the borrowed item's. Only quest items get generated icons and ground models.

The source's item system (one modifier per item: element, material from wooden to obsidian, or attribute) maps onto
the existing enchant tables without engine work (research §3.2). Use it as:

| Xeen idea | In this world |
| --- | --- |
| Material ladder (wooden … obsidian) | not used: no new bases (U-1). The MM tiers of the engine items carry the progression |
| Elemental prefixes | `of Fire / Flame / Infernos`, `of Sparks / Lightning / Thunderbolts`, `of Cold / Frost / Ice`, `of Poison / Venom / Acid` by tier; armour resistances |
| Attribute prefixes | the standard `of Might`, `of Thought` … enchants |
| Slayers (Dragon Slayer, Undead Eater) | `Dragon Slaying`, `Undead Slaying`. Golem Smasher, Bug Zapper and Beast Bopper need a new monster-type tag (optional engine work) |
| Gemsmith gear (Q-D7) | Ruby Broadsword, Emerald Leather, Sapphire Staff, Diamond Plate (12540–12543) at T4–T6, crafted from rocks and gems; skins of MM8 artifacts (below), common items here |

**Artifacts and relics** (MM6–MM8 artifact caps; `World: xeen` flag like MM9's). "Skin" is the engine item each row
copies (`source/items.yml` `like`): its picture, paper-doll art and ground model. Effects are unchanged by the skins
(all are the same slot and skill as before); the two season items that borrow an armour-bearing amulet and cloak set
their armour bonus back to 0.

| Item | Slot | Effect (MM terms) | Skin (engine item, picture) | Source |
| --- | --- | --- | --- | --- |
| **Xeen Slayer Sword** 12500 | Sword 2H relic | artifact-cap damage; the only weapon that harms Lord Xeen; double damage vs demons | MM7 Iron Feather 1303, `7item218` | M23 |
| **Elder weapons** 12501–12506 (Long Sword, Dagger, Mace, Spear, Staff, Long Bow) | set | each at the artifact cap; set bonus +10 all resistances. Hidden one per late dungeon | Puck 1302 `7item217`, Mordred 2020 `6ldagger4`, Mace of the Sun 538 `item340`, Gibbet 1310 `7item225`, Ethric's Staff 1317 `7item233`, Percival 2025 `6bow6` | WoX tables |
| **Seasons set** 12510–12513 (Flower, Leaf, Snowflake, Raindrop) | ring, amulet, belt, cloak | +10 one resistance each; set +10 all stats | Faerie Ring 1348 `7item303`, Morgan 2034 `6amulet6`, Titan's Belt 1326 `7item324`, Moon Cloak 1350 `7item348` | Q-C1 |
| Princess Roxanne's Tiara 12520 | helm (the copy) | the stolen tiara is a quest item, not worn; the copy given back as thanks is a unique helm: +10 Personality, +10 Intellect, +30 Mind resistance (DECISIONS D-2.6) | Noble Crown 900 `7item098`, the stolen tiara's own picture (it is its copy) | Q-C3 |
| Queen Kalindra's Crown 12521 | helm | +20 Personality, +10 all resistances | Phynaxian Crown 1325 `7item241` | M27 (gift after the wedding) |
| Ector's Ring 12522 | ring | +10 Might and Endurance, regeneration | Ruler's Ring 1315 `7item246` | Q-D21 |
| Holy Book of Elvenkind 12524 | relic | +5 Learning, +10 Spirit | MM7 spell book picture `7item190` (row 1202; Misc, not a spell book) | Q-C18 |
| Chalice of Protection 12525 | relic | +10 all resistances, party-wide while carried (DECISIONS D-2.5) | Sacred Chalice 2054 `chalice` | Q-D17 |
| Songbird of Serenity 12526 | relic | Mind resistance; cures Insane and Afraid | Eagle Statuette 2073 `statuet4` | M24 (after Dimitri) |
| Jewel of Ages 12527 | relic | immune to aging | Gem of Restoration 623 `item366` | Q-D18 |
| Vespar's Staff (rehilted) 12528 | staff | artifact staff, `of Lightning` | Merlin 2024 `6staff4` | Q-D8 |
| A dead paladin's armour 12529 | plate | artifact plate | Pellinore 2027 `6plate4` | Q-D24 |
| Megadragon's hoard piece (Wyrmfang) 12530 | weapon | top artifact | Elfbane 1333 `7item242` | Q-D26 |
| Gemsmith gear 12540–12543 | sword, leather, staff, plate | as Q-D7 | Terminus 502 `item236`, Serendine's Preservation 513 `item251`, Staff of Elements 530 `item335`, Supreme Plate 515 `item253` | Q-D7 |

Artifacts come only from fixed sources and level-6 chest slots (set `chestArtifactsOnly` if the world adopts MM9's
black-chest rule; the user decides).

### 4.3 Classes, skills, spells and training

No change to the shared class, skill or spell tables (research §4). Xeen's ten classes all exist in MMerge except the
Barbarian (offer Knight or a Troll); Xeen's races map onto MMerge races except the Gnome. Xeen spell names appear only in
guild flavour text. Secondary skills: WORLD_DESIGN §5.3.

Training halls and caps (adopted 2026-11-14): Vertigo 10 (×10), Rivercity 25 (×20), Castle Burlock and Castleview 40
(×25), Newcastle 60 (×30), Sandcaster 80 (×40), Castle Kalindra 200 (×50), Olympus unlimited (×80); Kai Wu's monastery
40 (×25). Every Xeen map gets a `LowerToEqual` row in `bolster_maps.txt`.

Sky Bandit (D-58): a thieves' tier of about 55 in its own faction, placed peaceful at D7's four tolls (two each), hostile on a refusal; not counted on the counted route.
