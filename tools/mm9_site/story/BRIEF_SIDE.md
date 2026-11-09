# Side and promotion quest walkthroughs (addendum to BRIEF.md)

Read BRIEF.md first: reader, tone, sources and their authority are the same. This addendum changes only the file
format. Side and promotion quests are not placed in chapters: a file holds a flat `quests:` list.

The guide shows every quest as: title; one-line summary (what it is); where to take it (giver, map); where to report;
then a collapsible **Walkthrough** with the steps; beside it compact maps that show only the quest's own points.

```yaml
quests:
  - quest: find-the-saboteur                    # a quest id (the list in your task)
    from: {map: sturmfordcity, npc: "Bjarni Herjolfssen"}   # who gives it: an exact POI name on that map in guide.js
    to: {map: sturmfordcity, npc: "Bjarni Herjolfssen"}     # where to report, if different or worth stating
    summary: "One sentence: what you are asked to do, in the player's terms."
    requires: "optional: what must happen first (another quest, a class, a key item)"
    steps:                                       # 3-8 concrete steps, as in BRIEF.md
      - "..."
    tips: ["optional"]
    reward: "optional: from the scripts (the rework's amounts)"
    points:                                      # extra points the maps must show (they already show every point
      - {map: sturmfordcity, name: "Randver"}    # tagged with the quest and the from/to NPCs): exact POI names
    maps:                                        # optional: which maps to show and where to focus; default: the maps
      - {map: sturmfordcity, focus: "Randver", caption: "..."}   # of the quest's points, giver first
```

If an NPC or object the quest needs has no POI in guide.js (or the wrong name or tag), list it in your report with
map, the DAT object name(s) and what it is, so the generator can add it to `tools/mm9_site/extra_pois.yml`; you may
still describe it in the steps. Promotion quests: also say what the promotion needs (classes come from
`MM9.Promotions` in `assets_dev/worlds/mm9/events/common/mm9_common.lua`; the promotions table in
`tools/mm9_site/site_config.yml` names the promoter and the quest notes it counts); report any quest notes that
belong to a promotion but are missing from that table, or listed wrongly.
