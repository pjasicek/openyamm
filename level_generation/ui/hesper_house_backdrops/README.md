# Hesper house backdrops — 2026-10-24

Fourteen Codex-generated interiors cover all **33 houses and eight vendor venues** currently registered by
`hesper_stage/skills.yml` and `npcs*.yml` (the request's count of 25 predates the current inputs).
The Sim Hall has its own simulator interior. Every kind has two retained candidates and one selected master.
The provisions shop and the Last Lamp inn (9812, 9813) were added on 2026-10-24 with Landfall's keepers.

- [Selected artwork, at native media size](review/selected_sheet.jpg).
- [Candidates 1–6](review/candidates_1.jpg), [candidates 7–12](review/candidates_2.jpg) and
  [candidates 13–14](review/candidates_3.jpg) (provisions, inn).
- [Exact prompts, raw-return provenance, choices and hashes](generation_runs_house_backdrops.json).
- [Picture allocation, house membership, runtime files and capture events](backdrops.json).

`candidates/` preserves all 28 original imagegen returns. `selected/` contains fourteen **460×344** PNGs;
`runtime/` contains corresponding silent two-second, 25 fps Theora `.ogv` clips, looped by the existing player.
These are still backdrops, with no invented animation. Imagegen returned 1450×1085 / 1451×1084 masters despite the
native-size request; the export uses full-frame Lanczos downsampling, no crop or repaint. Selection reasons and
both original and export hashes are in the generation manifest. Generation used the built-in Codex image tool.

## How a house picture reaches the screen

1. `skills_stage.py` and `stage.py` put each house's numeric `picture` in **column 4** of the staged
   `engine/data_tables/house_data.txt`. Vendors are appended separately by `HouseTable::appendVendorRows`, so they
   must not also be inserted into `house_data`.
2. [`HouseTable.cpp`](../../../game/tables/HouseTable.cpp), `loadFromRows` / `normalizeVideoStem`, treats a numeric
   Picture cell as metadata, not a filename. `loadAnimationRows` joins **house id → animation id** in
   `house_animations.txt` to **animation id → filename stem** in `house_movies.txt`. Before this change, Hesper's
   numeric 16/27/46 cells had no Hesper animation rows; changing the numeric cell alone would still leave an empty
   video name. The old "generic picture 27" description did not describe a complete working lookup.
3. This package allocates **picture/movie ids 9800–9813**, checked against the native movie table. The stage appends
   fourteen movie rows and 41 animation rows to its **copied** engine tables. Existing native rows are preserved.
   Animation rows carry no native house voices, portrait overrides or resident lists; Hesper's existing NPC rows
   and `MoveNPC` gates remain authoritative. Vendors with `picture` use `HouseVideo` instead of `LiveGameplay`.
4. [`HouseVideoPlayer.cpp`](../../../game/audio/HouseVideoPlayer.cpp) reads
   `Videos/Houses/<stem>.ogv`. Hesper's world mount supplies these from
   `worlds/hesper/videos/Houses/hes_house_<kind>.ogv`. No icon registry, engine change or `assets_dev` write is needed.
5. [`GameplayDialogueRenderer.cpp`](../../../game/ui/GameplayDialogueRenderer.cpp), `renderDialogueVideoArea`,
   draws the player frame in `DialogueVideoArea`: **460×344 logical pixels**, x=8, y=28 in the dialogue layout.
   The portrait/sidebar is separate; dialogue can cover the lower media area. Art contains no people, text or UI.
   A missing frame falls back to a grey rectangle, making the movie join essential.

Native references inspected before generation: MM6 `blckspor`, `armrich`, `tavmid`; MM7 `human poor house 2`,
`wizard bank`, `wizard magic shop`; MM8 `demedhs`, `lwpshp`, `mwepshp`, from each world's `videos/Houses/`.
All nine decoded at 460×344. These are framing references only; no native pixels are included in the new artwork.

## Places and assignments

Read against `STARPORT_REACH.md`, `zone1/dungeons/UNDERVAULT.md`, `THE_SCOUR.md`, `BROOD_SPIRES.md` and
`THE_CROWN.md`, including their house/stall descriptions. Art references were `concepts/06_architecture_styles.png`,
`02_lowhold_undervault.png`, `05_the_crown_cannon_ring.png`, and `zone3/concepts/z3_07_acid_garden.png`.
Maintained Ancient white/gold colony rooms are distinct from the patched service-bay refuge and tarp shelters.
The Crown's two live venues are salvage/scout stalls: their booth interiors combine colony salvage with bone ribs
and violet resin. No unregistered Kreegan palace house was invented. The greenhouse view has warm grow lights,
pale fungi and rain-streaked glazing.

| Picture | Kind / chosen candidate | All registered houses and vendors | Tour map / event / house |
|---|---|---|---|
| 9800 | arms_workshop / 1 | 9201 Salvage & Arms; 9213 Edda's house; 9453 The Workshop | hes_out1.odm / 51 / 9201 |
| 9801 | emitters / 1 | 9202 Emitters; 9215 Fenna's house; 9216 Tove's house; 9217 Nim's house; 9218 Hollis's house | hes_out1.odm / 52 / 9202 |
| 9802 | civic_post / 1 | 9203 The Warden's Post; 9454 The Council Hall; 9459 The bounty board | hes_undervault.blv / 11 / 9454 |
| 9803 | sim_hall / 1 | 9204 The Sim Hall | hes_undervault.blv / 9 / 9204 |
| 9804 | colonist_home / 2 | 9211 Corra's house; 9212 Halder's house; 9214 Rusk's house; 9460 Venn's home; 9461 Brin's home; 9462 Cael's home; 9463 Dorra's home; 9464 Esk's home; 9465 Fael's home; 9466 Garna's home; 9467 Avel's home; 9468 Isra's home; 9469 Jorel's home; 9470 Kalla's home | hes_out1.odm / 57 / 9211 |
| 9805 | clinic / 1 | 9219 Yara's house; 9220 Teodor's house; 9452 The Clinic | hes_undervault.blv / 6 / 9452 |
| 9806 | archive / 2 | 9455 The Archive | hes_undervault.blv / 12 / 9455 |
| 9807 | guardian_chapel / 1 | 9456 The Guardian's Chapel | hes_undervault.blv / 13 / 9456 |
| 9808 | kept_refuge / 2 | 9457 The Kept Refuge | hes_undervault.blv / 14 / 9457 |
| 9809 | field_camp / 1 | 9300 Thrix's stall; 9301 Tarro's lean-to; 9458 Kesh's stall | hes_out2.odm / 301 / 9301 |
| 9810 | acid_garden / 1 | 9351 Wren's post; 9352 The farm store | hes_out3.odm / 303 / 9352 |
| 9811 | crown_market / 2 | 9400 Vesk's stall; 9401 Sorrel's stall | hes_out4.odm / 301 / 9400 |
| 9812 | provisions / 1 | 9450 Provisions (Mother Ama's shop) | hes_out1.odm / 53 / 9450 |
| 9813 | inn / 1 | 9451 The Last Lamp (the inn) | hes_out1.odm / 54 / 9451 |

The Warden's house row 9203 receives the civic picture, but its existing event 55 still speaks directly to the
Warden; this art task does not rewire that service. The capture uses the Council for the civic kind. Street actors
have no house row to change.

## Rebuild and checks

From the repository root:

```sh
flock -s output/hesper_stage/locks/stage.lock python3 -B level_generation/ui/hesper_house_backdrops/scripts/build_media.py
flock output/hesper_stage/locks/stage.lock python3 -B level_generation/projects/hesper_stage/stage.py
flock -s output/hesper_stage/locks/stage.lock python3 -B level_generation/ui/hesper_house_backdrops/scripts/check_backdrops.py
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

The shared scenario wrapper takes both stage and engine-build locks **shared**, starts minimized, and does not
rebuild maps. Media regeneration writes the stage's sources, so hold `stage.lock` shared around `build_media.py`
while other builders are active. Stage exclusively after it finishes.

Checks completed: stage assembly; all 39 house/vendor joins; native movie/animation rows byte-preserved; all 24
raw master hashes and twelve selected-export hashes; staged/source clip identity; 460×344 Theora streams, no audio,
full decode of every clip. See [media check](review/check_backdrops.log) and [scenario sweep](review/scenarios.log).
The complete second sweep passed **77/77**, exit 0, with both shared locks held throughout. The first sweep
passed 75; its final two launches failed with OS permission errors before scenario execution. Both focused retries
and the full repeat passed. See `review/checks.json` and the builder's report in `requests/P4.md`.

## Native capture handoff

The minimized desktop attempt prepared its isolated save successfully, then failed with
**`SDL_Init failed: No available video device`** before loading it. No native screenshots were captured and no GPU
renderer ran. The selected-art sheet is an artwork review, not an in-game capture. Inspect the final dialogue
compositing and video playback on the integrator's desktop:

```sh
python3 -B level_generation/ui/hesper_house_backdrops/scripts/capture_tour.py
```

This regenerates five `review/tour_hes_*.yml` menu-input tours, launches the authorized `tools/run_game.sh` wrapper
minimized under **both shared locks**, and opens fourteen representative houses through their real map events.
It uses private saves, noon opening hours and explicit review-only quest bits for gated venues. Each house settles
for two seconds before capture. The wrapper exits normally on tour completion; its 60-second limit is a fallback.
On success, all fourteen native shots and `review/desktop/sheet.jpg` are created. Check that each shot actually shows
its house, the art fills the media frame, text/portraits are legible, and the five game logs have no house-video
load/decode errors. [Failed attempt log](review/desktop_unavailable.log) records the sandbox limit.

No engine or map code, models, service prices, stock, quest rules or native assets were changed. No design edits
apart from the requested appended builder's report; no git staging or commits.
