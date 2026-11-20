# Mist candidates in MM6-MM8 (inventory, 2026-11-12)

Which maps would gain from a scene `mist` block ([Mist](MIST.md)), and where in them.

**Status (2026-11-12):** every map in the two "strong fit" tables below has a `<map>_mist.scene.yml` overlay (49 maps),
plus Sweet Water and Paradise Valley with a faint one at the user's request. Their values were generated from the
heights here and only a few were tuned by eye: Murmurwoods, the Barrow Downs' high ground and the Tularean Forest's
north road are still too thick. The "optional" tables are not done.

**How this was made, and how far to trust it.**
- *Fit* is a judgement from each map's theme and its monsters (`map_stats.txt`), not from walking the maps.
- *Outdoor heights* come from each ODM's heightmap: the height the lowest tenth and quarter of the land lies under.
  `base_height` is a starting value just above the low ground.
- *Dungeon levels* come from the heights of the entities and spawns in each scene file, grouped in bands of 128. They
  say which floors exist and roughly where (an x, y box), not which rooms. **Room picks need a walk through the map**;
  the "where" column is where to look first.
- Colours are suggestions. Start from Shadowspire's other values (`falloff_height` 80, `visibility` 480,
  `max_opacity` 0.7) outdoors and the guild's (`falloff_height` 110, `visibility` 850) indoors.

A layer has one height for the whole map. Where the "note" says the land is spread over a wide range of heights, one
layer mists only the low part; the rest needs volumes or stays clear.

## Outdoor maps

### Strong fit

| Map | File | Colour | `base_height` | Low land (10 % / 25 %) | Note |
| --- | --- | --- | --- | --- | --- |
| Shadowspire (MM8) | `out06.odm` | grey-green | 100 | | done |
| Murmurwoods (MM8) | `out07.odm` | soft green | 330 | 288 / 480 | forest, wisps |
| Plane Between Planes (MM8) | `pbp.odm` | violet | 120 | 64 / 160 | |
| Deyja (MM7) | `7out05.odm` | grey-violet | 1600 | 1504 / 2400 | land spread 1500-4400: valleys only |
| The Barrow Downs (MM7) | `out11.odm` | pale grey | 130 | 96 / 96 | flat low moor: covers nearly all of it |
| Tatalia (MM7) | `7out13.odm` | swamp green | 200 | 160 / 512 | the swamp lowlands |
| Evenmorn Island (MM7) | `out09.odm` | grey-white | 130 | 96 / 128 | |
| The Tularean Forest (MM7) | `7out04.odm` | soft green | 720 | 672 / 1024 | |
| Mire of the Damned (MM6) | `outc3.odm` | sickly green | 190 | 160 / 160 | the best fit in MM6 |
| Misty Islands (MM6) | `oute2.odm` | white | 120 | 96 / 96 | by its name |
| Blackshire (MM6) | `outb2.odm` | grey | 190 | 160 / 160 | |

### Optional (a lighter touch, or a matter of taste)

| Map | File | Colour | `base_height` | Idea |
| --- | --- | --- | --- | --- |
| Dagger Wound Island (MM8) | `out01.odm` | white | 90 | thin sea mist between the islands |
| Garrote Gorge (MM8) | `out05.odm` | grey-blue | 150 | mist on the gorge floor and river |
| Ravenshore (MM8) | `out02.odm` | grey | 160 | harbour haze, thin |
| Plane of Fire (MM8) | `elemf.odm` | orange-red | 100 | glow haze over the lava (land is at 3000+) |
| Mount Nighon (MM7) | `out10.odm` | sulphur yellow | 560 | volcanic haze |
| Avlee (MM7) | `out14.odm` | soft green | 260 | |
| Frozen Highlands (MM6) | `outc1.odm` | blue-white | 190 | ice fog |
| Kriegspire (MM6) | `outb1.odm` | grey-brown | 190 | volcanic haze |
| Sweet Water (MM6) | `outa1.odm` | ochre-red | 190 | the devils' land |
| Hermit's Isle (MM6) | `outa3.odm` | white | 190 | |
| Bootleg Bay (MM6) | `outd2.odm` | white | 120 | sea mist |
| Eel Infested Waters (MM6) | `oute1.odm` | white | 120 | sea mist |

### Leave clear

Towns and bright or dry lands: New Sorpigal, Castle Ironfist, Free Haven, Silver Cove, Paradise Valley, Dragonsand
(MM6); Emerald Island, Harmondale, Erathia, the Bracada Desert, the Land of the Giants (MM7); Alvar, Ironsand Desert,
Ravage Roaming, Regna (MM8). Shoals is under water and has its own look.

## Dungeons

"Layer at z" means a map-wide layer with `base_height` about 30 above that floor: it fills that floor and everything
below it, and leaves the floors above clear. "Volumes" means flat, wide ellipsoids in single rooms.

### Strong fit

