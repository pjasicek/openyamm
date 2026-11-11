# MM9 rework: Thronheim City (`thronheimcity.blv`)

MM9's Thronheim City (the east gate and the prison street, the docks square, the central square with the town hall,
library and bank, the west town with the temples of Fre and Rata and Kira the Cold's council hall; 20 walk-in shops,
halls and temples; reached from the Thronheim wilderness by the east gate and the docks, and by Town Portal) converted
from its DAT world into a native **indoor map (BLV) open to the sky**, the second of MM9's seven cities after the
Sturmford City pilot ([CITIES_ROLLOUT.md](../../../devdocs/mm9_rework/CITIES_ROLLOUT.md),
[CITY_PLAYBOOK.md](../mm9r_common/CITY_PLAYBOOK.md)). Built on the shared converter and its city module, installed
in the review root `output/mm9_rework/assets_dev`. Props: [`../../props/mm9_thronheimcity_claude/`](../../props/mm9_thronheimcity_claude/README.md).

Status 2026-10-31 (unattended): **the city works as a BLV.** 63 sectors with the street/roof structure, our Enhanced
sky with time of day behind the sky faces, MM9's painted city map as the minimap, 43 people (40 with RUDE dialogues;
walk-in shops open by real clicks), the six council Jarls as posed talking props, 307 decorations, the doors, the
loft chest, every gameplay-relevant script as native Lua (the war council, Kira, the Honk missionaries, the bank's
orb, the Bad News scroll, Kira's Shield, the Desert Terror's breakout), both exits and three starts. Classic lighting
(no bake: [MM9_LIGHTING_DECISION.md](../../../devdocs/mm9_rework/MM9_LIGHTING_DECISION.md)). No converter or engine
change.

## Build and review

```sh
python3 level_generation/projects/mm9r_thronheimcity/convert.py            # build, compile, install (19-20 min, 3.6 GB)
python3 level_generation/projects/mm9r_thronheimcity/work/fast_build.py    # the same, geometry pass cached (40 s;
                                                                           #   delete work/geometry_cache.pkl after any geometry change)
python3 level_generation/projects/mm9r_thronheimcity/make_scenarios.py
for s in doors_exits shops chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_thronheimcity/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_thronheimcity/make_tour.py v03 [--original]
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated city_thronheim_blv --world mm9 --map thronheimcity.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 14377 164 3093 --yaw-radians 3.1416 --pitch-degrees 0 \
    --warmup 3 --seconds 170 --set logging.performance_trace=true --set logging.indoor_visibility=true \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_thronheimcity/review_tour_v03.yml
# the original: --map thronheimcity.odm --assets "$PWD/output/mm9_rework/thronheimcity_original_root"
#     --set video.view_distance=unlimited, tour review_tour_v03_original.yml (a private hard-linked copy of
#     assets_original whose worlds/mm6-8 actors.yml are the committed ones and whose old scene allows saving)
python3 level_generation/projects/mm9r_common/dungeon/sheet.py level_generation/projects/mm9r_thronheimcity/review/v03 \
    level_generation/projects/mm9r_thronheimcity/review/v03_original
python3 level_generation/projects/mm9r_thronheimcity/work/perf/counts.py work/perf/blv_v03.log work/perf/odm_v03.log
bash level_generation/projects/mm9r_thronheimcity/work/perf/loads.sh                         # map load, 3 x 2
```

City structure experiments (minutes instead of a 20-minute build): `work/city/cache_voxels.py` caches the voxel pass
(30 s), `work/city/try_structure.py <roof line> '<city settings json>' <tag>` tries a roof line and cut settings
(1 min, `streets_<H><tag>.png`), `work/city/street_views.py` picks open street views for the tours.

## Numbers and limits

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame: transitions and the painted map's
  bounds stay valid). Inside ±32 767.
- 12 475 source polygons -> 11 450 merged -> 17 234 native polygons -> **19 561 compiled faces, 31 192 vertices** (18 921 and 29 669, with 334 portal faces, since the merged top
  portals of 2026-11-01)
  (BLV indices are 16-bit: **48 % of 65 535**; no widening needed), 974 portal faces, 40 doors (39 mover models),
  48 BLV lights (at most 4 per floor point), **0 outlines** (painted minimap), 76 sky faces, 40 translucent faces.
