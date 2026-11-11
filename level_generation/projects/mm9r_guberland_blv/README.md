# Guberland (MM9 rework, region BLV)

`convert.py` builds MM9's GUBERLAND.dat as a BLV open to the sky (the shared part is `../mm9r_common/outdoor_blv.py`);
`regionlua.py` writes the region's scripted objects as map Lua (its docstring lists them; the script behaviour is
`work/scr_spec.md`).

## Cinematics

`newgame_talk` (`guberland.cinematics.yml`, built by `regionlua.scenes()`, installed by `convert.py`): Scandlan the
Long-tounged's and Broccan A'Norta's street talk (NPC150.scr :OnStart..:OnSpeak12, NPC151.scr), an **ambient**
cinematic (no camera, letterbox or input lock: MM9 plays it while the party walks about). Scandlan's FoundPlayer event
(56047 = 56000 + his DAT index, raised when he first perceives the party) starts it without key 5020.

- Timing: the scripts' fixed waits (not the wav lengths): Scandlan 01 at 0, Broccan 02 at 6.5, 03 7, 04 20.3, 05 20.8,
  06 39.3, 07 40.3, 08 47.3, 09 47.8, 10 60.3, Scandlan 11 61.3, :Trigger12 at 69.8, Scandlan 12 at 70.8 s (its wav
  ends at 78.7 s). Cues: the twelve voices (`voices\cinema\newgame\NN.wav`), each speaker's Loopanim conv clip
  (Scandlan conv2/4/5, Broccan conv1; neither OnStop resets the animation, so each loops his last clip), both facing
  each other (`target`). No subtitles (MM9 has no text for the lines).
- Steps (events 36001-36002, done 36000): `key` (5020) at 0; `walk_away` at 69.8 s: Broccan's :OnWalkAway (WalkTo
  Mata, CommonerHalfOrcMaleA0), `evt.MoveActorTo` to 100 units short of Mata. Not carried: his BaseWander after the
  walk and on loads with key 5020 (NPC151.scr :OnWander; he is placed immobile here and stands where the walk ends).
- Test without a conversion: `python3 cinematics_pilot.py` (scratch root `output/mm9_rework/cinematics_pilot_root`),
  then from `output/mm9_rework/cinematics_pilot_run`: `build/game/openyamm --world mm9 --headless-run-scenario
  <abs>/cinematic_newgame_talk_play.yml` and `..._skip.yml`. Captures: `captures_newgame_talk/sheet.jpg` there
  (`tour_newgame_talk.yml`).

## The stones game and whack-a-honky (2026-11-06)

`regionlua.py` `stones_game()` and `whack_a_honky()`: Thjorgard's implementation (mm9r_thjorgard_blv) with Guberland's
win keys (stones 7110, honky 7113) and its prize (`gameWon`: 7116 and a random prize 362-367). Piece0-35 and Honky0-3
click events and SetSprite keys 700-739; Switch0 is a `rotate` mover (overrides.yml) whose click (event 104) starts
the geese. Test: `scenario_games.yml` (whack-a-honky won, a stones game won by sweeping the board).

2026-11-06 evening: BanditAttack.scr carried (regionlua.py): the 3:30 bandits run from SpawnMarker to Atlimarker0
(`evt.MoveActorTo`, run) and stop to fight once they see the party (`evt.ActorSeesParty` on the watch's poll, then
`evt.SetActorTarget` party), or at the marker; a load sends the runners on. Checked with a scratch scenario (a Bandit
summoned at SpawnMarker runs toward the marker, sees a party on its way, turns on it). The sea (BlueWater0, 90 pieces)
reports 1 423 bed-hole samples in build_report.json `water` (the far sea past the near box has no seabed; the near
box is swum, as before).
No `scenario_swim_check.yml` here: `swim_check.py` picks its points from the DAT floors, and the deepest sea pieces lie in
the far sea, whose seabed the BLV does not build (a party set there sinks past -819 to -920); the near box's piece passes.

## Mata's cower (2026-11-11)

`ArmWrestle.scr :StartCower` after a won game: `cowerstart`, `cower` five times, `cowerstop`, his game's use removed
until it ends (5.4 s, runtime only). His click opens his dialogue too (DoRude 1), and while it is open he stands for
it: the cower shows once the dialogue closes (capture `output/held_items_check/b3_cower/gub3_sheet.png`).
`scenario_games.yml` and `scenario_lifecycle.yml` pass.
