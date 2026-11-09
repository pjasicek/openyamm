# Yorwick (MM9 rework)

The region as a BLV open to the sky: `convert.py` (the shared `../mm9r_common/outdoor_blv.py`), its scripted objects in
`regionlua.py`, its props in `props.json` (`level_generation/props/mm9_outdoor_regions_claude/scripts/placements.py`).

## Cinematics

`battlefield_sven` (yorwick.cinematics.yml; devdocs/mm9_rework/MM9_CUTSCENES.md): Svenspeech.scr's battlefield speech.
`regionlua.py scenes()` builds it and the conversion writes both its Lua and its yml (`extend`, `cutscenes.install`).

- Trigger: the map's load (Svenspeech.scr :Init) with key 95 and not 97 calls `MM9Cinematic.start("battlefield_sven")`.
  SvenShowTake.inc's tableau (the guard, Kira, the fallen, the swords and arrows: one SetSprite key, 401) and Sven
  (overrides.yml `people`, row 9249, mm9_sven.glb) are shown only then; every other load hides them.
- Timeline (66.3 s): Camera0 to CameraMarker0 at 70 LT/s (3.9 s), Camera1 to Camera2 at 40 (7.1 s), Camera3 to Camera4
  at 10 (8.6 s), then Camera5 and Sven_scene06's keys (SVEN.abc, 43.7 s): Camera6 4.7 s, Camera7 20.6 s, Camera8
  33.2 s, sven01-04.wav at 0, 5.3, 20.3, 34.8 s; its FadeOut key, wait 1, fade out 1, :FadeOut2, a 1 s fade into the
  party's view. Arrivals are distance / speed; fov 73.7.
- Steps (events 36001-36003, done 36000): `start` (tableau and Sven shown, AmbientSound0-7 off), `award` (Sven04:
  key 97 and the balanced 114 000 experience), `finale` (ambient sounds on, tableau and Sven hidden under the fade).
  Cues: fades, voices, quest.wav, Sven facing Camera5 and playing Talk (looped).
- Not carried: Sven_scene06 itself (mm9_sven.glb has no such clip), the dead Bjarni (Kira0) and Tryggva (no dead
  figures: placements.py LEFT_OUT).
- Test without a conversion: `python3 cinematics_pilot.py` (writes the yml, the installed Lua as the converter would
  write it, and the scene with Sven added, into output/mm9_rework/cinematics_pilot_root), then from
  output/mm9_rework/cinematics_pilot_run `build/game/openyamm --world mm9 --headless-run-scenario
  <abs>/cinematic_battlefield_sven_play.yml` (and `_skip.yml`). Captures: that directory's `tour_battlefield_sven.yml`,
  `captures_battlefield_sven/`.

## Mary's sheep (2026-11-06)

MarySheep.scr / NPC312.scr :RuntoMe (`regionlua.py` `ewe()`): Ewe0 is an `outdoor.people` actor (row 9272; no longer in
`monster_classes`) so that its click runs event 53249. The click starts the follow (map var EweFollow 1): a half-second
timer (340) sends it after the party by `evt.MoveActorTo` (running when more than 1 200 units behind). Within 512 LT of
Mary it gives key 466 and runs to her (EweFollow 2); her "Here's your sheep" row then gives 467 and the exit pays 468.
It stands before the click and after (MM9: BaseWander, Cat.scr). Test: `scenario_sheep.yml`.
