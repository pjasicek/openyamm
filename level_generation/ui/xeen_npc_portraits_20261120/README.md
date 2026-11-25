# Xeen NPC portraits, batch 1 (2026-11-20)

New portraits in the MM7 NPC portrait style for every NPC of the Xeen town files
`assets_dev/worlds/xeen/source/towns/x1.yml` (ids 4001-4052, 50 NPCs) and `x2.yml` (ids 4101-4155, 55 NPCs):
105 portraits, all installed as `assets_dev/worlds/xeen/icons_x2/npc<10000 + id>.png` (126x146, opaque RGBA, 0644).
Per the user's decision of 2026-11-20 they are generated new; Xeen's own face sprites were not used.

Review: [review/contact.png](review/contact.png) (all 105 installed portraits, labelled by NPC id).

## Method

1. `descriptions.yml`: one visual line per NPC, written from name, title, profession and greeting.
2. `refs/ref_a.png`, `refs/ref_b.png`: 3 x 4 grids of 24 real MM7 portraits (`assets_dev/worlds/mm7/icons_x2/`
   npc0536, 0537, 0529, 0535, 0530, 0917, 0890, 1516, 0960, 0791, 0591, 0894 and npc0574, 0815, 0525, 0682, 0797,
   0822, 0570, 0892, 0770, 0761, 0874, 0916), Lanczos x2.4 on white gutters, matching the requested sheet layout.
3. `sheets.yml` assigns the NPCs to sheets; `make_prompts.py` writes `prompts/<sheet>.txt` from it.
   `gen.py <sheet> <version>` runs one `codex exec` worker per sheet (the worker pattern of
   `level_generation/ui/mm9_town_portal_20261108/gen.py`: one built-in image_gen call with both reference sheets,
   the PNG copied unchanged to `raw/<sheet>_v<version>.png`, log beside it). At most two workers ran at once.
4. `extract.py` finds the white gutters actually present in a sheet (all ten sheets: found, no nominal fallback),
   trims each cell, crops it to 126:146 at full height, applies a 5 px median at sheet resolution (about 2 px at the
   target: smooths skin and cloth texture towards the waxy MM7 renders) and a 10 % saturation lift, and resamples
   to 126x146 with Lanczos.
5. `install.sh` cuts the accepted sheets into `assets_dev/worlds/xeen/icons_x2/`; `contact.py` makes the review sheet.

Rerun: `./install.sh` then `python3 contact.py review/contact.png 15 1 ../../../assets_dev/worlds/xeen/icons_x2/npc1*.png`.

## Sheets (10 codex calls)

| Raw sheet | Used | NPCs in reading order (3 columns x 4 rows) |
|---|---|---|
| `raw/sheet01_v1.png` | no (first prompt, 4 x 3 landscape: loose framing, too photographic) | 4001-4013 |
| `raw/sheet01_v2.png` | yes | 4001 4002 4003 / 4004 4005 4006 / 4007 4008 4009 / 4011 4012 4013 |
| `raw/sheet02_v1.png` | no (as sheet01_v1) | 4014-4026 |
| `raw/sheet02_v2.png` | yes | 4014 4015 4016 / 4018 4019 4020 / 4021 4022 4023 / 4024 4025 4026 |
| `raw/sheet03_v1.png` | yes | 4027 4028 4029 / 4030 4031 4032 / 4033 4034 4035 / 4036 4037 4038 |
| `raw/sheet04_v1.png` | yes | 4039 4040 4041 / 4042 4043 4044 / 4045 4046 4047 / 4048 4049 4050 |
| `raw/sheet05_v1.png` | yes | 4051 4052 4101 / 4102 4103 4104 / 4105 4106 4107 / 4108 4109 4110 |
| `raw/sheet06_v1.png` | yes | 4111 4112 4113 / 4114 4115 4116 / 4117 4118 4119 / 4120 4121 4122 |
| `raw/sheet07_v1.png` | yes | 4123 4124 4125 / 4126 4127 4128 / 4129 4130 4131 / 4132 4133 4134 |
| `raw/sheet08_v1.png` | yes | 4135 4136 4137 / 4138 4139 4140 / 4141 4142 4143 / 4144 4145 4146 |
| `raw/sheet09_v1.png` | cells 1-9 | 4147 4148 4149 / 4150 4151 4152 / 4153 4154 4155 / (4153 4154 4155 second takes, unused) |

