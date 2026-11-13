# Xeen: monsters, density and treasure

Proposal, 2026-11-12. Part of the [Xeen world design](README.md). The decoded source tables and the full conversion
reasoning are in `research/XEEN_SYSTEMS.md` (all 184 original monsters from `raw/dark/xeen.mon` and `dark.mon`, the
item system, classes, skills and spells). This file states what the world uses.

## 1. Conversion rules

Xeen's monsters have far less HP and far more damage than MM6–MM8's, and Darkside's experience is about seven times
Cloudside's, so **no Xeen number is carried over**. Each monster gets a level from its role and region, and the rest
follows the curve that nearly every row of `monster_data.txt` follows:

| Field | Rule |
| --- | --- |
| Level | By role and region (MAPS.md), checked against the MM6–MM8 monster of the same role. A family spans 1.5–2.5× from A to C |
| HP, XP | HP = L²/10 + 3L; XP = L(L+10). Bosses ×2–4 HP |
| AC, damage | Per-level medians of `devdocs/mm9_rework/BALANCE_PLAN.md` §7.1; golems, knights and dragons +25–50 % AC, casters and swarms −30 % |
| Whole-party attacks | Become area monster spells (Fireball, Ice Blast, Dragon Breath …) or `missile_blast` (`devdocs/MONSTER_MODIFIERS.md`); dragons and big casters only |
| Special attacks | The `Bonus` column's conditions (poison, disease, insane, sleep, paralyse, aging, stone, eradicate …); all exist |
| Damage types | Fire → Fire, electricity → Air, cold → Water, poison/acid → Body, energy → Energy, magic → Mind/Spirit spells |
| Resistances | From the level base; Xeen 100 → immune; Xeen's "energy" → Light |
| Behaviour | Bosses and signature monsters get `modifiers.yml` entries (frenzy, blink, charge, kite) and actor scripts where the source has a trick (breeder slimes split, Lord Xeen immune to all but the Slayer Sword, the Megadragon) |

## 2. Monster families

51 families, each A/B/C like MM6–MM8 (Goblin / Goblin Shaman / Goblin King). Levels are the A/B/C levels. "Reuse"
names an installed model to recolour into tiers (the colour-tier route of
`level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`); "New" needs a new 3D creature. Full stat rows (HP, AC,
damage, XP, resistances, comparables) are in `research/XEEN_SYSTEMS.md` §2.2.