- Estimate before the props and scripts work (plan pass): 12 556 native polygons -> about 24 000 vertices by
  Sturmford's ratio; the first compile gave 26 455, the floor splits below brought it to 31 192.
- Faces per sector: **max 1 460, median 142** (Sturmford 997 / 119; the per-sector face grid carries the large street
  sectors).
- Voxels: 16 LT, 737 x 159 x 531 = 62 M cells, 7.8 M air, 3.6 GB peak; the voxel pass takes 30 s, the face
  assignment most of the 19 minutes.

## Structure: sectors and portals

**63 sectors** and **974 portal faces**:

| What | Count | Notes |
| --- | --- | --- |
| Walk-in interiors (shops, temples, halls, the bank, the tavern, the prison, Kira's council hall) | 17 rooms | behind 15 MM9 UserPortals and 8 door-leaf portals; 10 glass portals (window panes: `thjorwindow2/4`, `windowlead1`) |
| Street rooms (open air under the roof line) | 42 | divided by **51 street-cut portals** (found automatically plus 3 by hand, split per pair of rooms; 6 automatic cuts dropped as loops) |
| Roof rooms (one per district: the east gate and docks, the centre, the west town) | 3 | joined to the streets by **215 merged top portals** (convex polygons over walls and roofs, `merged_top_portals`, 2026-11-01; were 890 roof-line rectangles, 41 blind) |

How the open air is divided (`../mm9r_common/city/structure.py`): a roof line at **1 472 LT** (256 over the streets at
1 216, under the lowest eaves: `work/city/street_clearance.png`), street cuts and top portals. Thronheim's streets are
wide (plazas, broad lanes), so the cuts may be up to 1 152 LT wide (default 768) every 1 024 LT (default 1 280) with a
96 LT corridor test; three hand cuts split the centre's west lane, the east gate square and the prison street
(`overrides.yml` `city`, plan `work/city/streets_1472_hand.png`, `work/rooms_street.png`). The many top rectangles came
from the diagonal streets (a 16 LT staircase at the roof line). Per view the renderer draws a median of **4 sectors**
(max 8).

**Merged top portals (2026-11-01, `merged_top_portals: true`; CITY_PLAYBOOK "The open air" step 3,
[CITY_STREET_COST.md](../../../devdocs/mm9_rework/CITY_STREET_COST.md) "Result of proposal 3").** The 890 rectangles
become 215 convex top portals (at most 8 corners; rebuilt with the final converter on 2026-11-01 evening; the afternoon build predated the sky-face rule): **974 -> 299 portal faces, 19 561 -> 18 886 faces,
31 192 -> 29 553 vertices**; only the portal faces change. On the 20 street poses of the v03 tour (before: the
2026-10-31 build, `output/mm9_rework/portals_1101/thronheim/before_oldtex`; after: `.../after`): traversal nodes median
59 -> 20, max 141 -> 39 (no cap hit before or after); portal link tests median 16 472 -> 1 138, max 55 721 -> 3 378.
Sectors drawn equal at every pose. All 32 images compared in 16 x 16 blocks: no hole, only the new x4 textures.
Scenarios chests, doors_exits, shops, scripted pass.

**Floors under house fronts** (`convert.py` `split_floors_at_walls`): MM9 lays one sidewalk or ground polygon from the
street on under a house; the shared converter gave the whole polygon to the house's sector, and the street drew sky
along the inn's front (review v02, `review/v02_compare.jpg`, s12). Every flat floor of 20 000 LT² or more is cut at the
plane of each wall that stands on it (foot at most 16 LT over it, 48 LT tall) where the wall's length reaches: 4 880
cuts, floor area under another room's air 193 141 -> 99 887 LT², and the strip is gone (v03).

## Sky and minimap

- **Sky**: MM9's 77 `skymarker` polygons (a lid 1 664-2 432 LT, walls, sky floors outside the walls) are 76 faces with
  `IndoorSky`; the scene opens to the sky (`sky: {mode: open, sky_texture: plansky3}`): our Enhanced outdoor sky with
  the game's time of day behind them. `review/sky01_sheet.jpg` (06:30, 12:00, 19:30, 23:30: dawn, noon, dusk with the
  sun, night stars). The static light does not follow the time of day yet (CITY_PLAYBOOK, "To build").
