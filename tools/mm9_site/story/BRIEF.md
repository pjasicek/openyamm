# Writing the MM9 guide's main-story walkthrough

The guide's Main story page (tools/mm9_site) renders hand-written walkthrough files from this folder, one per part:
`prologue_ch1a.yml`, `ch1b.yml`, `ch1c_ch2.yml`, `ch3_5.yml`. Each file is read by `build_site.py`; the page shows every
chapter expanded, as a document (no cards), with small inline maps beside the text.

## Reader and tone

A player on a blind first playthrough of MM9 as rebuilt in OpenYAMM. They want to know exactly what to do: where the
giver stands, where to go, what to click, kill or carry, puzzle solutions, traps to expect, the order of things, what is
easy to miss ("the keep has two entrances; three of the eight imp gates are only reachable from the north gate"), and
where to report. Concise and factual, no fluff, no story retelling, no headings inside steps. Plain sentences, second
person ("Enter by the north gate"). 3-8 steps per quest; tips only for things genuinely useful.

## Sources, in order of authority

1. **This rework's own data** (authoritative; the rebuilt maps can differ from the original MM9):
   - `assets_dev/worlds/mm9/events/maps/<map>.lua`: each handler's comments describe the mechanic precisely
     (doors, levers, puzzles, triggers, keys, items, rewards). Read the relevant map scripts fully for your quests.
   - `assets_dev/worlds/mm9/dialogue/rude/NPC<id>.rude` (CSV: npc, node, row, "player line", "answer", next node,
     required key, forbidden key, required key 2, ...; granted keys in later columns): what NPCs say and ask for.
   - `assets_dev/worlds/mm9/data_tables/english/quests_overlay.txt`: the journal notes (stage texts).
   - `assets_dev/worlds/mm9/state/quest_interactions.yml` `journal_stages`: which keys show and hide each note.
   - `output/mm9_site/data/guide.js` (`window.GUIDE` JSON): maps with their points of interest (`maps[].pois`: `t` type,
     `n` name, `d` detail, `quests`), NPC names and where they stand, quests with givers, steps, stages.
   - Map images: `output/mm9_site/img/maps/<map>.webp` (you can look at them to describe directions).
2. **Online guides** for player tips and puzzle answers, used only where they agree with the data:
   - `tools/mm9_site/story/online_notes.md`: notes already extracted from Lu Richardson's walkthrough (rpggamers.com).
   - The official MM9 hint book: https://mocagh.org/nwc/mm9-hintbook.pdf (fetch it; the most reliable online source).
   - UHS hints https://uhs-hints.com/uhsweb/mm9.php, the Italian solution
     https://multiplayer.it/soluzioni/la-soluzione-completa-di-might-magic-ix.html, stopgame.ru's walkthrough
     https://stopgame.ru/show/2416/might_and_magic_ix_writ_of_fate_prohozhdenie (and /p2).
   Paraphrase; never paste long text. When an online guide contradicts the scripts, follow the scripts and drop the tip.
   When the rework changes something on purpose, the scripts' comments say so ("MM9 ... ; here ..."): describe the
   rework's behaviour.

## File format (YAML)

```yaml
chapters:
  - id: 1                      # 0 prologue, 1-5 the chronicle's chapters (see below)
    title: "I: The Six Clans of the Chedian"
    intro: "One or two sentences: the goal of the chapter and how it is structured."
    sections:
      - title: "Sturmford: Jarl Bjarni Thorvaldssen"
        intro: "Where the Jarl is, what he wants (optional, one sentence)."
        giver: {map: sturmfordcity, npc: "Bjarni Thorvaldssen"}   # an NPC on that map (exact name from guide.js); optional
        quests:
          - quest: clear-out-anskram-keep        # a quest id from the list below
            requires: "optional: what must happen first"
            steps:
              - "Take the road north from Sturmford City to Anskram Keep; ..."
            tips:
              - "optional, short"
            reward: "optional: what the report gives (from the scripts)"
            figures:                              # optional: pictures under the steps, files in story/img/
              - img: darkpassageway_mirrors.webp
                caption: "What the picture shows."
            maps:                                 # 1-2 inline maps per quest, the ones the player needs
              - map: anskramkeep
                show: [exit, objective, lever, secret, trap]   # marker types to draw (see types below)
                focus: "Imp gate"                 # optional: a POI name substring to select at first
                caption: "The eight imp gates; the two marked north are reached from the north gate."
```

