# MM9 player-character voices (2026-11-08)

MM9's party members speak with MM9's own voices (the user: "they SHOULD be used, for the new PCs"), not with the
MM6-MM8 voice sets the MM9 portraits borrowed before.

## MM9's voices

`mm9/extracted/VOICES/VOICES/PC/`: 18 voice sets, seven personalities and two lich voices, female and male, numbered by
MM9's `getPCVoice` (FATEMAN.scr :Init): female Angry, Arrogant, Assertive, Cowardly, Dim, Happy, Sarcastic, Lich,
Half-Orc Lich 0-8, male the same 9-17. MM9 picks the personality at character creation; it is not tied to the face.

`mm9/extracted/DATA/DATA/PCVOICES/<SET>.txt` lists each set's 42 lines (the same text in every set), up to three takes
each. It is the authority: file numbers differ between sets. Quirks: the ArrogantF table spells its files `Arrrogant`;
eight listed files are not shipped (AngryF18a, AngryF29a, AngryF31a, DimF15d, DimF26c, SarcasticF34c, AngryM29a,
HappyM04a); some shipped files are listed nowhere. 1 370 takes in all.

## In OpenYAMM

`tools/mm9_import_discovery/generate_mm9_pc_voices.py` (`--check` to verify):

- converts every listed take to IMA ADPCM WAV, 22 050 Hz mono (the engine's own voices' format; MM9's are 16-bit PCM at
  the same rate): `worlds/mm9/audio/voices/pc/<set>/<file>.wav`, 27 MB against MM9's 97 MB;
- writes `worlds/mm9/data_tables/pc_voice_sounds.txt` (ids 55000 + 200 x set + 3 x line + take, inside MM9's sounds range
  50000-59999), a second `sounds` contribution in `worlds/mm9/world.yml`;
- writes the sets as columns 79-96 of `engine/data_tables/character_voices.txt` (79 + MM9's number). Each MM9 line feeds
  the sound types of the matching speech (`character_speech_events.txt`); a third take gets a row of its own under the
  group's last type name, in a block between the table's first blank line and its `Man` row, with the sets' `Name`
  (Angry ...) and `World` (mm9) rows; the `Man`, `Woman`, `Undead Man`, `Undead Woman` rows mark their sex.

| MM9 line | Sound types |
|---|---|
| disarmed the trap / the store is closed / the trap went off | Disarmed / Closed / FailedDisarm |
| pick this character voice (missing in Lich F, Lich M, Half-Orc Lich F: their hellos instead) | ChooseMe |
| weak / strong / can't identify item; repaired / can't repair | BadItem / GoodItem / CantIdent; Repaired / CantRep |
| an easy kill / a tough opponent / can't identify this monster | WeakMonster / BigMonster / CantIdMon |
| spell is ready | QuickSpell |
| was hit (two lines) / time to go get healed / was killed | SoftInjure1 / HardInjured / Dying |
| drank too much, insane, poisoned, cursed / Whoa! | Drunk, Insane, Poison, Cursed / Fall |
| not safe to rest / not enough gold / the door is locked | CantRestHere / NeedMoreGold / NeedAKey |
| learned a spell / can't learn it / can't wield that weapon | LearnSpell / CantLearn / CantEquip |
| Hello (two lines) / Good evening | Hello1-4 / Hello5-6 |
| killed a powerful / a weak monster / left alone | Win! / Heh / LastStanding |
| entered a new dungeon / Yes / How rude! / Thanks / Shhh / Get out of the way! | Enter / Yes / Indignant / Thanks / n/uShutUp / Move! |
| can't talk, danger nearby; No | none (no OpenYAMM speech) |

No MM9 line for Hungry, InventoryFull, PotionMixed, FailMixing, Leave: an MM9 voice stays silent there. `Yes` and
`ThankYou` reactions have no sound types in `character_speech_events.txt` for any voice (MM6-MM8 included), so MM9's
Yes and Thanks lines are in the table but not played; giving those reactions sound types would make every world's
voices speak in dialogues and shops (a separate decision).

## Portraits and party creation

`character_data.txt` gives the MM9 portraits MM9 voices: 9001 Assertive M, 9002 Assertive F, 9003 Arrogant M, 9004 Happy
F, 9005 Sarcastic M, 9006 Arrogant F, 9007 Happy M, 9008 Sarcastic F, 9009 Angry M, 9010 Angry F, 9011 Dim M, 9012 Dim
F, 9013 Cowardly M, 9014 Cowardly F, 9015 Happy M, 9016 Assertive F; the liches 9019/9023 Lich M, 9020/9024 Lich F
(which lich portraits are MM9's half-orc liches is not known: the Half-Orc Lich voices are offered, not defaults).

The voice picker (`NewGameScreen::availableVoiceIdsForSelectedCandidate`) offers an MM9 face every MM9 voice of its sex
(the lich voices for a lich face) and only those, labelled by name (`voiceLabel`, `Engine::localize(name, "voice")`);
other faces keep their offer (the voices of offered portraits of their race and sex) without MM9's. The table's
`World` row, read by `MergedCharacterVoiceTable::voiceSetsOfWorld` / `voiceSetProperty`, decides.

MM9's voices are world sounds: they play wherever the MM9 package is mounted (every world's audio is indexed together),
so an MM9-voiced character keeps its voice in MM6-MM8 maps.

## Not done

- A character who becomes a lich takes the lich portrait's voice (`Party.cpp`), an MM6-MM8 one for an MM9 face.
- The Arslegard `gate_fate` cutscene always plays the Assertive Male lines (MM9 chooses by the speaker's voice:
  `voices/cinema/<Personality><Sex>/`).
- Existing saves keep their characters' voices.