| Map | File | Colour | Form | Where to look first |
| --- | --- | --- | --- | --- |
| Necromancers' Guild (MM8) | `d19.blv` | green | layer at -832 | done (a violet volume was tried and removed) |
| Mad Necromancer's Lab (MM8) | `d20.blv` | green | layer at 0; denser one would suit -1024 | main floor at 0; a lower level at -1024 |
| Vampire Crypt (MM8) | `d21.blv` | blue-grey | layer at 0 | main floor at 0 (galleries at 128, 256 stay clear) |
| Troll Tomb (MM8) | `d13.blv` | grey | layer at -1536, volumes above | lowest floor -1536 (x -1500..250, y 2800..6400); halls at -512, -768 |
| The Crypt of Korbu (MM8) | `d26.blv` | grey-violet | layer at -1024 | lowest chamber (x 400..1900, y -770..560) |
| Tomb of Lord Brinne (MM8) | `d28.blv` | pale grey | layer at 384 | single level |

| Smuggler's Cove (MM8) | `d07.blv` | grey-blue | layer at 0 | the water level; walkways at 128 just above it |
| The Barrows I-XV (MM7) | `mdk01-05`, `mdt01-05`, `mdr01-05` | pale grey | layer at each map's lowest floor | small maps, one recipe; e.g. Barrow VII -512, Barrow II -1408 |
| The Hidden Tomb (MM7) | `mdt11.blv` | grey-green | layer at -1280 | single level |
| Zokarr's Tomb (MM7) | `7d13.blv` | grey | layer at -640 | the tomb level below the entrance |
| Castle Gloaming (MM7) | `d03.blv` | grey-violet | layer at -2432 | the deep level (x -13500..-3800, y -15400..-12700) |
| The Wine Cellar (MM7) | `7d16.blv` | red-grey | layer at -512 | the cellar proper |
| The Haunted Mansion (MM7) | `7d37.blv` | pale grey | thin layer at 0, or volumes | ground floor; upper floor at 384 stays clear |
| The Erathian Sewers (MM7) | `d01.blv` | green | layer at -512 | the channel level |
| The Tidewater Caverns (MM7) | `7d17.blv` | grey-blue | layer at 128 | the lowest caves by the water |
| The Pit (MM7) | `7d26.blv` | violet-green | thin layer at 0 | a city in a cavern: keep it light |
| The Hall of the Pit (MM7) | `t04.blv` | grey-violet | layer at 0 | |
| Corlagon's Estate (MM6) | `6d11.blv` | pale grey | layer at -768 | the lower floors (-768 and the crypt at -1792) |
| Tomb of Ethric the Mad (MM6) | `6d14.blv` | grey-green | layer at 768 | single main level |
| Castle Darkmoor (MM6) | `cd2.blv` | grey-violet | layer at -256 | the sunken parts (-128, -256); the map is large |
| Free Haven Sewer (MM6) | `sewer.blv` | green | layer at 0 (and -768) | the whole network |
| Abandoned Temple (MM6) | `6d02.blv` | grey | layer at -1664 | the deep caves (-1664, -2176) |

### Optional

| Map | File | Colour | Idea |
| --- | --- | --- | --- |
| Abandoned Temple (MM8) | `d05.blv` | green-grey | the lower levels (-640, -896) |
| Castle of Air, Prison of the Lord of Air (MM8) | `d27.blv`, `d36.blv` | white | cloud on the lowest floor |
| Plane of Earth (MM8) | `eleme.blv` | brown | dust haze |
| Temples of Eep (MM8) | `d44-46.blv` | green | wererat warrens |
| Passage Under Regna (MM8) | `d33.blv` | grey | damp tunnels (many levels: volumes) |
| Ancient Troll Home (MM8) | `d43.blv` | grey | lowest floor -1024 |
| The Temple of the Moon, Grand Temple of the Moon, Temple of the Dark (MM7) | `7d06`, `7d19`, `t02` | violet | altar rooms as volumes |
| The Hall under the Hill (MM7) | `7d22.blv` | green-gold | the fairy mound, lowest floor -4352 |
| Celeste (MM7) | `7d25.blv` | white | cloud at the feet of the city (floor 0) |
| The Tularean Caves, White Cliff Cave (MM7) | `7d08`, `7d21` | grey | cave floors |
| Nighon Tunnels, Tunnels to Eeofol (MM7) | `7d35`, `7d36` | sulphur yellow | |
| Colony Zod (MM7) | `7d27.blv` | red | |
| Lair of the Wolf (MM6) | `6d17.blv` | grey | the den at -512 |
| Temple of the Snake, Temple of Tsantsa (MM6) | `6t8`, `6t3` | green | lowest rooms |
| Icewind Keep (MM6) | `6d15.blv` | blue-white | cold floor mist, single level |
| Tomb of VARN (MM6) | `pyramid.blv` | sand | thin haze on the main level (768) |

Not wanted (user, 2026-11-12): the Walls of Mist (MM7) and the Hive (MM6); outdoors the Planes of Air and Water (MM8;
the Plane of Water already has its own fog).

Not listed: guild halls, keeps, castles in use, forts, mines, laboratories, dragon caves and the fire dungeons, which
read better clear (or would want smoke, which is not mist).

## What the feature lacks for some of these

- **Time of day and weather.** "Morning mist" and "mist after rain" are not possible: a map's mist is constant. The
  sea-mist and harbour ideas above would be better with it.
- **One layer per map.** Several floors each with their own floor mist (Troll Tomb, Castle Gloaming, the Passage Under
  Regna) need volumes for all but the lowest.
- **Smoke.** Fire dungeons and dragon caves would want a dark, rising haze near the ceiling; the layer only thins
  upward.
