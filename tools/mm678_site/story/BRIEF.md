# Writing the MM6, MM7 and MM8 walkthroughs

The MM6 (Enroth), MM7 (Antagarich) and MM8 (Jadame) books of the OpenYAMM Guide (`tools/oy_guide/`) render
hand-written walkthroughs from `story/<world>/*.yml` (read in file-name order) and a FAQ from `faq/<world>/faq.yml`.
`build_site.py --world <world> --skip-images` loads and checks them (every quest id, map, marker type, NPC and point
must exist in the generated data) and writes `output/<world>_site/`.

## Reader and tone

A player on a blind first playthrough of the game as OpenYAMM plays it under the Standard (MMMerge) ruleset. They want
to know exactly what to do: where the giver stands, where to go, what to click, kill or carry, puzzle solutions, keys
and doors, traps, the order of things, what is easy to miss, and where to report. Concise and factual, no fluff, no
story retelling, no headings inside steps. Plain sentences, second person ("Take the east door"). 3-8 steps per quest;
tips only when genuinely useful. Name quests and places as the game does.

## Sources, in order of authority

1. **OpenYAMM's own data** (authoritative; the merged game differs from the original games in places):
   - Map scripts `assets_dev/worlds/<world>/events/maps/<map>.lua` and their `<map>_mmmerge.lua` overlays (doors,
     levers, puzzles, triggers, quest bits set or checked, items given or taken, rewards).
   - Global events (NPC topics, quest dialogue): `assets_dev/engine/events/Global.lua` and the per-world global files
     beside it; NPC topic texts `assets_dev/engine/data_tables/npc_topic.txt`, `npc_topic_text.txt`, `npc.txt`.
   - Journal notes `assets_dev/engine/data_tables/english/quests.txt` (Owner Enroth / Antagarich / Jadame; the Notes
     column often names giver and taker), autonotes `autonote.txt`.
   - `output/<world>_site/data/guide.js` (`window.GUIDE` JSON): maps with their points (`maps[].pois`: `t` type, `n`
     name, `d` detail, `quests`), quests (`id` like `q642`, `cat`, `chapter`, givers, steps, stages, reward, `path`),
     promotions. Map images in `output/<world>_site/img/maps/` (look at them to describe directions).
   - `tools/mm678_site/site_config.yml` (your book's section): chapters, main-story quest lists, giver texts.
2. **Behaviour references** for intent: GrayFace's decompiled scripts `reference/mmext-scripts/Decompiled_Scripts/`
   (per-world `txt/` folders read best), MMMerge data `reference/mmerge_data_forus/`. Never copy script code.
3. **Online walkthroughs** for player tips and puzzle answers, only where they agree with the data (paraphrase, never
   paste). When a source contradicts OpenYAMM's scripts, follow the scripts.

## Files

- `story/<world>/main.yml`: the main story, `chapters:` with `id` matching `site_config.yml`'s chapters (their names
  win), `intro`, and `sections` (one per hub or quest giver) holding `quests:` entries. MM7: chapters V and VI are the
  Light and Dark paths; say in chapter IV how the choice is made and what it closes off.
- `story/<world>/side.yml` and `story/<world>/promotions.yml`: flat `quests:` lists (no chapters), one entry per quest.
  Promotions: for each class line, the giver, the task, where, and what the promotion gives; MM7 notes Light/Dark.
- `faq/<world>/faq.yml`: `questions:` with `id`, `short`, `q`, `answer` (list of paragraphs, `[text](#route)` links:
  `#map-<map>`, `#map-<map>-<poi>`, `#quest-<id>`, `#teachers`, `#travel`), optional `figures`. 6-12 questions a new
  player of this world asks (getting started, money, travel and the stables/boats, where to train, promotions, the
  other continents and how to reach them in OpenYAMM, things the merged game does differently).

Entry format, same as the MM9 guide (`tools/mm9_site/story/BRIEF.md` "File format", and its `ch1b.yml` as a model):

```yaml
chapters:
  - id: 1
    intro: "One or two sentences: the chapter's goal and structure."
    sections:
      - title: "Emerald Island"
        giver: {map: 7out01, npc: "Lord Markham"}     # optional: an NPC point name on that map, exact
        quests:
          - quest: q513
            requires: "optional"
            steps: ["...", "..."]
            tips: ["optional"]
            reward: "optional, from the scripts"
            maps:                                     # 1-2 compact maps the player needs
              - map: 7out01
                show: [objective, quest, exit, chest]
                focus: "optional POI name substring"
                caption: "What the map shows."
```

Marker types: see `poiTypes` in your book's guide.js. Reference only map ids, NPC names and points that exist there.

## Classification

`site_config.yml` decides main / side / promotion and the chapters. If a quest is clearly misfiled (a side errand in
the main story, a main-story step missing), fix your own book's section in `site_config.yml` with targeted edits (other
writers edit the other books' sections at the same time; never rewrite the file). Quests the generator split into
several journal lines may share one walkthrough: write it on the first and keep the others short ("see ...").

## Rules

- Player text: no developer wording (quest bits, event numbers, identifiers, "the script", file names). The build
  refuses it.
- Rebuild with `python3 tools/mm678_site/build_site.py --world <world> --skip-images` (about 20 s, Python only) until
  it passes; then check your pages render in the book's standalone page (`output/<world>_site/index.html#quests-main`,
  headless Chrome is available as `google-chrome`). Do not run `tools/oy_guide/build.py` (the lead assembles the guide;
  parallel runs would clobber each other).
- Only edit `story/<world>/`, `faq/<world>/` and your book's section of `site_config.yml`. No git commands.