Prompts: `prompts/sheet01_v1.txt` and `prompts/sheet02_v1.txt` are the first prompt (4 x 3 landscape, sent with
4 x 3 versions of the reference grids, since rebuilt as 3 x 4); `prompts/sheetNN.txt` is the prompt of every
accepted sheet. The prompt asks for a 2:3 sheet of 3 x 4 cells on white gutters, the MM7 pre-rendered 1999 CG look
(smooth plastic-like skin, Gouraud-style shading, simple modelled hair), the MM7 close crop (face about two thirds
of the cell width, head touching the top edge, chin at three quarters), its own soft background per cell, no text,
then the twelve numbered descriptions from `descriptions.yml`.

## Notes and weak points

- Every NPC got an accepted portrait on the first pass of the final prompt; no retry sheet was needed.
- The look is cleaner and more detailed than real MM7 renders (modern image model): the median pass narrows the gap
  but they still read slightly richer than MM7 beside it. Acceptable for a first batch; consistent within the set.
- 4151 Barok (human sorcerer) came out with slightly pointed ears.
- 4155 Ligono (the ghost) is a little more painterly than the rest; 4048 the Spring Druid reads as a young man.
- 4028 Vern has a feather behind his ear instead of a quill (reads the same at 126x146).
- The two Kettles, Mudds, Ladles and Fletchers are drawn as separate people, not visibly related.

## Batch 2 (2026-11-20, A4 second session)

99 portraits: the two fixes, the twelve Act II people fixed ahead of their maps, and every NPC of the Act II town
files (`x3.yml`, `x4.yml`, `x5.yml`, `x6.yml`, `xd07.yml`, `xd13.yml`, `xd02.yml`), all installed. Review:
[review/contact_batch2.png](review/contact_batch2.png); [review/contact.png](review/contact.png) now holds all 202.
Same method and prompt head as batch 1; `make_prompts.py` now takes sheet names, so accepted prompts stay as sent.

| Raw sheet | Used | Notes |
|---|---|---|
| `raw/sheet10_v1.png` | all but 4201 | 4151 Barok with human ears (hidden by hair), 4048 the Spring Druid about seventy; 4201 Ebenezer came out with elven ears |
| `raw/sheet11_v1.png` … `sheet17_v1.png` | yes | 4201 (round ears, under a hat), 4304, 5701, then the Act II towns in `sheets.yml` order |
| `raw/sheet18_v1.png` | 4283, 4284, 4332 | the rest are second takes, not used; 4332 Sarah Slither's second take has the clearer snake eyes |
| `raw/sheet19_v1.png` | no | a 2 x 3 grid: the worker copied faces from the reference sheets |
| `raw/sheet19_v2.png` | cells 1-2 | 4601 the Summer Druid, 4602 Saul (X6); the 3 x 4 grid of six takes each |

Weak points: the gnomes (4210-4212, 4524, 4525) have pointed ears, as gnomes may; 4528 Thickbark is a tree face.
The 2 x 3 grid failure says: keep the 3 x 4 grid that matches the reference sheets.

## Batch 3 (2026-11-20, A4 second session): the Darkside towns

122 portraits for `d1.yml`, `dd03.yml`, `d2.yml` and `d3.yml` (Castleview, Castle Kalindra, the sprites, Sandcaster,
the Crossroads), all installed: sheets 20-29 in full, and from `raw/sheet30_v1.png` 5246 Thaddeus, 5247 Cornelius
and the second take of 5106 Nibbler (more monkey than dog); its other cells are unused second takes. Review:
[review/contact_batch3.png](review/contact_batch3.png); `review/contact.png` holds all 324.

## Batch 4 (2026-11-20, A4 third session): Rivercity's sorceresses and the phase 4-6 towns