- **Minimap**: MM9's painted city map (`ui/maps/thronheimcity.pcx`, catalog entry kept by `painted_minimap: true`).
- **Fog**: off (WorldProperties `EnableFog 0`; MM9's FoggyDay/FogNight objects are WeatherMan presets, not carried).

## Content

- **People** (43 actors, all friendly until the breakout; plus one hidden guard): the old import's NPC records (names,
  rows, 40 RUDE dialogues) with MM9's bodies; the Honk missionaries (MM9 Honk rows, RUDE 271/272/279 from Honkies.scr)
  and Lt. Dain (RUDE 278, DoRude.scr) get their dialogues from their scripts; monster-family rows talk with a peasant's
  relations (`ally` 118). Townsfolk stand where MM9 placed them (immobile: MM9's wander rails, Knut and Ake's
  four-place cycle and the MM_Thronheim schedule are not carried). The old import's three "dogs" were ambient dog
  sounds (AmbientSound Dog0-2): not placed.
- **Walk-in shops**: William the Framish (weapons, 247), Rustavius (armour, 248), Bones the Pale (Fre's Light, 249),
  Jofridr (the tavern, 254), Thakkrad (wands and rings, 255), Robert Bloodstopper (Fre's Hand temple, 256), Erpr (town
  hall, 258), Jormunrek (library, 259), Magnus (The Hall, training, 260), Brynhildr (bank, 243). A click opens the
  dialogue and its service row the shop (scenario: the weapon smith and the apothecary). Shops and the bank close
  20:00-06:00 (key 5017).
- **Posed talking props**: the six council Jarls (Sven 3, Tryygva 180, Markel 127, Forad 2, Sigmund 87, Bjarni 45,
  PropAnim "Sit") in Kira's hall, shown from both treaty signatures (keys 90, 91) until key 94; a click opens their
  dialogue.
- **Doors**: 39 mover models: MM9's swing doors (`rotate`, pairs open together), 13 locked groups (the facade doors
  Door1-4, the safe, the guard house, the second inn, the two cell doors, the bank vault: a click says so), the secret
  door to the loft, Kira's council door (its own event: the war council) and the prison's back wall (a scene destructible
  the breakout breaks, on the `break` route with a doorway portal between the street and the cell since 2026-11-08:
  built `static` it sealed the cell, so its hole showed the clear colour and nobody saw through it).
- **Chest**: the loft's treasure chest (TreasureChest0, Chest5, loot container 0), reached by Ladder2.
- **Ladders**: Ladder2 (the room under the loft -> the loft) and Ladder0 (the low ladder by the apothecary). Ladder1
  has no brush in the DAT.
- **Exits**: ExitTrigger1 (the east gate) and ExitTrigger0 (the docks) to the Thronheim wilderness, both reached down to
  the street (`exits: bottom_lt 1200`: MM9's boxes start 4 LT over it). **Starts**: StartPoint0 (east gate, from the
  wilderness), StartPoint1 (docks), TownPortal; on their floors, facing MM9's 90 - ry.