| Family | A / B / C (levels) | Where | Model |
| --- | --- | --- | --- |
| Goblins and gremlins | Goblin 4 / Gremlin 6 / Gremlin Guard 10; Gettlewaithe 15 | Witch Tower, D1, Gremlin Court | Reuse `mm6_gob2` |
| Orcs | Orc Archer 7 / Orc Guard 12 / Orc Elite 25; Shaalth 30 | X1, Orc Caves, Temple of Bark | Reuse an MM9 half-orc or **new** tusked orc |
| Mad dwarves | Mad Dwarf 7 / Clan Sergeant 12 / Clan King 18 | Dwarf mines | Reuse `mm6_dwa1` |
| Ogres | 18 / 22 / 30; Graalg | X2, X4, D2 | Reuse `mm6_ogr` |
| Trolls | 18 / 28 / 38 (Ice Troll tier); Hobstadt 42 | X5, Troll Holes | Reuse MM7/MM8 trolls |
| Giants and cyclopes | Cyclops 36 / Giant 50 / Elder Giant 62 | X5 corner, D5 | Reuse MM8 cyclops, MM9 giant |
| Minotaurs and gorgons | 58 / 65 / 78 | Lost Souls | Reuse MM8 minotaur (gorgon = bronze tier) |
| Barbarians | 12 / 30 / 38; Yog | X5, X6, D1 | Reuse `mm6_bar1` |
| Outlaws | Rogue 12 / Thief 18 / Master Thief 30 | Rivercity, Southern Tower | Reuse `mm6_thf` |
| Ninjas | 22 / 30 / 40 | Ninja Pagoda | Reuse a monk tier, or **new** |
| Archers and rangers | 20 / 28 / 36 | X2 camps | Reuse `mm6_arc1` |
| Burlock knights | Jouster 24 / Yang Knight 32 / King's Guard 40; Captain Yang | X4, Castle Burlock, Rivercity | Reuse `mm6_kni`, `mm6_gua` |
| Dark knights | Slayer 45 / Death 55 / Doom Knight 75 | Northern Tower | Reuse `mm6_kni` (black/red tiers) |
| Witches | Wicked Witch 14 / Witch 32 / Coven Witch 50 | Witch Tower, Lakeside | **New** (pointed-hat witch) or MM9 hag |
| Sorceresses | 30 / 40 / 55; Morgana | Rivercity, Sandcaster | **New** female caster |
| Wizards | 36 / 45 / 60; Valio, Darzog (+clones), Xenoc | X6, Darzog's Tower, Sandcaster | Reuse `mm6_sor1` |
| Floating mages | Mystic 45 / Magic 55 / Mega Mage 70 | Eastern Tower | Reuse MM7 hovering warlock |
| Cultists | Cleric of Yak 16 / Yak Priest 25 / Mok Heretic 40 | Temple of Yak, Western Tower | Reuse `mm6_cle` |
| Madmen | Insane Beggar 4 / Mad Fool 8 | Rivercity, Castle Burlock | Reuse peasants |
| Skeletons | 6 / 12 / 16 | X1 dead forest, Yak | Reuse `mm6_ske` |
| Rotting dead | Zombie 10 / Ghoul 18 / Mummy 30 | X1, X3, Tomb | Reuse MM7 zombie, MM9 mummy |
| Spirits | Polter-Fool 18 / Tomb Guard 26 / Tomb Terror 40 (Ghost Rider) | Winterkill, Tomb | Reuse `mm6_gst`, MM9 ghost |
| Pyramid mummies | 50 / 75 / 85 | Great Pyramid, Southern Sphinx | Reuse MM9 mummy (new tiers) |
| Liches | Yak Lich 35 / Power Lich 60 / Skeletal Lich 85; Yak Master 50, Sandro 70 | Yak, Necropolis, Kalindra dungeon | Reuse `mm6_lch`, MM9 lich king |
| Vampires | Gnome Vampire 32 / Vampire 48 / Vampire Lord 62; Count Draco 45, Count Blackfang 90 | Nightshadow, Blackfang | Reuse MM8/MM9 vampires |
| Bats | Giant Bat 3 / Bat Queen 10 / Beholder Bat 20 | Mines, Nightshadow, Ellinger | Reuse `mm6_bat` |
| Spiders | 5 / 10 / 14 | Mines, D1 | Reuse `mm6_spi1` |
| Swarms | Doom Bug 2 / Insect Swarm 12 / Stingers 20; Hell Hornet 45 | Vertigo, X2, D3 | **New** swarm (particle cloud) |
| Giant crawlers | Scorpion 16 / Electrapede 20 / Mantis Ant 38; Lava Roach | X6, D1, D3 | **New** (one arthropod rig, three meshes) |
| Oozes | Slime 2 / Breeder Slime 4 / Sewer Slug 6 | Vertigo, sewers | Reuse `mm6_ooz` |
| Rats | Sewer Rat 5 / Rooka 12 / Sewer Stalker 35 | Sewers | Reuse `mm6_rat` |
| Wolves and cats | Dark Wolf 16 / Sabertooth 22 / Snow Beast 28 | D2, X5 | Reuse MM8/MM9 wolf, MM9 bigfoot; **new** sabertooth |
| Werewolves | 20 / 30 / 40 | Castle Basenji | Reuse `mm6_wwf` |
| Burrowers | Tiger Mole 9 / Sand Worm 38 / Armadillo 45 | Mines, X6, D3 | **New** (mole, worm, armadillo) |
| Swamp things | Giant Toad 11 / Swamp Thing 26 / Octopod 60 | X1, X3, D4 | **New** toad and octopod; swamp thing from the MM7 treant |
| Serpents | Giant Snake 5 / Guardian Asp 35 / Killer Cobra 45 | X1, Asp, D3 | Reuse `mm6_cob` |
| Snake men | 24 / 32 / 40 | Asp | Reuse MM8 serpentmen |
| Great lizards | Iguanasaurus 60 | D5 | Reuse MM6 lizard |
| Harpies | 14 / 18 / 24 | X8 | Reuse `mm6_hrp` |
| Sprites | Medusa Sprite 12 / Killer Sprite 16 / Sharla 20 | X2, D2 | **New** small winged fey |
| Gargoyles | 22 / 33 / 40 | X4, D4 | Reuse `mm6_gar` |
| Great birds | Roc 35 / Griffin 48 / Vulture Roc 58 | X9, D4, D6 | Reuse MM7 roc and griffin |
| Eyes | Floating 30 / Terrible 40 / Gamma Gazer 75 | D6 | Reuse `mm6_bh`, MM9 eye |
| Material golems | Wood 24 / Stone 40 / Iron 52; Diamond 70, Onyx 100 | Golem Dungeon, Darkstone | Reuse MM7 golem with material skins |
| Elemental golems | Sand 22 / Water 28 / Cloud 50; Lava 55, Sky 80 | X6, Cave of Illusion, sky maps | Reuse MM7 golem with an elemental shader |
| Magic constructs | Flying Feet 18 / Guardian 24 / Carnage Hand 35; Xeen's Guard 60 | Tower of High Magic, Darzog, Castle Xeen | **New**: the most Xeen-specific monsters |
| Robots | Patrol 50 / Annihilator 70 / Autobot 90 | Castle Alamar, D6 | Reuse `mm6_rob1` |
| Elementals | Lesser 50 / Elemental 65 / Greater 80 | Planes, D6 | Reuse MM6 elementals |
| Demons | Demon 50 / Devil 62 / Screamer 80; Barkman, Lord Xeen 110 | Volcano Cave, Castle Xeen | Reuse MM6 demons, MM9 greater demon |
| Clouds dragons | Water 60 / Acid 66 / Fire 75; Frost 85, Dragon King 100, Xeen's Pet 90 | X2 lake, X7, Dragon Cave | Reuse `mm6_cdr1`, MM9 dragon king |
| Darkside dragons | Cloud 80 / Green 88 / Phase 105; Energy 115, **Megadragon 150** | D7, Great Pyramid | Reuse MM8 dragon |
| Hydras | 45 / 55 / 65 | X7 | Reuse `mm6_hyd` |
| Undead dragons | Bone 45 / Undead 60 / Dragon Mummy 95; Scraps | Kalindra dungeon | Reuse MM8 bone dragon |