71 portraits for X2's sorceresses (4156, 4157), `d4.yml` Lakeside, `d6.yml` Necropolis, `d7.yml` Olympus, `dd25.yml`
Bosco's Hall, `d5.yml`, `xd17.yml` Shangri-La, `xd18.yml` and `fd04.yml`, all installed: sheets 31-35 in full and the
first eleven cells of sheet36 (its last cell, a second take of 5309 Sir Malvern, is not used). Every sheet passed on
the first take. The dragons (5451, 5702, 5703), Stumpy the tree (4718) and Lacey the unicorn (4719) are head
portraits, as described. Review: [review/contact_batch4.png](review/contact_batch4.png); `review/contact.png` holds
all 395.

## Batch 5 (2026-11-20, A4 fourth session): X6's Sphinx Wells, the Warzone coachman, Sablewing again

Six portraits from `raw/sheet37_v1.png` (first take; cells 7-12 are near-identical second takes, not used):
4603 Hadda, 4604 Oskar, 4605 Gorm, 4606 Old Ibb, 4607 Tansy (`x6.yml`) and 4720 Sablewing, whom D-5.2 moved from the
Desert of Doom to X7's volcanic south slope (old id 5451 retired; this take, on a volcanic slope, replaces sheet35's
desert one). Review: [review/contact_batch5.png](review/contact_batch5.png); `review/contact.png` holds all 400.

## Batch 6 (2026-11-20, A4 fourth session): A3's quest and story people

Eleven portraits from `raw/sheet38_v1.png` (first take; cell 12, a second take of the Dragon Pharaoh, not used):
4955 Gettlewaithe, 4956 Joe the Mapmaker, 4957 Valio the Simple (`d1.yml`), 5109 the Master Thief, 5110 Hobstadt
(`d2.yml`), 5317 Slibo, 5318 Naomi (`d4.yml`), 5453 the Dragon Pharaoh (`d5.yml`), 5512 Ambrose, 5513 Corak
(`d6.yml`), 4608 Arie (`x6.yml`). Review: [review/contact_batch6.png](review/contact_batch6.png); `review/contact.png`
holds all 411.

## Batch 7 (2026-11-20, A4 fifth session): A3's promotion and quest people

Three portraits from row 1 of `raw/sheet39_v1.png` (four takes of each; rows 2-4 not used): 4530 Shinobu, the ninja
clan master's heir in XD-22's cellar (`x5.yml`, T2-CLAN), 5319 Leafpoint the tree and 5320 Ector the Woodsman
(`d4.yml`, T2-LEAFPOINT, Q-D21). Review: [review/contact_batch7.png](review/contact_batch7.png); `review/contact.png`
holds all 414.

## Batch 8 (2026-11-20, A4 sixth session): D-26's Felix and Carl, D-27's DD-09 prisoners

