# What the final MM9 rebuild still lacks (2026-11-05)

The user's question before the one final reconversion of every MM9 map: what must be in so the maps are "final"?
Three read-only sweeps over all 44 maps answer it (sources and helper scripts: the session scratch `sweep/`; the
reports are summarised here):

- **A, our records**: every map's `work/scr_spec.md`, README, map-Lua generator, `build_report.json`, `content.json`.
- **B, the DATs**: 44 960 objects in 282 classes, each class traced to the converter code and the converted outputs.
- **C, MM9's scripts**: 418 scripts (1 566 objects) and their commands against OpenYAMM's Lua API (`evt.*`, `MM9.*`,
  actor behaviours) and `reference/openmm9/docs/`.

Rule for "needs the rebuild": only what changes the converter's output (geometry, the scene: props, actors, doors,
lights; the map Lua; the lightmap sidecar). Engine, AI, rendering and model changes load at runtime. Any later fix
reconverts only the maps it touches (minutes each; the whole set about 1.5-2 h with the lightmap transfer).

Checked by hand in this file's session: key 94 (YRSAS_QUEST_COMPLETED) only from THJORGARDGAMESCOMMON.inc's prize after
all six Thjorgard games, and Bikki (NPC244.scr) and Svenspeech.scr test key 95; Hall of the Gods' `convert.py:79`
`AFTERWORLD = "afterworld.odm"`; linear doors have no auto-close (only the rotating `mover` block's
`auto_close_seconds`, game/maps/IndoorSceneYml.cpp); bone piles are read by the engine
(game/gameplay/SearchableLootPropRuntime.cpp, kind `bone_pile`) and written by no MM9 converter.

## 1. Progression and quests (fix before the rebuild unless noted)

