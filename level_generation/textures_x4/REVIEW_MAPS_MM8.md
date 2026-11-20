# MM8 x4 review maps

The smallest set of MM8 maps whose faces together show every in-scope MM8 surface texture (exact minimum, solved as
a set cover over `inventory.json` map usage). Regenerate with
`python3 review_maps.py mm8` after an inventory rebuild.

"Only here" counts textures that no other map in this set shows. Event-switched textures appear only after the
map script swaps them (for example opening a vault), so trigger those events when reviewing.

| Map | Name | Textures | Only here | Event-switched |
| --- | --- | ---: | ---: | --- |
| `elema.odm` | Plane of Air | 32 | 7 | - |
| `elemf.odm` | Plane of Fire | 21 | 6 | - |
| `elemw.odm` | Plane of Water | 25 | 4 | - |
| `out01.odm` | Dagger Wound Island | 150 | 56 | - |
| `out02.odm` | Ravenshore | 130 | 57 | - |
| `out03.odm` | Alvar | 88 | 30 | - |
| `out04.odm` | Ironsand Desert | 69 | 40 | - |
| `out05.odm` | Garrote Gorge | 71 | 32 | - |
| `out06.odm` | Shadowspire | 102 | 32 | - |
| `out07.odm` | Murmurwoods | 62 | 32 | - |
| `out08.odm` | Ravage Roaming | 80 | 42 | - |
| `out13.odm` | Regna | 96 | 17 | - |
| `pbp.odm` | Plane Between Planes | 17 | 3 | - |
| `d05.blv` | Abandoned Temple | 61 | 33 | t65a05bl t65a05br t65b11b t65b11c |
| `d06.blv` | Pirate Outpost | 60 | 22 | - |
| `d07.blv` | Smuggler's Cove | 33 | 3 | - |
| `d09.blv` | Merchant House of Alvar | 36 | 12 | - |
| `d10.blv` | Escaton's Crystal | 14 | 6 | gcrysc1 gcrysc2 gcrysc4 gcryswal |
| `d11.blv` | Wasp Nest | 6 | 1 | - |
| `d12.blv` | Ogre Fortress | 25 | 3 | - |
| `d14.blv` | Cyclops Larder | 43 | 9 | - |
| `d16.blv` | Dragon Hunter's Camp | 40 | 7 | - |
| `d18.blv` | Naga Vault | 17 | 2 | - |
| `d19.blv` | Necromancers' Guild | 40 | 5 | - |
| `d20.blv` | Mad Necromancer's Lab  | 34 | 2 | - |
| `d21.blv` | Vampire Crypt | 26 | 1 | - |
| `d22.blv` | Temple of the Sun | 12 | 1 | - |
| `d24.blv` | Balthazar Lair | 42 | 29 | - |
| `d25.blv` | Barbarian Fortress | 30 | 2 | - |
| `d26.blv` | The Crypt of Korbu | 18 | 4 | - |
| `d28.blv` | Tomb of Lord Brinne | 18 | 2 | - |
| `d29.blv` | Castle of Fire | 19 | 1 | - |
| `d30.blv` | War Camp | 17 | 5 | - |
| `d32.blv` | Abandoned Pirate Keep | 39 | 3 | - |
| `d34.blv` | Small Sub Pen | 14 | 2 | - |
| `d37.blv` | Prison of the Lord of Fire | 11 | 2 | - |
| `d40.blv` | Uplifted Library | 23 | 1 | - |
| `d43.blv` | Ancient Troll Home | 14 | 2 | - |
| `d44.blv` | Grand Temple of Eep | 39 | 2 | - |
| `eleme.blv` | Plane of Earth | 26 | 1 | - |

776 textures, 60 maps use them, minimum cover 40 maps
