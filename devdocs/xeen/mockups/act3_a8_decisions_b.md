# Phase 3, lane A8's graphs DD-09, DD-10A–C, DD-18: decisions (D-27)

Decider D-27, 2026-11-20. Wins over the graphs in `act3_graphs/` (dd09, dd10a-c, dd18) and
`act3_dungeon_graphs.md` where they differ. DD-01 to DD-04 are D-26's.

## Approval

- **DD-09 Temple of Bark**, with changes: no seven-potion room; limb alcoves hover "Limb alcove", root alcoves "Root
  alcove"; the Book of Ascension names the Crystal Water; freed prisoners hidden on the next entry (XD-25's pattern);
  Barkman's XP counts in Act IV (D-1.2); otherwise as drawn (22 rooms, 50 monsters, 5 chests, 4 loops, 7d22 with D2's
  bark, 2 new textures).
- **DD-10A** (west), with changes: three refill bits plus `q-d7.dug`; one exploding bone heap; Nighon Tunnels 7d35.
- **DD-10B** (east), with changes: Sand Golem 22 → Stone Golem 26 (11581); the God of Minerals refuses payment while
  nothing has been dug; refill bits as A.
- **DD-10C** (north), with changes: layout as drawn; **moves to Act V** at D6's lower band (38–50), D6's own families
  (A2 picks; no Lava Roach, Arachnoid Queen or Sand Golem), 20 monsters, treasure 5; geometry built now with A and B and
  kept in scratch; monsters, exit and install in phase 5 with D6 (A6 plans the adit). Hector's line: "Diamonds come
  only from the north adit in the Forbidden Zone. Few who go there come back." (Diamond Plate 12543 is tier 6; Act III
  diamonds would break the curve.) Act III's DD-10+11 group then ~19.3k of 22.1k (−13 %); Act V +~11k.
- **DD-18 Sandcaster Sewer**, with changes: role "Optional: Barticus' members' room; the long tunnel to D5" (MAPS row
  corrected, the Q-D14 reference removed), M size, 50 monsters; desert grate bolted on the D5 side; a find at the grate
  (a sand-buried prospector's pack); Barticus in town points down; the tunnel rumour in d3.yml.

## Decisions

| Map | Question | Decision | Who acts |
| --- | --- | --- | --- |
| DD-09 | Flasks | Red +2 Might and blue +2 Personality in the Chapel of Sap, once per character (XD-08's method); no seven-potion room | A8, A2 (record) |
| DD-09 | Black barrel | Kept, once per character, in the sap store: +1 to all seven stats and one year of age through the event age variable (the Jewel of Ages protects, D-2.4); text "Your statistics have improved, but you have suffered a little magical aging."; sign "Danger: Unpredictable Effects."; playtest asserts both; if an event cannot add age, A1 adds it (no aging message that does nothing) | A8, A2, A1 (only if needed) |
| DD-09 | Disciples' chapel | Three dials as map variables ("Dial reads N. Turn?"), then the lever, then the Crystal Water; wrong dials: "Nothing happens."; the Book's scrap ends "...pull lever and drink of the Crystal Water."; the Dark Water poisons and does ~a tenth of HP, never kills; reward the vault (treasure 3) and award "Disciple of Bark" for every member, no stat | A8 (+ playtest: wrong dials, Dark Water, right sequence), A3 (Book text, award) |
| DD-09 | Prisoners | Four peaceful talking actors (Nathan and Sky in the pens, Snog and Alicia in the cells); the pens' lever ("You hear a rumbling in the distance.") opens both sets, two-state; each first thanks topic 500 XP (`q-d10.prisoners` or a bit each); their source hints kept ("Orcs can't jump", Alicia's tea warning); hidden on the next entry | A3 (four NPC rows, topics, hook), A8, A2 (Snog peaceful by his own group, not the orcs' relation) |
| DD-09 | Orcs' tea | A clicked kettle: the source's invitation, then "Drink?"; Yes poisons the clicking member; repeatable; no NPC | A8, A3 (text) |
| DD-09 | Barkman | Hidden in his hollow, own group, shown by `show_actors` the first time any limb alcove takes a gem (map variable; stays shown after reload); his chest (hoard 4) opens only once he is dead; XP in Act IV | A8 (+ playtest: absent before, shown after, kept after reload), A2 |
| DD-09 | Roots and limbs | Arachnoids (14, Hunter 18) | — |
| DD-10 | Refill | Five veins per gem, one rock each, each a map variable; bits `refill_a`, `refill_b`, `refill_c`, each pocket's entry resets its veins and clears its bit; `q-d7.dug` set by the first vein in any pocket; the God takes 10,000 gold only while `dug` is set, else "The mountains are full. Empty them first."; paying sets all three refill bits and clears `dug` | A3 (bits, text), A8 (+ playtest: pick, pay, re-enter, full) |
| DD-10 | Traps | One false vein in B and one in C ("A gem exploded!", fire, a sixth vein), one exploding bone heap in A ("The bones explode!"), each once; damage ~⅒–⅕ of a band-level character's HP (C scaled to Act V) | A8 |
| DD-10 | Gem maker's throne | Flavour: hover "Gem maker's throne", click "The throne hums. It was not made for you." | A8 |
| DD-10 | Rock Golem | No rename, no new row: Stone Golem 26 (11581) instead of Sand Golem 22 | A8, A2 (recount) |
| DD-10 | Textures | MM7 Nighon Tunnels 7d35 for all three, MM6 6d18 lava for C's seam; four new vein textures (A 2, B 1, C 1) in one batch, one style | A6 (`dungeon_families.yml` `mines`, `textures.yml`), A8 |
| DD-18 | Role | Optional; MAPS row corrected; rumour "There is a passage in the sewer that leads a long ways under the desert." in d3.yml | A8 (MAPS row), A4 (rumour) |
| DD-18 | Barticus | Training stays in town (4607, cap 80); the sewer room is the gym's members' room under A6's `xstraining` sign; a pay box "It costs 5,000 gold to use the gym. Pay?" (the source's "charity gym" refusal when short), once per party (qbit); then the Vitamin Brew +2 Endurance and the Protein Brew +2 Might once per character; The Art of Bodybuilding readable; Barticus's town topic: "The members' room is under the street, with the brews. The stalkers got in." | A3 (texts, price, qbit), A4 (topic), A8, A2 (record) |
| DD-18 | Tunnel to D5 | Bolted on the desert side: from the sewer "Sand blows through the bars. The bolt is on the other side."; D5's grate a plain click in Act V: "You draw the bolt. The grate swings open on a long tunnel." (sets a world qbit); then the `exit` preset both ways; the find at the grate's foot | A8 (gate, find; exit in phase 5), A3 (qbit, texts), A6 (phase 5: D5 grate and arrival), A5 (D3's street shaft, entrance preset, "Descend to the sewer?" as its meaning) |
| DD-18 | Monsters | Sewer Stalker 25 and Stalker Matriarch 35, Guardian Asp 30 and Killer Cobra 38, Mantis Warrior 30 and Mantis Queen 38; no hornets | A2 (confirm +5 %) |