- **The Argument cinema stage** under the city (y -32..260 LT, a copy of Kira's hall) is not built: nothing seeds its
  air (`seed_exclude`), its faces drop (most of the 2 308 "no air in front" faces). Its six actors (Kira, Bjarni,
  Sigmund, Forad, Tryygva, Markel) are placed in Kira's hall instead, hidden, for the council cinematic (Cinematics).

### Scripted objects (`citylua.py`; behaviour spec of every script: `work/scr_spec.md`)

| Script | Native |
| --- | --- |
| Argument.scr (+ ARG_*, Arguecam1, Arguetreaty) | opening Kira's council door with keys 90 and 91 and no 40 plays the cinematic `council_argument` (Cinematics): Forad leaves the party at :Cam2b, :War (keys 184, 40, 85, 93, 26 500 xp, the Peace Treaty 401 taken) at :Cam3, at :End2 the live Markel prop is swapped for the dead one and Yrsa appears 7 s later and opens RUDE 1 |
| ARG_Unhide.scr | the council set (six Jarls, book, treaty) shown from 90 + 91 until 94; Markel alive only before 40 |
| ARG_Yrsa.scr (Yrsa the Troll, RUDE 1) | after the council: a click gives 93 and opens RUDE 1; the exit gives 185 and she vanishes |
| NPC239.scr (Kira the Cold, RUDE 239) | click: 178 with the five clan keys; exit: 147 (item 247 taken), 146, 152, 179, 181 (item 401 given); hidden on 40 unless 108; the 06:00 key 180 after 88 |
| Honkies.scr (three Honk missionaries) | each holds a Honk pamphlet (`held_items`: `mm9_item_honkpamphlet.glb` on `Socket_pamphlet`, :Init AttachProp) and wanders (BaseWanderInit); with the dock captain's plan (145) each persuaded one (142/143/144) runs to HonkyMarker at the docks and is gone there (:Walk, :OnShanghai; arrival events 265-267); the third gives 77 and 8 000 xp; gone on 77 |
| BankOrb.scr (Brynhildr, 243) | the Orb of Linking: 330 on a click with the orb, the exit places it (331 -> 328); six orbs: 337, 20 000 xp, 15 000 gold |
| NPC241.scr (Ealusaid) | 314 -> 315, 50 000 xp, 10 000 gold, the Black Orb (250) taken |
| NPC242.scr (Dagfari), NPC246.scr (Erlend) | the Scroll of Bad News (251): 316 -> item + 317; 318 -> 319, item taken; 320 -> 321, 5 000 xp, 5 000 gold |
| NPC378.scr (Thorolf, two copies) | as Sturmford; with 83 Thorolf0 waits at MM9's Thronheim spot |
| KiraShield.scr | Kira's Shield (375) is a world item (`dungeon/pickups.py`), always there; taken only with 214 (no sparkle before), giving 216 |
| Thronheimcity_BadAss.scr (+ BadAssTrigger/0, Thronheimcity_Guard.scr) | walking across one of MM9's two planes by the prison (polled every second, a jump over 1 500 is a teleport, not a walk): the Terror walks to BadAssWander1 and breaks the prison's back wall (a scene destructible: crumble, dust), runs to Shmoe and kills him (`evt.MoveActorTo`, `evt.KillMapActor`; 12 s at most, a load finishes it), then turns hostile (its group's Hostile bit) and walks (`evt.SetActorImmobile`: :Taunt3Done's BaseInit lifts its placement's stillness) with Ben as its target (:Taunt3Done's `Target Ben`, `evt.SetActorTarget`; 2026-11-08: before, it took the nearest, usually the party); Ben runs to BenMarker, then to Guard1, bringing it to the guards. Guard1 and Guard2 sleep at their posts (Thronheimcity_Guard.scr GotoSleep: scene `dormant`, `mm9_ai.dormant {until: trigger, pose: sleep}`, no wander), Guard2 until it is hit (it stood awake and unable to move before 2026-11-08), Guard1 until :GetExtraGuard's OpenEyes (`evt.WakeActor`) gives it the Terror; the guards drop their peasant ally (`ChangeGroupAlly`, still friendly) so relations.yml sets them and the Terror against each other; 6 s later one more guard appears at GuardSpawn1 and goes for the Terror. Each guard sent gets the Terror as its target once (:GetBadAss, `evt.SetActorTarget`), not a renewed walk to where it stands as before 2026-11-08. Every dead Guard1/Guard2/extra guard, and every guard sent, sends a new one from GuardSpawn0 (Thronheimcity_Guard.scr :OnDeath, the kill hook), also after the Terror's death (MM9: the dying guard's OnDeath fires and GuardSpawn0 is no AI, so the dead-receiver rule drops nothing), running for the Terror while it lives, at most 12 (`GUARDS_SENT_CAP`). No key gate (as MM9) |
| Retainer.scr (Cleirach A'Lyrae) | hidden while hired (461) |
| ForadWorld.scr, TownPortal.scr | location key 1030 (1024-1033 cleared), shop hours 5017; the altar's click gives 5016 (the dirty altar hides and its clean twin `mm9_portalclean` at its place shows, also on load: `../mm9r_common/dungeon/town_portal.py`) |
| BookLetter.scr | the four letters (466-469) |
| KnutSpeech.scr, Ake.scr | Knut's rant (Cinematics): ambient Lua, key 114 |
| Book.scr, PropAnim.scr, Shopkeeper.scr, NPC240, Thronheimcity_Actor, MM_Thronheim | cosmetic (animations, voices, fleeing, schedule); not carried |

Choices against MM9, written down: Honkies.scr sends every Honk whose dialogue closes with 145 and any of the three
keys; here only the persuaded one leaves (and stays gone on reload). Yrsa also waits on later visits until 185 (MM9
shows her only during the council's session). Kira's 06:00 key 180 is given once a 06:00 has passed since the poll
first saw key 88 (MM9: only with the map loaded at 06:00). MM9's guards respawn endlessly, the Terror alive or dead (a
guard sent after its death finds only its corpse); here at most 12 come, since MM9's HitPoints 250 / AC 20 for the Terror at the breakout are not
carried. The Terror's taunts and the fleeing townsfolk are not carried.

## Cinematics (2026-11-06; `council.py`, devdocs/mm9_rework/MM9_CUTSCENES.md)

**`council_argument`** (`thronheimcity.cinematics.yml`): ARGUMENT.scr's war council, 167.1 s, 27 shots. MM9 films it
on its stage under the city; the stage is Kira's hall moved by (-4400, 1312, 6464) LT (floors, table tops, candles,
walls and Jarls agree to 8 LT), so the cameras (Camera0-11, CameraMarker0, KiraMarker1, treatymarker) and the stage's
six actors are moved into the hall and the scene plays there. `convert.py` places the stage actors at the end of the actor list
(hidden, immobile, their MM9 rows 246-252 with the GLBs' Argument clips); the `stage` step swaps them in for the posed
Jarl decorations (Sven keeps his: his model sits on its own chair, so he neither claps nor agrees) and hides Kira the
Cold, the `end` step swaps back with Markel dead. Kira's sword (ARG_Kira.scr's AttachProp, 2026-11-11): the
`kira_sheath` step hangs `mm9_item_kirasword.glb` on her `Socket_Sheath` as she stands, `kira_draw` moves it to
`Socket_RHand1` at Sc2_Kira17's attach key (0.966 s, with DrawSword.wav), and the `end` step takes it off.
Kira's seated clips are lowered 24 units onto her chair in the model (`mm9_kira_claude/scripts/seat_clips.py`,
2026-11-11): MM9's sit keeps her standing hips, and the stage actor cannot go under the hall's floor.

- Timing: Camera0's MoveToPos arrival (200.6 LT at 40), then the 24 :OnDone callbacks from the `.abc` key events of
  the Sc2_* animations (Done, Done2, Cam3), DrawSword.wav's end and 18.wav's end, and the script's waits (wait 1 4,
  wait 2, fades); Kira and Markel walk at MONSTERS' WalkVelocity 50 (Kira round the left row of chairs, standing
  outside it facing Markel, where Camera9 and 10 frame her: MM9 paths and collides).