| Gap | Maps | Needs | Notes |
| --- | --- | --- | --- |
| Thjorgard's games: whack-a-honky, arm wrestling skipped | Thjorgard | engine (a prop moved from Lua; a click on an actor without dialogue) + Lua | **Main quest**: the six wins give key 94, Bikki needs it for 95, the Yorwick battlefield (97) needs 95. Also check the boat race is reachable |
| Forad Darre not placed (Retribution's counter); ExitTrigger1 open before Rebirth (key 390) | Afterworld | converter | **Main quest**: key 102 never given |
| Hall of the Gods' trip targets `afterworld.odm` | Hall of the Gods | converter | breaks once the old imports go |
| Adult Magreeb not placed | Thjorgard | converter (+ hostility check: MM9's flees) | Scholar promotion |
| tm_Hardrock "6 129 6000" read as destructibles: it counts seven bandits' deaths (YobboeMan) | Drangheim region | converter/Lua | key 129: Keith Bloodaxe's Crusader promotion |
| Promotion keys 401-448 ("every character holding key N"): nothing found that sets them | cities | verify in game; engine/Lua if missing | every promotion |
| Yrsa leaves on re-entry once Forad joined | Isle of Ashes | Lua | bunker key can be lost |
| Exit trigger 777 (to Iver's Estate) records no transition | Yanmir's Fort | converter (investigate) | |
| Thjorgard -> Training Hall exits start disabled in MM9 (a trigger enables them); 5 more disabled-at-start exits | Thjorgard + others | converter | sequence breaks |
| Mary's sheep (MarySheep.scr: a follower) | Yorwick | engine (followers) | side quest, key 466 |
| The MM9 ending: WinMan.scr `:End` calls DoHighScore | Hall of the Gods + world.yml | data + map Lua | the engine's completion certificate (world.yml `completion`, as MM8's): MM9's own `LOCALART/MISC/WINBG.pcx` (800x600, "Might and Magic IX Congratulations!" over the world map), its text ENGLISHGAMETEXT.txt lines 539-543 (headline, per-character line, the Njam ending paragraph, total time, score); WinMan's end sets the completion qbit |
| MM9's party death (LoseMan.scr; the engine's `Lose`) | every MM9 map | data (+ cinema later) | from the scripts: the first arrival at Arslegard by travel is FateMan.scr (Hanndl's "destiny", key 98, out by the Dark Passageway: carried); a party wipe sends the party to Arslegard City's Great Gate, where LoseMan.scr plays Hanndl's "You again!" scene and leaves the party in Arslegard (no exit fired). Ours: the MM9 world has no continent_settings.txt death map. Fix: an MM9 death map (Arslegard City at the gate), `LoseGame.bik` (mm9/game/Movies) as its death movie; Hanndl's lines as text until cinemas exist |

## 2. Converter-only completeness (cheap: do before the rebuild)

| Gap | Size | Notes |
| --- | --- | --- |
| Flat letters (BookLetter.scr bDown 1) | 40 letters, 17 maps | model built (props/mm9_outdoor_regions_claude/scripts/scrollflat.py); the shared rule and rows remain |
| Bone and trash piles give no loot | 77 piles, 14 maps | the engine's `bone_pile` loot exists; the converter does not write them |
| Perception hint brushes (trap hints) | 187, 20 maps (every city and region) | Anskram Keep's helper into the shared code |
| Always-burning fires (Fire objects) not built | 53, 18 maps | mostly cities and regions |
| Ladders not set up | 14: Boot Camp, Sturmford, Lindisfarne, Drangheim, Sturmford City Ladder2-6 (one is Beethoven's grate shaft), 1000 Terrors | scene `ladders` exists |
| Destructible urns drop no treasure; exploding destructibles do not explode | 22 urns (Bathhouse, Beethoven); 49 (3 maps) | engine loot call exists |
| Start-open doors built closed | Ta'Sar's two switches, Wizard's Lab's closets | |
| Swimming off (wading floors) | ~10 dungeons, 2 cities | `swim: true` |
| Breakables break on a click, not by damage | ~7 dungeons | the shared destructibles route |
| Monster wake-ups not wired | Frosgard's jumping yetis, Thjorgard's bandit ambush, the Isle's BoneThrasher resurrect and Peter | Lua |
| Shooters not carried | Frosgard City (the cannon test), Wizard's Lab | Lua |
| Sturmford City's magic shop has no ceiling | Sturmford City | investigate (geometry) |

## 3. Engine + converter, medium

| Gap | Size | Notes |
| --- | --- | --- |
| Linear doors and lifts never auto-close (CloseWaitTime) | 313 objects, 18 maps | only rotating doors have auto-close |
| Touch-to-open doors and touch triggers (walls, props) | 21 (1000 Terrors' 14 WeightedLifts built static, Bathhouse Door3/4) | `FaceAttribute::TriggerByTouch` unhandled |
| Ambient sounds switched by Lua | 80 trigger links; 58 sounds point at missing audio (import) | |
| Lua: kill an actor (death, loot), walk an actor to a point | many scripts (converters give the keys instead) | done: `evt.KillMapActor` (E5), `evt.MoveActorTo` (M22) |
| Companions (AddNPC: Tamur) | | `AddFollowerNpc` exists, no converter uses it |
| Wells, cauldrons, cook pots, clover bonuses | 44 objects | MM9 game code: needs RE |
| Weather and fog switching | 4 triggers | |

## 4. Engine, large (later; each touches a few maps)

Cutscene cameras, letterbox and fades (80 camera objects, 12 maps; 21 scripts), camera shake (29, 7 maps) (engine,
format and Isle pilot done 2026-11-06: [MM9_CUTSCENES.md](MM9_CUTSCENES.md); the maps: FINAL_REBUILD_WORK.md C11), continuous
spinners (RotatingBrush 15, 5 maps; done 2026-11-06: scene `mover.spin`, `evt.SpinMover`,
[INDOOR_ROTATING_MOVERS_AND_LADDERS.md](../INDOOR_ROTATING_MOVERS_AND_LADDERS.md) "Continuous spinners"), moving or animated decorations and model swaps (animated
decorations done 2026-11-10/11, [ANIMATED_DECORATIONS.md](../ANIMATED_DECORATIONS.md): Beethoven's coffins, every
TreasureChest lid, Lindisfarne's bells, the Lich Lab's switch, engine and shooting books, Dark Passageway's switch
statues, the Thousand Terrors' win lever, skull and sorceress statues, Thjorad Mine's cart, the windmill, banners and
stat stones' loops, Book.scr books; with them the KingKong break-out swings and Yanmir's door kick. Still open: the
sorceress statues' casting smoke, MM9's chest close sound, DarkP's missing awareAir/CastSpell start clips (not in the
models)), held props (AttachProp), hidden
model parts, runtime skin swaps (Banshee decay, Ebora's sirens), NPC-to-NPC conversation (Converse), NPC navigation
messages, monster-triggered volumes (71, 4 maps), PerceptionLight (61, Dark Passageway; done 2026-11-06 as scene pulsing lights,
[INDOOR_PULSING_LIGHTS.md](../INDOOR_PULSING_LIGHTS.md) "Switched lights"), clock-scheduled shows
(Guberland Players, the Honk ceremony; done 2026-11-06 as map Lua with positional voices, without the actors' walks), the other minigames (Guberland's stones and whack-a-honky, the racing boat,
Mastermind), sound handles (stop, finished), positional script sounds, walking NPCs and patrols, monsters opening
doors, the stat stones' spin.

## 5. No reconversion needed

Creature models (the creatures session's triangle reductions), missiles hitting props, rendering and AI fixes,
redrawn skins, sound imports (the files; their wiring is section 3), the Sturmford drawbridge oddity, installing the
maps into assets_dev and consolidating the review roots.

## 6. Classes and skills (user, 2026-11-05)

- **Skills separate, as MM6-MM8** (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Skills And Mastery"): no composite
  Elemental/Blade/Cudgel/Armor topics; every MM6-MM8 skill and school (Mind and Body included) trainable in the MM9
  world, with added trainer NPCs where MM9 has none. Done for the trainers (D2, 2026-11-05: Axe, Staff, Mind, Body,
  Stealing, Regeneration and Alchemy by existing MM9 trainers); Blaster and the racial abilities need new trainer
  NPCs (proposal in the integration document), placed actors: before the rebuild.
- **Promotions**: MM9's tree is Fighter -> Mercenary (-> Gladiator, Assassin) or Crusader (-> Paladin, Ranger);
  Initiate -> Scholar (-> Mage, Lich) or Healer (-> Priest, Druid) (mm9/extracted/DATA/DATA/GAMETEXT.txt). Ours
  (worlds/mm9/events/common/mm9_common.lua `MM9.PromotionClasses`, `givePromotion`) sets one fixed MMerge class per MM9
  promotion with `SetPlayerClass`, no tier, line or eligibility check (a Sorcerer could become a Cavalier), for the
  characters holding MM9's per-character keys 401-448, which nothing seems to grant. User decision (2026-11-05): own line, by
  tier (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes"); the approved
  quest -> line table and rules are there; implementing it (table, `MM9.givePromotion`, the maps' handlers, RUDE
  visibility) is pre-rebuild work.

## 7. ~~The Tomb of a Thousand Terrors is not grown~~ (found 2026-11-09, MAW in MM9 work, openyamm-14; done the same day)

The Tomb holds 114 monsters against its density target of 465 (`mm9_density_targets.yml`): `work/density.json` placed
0 of 372 copies. Every member counts as scripted (`density.py` `scripted_reason`: "named by the map Lua", 93 members,
and "scripted damage", 19): the map's triggers wake its monsters by DAT name (`send(target, "go")` ->
`evt.WakeActor(ACTOR[target])`, and `FLY_LEAVE` removes the fliers after their flight), so a copy would stand dormant
for good. To grow it, the copies must follow their member: the converter (`mm9r_1000terrors/convert.py` and
`density.py`) adds each copy to what wakes and removes its member (for example an `ACTOR_COPIES[name] = {indices}`
table the `go` and `FLY_LEAVE` branches walk as well), then lets `grow` copy those members; the Tomb also needs
`density_arrivals` at its teleports and drops, so a party is not put down among a grown pack. After its reconversion,
MAW's pack reserve picks it up (`tools/maw/mm9_pack_reserve.py 1000terrors`; devdocs/maw/MM9_BALANCE_DESIGN.md).
Not done in the MAW work: `density.py` and the Tomb's converter were being changed by another session then.

State on 2026-11-09 evening (scratch build, `convert.py --scratch`): the converter now declares `ACTOR` a directory
(`density_lua_directories`), but the build still places 0 of 372 copies, all members "named by the map Lua". Left:
the map Lua's `KIND` table (`["DesertTerror3"] = "actor"`, used by `send`) names every monster too and is not a
directory; the copies would join `ACTOR` under their own names (`<member>_grow<k>`), which no trigger sends `go` to,
so they would stay asleep (they must wake and leave with their member); and no `density_arrivals` at the teleports
and drops yet.

Done 2026-11-09 (late): `KIND` became a `density_lua_name_tables` entry (`dungeon/build.py`, `density.lua_name_tables`,
also read by `density_dry_check.py` and `tools/maw/mm9_pack_reserve.py`), and the two loops that walk every actor by a
variable `index` now use `scan` (the Lua scan followed `index` through the whole script: 913 indices). The fly-past
critters are the only monsters messages name; they stay uncopied, so no copy has to follow a member. Forced arrivals
at StartPoint0 and the trap-door pit. First result at 5x: 319 of 372 copies, 412 monsters against 465 (README "Pack growth").
The user found that far too many (an open hall went from 7 monsters to 72) and set the Tomb to 2x the same evening:
93 copies, 186 monsters (BALANCE_PLAN.md 3.6).
