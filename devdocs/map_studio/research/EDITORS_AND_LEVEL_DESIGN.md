# Research: level design practice, editors and the original games (2026-11-12)

Digest of the research behind the workflow (seven stages) and the screen layout. Details tagged "recall" in the
original pass came from memory and are omitted here unless important.

## Level design process

- The Level Design Book (https://book.leveldesignbook.com/process/overview): pre-production, layout (thumbnails,
  bubble diagrams, floor plan with the critical path), blockout, scripting, lighting, art, release. An early art pass
  locks in layout mistakes. Test blockouts by walking, not flying. Doors are among the hardest scripted features.
  Metrics: decide player size, door and corridor standards early; build a metrics test map.
- Bethesda kits (Burgess, GDC 2013, https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design):
  7 kits built 400+ dungeon cells; footprints in multiples; one door-frame size; pivots at floor centre;
  "snap to reference" for angled pieces.
- Locks and keys: Mark Brown's Boss Keys diagrams; Jaquays' looping dungeons
  (https://thealexandrian.net/wordpress/13085/roleplaying-games/jaquaying-the-dungeon); hard and soft locks
  (https://www.boristhebrave.com/2021/02/27/lock-and-key-dungeons/); cyclic generation (Dormans, Unexplored).
- Landmarks: Breath of the Wild's triangle rule and three scales of landform
  (https://www.blog.radiator.debacle.us/2017/10/open-world-level-design-spatial.html); Witcher 3: two points of
  interest on the horizon; Disney "weenies".
- Door checklist: Liz England, "The Door Problem" (https://lizengland.com/blog/2014/04/the-door-problem/).

## Editors

- **Doom Builder / Mapster32:** draw a closed polygon to make a sector, join sectors, raise floors by aiming in 3D;
  Mapster32 copies a surface with Tab and pastes with Enter, plays from the camera with Ctrl+P
  (https://wiki.eduke32.com/wiki/Build/Mapster32_Keyboard_Commands). Closest model to BLV.
- **TrenchBroom:** brush drawing, face extrusion, live issue browser with quick fixes, unlimited undo, entity browser
  with drag to surface (https://trenchbroom.github.io/manual/latest/).
- **Hammer:** inputs and outputs between entities, Check for Problems; Hammer++ loved for autosave on crash
  (https://developer.valvesoftware.com/wiki/Inputs_and_Outputs).
- **Unreal:** landscape splines that raise or lower terrain and paint a layer, on their own edit layer
  (https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-splines-in-unreal-engine); foliage painting;
  Play From Here.
- **Unity terrain tools:** brush mask filters by slope and height.
- **Grimrock:** connectors drawn between plates, buttons and doors; instant in-editor preview
  (https://rpgcodex.net/article.php?id=8417).
- **NWN Aurora:** tile-painted areas with road and river "crossers"; wizards; conversation editor.
- **Heroes 3, Tiled:** automatic transition tiles (Wang sets).
- **World Machine, Gaea:** non-destructive heightfield graphs; masks as outputs.
- Complaints that make editors clunky: slow undo (UE4 brushes), tables instead of navigation and no transform keys
  (OpenMW-CS), crash-prone tools (Divinity: Original Sin 2), hidden modes (Doom Builder auto-finish).

## The original games

- No primary source describes NWC's in-house editor. MM6 had an outdoor engine "Horizon" and an indoor engine
  "Labyrinth" (pre-release FAQ, https://discmaster.textfiles.com/view/16071/PCPP_GG2.iso/PCPP/faqs/mm6faq.txt). Ten
  people credited with level design on MM6, four on MM8 (lead Richard Corredera); MM9 lead level design Kenneth
  Spencer (MobyGames credits). Tim Lang: some MM6 dungeons came from a Wisconsin team; the Tomb of VARN was modelled
  in LightWave.
- `map_stats.txt` names designers for some MM6 maps ("Chris" for Warlord's Fortress, "Tim" for MM6's Temple of the
  Moon).
- Shipped data: MM8 outdoor maps all carry the header `blank` / `default.odm` (cloned from a template); Shadowspire
  BModels are named `06n_poor1N`, `06n_med3E`, `06n_rich2N`, `06n_temple_AN…DN` (regional prefab library, tiers,
  multi-part assemblies, facing letters).
- Event scripts across MM6–MM8: 5 263 `SetDoorState`, 2 883 `OpenChest`, 1 565 `EnterHouse`, 1 007 `StatusText`,
  556 `MoveToMap`, 448 `SetTexture`, 389 `SummonMonsters`, 366 `CastSpell` (counted in
  `assets_dev/worlds/mm6–mm8/events/maps`).
- Community: GrayFace's MMEditor in MMExtension (in-game, Alt+F1, OBJ import, `_Portal_` textures, spawn objects
  `m1`–`m3`; https://raw.githubusercontent.com/GrayFace/MMExtension/master/MMEditor%20Readme.txt). Complaints
  (https://www.celestialheavens.com/forum/10?p=387843): missing documentation; changing a vertex wipes its faces'
  properties including door settings; modders import whole dungeons as one room to avoid portals. Mike Kienenberger's
  MM8LevelEditor (Java, 2004–05) decoded formats.

## What the plan took from this

Seven stages; plan view plus 3D view on one model; rooms drawn, sectors and portals derived; presets first and Lua
second; visible connections; face settings that survive re-import; Play here with test switches; always-on checks;
tool options separate from object properties; help inside every tool; kit libraries with tiers and assemblies.