- Steps (map events 36001-36004, done 36000, each once): `stage` 0.95 s, `forad` 6.5 s (:Cam2b RemoveNPC 2), `war`
  21.2 s (:Cam3 gosub War), `end` 166.2 s (:End2: the hall restored, Yrsa's timer 36040: 5 s windup, 2 s Town Portal
  sound and she shows, 3 s later key 93 and RUDE 1). The council door's handler (232) calls
  `MM9Cinematic.start("council_argument")`.
- Cues: the shots (fov 73.7), fades (OnStart 1, Cam1/Cam2b 0.5, End/End2 1), the voices 01-20 and 16a, signatures,
  page turn, book, chair slide, claps at the Applause keys, sword, cflesh, Bjarni's "Yeah"; every actor animation as
  a clip cue with the GLB name (ArgumentShot1A, Sc2_MARKEL02 ..., Sit loops between), walks as move cues with Walking,
  faces; the treaty decoration (cog 406) lies before Bjarni and slides to Sigmund at 4 LT/s.
- Not carried: subtitles (the lines' text is in no MM9 data file: only fragments in the script's comments),
  Markel's chair sliding back (the chair decoration has no cog), the book's open animation.

**Knut's rant** (KnutSpeech.scr, Ake.scr): not a cinematic (MM9 leaves the player in control for its 91 s; a cinematic
locks input and saving): map timer 36050 polls; when the party first comes within Knut's sight (1536) he plays his talk
clip, a second later key 114 and his speech at him; Ake faces him and heckles (ake01-05.wav at Ake, talk clip) on
Ake.scr's waits (7.5 s between) until :shutup 5 s before the end. Once (key 114); MM9's four-place cycle is not carried.