About 41 families reuse an installed model with new colour tiers. **New models, in priority order:** magic constructs
(Flying Feet, Guardian, Carnage Hand, Xeen's Guard), witch, sprite, swarm, arthropod rig (scorpion, electrapede,
mantis), toad, octopod, sabertooth, burrowers, female caster, optionally an orc and a ninja. That is 10–13 new creature
projects through the standard creature-to-3D route.

## 3. Density

| Space | Target | Basis |
| --- | --- | --- |
| Surface ODM | 45–75 spawn markers, **110–150 hostiles at load**, 3 families per map at the map's d-level, 8–15 encounter areas with quiet gaps, packs of 2–5 and some loose patrols | MM7/MM8 medians (MM6's 200+ is too grindy) |
| Town maps | The same total, but none inside the town buffer; the first fight 2,000–6,000 from each arrival | MAP_CRAFT §6.1 |
| Sky maps | 60–100 hostiles, all placed (no respawning spawns), on islands and causeways | MM9 open-air practice |
| Planes | 40–70 each | Small by design |
| Dungeons | S 20–35, M 35–65, L 70–120; about 2–2.5 per sector, uneven | MAP_CRAFT §6.3 |
| Whole world | **≈ 4,700 monsters** on a first visit: 13 ODMs × 135 + 3 sky × 80 + 4 planes × 55 + dungeons ≈ 2,400 | MM7 ≈ 4,470, MM8 ≈ 4,130; this is two games' worth of story |

