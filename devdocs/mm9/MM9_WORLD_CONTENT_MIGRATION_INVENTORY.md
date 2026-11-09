# MM9 World Content Migration Inventory

## Scope

MM9 keeps its world-specific dialogue, journal content, and presentation assets under `assets_dev/worlds/mm9/`.
OpenYAMM continues to provide the normal HUD, inventory, character, map, journal, shop, chest, and other shared UI.
The only MM9-specific UI in this scope is the RUDE dialogue popup.

`mm9/extracted/` is importer input, not a runtime asset root. Migration must be deterministic and preserve the original
rows, ids, ordering, unknown fields, and source provenance.

The desired gameplay behavior is defined in `MM9_RUDE_SCR_INTEGRATION.md`.

## Import Status

The original RUDE tables, `JOURNAL.txt`, and the required RUDE popup assets listed below are copied into the MM9 world.
`NPC997.rude` now generates the world-owned `data_tables/english/quests_overlay.txt`; the shared journal loader merges
that optional overlay and evaluates its required/forbidden QBits without knowing that the content comes from MM9.

## Migrate

- NPC dialogue graphs: copy the 436 normal numbered NPC files from `RUDE/RUDE/` to `dialogue/rude/`. Retain RUDE
  semantics and all 30 columns.
- NPC names: copy `NPCNAME.rude` to `dialogue/rude/NPCNAME.rude`; it contains 439 id/name rows.
- NPC opening blurbs: copy `TOPBLURB.rude` to `dialogue/rude/TOPBLURB.rude`; it contains 439 id/text rows.
- Active quests: copy `NPC997.rude` to `dialogue/rude/NPC997.rude`. Its 143 entries use OpenYAMM's shared quest UI.
  Generate their conditional journal projection with `generate_mm9_quest_overlay.py`; do not hand-edit the overlay.
- Autonotes: copy `NPC998.rude` to `dialogue/rude/NPC998.rude`. Its 91 entries use the shared autonote UI.
- Awards: copy `NPC999.rude` to `dialogue/rude/NPC999.rude`. Its 55 entries use the shared awards UI.
- Campaign chronicle: copy `DATA/DATA/JOURNAL.txt` to `journal/JOURNAL.txt`. Its eight quoted, sometimes multiline
  history records require a real tabular parser.
- Dialogue-linked scripts: import the `.scr`/`.inc` dependency closure reached by mounted maps and NPCs into the
  existing `events/maps/` output. Include `DoRude` and `OnRudeExit`; do not bulk-import AI scripts.
- Dialogue object bindings: preserve DAT properties such as `NPCNbr`, `DoRude`, `ScriptName`, and `GreetingSound` in
  generated map event/binding sidecars. Extend the existing importer instead of maintaining a second registry.
- Quest-state registry: generate `state/quest_keys.yml` from RUDE conditions/actions and referenced script keys. Use
  namespaced MM9 ids consistently in dialogue, events, quests, notes, and awards.
- Dialogue item subset: import the MM9 items referenced by reachable RUDE/SCR behavior from authoritative MM9 item
  data. Keep canonical MM9 identity and explicit global-id mappings. Generate inventory-compatible 2D sprites from
  their source icons later; explicit gameplay-stat overrides may retune them for OpenYAMM.

The original `.rude` files should remain authoritative world assets. Generated indexes or typed caches are allowed when
useful, but they must be lossless, reproducible, and must not replace the source rows as authority.

## RUDE Popup Assets

Migrate only these MM9 presentation assets:

- `ART/ART/INTERFACESCREENS/NPCPOPUP/RUDEBG.pcx`;
- `LEFTARROWNORMAL.pcx`, `LEFTARROWHIGH.pcx`, and `LEFTARROWDOWN.pcx`;
- `RIGHTARROWNORMAL.pcx`, `RIGHTARROWHIGH.pcx`, and `RIGHTARROWDOWN.pcx`;
- `ART/ART/FONTS/RUDEFONT.pcx` and `RUDERED.pcx`;
- `NPCPOPUPCOORDS.txt` as layout/import evidence;
- `NPCDIVIDER.pcx` only if comparison against the original popup proves it is separately rendered.

Place them under `assets_dev/worlds/mm9/ui/dialogue/` and expose them through an MM9 dialogue presentation profile.
Do not migrate the `*256.pcx` fonts or `*2.pcx` arrow variants unless visual validation proves they are needed.

## Deferred

- `BOOK AND SCROLL TEXT.csv`: migrate when readable books, letters, scrolls, and quest documents are implemented.
- RUDE service operations that require MM9 items, equipment, classes, or economy tables: preserve their raw opcodes
  now and implement them incrementally through shared OpenYAMM services.
- MM9-specific notes, journal, inventory, merchant, character, map, HUD, and menu artwork: use OpenYAMM UI instead.

## Audio Ownership

`import_mm9_world_audio.py` imports every MM9 sound (all of `SOUNDS/`: ambience, monster animation and death banks,
doors, events, pickups, weapons, magic and spell banks, player sounds and footsteps, gibs, battle music; 2026-11-08: a
world must not miss a sound its scripts, effects or placements name), the NPC voices and the cutscene voices into the
MM9 world package. MM9's player-character voices (`VOICES/PC`) are the party's: `generate_mm9_pc_voices.py` converts
them and makes them voice sets 79-96 ([MM9 PC voices](../mm9_rework/MM9_PC_VOICES.md)).
Root filenames already owned by engine audio are not duplicated. MM9's explicit `QUEST.wav` script cue maps to the
shared `SoundId::Quest`, so no second quest-notification asset is needed.

The original `MM9-Song01.mp3` through `MM9-Song17.mp3` soundtrack is imported into the MM9 world's `music/` directory
with globally unique track ids `90001-90017` (`MM9-SongNN` is `900NN`). MAPSTATS "Music Track" counts CD tracks (the
CD's track 1 was data), so Music Track N plays `MM9-Song(N-1)`: the MM9 `map_stats.txt` rows store
`90000 + Music Track - 1` (`generate_mm9_map_stats_encounters.py`; Thousand Terrors' track 18 is `90017`, Song17;
Temple of Honk, blank in MAPSTATS, gets Guberland's). See [MM9 ambient audio RE](../mm9_rework/MM9_AMBIENT_AUDIO_RE.md).

## Excluded For Now

- MM9 spell tables, spell art, spell models, and spell effects; use OpenYAMM spells, spellbooks, and spell scrolls;
- MM9 items outside the dialogue-referenced incremental import, plus full weapon/projectile/shop integration;
- MM9 monster tables, models, skins, AI, combat scripts, and spawn catalogues;
- MM9 character creation, classes, player models, portraits, and voices;
- credits, main menu, options, pause, beacon, formation, and other MM9 UI screens.

No obelisk data or obelisk quest was found in the extracted MM9 RUDE, DATA, or script content. Do not create an MM9
obelisk table unless later source evidence establishes one.

## First Bootcamp Slice

For the initial playable slice, migrate `NPC436.rude`, NPC 436's rows from `NPCNAME.rude` and `TOPBLURB.rude`, the RUDE
popup assets/fonts, and the already generated `NPC436.scr`/map binding behavior. Preserve keys `474` and `475` even if
their item/reward effects remain deferred. Once that path works, migrate the complete RUDE set and shared journal data.

Raw MM9 quest keys use the reserved global QBit namespace `90000-99999`, with the reversible mapping
`qbit = 90000 + raw_key`. Raw key `0` is invalid, so QBit `90000` is reserved rather than active.