Six portraits from rows 1-2 of `raw/sheet40_v1.png` (first take; rows 3-4 are second takes, not used): 4958 Felix the
Tinker (`d1.yml`, DD-01), 5014 Carl the Mason (`dd03.yml`, Castle Kalindra's kitchen), 5111 Nathan, 5112 Sky,
5113 Snog the orc and 5114 Alicia the Just (`d2.yml`, DD-09's pens and cells). Review:
[review/contact_batch8.png](review/contact_batch8.png); 420 portraits in all.

## Batch 9 (2026-11-20, A4 seventh session): Picard the Aged

One portrait, cell 1 of `raw/sheet41_v2.png`: 5704 Picard the Aged (`fd02.yml`, FD-02's Home of the Aged, M40).
`raw/sheet41_v1.png` is not used: its prompt repeated one description twelve times and the worker drew twelve
unrelated people (`prompts/sheet41_v1.txt`); v2 gave four wordings of him (variant ids 95701-95703 in
`descriptions.yml`, not NPCs), three takes each. 421 portraits in all.

## Batch 10 (2026-11-20, A4 ninth session): Tern

One portrait, cell 1 of `raw/sheet42_v1.png`: 5321 Tern, Ferris Gull's mate, who rows the party back from the Isle of
Lost Souls (`d4.yml`, house 4667, D-36 (6)). Same method as batch 9: four wordings of him (variant ids 95321-95323 in
`descriptions.yml`, not NPCs), three takes each; cells 5 and 9 are near copies of cell 1. 422 portraits in all.

## Batch 11 (2026-11-20, A4 tenth session): Varro

One portrait, cell 1 of `raw/sheet43_v1.png`: 4609 Varro, the Arena Master behind XD-20's booth windows (`x6.yml`,
D-39): bald, a scar through one eyebrow, a black-grey moustache and a hard grin, a studded leather harness, an arena
wall with red banners behind. Same method as batch 10 (variant ids 94691-94693, not NPCs), but the worker drew a 4x4
grid of the four wordings, so `extract.py --grid 4x4`. 423 portraits in all.

## Batch 12 (2026-11-20, A4 eleventh session): Blastem

One portrait, cell 1 of `raw/sheet44_v1.png`: 5248 Blastem the Wizard, DD-19's talking wizard in the Guild Common
(`d3.yml`, D-42 Q5): gaunt and sneering, a tall purple hat, a pointed grey beard, gold sigils on a black-and-violet
collar, a candlelit guild library behind. Same method as batch 10 (variant ids 95248-95250, not NPCs), the default
3x4 grid. 424 portraits in all.

## Batch 13 (2026-11-21, A4 thirteenth session): Alister

One portrait, cell 1 of `raw/sheet45_v1.png`: 5705 Alister the Druid, the fraud in FD-04's gate hall who takes the
Dragon Egg and drinks his egg potion (`fd04.yml`, D-57 Q27): a round eager face with a toothy smile and darting eyes,
a greying scruffy beard, an oak-leaf wreath, a moss-green hooded robe with a green potion vial on a rope cord, black
volcanic stone lit red behind. Same method as batch 12 (variant ids 95705-95707, not NPCs), the default 3x4 grid.
425 portraits in all.

## Batch 14 (2026-11-21, A4 fourteenth session): Cyrano Jones

One portrait, cell 1 of `raw/sheet46_v1.png`: 5614 Cyrano Jones the Salesman, who keeps Pets Unlimited in DD-26
Olympus Sewer and sells the Tribble (`dd26.yml`, D-65 Q57): a plump ruddy face with a broad salesman's grin, dark
curls greying at the temples, a purple coat with gold braid and a lace ruffle, a tan furball on his shoulder, marble
pillars and a lamp behind. Same method as batch 13 (variant ids 95614-95616, not NPCs), the default 3x4 grid.
426 portraits in all.

## Batch 15 (2026-11-21, A4 sixteenth session): Sparrow

One portrait, cell 1 of `raw/sheet47_v1.png`: 4158 Sparrow the Pit Fighter, Rivercity's teacher of Dodging and
Unarmed Expert in Martial Training beside Flint (`x2.yml`, D-73): a wiry woman about thirty-five, a sharp face with a
sly half-smile and a scar through one eyebrow, short dark hair, a faded red sleeveless vest, straw dummies in a wooden
hall behind. Same method as batch 14 (variant ids 94158-94160, not NPCs), the default 3x4 grid. 427 portraits in all.

## Batch 16 (2026-11-25, agent xeen-fb4-town): the goblin-eared boy, Rudd, Marla

Three portraits from row 1 of `raw/sheet48_v1.png` (one Codex worker, the default 3x4 grid of `sheets.yml`'s
`sheet48`: four rows of the three): 4053 the Goblin-eared boy, the half-turned child in XD-04's cage 1 (`x1.yml`,
D-155: a freckled sulking boy with large green goblin ears, cage bars and green candlelight behind), 4054 Rudd, Nystor's
mate at Vertigo's creek landing (`x1.yml`, D-150) and 4346 Marla, his river pilot at X4's upriver landing (`x4.yml`,
D-150). The worker drew unrelated new faces in rows 2-4 instead of second takes: not used. Review:
[review/contact_batch16.png](review/contact_batch16.png). 430 portraits in all.