Respawn: MM6–MM8 rules (outdoor spawn points refill after the map's reset period; placed bosses do not).

Placement rules that keep Xeen recognisable (research §2.2): Vertigo's pests, the orc outposts to burn, the dwarf mines'
spiders and mad dwarves, Witch Tower goblins, Rivercity's beggars and robbers, Winterkill's three ghost waves,
Nightshadow's bats, the Golem Dungeon's material ladder, the Tower of High Magic's flying feet, Darzog's carnage hands,
Castleview's goblins and gremlins, the troll holes, Bark's orcs, the four towers' themes, Blackfang's vampires, Alamar's
robots, the Skyroads' cloud dragons.

## 4. Treasure

### 4.1 Treasure levels

The MM9 stage rule on monster level (BALANCE_PLAN §3.3): monster levels 1–7 → treasure level 1, 8–15 → 2, 16–30 → 3,
31–44 → 4, 45–64 → 5, 65+ → 6. Chests one step above the area's monsters. Map `Tres` (map_stats) as in the MAPS
sheets: X1 1, X2 2, X3/X4 2–3, X5/D1/D2 3, X6/D3/D4 4, D5 4–5, X7/D6 5–6, sky and planes 5–6. Lock/Trap 0 → 4 → 10
→ 20 (calibration). Gold per experience at MM7's ratio.

**Gems as a second currency.** The source pays talking skulls, the dragon tax, gemsmiths and guild fees in gems. Add
gems (MM6–MM8 already have gem items) to the random loot at all levels and let those vendors take them. This is the
cheapest way to keep a strong Xeen flavour.

### 4.2 Items

The source's item system (one modifier per item: element, material from wooden to obsidian, or attribute) maps onto
the existing enchant tables without engine work (research §3.2). Use it as:

| Xeen idea | In this world |
| --- | --- |
| Material ladder (wooden … obsidian) | **Names** of the world's new tiered bases: wooden/bronze T1, iron/silver T2, steel/crystal T3, gold/amber T4, platinum/ebony/quartz T5, ruby, emerald, sapphire, diamond and obsidian T6. Numbers follow the MM tier ladder, not Xeen's (+50 damage obsidian is off any curve) |
| Elemental prefixes | `of Fire / Flame / Infernos`, `of Sparks / Lightning / Thunderbolts`, `of Cold / Frost / Ice`, `of Poison / Venom / Acid` by tier; armour resistances |
| Attribute prefixes | the standard `of Might`, `of Thought` … enchants |
| Slayers (Dragon Slayer, Undead Eater) | `Dragon Slaying`, `Undead Slaying`. Golem Smasher, Bug Zapper and Beast Bopper need a new monster-type tag (optional engine work) |
| Gemsmith gear (Q-D7) | Ruby/Emerald/Sapphire/Diamond named items at T4–T6, crafted from rocks and gems |

**New bases** (MM6–MM8 lack them): katana and wakizashi (Sword), scimitar and sabre, flamberge (Sword 2H), naginata,
glaive, pike and bardiche (Spear/Axe 2H), grand and great axe, nunchaku and flail (Mace), sling, robes (Leather, for
casters), scale/ring/splint mail (Chain/Plate), and brooch/medal/cameo/scarab/pendant variants of the amulet slot. About
60–90 item rows with their icons (generated through the existing icon pipeline).

**Artifacts and relics** (MM6–MM8 artifact caps; `World: xeen` flag like MM9's):

| Item | Slot | Effect (MM terms) | Source |
| --- | --- | --- | --- |
| **Xeen Slayer Sword** | Sword 2H relic | artifact-cap damage; the only weapon that harms Lord Xeen; double damage vs demons | M23 |
| **Elder weapons** (Long Sword, Dagger, Mace, Spear, Staff, Long Bow) | set | each at the artifact cap; set bonus +10 all resistances. Hidden one per late dungeon | WoX tables |
| **Seasons set** (Flower, Leaf, Snowflake, Raindrop) | ring, amulet, belt, cloak | +10 one resistance each; set +10 all stats | Q-C1 |
| Princess Roxanne's Tiara | helm | +15 Personality, +15 Intellect, Mind immunity | Q-C3 (copy given back as thanks) |
| Queen Kalindra's Crown | helm | +20 Personality, +10 all resistances | M27 (gift after the wedding) |
| Ector's Ring | ring | +10 Might and Endurance, regeneration | Q-D21 |
| Barok's Pendant | amulet | +30 SP, SP regeneration | Q-C2 |
| Holy Book of Elvenkind | relic | +5 Learning, +10 Spirit | Q-C18 |
| Chalice of Protection | relic | Day of Protection once a day | Q-D17 |
| Songbird of Serenity | relic | Mind resistance; cures Insane and Afraid | M24 (after Dimitri) |
| Jewel of Ages | relic | immune to aging | Q-D18 |
| Vespar's Staff (rehilted) | staff | artifact staff, `of Lightning` | Q-D8 |
| A dead paladin's armour | plate | artifact plate | Q-D24 |
| Megadragon's hoard piece | weapon | top artifact | Q-D26 |

Artifacts come only from fixed sources and level-6 chest slots (set `chestArtifactsOnly` if the world adopts MM9's
black-chest rule; the user decides).

### 4.3 Classes, skills and spells

No change to the shared class, skill or spell tables (research §4). Xeen's ten classes all exist in MMerge except the
Barbarian (offer Knight or a Troll); Xeen's races map onto MMerge races except the Gnome. Xeen spell names appear only in
guild flavour text. Secondary skills: WORLD_DESIGN §5.3.
