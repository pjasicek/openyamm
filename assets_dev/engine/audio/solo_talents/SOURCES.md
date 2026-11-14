# Solo talent sounds

Sounds of the MAW solo run's talents (`devdocs/solo_action/TALENT_TREE_V2_BUILD.md`), played by name.

| File | Plays | Source |
| --- | --- | --- |
| `talent_cleave.wav` | Cleave, at the blow (`useSoloTalent`) | ElevenLabs, `level_generation/sounds/solo_talents_20261114/jobs.yml` |
| `talent_charge.wav` | Charge, as the dash starts (`useSoloTalent`) | the same |
| `talent_cheat_death.wav` | Cheat Death saving the solo (`MawCombatRules`) | the same |

The user's first Cleave and Charge sounds (`CleaveTarget.ogg`, `568712.ogg`) are kept in that folder's `supplied/`;
installing one is a conversion to WAV under the same name (`ffmpeg -i <file>.ogg -acodec pcm_s16le <name>.wav`).
Another take of a generated sound: `choice: vN.wav` in the folder's `picks.yml`, then `process` and copy.
