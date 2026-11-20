# Vanilla mode

Status: investigation only (2026-10-22). Nothing is implemented. This folder collects what a "vanilla" playthrough
of MM6, MM7 or MM8 would need, so that the work can be planned before any of it starts.

## Goal

Some players want the original single-game experience, not the merge. A vanilla new game:

- plays **one** world: MM6 (Enroth), MM7 (Antagarich) or MM8 (Jadame);
- has **no MMerge additions**: no cross-continent travel, Dimension Door, connector stones, Verdant or merged
  metaquests, no extra classes, races, quests or items, no bolstering;
- follows **that game's rules**: its classes, races, skills, masteries, spells, party size, hirelings, resistances
  and calendar;
- is chosen **once, at new game**, and stays fixed for that save.

OpenYAMM's own improvements (3D models, HD textures, terrain, weather, sky, the Obsidian UI) are presentation, not
rules. This investigation assumes they stay in vanilla mode; see the open questions.

## Documents

| Document | Contents |
|---|---|
| [ENGINE.md](ENGINE.md) | How the engine mounts content, loads tables, starts a game and saves; what a ruleset needs from it |
| [MMERGE_FEATURES.md](MMERGE_FEATURES.md) | Every MMerge feature we implement, where, and how to switch it off |
| [CONTENT_PROVENANCE.md](CONTENT_PROVENANCE.md) | Where our maps, events and tables came from; which original data we have; id numbering |
| [RULES.md](RULES.md) | Rule differences between vanilla MM6, MM7 and MM8, and what MMerge changed |
| [SPELLS.md](SPELLS.md) | The full spell list of all three games, slot by slot |

## Summary of findings

1. **The engine has no ruleset concept.** All three worlds are always mounted, every gameplay table comes from the
   single MMerge set in `engine/data_tables/`, the active world is inferred from the map name, and nothing in a
   save records which rules it was started with. See [ENGINE.md](ENGINE.md).
2. **Everything we ship is MMerge content.** Maps, events and tables were imported from MMerge's data, not the
   original games. MMerge renumbered QBits, NPCs and houses into one merged id space, but it changed very few events
   structurally (about 100 of 11,400). See [CONTENT_PROVENANCE.md](CONTENT_PROVENANCE.md).
3. **Original data is uneven.** Vanilla MM8 is fully available locally (`re_mm8/mm8_orig/`, `data/`, and our own
   pre-merge build at commit `6bb16f623`). There are **no original MM6 or MM7 binaries or tables** in the repository;
   only GrayFace's decompiled event scripts.
4. **Switching off the merge is mostly data and small gates.** Cross-world travel, continent settings, bolster,
   racial skills and the `_mmmerge` Lua overlays are table- or file-driven. A few things are hard-coded: Town Portal
   groups chosen by map-id range, Dimension Door items, and bounty hunts drawn from every world.
   See [MMERGE_FEATURES.md](MMERGE_FEATURES.md).
5. **Vanilla rules are the expensive part, and the cost grows from MM8 to MM6.**
   - MM8 is close to what we run: MMerge is built on the MM8 engine.
   - MM7 needs its 36-class, 4-race system, a fixed party of 4, hirelings and the Light/Dark choice.
   - MM6 needs 18 classes with no Grandmaster rank, 31 skills, 5 resistances, 17 conditions, no Arcomage, a
     different item table and 23 spells we don't implement.
   See [RULES.md](RULES.md) and [SPELLS.md](SPELLS.md).

## Recommended approach

Keep one engine and one merged id space; make **which content is reachable** and **which rule tables apply** a
per-save choice. Don't rebuild each game from its original ids.

- **Why not original ids.**
  - MMerge's renumbering is regular: MM6 QBits +1024 and NPCs +785; MM7 QBits +512 and NPCs +339; houses through
    a lookup table.
  - Our event exporter, overlays, tables and saves all already speak the merged ids.
  - Re-importing original ids would fork every subsystem that touches a QBit, NPC, house or item, and would need
    MM6/MM7 originals we don't have.
- **What changes per game is the ruleset:** classes, races, skills, masteries, spells, party rules, resistances,
  conditions, calendar, start map, and which worlds and travel links are reachable.

The pieces, in the order they would be built:

