# Solo talent sounds

Sounds of the MAW solo run's talents (`devdocs/solo_action/TALENT_TREE_V2_BUILD.md`), played by name.

| File | Plays | Source |
| --- | --- | --- |
| `talent_cleave.wav` | Cleave, once per monster struck, at it (`useSoloTalent`) | the user's `CleaveTarget.ogg` (`level_generation/sounds/solo_talents_20261114/supplied/`), converted to WAV |
| | | (the ElevenLabs take stays in that folder's `out/talent_cleave/`) |
| `talent_charge.wav` | Charge, as the dash starts (`useSoloTalent`) | ElevenLabs, `level_generation/sounds/solo_talents_20261114/jobs.yml` |
| `talent_blink.wav` | Blink, where the party arrives (`queueTalentMovePresentation`) | the user's `569766.ogg` (`supplied/`), converted to WAV |
| `talent_cheat_death.wav` | Cheat Death saving the solo (`MawCombatRules`) | the same |
| `talent_power_shot.wav` | Power Shot, with the ordinary bow shot as the arrow leaves (`useSoloTalent`) | made by script from `shoot bow01.wav` and synthesis: `level_generation/sounds/power_shot_20261116/make_power_shot.py` (take in its `picks.yml`) |

| `talent_challenge.wav` | Challenge, as it is used (`useSoloTalent`) | ElevenLabs, `level_generation/sounds/solo_archetypes_20261118/jobs.yml` (2026-11-18; the automatic pick, not yet listened to) |
| `talent_heroic_strike.wav` | Heroic Strike, at its blow (`useSoloTalent`) | the same |
| `talent_demoralizing_shout.wav` | Demoralizing Shout, as it is used (`useSoloTalent`) | the same |

The user's first Cleave and Charge sounds (`CleaveTarget.ogg`, `568712.ogg`) are kept in that folder's `supplied/`;
installing one is a conversion to WAV under the same name (`ffmpeg -i <file>.ogg -acodec pcm_s16le <name>.wav`).
Another take of a generated sound: `choice: vN.wav` in the folder's `picks.yml`, then `process` and copy.
