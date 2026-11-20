# Afterworld (MM9 rework)

The region as a BLV open to the sky: `convert.py` (the shared `../mm9r_common/outdoor_blv.py`), Skraelos' Six Fires of
Penance in `regionlua.py`.

## Cinematics

`afterworld_guilt` (afterworld.cinematics.yml; devdocs/mm9_rework/MM9_CUTSCENES.md): SixFires.inc :Guilt.
`regionlua.py scenes()` builds it and the conversion writes both its Lua and its yml (`extend`, `cutscenes.install`).

- Trigger: Skraelos' dialogue exit (NPC336.scr :OnRude, event 50094) with key 380 and not 381 calls
  `MM9Cinematic.start("afterworld_guilt")` (`GUILT_LINES`); the other fires' branches are unchanged.
- Timeline (13.4 s): Camera9 to AfterMarker0 at 100 LT/s (AfterWorldCam1.scr, 10.4 s), its arrival (:OnDone): key 381
  and quest.wav, fade out 2 s (:End), then :FadeIn2's 1 s fade into the party's view and his greeting.
- Steps (events 36001-36002, done 36000): `done` (key 381), `greeting` (key 379, RUDE 336, his voice). Cues: the fades
  and quest.wav.
- Test without a conversion: `python3 cinematics_pilot.py` (the yml and the installed Lua as the converter would write
  it, into output/mm9_rework/cinematics_pilot_root), then from output/mm9_rework/cinematics_pilot_run
  `build/game/openyamm --world mm9 --headless-run-scenario <abs>/cinematic_afterworld_guilt_play.yml` (and
  `_skip.yml`). Captures: that directory's `tour_afterworld_guilt.yml`, `captures_afterworld_guilt/`.

## The Six Fires (2026-11-06)

`regionlua.py` `populate()` (called from the shared `outdoor_blv.py` populate) places GuiltFire .. RebirthFire (Fire
objects with On 0) as `mm9_gatefire_x8` with SetSprite keys 420-425; `sixFires()` shows each once its stage is done
(381, 383, 491, 387, 389, 391), on load, after Skraelos' click and exit and Forad Darre's death. MM9 never lights
GuiltFire (no script names it); here it lights with 381. Their lights and sounds are not placed. Test:
`scenario_fires.yml`.
