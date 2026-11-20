# MM9 talk dialogue: study, 2 November 2026

The user's request: "check the mm9 'talk' dialogue menu/popup - it has blurred text and overall looks really bad
compared to rest of our UI. I want like 3 proposals how to make it better, how we should display it. taken into
account the amount of dialogue options it can have and the length it can have etc. so it fits our overall style best."

This is design work only. No engine code, layouts or `assets_dev/` content were changed. The mockups are static
HTML at 1600x900. They use real RUDE text, the faithful MM fonts and the staged Carved Obsidian art, drawn over
engine-native captures of Bjarni's hall in Sturmford City.

![Overview: A, B and C, typical and ten-choice states](previews/overview.jpg)

## Native implementation (2026-11-04)

The user chose **A, the conversation bar**, first shown with the basebar on. **Since 2026-11-06 a talk hides the
party** (see [the 2026-11-06 refinement](#refinement-2026-11-06-no-basebar-per-member-trainers-sharp-text)). It is in
the engine:

| 1600x900, eight choices | 4:3 | 1080p, after a choice |
| --- | --- | --- |
| ![](native/1600_eight_choices.png) | ![](native/1200_eight_choices.png) | ![](native/1920_echo.png) |

More: [entry](native/1600_entry.png), [long reply](native/1600_long_reply.png). Tour:
[`native/bjarni_tour.yml`](native/bjarni_tour.yml) (`debug.menu_input_tour_path`, the capture command below with
`--set video.resolution=1600x900`, `1200x900` or `1920x1080`).

- **Renderer and input**: `game/ui/GameplayMm9TalkBar.cpp` lays the bar out once for both. It replaced
  `renderMm9RudeDialogueOverlay` and the input's copy of the 800x600 canvas (the PCX fonts, `RUDEBG` and the six-row
  cap are gone). Sizes are the mockup's 1600x900 pixels scaled by the basebar's height, the way the potion and scroll
  popups scale. The panel is `GameplayUiSkin::renderPanel` (the shared frame pieces), not a separate 9-slice.
- **Text**: Fondamento name, Lucida place and hints, the party's last sentence quoted in Lucida (`EventDialogContent::echo`),
  the reply in Arrus, choices in Create; MM9's double spaces collapsed.
- **Rows**: the exit row last, on Esc; 1-9 and 0 choose the others (in a talk they no longer pick a party member); Up, Down and the wheel move the selection, Enter takes it. From seven rows, two columns. Marks
  come from `buildMm9RudeContent`: a gold diamond for a quest row (one that needs keys) not chosen yet, a check for a row
  chosen before (`Party::chosenMm9RudeRows`, saved since save version 146), a door for the exit (and the trainer's
  Back), blue tags for services ("Shop", "Train · Expert").
- **Height**: the panel stops at 47 % of the screen's height; past that the rows scroll with the selection, with small
  arrows. On Android and iOS the rows are 54 study pixels high and have no key caps.
- **No talk camera** (removed 2026-11-06 at the user's request): the view stays where the player left it. Instead the
  medallion shows the speaker's **live head and shoulders** from their model (`ActorModelPreview` with
  `ActorPortraitKind::Talk`, its own offscreen view `ActorTalkPortraitView`; framing from the skin joints named for the
  head, `WorldFxSystem::syncInspectPortrait`; standing and fidget clips only). The speaker is the actor the talk was
  opened on, else the nearest actor with the talk's RUDE id (`game/gameplay/Mm9DialogueSpeaker.cpp`). A speaker that
  is no actor (Bjarni Thorvaldssen is part of his throne prop) or has no model keeps the monogram. The same portrait
  fills the portrait frame of an MM9 shop's or venue's house sidebar.
- **Not done**: not yet checked on Android (the study expected the
  thumb groups to need hiding while the bar is open at 4:3).

### Refinement 2026-11-06: no basebar, per-member trainers, sharp text

The user's decisions of 2026-11-06, after checking which MM9 services need a party member picked during a talk (only
the skill trainers: shops, training halls, inns, banks and temples open the shared house screen with its own
portraits; promotions, quest experience and hireling heals take the whole party):