Marker types available: teacher, promoter, quest (quest NPC), vendor, service, transport, hireling, npc, objective
(quest step), exit, chest, loot, bonus, lever, secret, hint, teleporter, breakable, trap, ladder, door, monster.
A map's points are listed in guide.js; only reference map ids and names that exist there. If a needed point is missing
from guide.js (for example the imp gates are not marked), say so in your final report with the map, the DAT object
names and their positions from the scripts or `assets_editor_dev/worlds/mm9/maps/<map>.raw_objects.yml`, so the
generator can add them; you may still describe them in the steps.

Quest ids for the main story (keep exactly these; group sub-quests under their parent with one entry each):
prologue: complete-your-training, search-for-anyone-living-on-this-island, find-yrsa-the-troll, help-yrsa-the-troll,
kill-the-bone-thrashers, find-a-way-off-the-island.
ch1: unite-the-clans, clear-out-anskram-keep, rescue-ivsar-forktooth, disable-anskram-keep-s-defenses,
retrieve-the-crona-kiga-from-the-chasm-of-the-dead, retrieve-thjorad-from-lindisfarne,
find-out-why-the-elemental-thjorad-production-has-stopped (with sub-notes find-the-cave-in,
break-through-the-hard-rock, fix-the-refinery-machine: give each its own entry right after the parent),
get-the-book-of-rules-from-the-ta-sar-academy, beat-ivan-the-smart-at-trivia, defeat-yanmir-the-frost-giant,
break-up-the-ice-that-surrounds-the-docks, rid-thronheim-of-honk-worshippers, find-the-mountain-pass,
go-to-thronheim-for-the-war-council.
ch2: stop-the-war-between-sturmford-and-drangheim, win-a-prize-at-the-thing-for-yrsa-s-daughter, return-to-war-council,
meet-army-in-yorwick, get-your-army-back.
ch3: get-a-writ-of-fate, take-the-capstone-of-order-to-the-verhoffin-ruins, pick-up-the-writ-of-fate,
return-to-arslegard.
ch4: light-the-six-fires-of-penance, speak-to-sven-forkbeard, lead-army-against-the-beldonian-hordes.
ch5: find-out-why-you-and-tamur-leng-have-writs-of-fate, stand-before-krohn,
imprison-njam-the-meddler-in-the-tomb-of-1000-terrors.

Established facts (from the Jarls' dialogue conditions): each Jarl joins only after **both** of their tasks are done:
Bjarni (Sturmford): Clear out Anskram Keep + Rescue Ivsar Forktooth; Sigmund the Stressed (Drangheim): Disable Anskram
Keep's defenses + Retrieve the Crona Kiga; Sven Forkbeard (Thjorgard): Retrieve Thjorad + restart Elemental Thjorad
production; Markel the Great (Guberland): Book of Rules + Beat Ivan at trivia; Tryggva Ravenlocks (Frosgard): Defeat
Yanmir + Break up the dock ice; Kira the Cold (Thronheim): Rid Thronheim of Honk worshippers + Find the Mountain Pass.
The six pledges (keys 82, 38, 51, 34, 63, 74) give key 178 at any Jarl, then "the clans are united" (key 83) starts the
war council. "Slay the Dragon" (Snorri the Fist) is not part of the main story; leave it out. Chapter I's sections are
one per clan, in a sensible travel order starting from Sturmford.

## Your final report

Reply with: the file you wrote, a list of facts you could not confirm (and what you assumed), and the POIs the
generator should add (map, label, DAT object names, positions). Do not edit any other file.