Test without a conversion: `python3 cinematics_pilot.py` writes the cinematic, the installed Lua as the changed
converter writes it and the installed scene with the stage actors (44-49) into
`output/mm9_rework/cinematics_pilot_root`; then from `output/mm9_rework/cinematics_pilot_run` run
`build/game/openyamm --world mm9 --headless-run-scenario <abs>/cinematic_council_argument_play.yml` (and `_skip.yml`,
`knut_rant.yml`). Captures: `output/mm9_rework/cinematics_pilot_run/captures_council_argument/` (tour
`tour_council_argument.yml`). Since 2026-11-11 `cinematic_council_argument_play.yml` and `_skip.yml` check the installed
map's actors (Kira's stage actor 50, Markel 46, Kira the Cold 41, Yrsa 42; the pilot root numbered the stage actors
44-49) and pass against `assets_dev` (`./build/game/openyamm --headless-run-scenario <abs yml>` from the repository).

## Quality gates

1. **Every DAT world model has a rule** (96 + PhysicsBSP); skipped with reasons: the sky box and TOD star shell, 9 AI
   barriers, 4 PortalZones (MM9 renderer zones, invisible), 349 AI rails, 12 PerceptionBrushes, the 2 ladder volumes.
2. **Sealed air**: `leaked_to_border` false, 1 air component (7.8 M voxels). 2 308 faces without air in front dropped
   (`work/dropped_faces.json`): the cinema stage, the pieces of floors under walls (the splits above), faces between
   brushes.
3. **Every portal joins two rooms**: 0 without two rooms (Portal45, TrainingHallSmallDoorPortal1 and HolePorta, door-less
   UserPortals that separate nothing, are skipped).
4. **No holes**: the 32-view sheet `review/v03_compare.jpg` shows none (v02 showed the sky strip along the inn front,
   fixed). Floor holes 0, cracks 0 (6 welded). Floor check 99 887 LT²: cut strips and wall tops at the roof line, as
   Sturmford; no review view shows a wrong sector.