- **The party is hidden during a talk**: no basebar, portraits or hireling rail (`activeEventDialogHidesPartyFrame`
  in `GameplayOverlayTypes.h`; the portrait and hireling hit rects resolve to nothing, so a click on their place does
  nothing). The bar keeps the basebar's scale and stands where the basebar was, on the screen's bottom edge; the
  status plate goes above it.
- **A trainer lists its lessons per member** (`GameplayDialogController`, `Mm9RudeSkillTrainerOffer`, `...Skill`,
  `...Learn`): a trainer of several skills (Blade: Sword, Dagger, Axe) first lists them ("Expert Sword", tagged
  "1 of 4 can learn", muted when nobody can), then the chosen skill's rows, one per member in party order: the lesson
  and its price with a "Train · Expert" tag, or the member's reason, muted (the new `Locked` choice mark). A
  single-skill trainer opens on the member rows. The selection starts on the first member who can learn; a lesson
  trains that member (not the active one), the reply then says "Aslaug is now a Expert in Sword." and the rows show the
  new state. Back returns to the skills, then to the talk. The shared training takes the member explicitly
  (`evaluateSkillMasteryTraining` / `applySkillMasteryTraining`); the MM6-MM8 teachers pass the active member.
- **Sharper, heavier text**: the bar's Arrus, Create and Lucida were the legacy faces' four-times atlases mipmapped
  down to about 21 pixels, soft and thin. They are now the same outlines as independent faces rasterized at the drawn
  pixel height and drawn at scale 1 on whole pixels (`talk_arrus`, `talk_create`, `talk_lucida` in
  `engine/fonts/truetype/`; `GameplayUiRuntime::findHudFont(name, pixelHeight)`, the menus' path), and thickened a
  little: the descriptors' new `embolden: 0.03` adds 3 % of the height right and down from the rendered coverage
  (`engine/FontAsset.cpp`; an outline embolden lost the dots of the i, whose contours run the other way). Fondamento
  was already independent.

| Entry, no basebar | A trainer's skills | Its member rows |
| --- | --- | --- |
| ![](native/refinement_20261106/1600_entry_no_basebar.jpg) | ![](native/refinement_20261106/1600_trainer_skills.jpg) | ![](native/refinement_20261106/1600_trainer_members.jpg) |

Text before (top) and after, 1.5x: ![](native/refinement_20261106/text_before_after.png)

Katrina Vianni (RUDE 80, Expert/Master Blade), Sturmford City, a four-member party with the Knight at Sword and
Dagger 10: [`native/refinement_20261106/katrina_trainer_tour.yml`](native/refinement_20261106/katrina_trainer_tour.yml)
with `--position 4424 15190 19723 --yaw-radians -1.5708 --pitch-degrees -3` and the capture command below (set the
tour's `output_dir` to an absolute path).

## Current state

Bjarni Thorvaldssen, Sturmford City (`sturmfordcity.blv`, review root `output/mm9_rework/assets_dev`, prop event
308). Eight of his entry rows are unlocked (keys 20 196 23 39 84 89). Engine-native captures, four-member party:

| 1600x900 (RUDE canvas x1.5) | 1920x1080 (x1.8) |
| --- | --- |
| ![1600](current/shots_1600/01_bjarni_entry_eight_choices.png) | ![1920](current/shots_1920/01_bjarni_entry_eight_choices.png) |

The other captures are in `current/shots_1600/` and `current/shots_1920/`: hover, node 18, and the 228-character
"What can we do for you?" reply. Text at 3x, compared with the Obsidian house dialogue:
![zoom](current/text_zoom_comparison.png)

### Why the text looks blurred

`renderMm9RudeDialogueOverlay` (`game/ui/GameplayDialogueRenderer.cpp`, constants at lines 80-94) draws everything
on a fixed 800x600 canvas and multiplies it by `min(viewport / 800x600)`.

1. **A tiny bitmap font, scaled by a fractional factor.** The `RUDEBLACK` and `RUDERED` PCX strips are 15 px tall,
   with an x-height of about 5 px. They are loaded on the separate column-PCX path in `GameplayHudCommon.cpp`
   (`ui/dialogue/*.pcx`, `TextureFilterProfile::Text`) and drawn at scale 1.5 (900p), 1.8 (1080p) or 2.4 (1440p).
   - With the default `text_filtering=nearest`, pixel columns are doubled unevenly: stems alternate between one and
     two pixels, and the gaps vary ("Thor valdssen").
   - The font's grey anti-aliasing pixels become 2-pixel grey smears, which reads as blur.
   - With `text_filtering=linear` it is genuinely bilinear blur.
2. **The rest of the UI no longer works this way.** Since the font replacement work
   (`tools/font_upscale/FONT_REPLACEMENT_PLAN.md`), every other screen uses faithful TTF outlines. They are rasterized
   at 4x and mip-filtered, then drawn at the target size. The MM9 face is the one open row of that plan (row 9: no
   TTF, and the PCX path returns before TTF replacement).
3. **The background is stretched.** `RUDEBG_OPENYAMM_LIGHT_ORNATE_SLIM.png` is 540x192 and is stretched to 810x288
   or 972x346 with linear UI filtering, so its frame and parchment are soft too.
4. **The `?` glyph is broken.** In the PCX, `?` is a 3-pixel hook without a dot, so "What can I do for you?" reads
   as "you!" or "you]" once scaled.

### Other problems

- **Choices are lost.** At most six choices are drawn and clickable: `std::min(actions.size(), 6)` in the renderer
  and again in `GameplayOverlayInputController.cpp` (around line 3836). Bjarni's eight rows lose "We have a peace
  treaty..." and the **exit row "Sorry to bother you."** The design doc's "three per page with previous/next"
  (`devdocs/mm9/MM9_RUDE_DIALOGUE.md`) was never built.
- **The body is clipped.** It stops at the topic line, which leaves 4 lines. The line advance is 12 px for a 15 px
  font, so lines nearly touch.
- **The party basebar is hidden.** The 540x192 panel at y 408-600 of the canvas sits on top of it, although the
  HUD is "preserved" (`activeEventDialogPreservesGameplayHud`): no portraits, HP/SP or selection during talk.
- **The style is foreign to Obsidian.** It is light parchment with a green ornate frame. There is no portrait, the
  name is the same size and colour as the body, and hover is shown only by red bitmap text. Keyboard selection is not
  drawn, and there is no visited/new marking.
- **The geometry is owned twice.** The renderer constants and the input constants are separate copies of the same
  hard-coded 800x600 numbers.

## Data limits

Measured by [`tools/rude_stats.py`](tools/rude_stats.py), with full output in
[`rude_stats.json`](rude_stats.json). It covers `assets_dev/worlds/mm9/dialogue/rude/`: 435 talk NPCs, 1,863 nodes and
4,193 rows. It excludes the journal lists stored as RUDE (997 Quest Notes, 998 Auto Notes, 999 Awards) and the
designers' key-debug NPC 400.

| Measure | Median | p90 | p95 | p99 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rows per node (all conditions) | 2 | 4 | 5 | 7 | 14 |
| Rows that can show at once (no row forbids a key another requires) | 2 | 4 | 4 | 7 | 14 |
| Non-exit choices per node | 1 | 3 | 4 | 7 | 13 |
| Party prompt, characters | 25 | 42 | 49 | 59 | 63 |
| NPC response, characters | 39 | 147 | 183 | 238 | 254 |
| Entry blurb (TOPBLURB), characters | 18 | 40 | 47 | 70 | 88 |
| NPC name, characters | 16 | 20 | 21 | 27 | 33 |

- **Choices.**
  - 256 nodes can show more than 3 choices, and 22 more than 6.
  - The 14 is Forad Darre's node 10, where ten "What do you know about this place?" rows are gated by location keys,
    so only one shows. The real maximum is **10 choices**: the entry nodes of Sven Forkbeard, Sigmund the Stressed,
    Kira the Cold and Bjarni Thorvaldssen.
  - Design for 10, and degrade gracefully to 14.
- **Text.**
  - Responses never exceed **254 characters**, which looks like the original's 255-byte field. That is about 4 lines
    in a 900 px column of 23 px Arrus, so no paging is needed for RUDE itself.
  - Services can append a line ("Sorry, come back another day."), so a scroll fallback is still worth keeping.
  - Prompts are at most **63 characters**; 24 rows exceed 60.
  - The longest name is "Fland de Allasan A'Lanth a'ryshar" (33).
- **Row kinds.**
  - 2,938 rows go to another node and 1,001 exit (`next = -1`); 992 nodes have an exit row. 415 rows are quest-gated
    (they require keys).
  - 254 rows are services: skill training 115, shop 48, hire 17, dismiss 13, quest handoff 11, then healer, travel,
    training, bank, inn and donation (7-8 each), town portal 3 and item combine 2.
- **Choice states for the designs.**
  - **New:** a quest-gated row not chosen before.
  - **Visited:** chosen before. This needs a small save addition, per RUDE row.
  - **Service:** the row's opcode.
  - **Locked:** a trainer row whose `skill_trainers.txt` requirement fails, e.g. Hrapp Tjorvissen's Master Meditation
    needs rank 7.
  - **Exit.**
  - Rows that fail their quest keys stay **hidden**, as RUDE intends. Showing them would spoil the story.

## Shared rules (all three proposals)

- **Crisp text.**
  - Draw RUDE with the shared TTF faces at the target pixel size, not a scaled bitmap: **Arrus** for the NPC's words
    (the house dialogue body), **Create** for the party's sentences (the MM6-8 topic face), **Fondamento** for the
    name and buttons, and **Lucida** for hints and tags.
  - Lay the screen out in UI layout YAML through `UiLayoutManager`. Draw the panel as a 9-slice of the Carved
    Obsidian frame master. Delete the 800x600 canvas, the stretched PCX background and the `RUDEBLACK`/`RUDERED` use.
  - FONT_REPLACEMENT_PLAN row 9 (an "OpenYAMM Rude" TTF) becomes optional. Do it only if the user wants MM9's own
    face back, and fix `?` if so.
- **Verbatim prompts** (the MM9 decision): no topic labels. MM9's double spaces after full stops are collapsed.
- **States:** new = gold diamond, brighter ivory; visited = muted ivory with a small check; service = blue tag
  ("Train · Expert"); locked = grey text with a coral reason tag ("needs Meditation 7"); exit = always last, muted,
  door glyph, Esc.
- **Input.**
  - Mouse: hover or click anywhere on the row.
  - Keys: 1-9 and 0 choose; Up/Down plus Enter move `selectionIndex`, which is already in the controller; Esc takes
    the exit row (or closes if there is none).
  - Touch: tap a row. Rows are at least 54 px tall at phone scale, with no keycaps.
  - One owner for geometry: the renderer and input both resolve the same layout rects.
- **The basebar stays visible** (A and C live, B like the house screens), so the party is never hidden while talking.
- **Portraits.** MM9 has no portrait art for RUDE NPCs: they are 3D actors.
  - Real faces: render the actor's head to a texture when the talk opens (model renderer, offscreen view), or bake
    one PNG per NPC from the models once (an asset job).
  - Fallback: a Fondamento monogram medallion.
  - The mockups show both: Bjarni's crop of the in-world model, and monograms for Sven, Keith and Hrapp.

## Proposal A: conversation bar (in-world, bottom-anchored)

| Typical (Bjarni, 4) | Ten choices (Sven) | Longest reply (Keith, 254 chars) | Trainer (Hrapp) |
| --- | --- | --- | --- |
| ![](previews/a_typical.png) | ![](previews/a_many.png) | ![](previews/a_long.png) | ![](previews/a_service.png) |

4:3 and a 19.5:9 phone (touch, no keycaps): [many 4:3](previews/a_many_4x3.png),
[long 4:3](previews/a_long_4x3.png), [phone](previews/a_many_phone_touch.png).

- **What it is.**
  - An Obsidian panel 1000 px wide (at 1600x900) whose bottom edge stands on the party basebar. It grows upward with
    its content, about 300-540 px, and the world and the NPC stay in view above it.
  - A round portrait medallion breaks the top-left corner, with the name in Fondamento and the place in Lucida.
  - The party's last sentence is echoed in quotes above the NPC's reply, which is Arrus. Then a divider and the
    choices.
  - Seven or more choices switch to two columns in a 1160 px panel, with the exit row spanning the bottom.
  - A light floor shade keeps the text legible on bright scenes.
- **Why it fits.**
  - It keeps MM9's in-world "NPC popup" presentation, which `MM9_RUDE_DIALOGUE.md` chose.
  - It has the look of the newest native Obsidian popups: the potion and scroll popups that also rise from the
    basebar, and the shared overlay palette.
  - It is the smallest change to the player's experience.
- **Pros.** The NPC stays visible, and with a talk camera that pitches to frame the NPC (the captures use pitch
  -0.2), the speaker is above the panel. The basebar stays live. It adapts from 4:3 to ultra-wide by width alone, and
  long replies are only 4 lines.
- **Cons.**
  - Ten choices plus a long reply would cover most of the NPC, though the head stays visible at 900p.
  - Two-column rows wrap the longest prompts onto two lines.
  - On Android, the gameplay thumb groups must hide while it is open (it overlaps them at 4:3).
- **Engine work: S-M.**
  - **S.** Replace `renderMm9RudeDialogueOverlay` with a layout-driven panel. A world-scoped `ui/` layout YAML for
    MM9 holds the frame slices, text regions and row template. Reuse the measured dynamic-height body code that the
    Obsidian dialogue already uses (`calculateDialogueBodyTextMetrics`). Resolve pointer rows from the same layout in
    `GameplayOverlayInputController.cpp`, remove the 6-row cap, and add the 1-9 and Esc keys.
  - **S.** Add choice flags (new, visited, service, locked, exit) to `EventDialogAction`
    (`game/events/EventDialogContent.h`). Fill them in `buildMm9RudeContent`
    (`game/gameplay/GameplayDialogController.cpp`) from the row's keys, `next` and the trainer table. Save visited rows
    explicitly (`EventRuntimeState` and `game/maps/SaveGame.cpp`).
  - **M, optional.** A head portrait rendered from the actor model, and the talk camera. The monogram fallback ships
    first.

## Proposal B: audience frame (the house-dialogue screen)

| Typical | Ten choices | Longest reply | Trainer |
| --- | --- | --- | --- |
| ![](previews/b_typical.png) | ![](previews/b_many.png) | ![](previews/b_long.png) | ![](previews/b_service.png) |

- **What it is.**
  - The approved Carved Obsidian 4:3 house screen, paused. Top left is a live view framed on the speaker, inside the
    frame master.
  - Bottom left is the conversation box: the echo and reply in Arrus at house-body size (25 px), then the numbered
    choices. It grows upward over the live view for long replies or many choices.
  - On the right is the house sidebar with name, place, portrait, a topics summary ("9 topics · 5 new") and the exit
    row as the Leave button with its verbatim text.
  - The world outside the 4:3 column dims, and the party basebar stays bright below.
  - In the mockup the live view is a scaled crop of the Bjarni capture in every state, so Sven's and Keith's views
    show Bjarni. In game it is the speaker, rendered at native resolution.
- **Why it fits.**
  - One frame for every conversation in the game: the MM6-8 houses and the MM9 walk-in shops. Those already open this
    house screen with the `LiveGameplay` scene policy (`service_venues.txt`).
  - "Show us your stuff." then changes the shop's content, not the whole screen.
  - The choices stay full width; the narrow MM6-8 topic column is not used, as the MM9 decision requires.
- **Pros.**
  - Largest, calmest reading area.
  - Consistent with house dialogue on Android, which already has touch handling.
  - Pausing is natural, and the sidebar has room for service context (trainer, prices).
- **Cons.**
  - It hides the world. MM9's in-place conversations become a modal screen, which is heavier than the original.
  - A portrait (or live view) is required to fill the frame.
  - Wide screens show a dimmed world on both sides.
- **Engine work: M.**
  - A MM9 profile of the house dialogue: new layout elements in a world-scoped copy of `dialogue.yml` for a choice
    list inside the body box, plus the shared row/flag work from A.
  - The `LiveGameplay` view needs a talk camera that frames the NPC in the viewport.
  - The sidebar portrait needs the head render, or the monogram.

## Proposal C: chronicle (side transcript)

| Typical | Ten choices (scrolls beyond six) | Longest reply, with history |
| --- | --- | --- |
| ![](previews/c_typical.png) | ![](previews/c_many.png) | ![](previews/c_long.png) |

- **What it is.**
  - A tall Obsidian column at the right edge, 560 px wide at 1600x900 (500 at 4:3, 620 when wide), covering the
    minimap while it is open.
  - Under the name and portrait is a scrolling transcript of the conversation. NPC lines are Arrus with a brass bar,
    and the current line is gold. The party's sentences are Create in pale brass, right-aligned. Earlier visits to
    this NPC are collapsed above a date line.
  - The current choices dock at the bottom. Beyond six they scroll on their own ("scroll for 3 more"). The exit row is
    pinned under them.
- **Why it fits.** It reads like the Obsidian journal: Arrus prose on dark stone and a scrollable record, and it
  keeps the centre of the screen and the NPC free.
- **Pros.**
  - Unlimited length.
  - Players can re-read what an NPC said (MM9 quest givers repeat tasks only if asked).
  - Uses the spare width of wide screens well.
  - Could feed a "Conversations" journal tab later.
- **Cons.**
  - More text on screen than needed: the median reply is 39 characters.
  - At 4:3 it covers 40% of the width.
  - Two independent scroll regions. Hidden choices need scrolling (keys 1-0 still reach them).
  - On Android it sits where the right-hand Attack/Spell thumb group lives.
  - Furthest from both MM9 and our MM6-8 dialogue.
- **Engine work: L.**
  - Transcript state per conversation, optionally saved per NPC.
  - A scrollable text viewport: reuse `JournalTextViewport`, with wheel and drag.
  - Choice dock scrolling and new layout YAML, plus the shared row/flag work from A.

## Recommendation

**A, the conversation bar.**

- It fixes every measured problem: crisp TTF text, all 10 choices visible (two columns beyond six), the 254-character
  maximum in 4 lines, a visible basebar, and states and keys. The core is only S-sized work in the files that already
  own MM9 talk.
- It keeps MM9's in-world conversation, matches the newest native Obsidian popups, and works from 4:3 to phones.
  - Ship it with the monogram medallion.
  - Add the model-rendered head portrait and the framing talk camera as a follow-up.
- Two ideas worth borrowing:
  - **From B:** keep service rows as tagged rows (Shop, Train, Travel) that hand over to the existing house screen.
    That is what MM9 walk-in shops already do, so a conversation that becomes a shop changes frame only once.
  - **From C:** a transcript could become a later journal feature without changing the talk panel.

## Files

- [`mockups/a_conversation_bar.html`](mockups/a_conversation_bar.html),
  [`mockups/b_audience_frame.html`](mockups/b_audience_frame.html), [`mockups/c_chronicle.html`](mockups/c_chronicle.html):
  these take `?state=typical|many|long|service&w=1600|1200|1950&touch=1`. The shared files are
  [`mockups/common.css`](mockups/common.css) (fonts, palette, rows) and [`mockups/data.js`](mockups/data.js) (the
  real RUDE states and their sources).
- `previews/`: the rendered PNGs and `overview.jpg`. Re-render with `tools/render_mockups.sh`, which runs a local
  HTTP server, because the fonts do not load from `file://`.
- `current/`: engine captures.
  - Menu input tours `current/tours/bjarni_1600.yml` and `bjarni_1920.yml` (`debug.menu_input_tour_path`): they add
    three members, set the keys, run `event 308`, then hover and click rows.
  - Screenshot tours `current/tours/backdrop_*.yml` for the 1600x900, 1200x900 and 1950x900 backdrops.
  - Hover, node and long-reply shots were converted to JPG; the entry shots stay PNG for the zoom.
  - [`tools/prepare_assets.py`](tools/prepare_assets.py) cleans the backdrops (removing the "Talk" plate and the
    crosshair), crops Bjarni's portrait and builds the zoom sheet.

Capture command (1600x900; use `--set video.resolution=1920x1080` and the 1920 tour for the other):

```sh
./tools/run_game.sh --isolated mm9talk1600 --world mm9 --map sturmfordcity.blv \
  --assets "$PWD/output/mm9_rework/assets_dev" --position 6900 8192 19799 --yaw-radians 0 --pitch-degrees -3 \
  --set video.resolution=1600x900 \
  --set debug.menu_input_tour_path=$PWD/level_generation/ui/mm9_talk_dialogue_study_20261102/current/tours/bjarni_1600.yml \
  --warmup 3 --seconds 40
```
