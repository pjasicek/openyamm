# MM9 ambient sounds: consistency of interiors (findings, 2026-11-08)

Findings only; nothing here is implemented. The user asked whether a tavern should have ambient sound (Sturmford City's
is silent) and whether taverns, shops and other places are consistent. Companion to
[MM9 ambient sound and music](MM9_AMBIENT_AUDIO_RE.md) and [MM9 ambient volume](MM9_AMBIENT_VOLUME_RE.md); the engine's
side is [placed ambient sounds](../AMBIENT_SOUNDS.md).

## Method

Every tavern, shop, temple, bank, library and training hall of the seven cities, Bootcamp (Ravensford), Lindisfarne,
Yorwick and the Isle of Ashes, found from the shopkeepers in our scenes (their RUDE id against the vendor and service
tables), MM9's zones (`Tavernzone` and the like) and the forge and anvil props; for each, every placed sound
(`ambient_sounds` of the scene, MM9's AmbientSound objects of the DAT) whose outer radius reaches it, fires included.
Scripts: `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/ambient2/`
(`dump.py`, `venues.py`, `anchors.py`; session scratch, not kept).

## The runtime is not at fault

At the reported spot (Sturmford City, -391 -486 19756, the tavern) nothing is in reach: the nearest of the scene's 29
sounds, a torch crackle, is 2 859 units away. A run at the city's church plays `ambient/people/monks chanting.wav`.
Listener (party + 160), switching (`AmbientSound<key>`, sprites, `start_on`), parsing and file lookup were checked; see
`game/audio/WorldAmbientSounds.cpp`. 25 of Sturmford City's 29 sounds are `ambient/torchlight.wav`, about 22 dB under
the music within a torch's 128-512 units, so the city sounds nearly silent everywhere; MM9's own DAT has only six
AmbientSound objects there (two birds, two chants, a dog, a tent flap).

## Consistency

| Kind | Total | With a fitting sound | Silent |
|---|---|---|---|
| Taverns | 9 | 2, `ambient/people/tavernambience.wav`: Arslegard City (DAT key 620), Thronheim City (925) | Sturmford City, Thjorgard City, Drangheim City, Frosgard City, Guberland City, Bootcamp, Lindisfarne (inside, or only outdoor birds, crickets, wind, waves, a bell) |
| Weapon and armour shops, smithies | 8 | 3 with anvil hammering: Arslegard (621, 622), Thronheim (926, 927), Guberland (756, day only, switched by two triggers, which our Lua does too) | Sturmford (a forge, 2 anvils), Thjorgard (2 forges, 2 anvils), Frosgard (forge, anvil), Drangheim (anvil; a torch only), Lindisfarne (anvil); Thronheim's own forge room is out of reach of its hammers |
| Temples | 8 | 5 with `monks chanting`: Sturmford (337, 338), Thjorgard (1009), Frosgard (665, 667), Guberland (755, day only), Thronheim's Fre's Hand (930; a ritual chant 929 at the pews too) | Arslegard's Temple of Fre (outdoor bells only), Drangheim's Fre's Touch (a bell), Thronheim's Ealusaid service |
| Magic shops | 9 | 1: Thronheim's Fre's Light (magic loop, 928) | the rest |
| Banks, libraries, general stores, apothecaries, training halls | about 35 | none, anywhere | all |
| City streets | 7 | each city its own mix; only Thronheim has a market crowd (924) | Sturmford's streets: a dog and a flag |

**No converter losses.** Every name in the build reports' `ambient_sounds_missing_files` is a file MM9's SOUNDS.REZ
does not hold (silent in MM9 too): `Ambient/bird01`-`bird17.wav` (MM9 ships `Ambient/Birds/birdsNN`; Sturmford City's
two birds and Drangheim City's three), `CanyonwindLoop.wav` (MM9 ships `WIND-CANYONLOOP`), `Spells/invisibiltiy/loop.wav`.
Everything else in the DATs is carried with its radius, volume and day/night setting. Every gap above is MM9's own.

## If the gaps are ever filled

Not MM9: per-map overrides (an overlay's `ambient_sounds`), not the converter. No occlusion, so an outer radius about
the room's size. Parameters copied from MM9's own placements of the same sound (scene units, LithTech x 2.56; volume
as the converter computes it):

| Sound | MM9's placement used | inner / outer | volume | play |
|---|---|---|---|---|
| `ambient/people/tavernambience.wav`, large tavern | Arslegard's Bar0 | 256 / 1536 | 0.315 | loop |
| the same, small tavern | Thronheim's Bar | 256 / 768 | 0.262 | loop |
| `ambient/hammer hitting anvil.wav` (or `… 02`) | Arslegard's Hammering0 | 256 / 1280 | 0.525 | wait 2-10 s; day only, as Guberland's |
| `ambient/people/monks chanting.wav` | Thjorgard's | 512 / 2048 | 0.367 | loop |
| magic loop | Thronheim's Fre's Light | 128 / 768 | 0.262 | loop |
| `crowdnoise-ambience loop 01` (a market) | | 256 / 1536 | 0.315 | loop |

Positions (native units). Taverns from MM9's tavern zone (the room's centre): Sturmford (-671, 128, 20009; the room is
about 1 460 x 2 690), Thjorgard (-1475, 819, 399), Drangheim (16663, -3128, 737), Bootcamp (2214, -3922, 1556),
Lindisfarne (-17632, -5852, 727); Frosgard (655, -3441, 374) and Guberland (-1782, -4301, 328) have no zone (the keeper
128 LithTech units up; check against the room). Anvils: Sturmford (82, 19374, 20086), Thjorgard (-164, 11510, 364),
Frosgard (8724, -3133, 407), Drangheim (19333, -2376, 732), Lindisfarne (-17483, -3156, 776), Thronheim's forge room
(3604, 3604, 3517). Temples: Arslegard (-328, -398, 614), Drangheim (15401, -7291, 870).

MM9 ships tavern-like files it never places: `ambient/people/taverncrowd.wav`, `barcrowd.wav`, `dining ambience.wav`;
`ambient/fire/fireplaceloop01`-`03.wav` are placed only as fires (inner 0, outer 300 / 200, full volume in Arslegard;
Klusos's House 80 / 320, volume 80). `ambient/interior/int_amb*` are MM9's dungeon room tones; banks, libraries and
stores have nothing in MM9 and are best left so.

## Also found: ambience against music

[MM9 ambient volume](MM9_AMBIENT_VOLUME_RE.md) "Against OpenYAMM" puts OpenYAMM's sounds 3.5 dB above music at the
default sliders, but leaves out the engine's music factor (`MusicVolume = 0.34`, `game/audio/GameAudioSystem.cpp`):
with it, MM9's ambience plays about 7 dB above the music at the default sliders (sound 3/9, music 2/9), against about
-2 dB in MM9. The ambience is louder against the music than in MM9, not quieter; matching MM9 exactly would mean a
lower `MM9_AMBIENT_MUSIC_BALANCE` in `ambient.py`. Not changed.