5. **Review sheet**: MM9 original (the old ODM import, view distance unlimited) | native BLV, **32 eye-level views**
   (20 streets and squares picked from the street air, 12 interiors): `review/v03_compare.jpg`; looked at: same
   geometry, props and textures in every view. Ours is darker in the streets (classic vertex light against the old
   import's bake) and shows no green hover outline; the street lamps' lanterns read as a dark frame from below (the
   props project's `lamppost4`). Time of day: `review/sky01_sheet.jpg`.
6. **Walkability** (`work/audit.log`): 136 steps, 25 flights, 10 unreachable regions, 2 pits, 26 mover notes, 0 actor
   notes. Looked at in game (`work/probes/regions_tour.yml`, `work/probes/regions/`): the 10 regions are the shops'
   counter platforms (town hall 102, apothecary 92-97, the armour shop 95), building plinths 41 and 62 high, a 38-unit
   ledge the party steps, and a closed courtyard 79 over the street (sector 22, 2.24 M units², walls on every side and
   a painted gate: nobody stands there in MM9). The pits: the loft (its way out is Ladder2) and a yard closed by doors
   (sector 11). **Half steps** (`city: {half_steps: true}`, CITY_PLAYBOOK "Raised floors"): 4 steps (8 faces); the
   forward-walk probes (`work/probes/half_steps.yml`, `.log`) climb 82 and 77 onto the plinth at (8530, -1777), 46-47 at
   the council hall step, 31 at the two terrace steps at 1 473 LT.
7. **Scenarios pass** (headless, real clicks where the engine picks): `scenario_doors_exits` (22 steps: the weapon
   shop's double door stops the party, opens on its click, the party walks in; a facade door stays locked; both exits
   raise their transitions), `scenario_shops` (31: William's and Thakkrad's dialogues by press_interact, their service
   rows open the shops; Bjarni's posed prop by its click), `scenario_chests` (7: the loft chest by press_interact, the
   climb up Ladder2), `scenario_scripted` (38: 1030, 5017 at night and not by day, the war council's keys and the
   council door open, Ealusaid's reward on her dialogue's close, Kira's Shield, a letter, the breakout opening the
   prison wall when the party walks across the plane).
8. **Starts**: three, each on its floor (`build_report.json` `starts`); the tour's first view is the east gate start.
9. **Compiler unit tests**: `openyamm_indoor_source_tests` 21 of 21 (no engine build: no engine change).
10. **Lights**: 48 BLV lights, at most 4 per floor point (`content.json` `light_coverage`).

## Performance (counts; frame rate needs a single-session run)

Same 32 views (`review_tour_v03*.yml`), `logging.performance_trace` + `logging.indoor_visibility`, minimized isolated
desktop runs on a shared machine (`work/perf/`).

| Map | Draw calls, median / max | Triangles, median / max | Sectors drawn | Textured batches |
| --- | --: | --: | --: | --: |
| **Thronheim City, native BLV** | **206 / 381** | **26 000 / 51 300** | 4 / 8 | 115 / 273 |
| Thronheim City, old ODM import | 1 069 / 1 576 | 86 200 / 157 700 | – | – |
| (Sturmford City, native BLV) | 218 / 385 | 30 600 / 70 800 | 5 / 12 | 96 / 238 |

- **Map load** (median of 3, `OPENYAMM_MAP_LOAD_TIMING=1`, `work/perf/load_*.log`): BLV **2.43 s** (asset load
  0.95 s) against the old ODM 2.93 s (0.99 s); the first run of each was cold (3.7 / 6.9 s).

## Engine and converter changes

None. Map-local only: `convert.py` (`split_floors_at_walls`, actors, the extra guard), `citylua.py`, `overrides.yml`.

## Open items

- Thjorgard City's props project plans the same model names for the same ABCs and skins (`coatrack2`, `herbrack1`,
  `plateset2`, `shield3flat`, `shield4flat`, `steinfancy01`, `suitofarmor01plain`): this city installed them first,
  so Thjorgard can reuse them (props README).
- **Daylight and street lights done (2026-10-31):** `city: {daylight: true}` (MM9's ambient 80 and its StaticSunLight,
  which stands nearly overhead here, by the time of day), `map: {fog: lithtech}` (no fog at the start in MM9: nothing
  written; its `Foggy`/`Clear` weather and day/night fogs are scripted and not carried; under them MM9 greys the sky
  too, devdocs/INDOOR_FOG.md "The sky in fog") and `map: {bright_scale_lights: true}` (29 of 48 lights at colour x
  0.5-0.8). Noon streets now match the old import; interiors unchanged; nights dark: `review/dl2_compare_1200.jpg`,
  `_2330.jpg` (old ODM | before | after). Scenarios rerun: doors_exits, shops, chests, scripted pass.
- Long screenshot tours on the BLV ended in a death video (here after the sixth view of the before run). Fixed
  2026-11-01: the tour's clock, not the city (`../mm9r_common/CITY_PLAYBOOK.md` "Daylight and fog"); the same 16-view
  tour now ends alive (the old binary still plays the video).
- Not carried: MM9's wander rails and
  schedule, breakable windows, Perception hints (12 PerceptionBrushes), the hire key 461 (MM9's hire service grants it implicitly), ambient sounds.
- Townsfolk draw as stand-in peasants until the MM9 town NPC models exist (another session's work).