| Phase | Work | Depends on |
|---|---|---|
| 0 | Decide the open questions below; agree the ruleset layout and save field | — |
| 1 | **Ruleset identity.** A ruleset id (`mmerge`, `mm6`, `mm7`, `mm8`) chosen at new game, stored in the save, shown on the Load screen; a mounted-worlds allow-list; common game data reloaded when the ruleset changes | 0 |
| 2 | **Single-world content.** No cross-world travel, Dimension Door, Verdant or `_mmmerge` overlays; per-world item, loot, shop, bounty and random-monster filters; vanilla start map, date and continent settings; bolster off | 1 |
| 3 | **Vanilla MM8 rules.** Original MM8 class, skill, spell and roster tables (available locally); MM8 recruitment; remove MMerge rule tweaks | 2 |
| 4 | **Vanilla MM7 rules.** 36 classes, 4 races, party of 4, 2 hirelings, Light/Dark promotion, MM7 spell slots and damage | 2; source tables for MM7 |
| 5 | **Vanilla MM6 rules.** 18 classes, Normal/Expert/Master only, 31 skills, 5 resistances, 17 conditions, 23 MM6-only spells, MM6 items, no Arcomage | 2; source tables for MM6 |
| 6 | **Event audit.** Compare the ~100 structurally changed events and every `_mmmerge` overlay against GrayFace's vanilla decompiles; add vanilla-only overlays where MMerge altered a quest | 2 |

Phases 1 and 2 already give a useful "single continent, merged rules" mode. Phases 3 to 5 are independent of each
other and can ship one game at a time.

## Conflicts with current project rules

Vanilla mode cuts across three standing instructions in `AGENTS.md`. Each needs an explicit decision before work
starts:

- **"MM6/MM7/MM8 worlds must not own active TXT/BIN gameplay tables."** Per-game rule tables have to live somewhere.
  Proposal: a ruleset package (for example `assets_dev/engine/rulesets/mm7/`) that overrides named engine tables, not the
  world folders.
- **"Do not add a separate campaign package layer for now."** A ruleset is close to a campaign. The unread
  `assets_dev/campaigns/default/campaign.yml` and the multiplayer plan's `CampaignState` (ruleset plus content
  fingerprint) suggest the two should share one identity.
- **The merged-base principle** (shared items, skills, spells and classes). Vanilla mode keeps the merged ids but
  restricts and re-tables them per ruleset; that still has to be agreed as the interpretation.

## Open questions

1. **Baseline for "vanilla."** Retail behaviour or GrayFace's patched behaviour? GrayFace's patches fix many bugs
   and change some events (34 of 82 MM6 event files differ between `mm6orig` and `mm6`). Recommendation: GrayFace
   patched, which is what most players mean by vanilla.
2. **Presentation.** Keep OpenYAMM's 3D creatures, HD art, weather and Obsidian UI in vanilla mode, or offer a
   classic look? Recommendation: keep them; vanilla means rules and content.
3. **MMerge fixes that aren't additions.** Some MMerge changes are bug fixes (Fire Spikes, Shield, Dragon attack
   bonus, Blaster in MM8). Keep fixes, drop additions? This needs a per-item list (see [RULES.md](RULES.md)).
4. **MM6/MM7 source data.** Where do vanilla MM6 and MM7 tables come from? Options: the user's own retail/GOG
   install imported by a tool; reconstruction from MMerge plus OpenEnroth (MM7) and MMExtension; or hand-authored
   tables. Licensing of shipping original tables is the same question as the MMerge tables we ship today.
5. **Granularity.** One switch ("vanilla MM7") or separate toggles (no cross-world travel; vanilla classes;
   vanilla spells; no bolster)? Separate toggles multiply test combinations; recommendation: fixed rulesets, with
   bolster as the only extra option.
6. **Party size and creation.** MM6/MM7 create exactly 4 characters; MM8 creates 1 and recruits up to 5. Vanilla
   party creation needs per-ruleset screens or modes.
7. **Saves.** A save made under one ruleset never loads under another. Should an MMerge save be convertible to a
   vanilla one (no), or a vanilla save be continued as MMerge (possible, since the id space is shared)?

## Related findings outside vanilla mode

- **MM8 map deltas don't match the MM8 maps.** `assets_dev/worlds/mm8/_legacy/map_delta` holds the vanilla MM8
  deltas, while 14 of our MM8 maps are MMerge's edited versions (`d07`, `d12`, `d16`, `d17`, `d19`, `d41`, `elemf`,
  `out01`, `out02`, `out04`-`out07`, `out13`). See [CONTENT_PROVENANCE.md](CONTENT_PROVENANCE.md).
- **`bolster_formulas.txt` is loaded but unused**; the formulas are reimplemented in C++.
- **`additional_ui.txt` is loaded but has no consumer.**
