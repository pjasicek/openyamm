# Phase 3, lane A7's dungeon graphs: decisions (D-25)

Decider D-25, 2026-11-20. This file wins over the graphs in `act3_graphs/` (xd22, xd23, xd24, dd06, dd13, dd11a-c) and
their `notes_cloudside.md` / `notes_d2.md` where they differ.

**General rule:** a peaceful group is its own monster row in its own faction, never a map group of a hostile kind (the
game sets attitude to the party by kind; ACT2_BUILD; Q11's default). The King's Guard 11143 and Graalg's Brute 11065
are the pattern.

## Approval

All eight graphs approved for L1–L4.

- **XD-24 Nightshadow Crypt**, with changes: the iron door's refusal says "door": "The door refuses to budge. A symbol
  etched on its surface flashes pale blue whenever you try to move it." (paraphrase of aaze0029:24; "Only at night can
  you put up a fight." over the door). Once opened it stays open. Ossuary 2 + 2, niches 2 + 3. The vault stair stays
  empty of monsters (rest until 21:00).
- **XD-22 Ninja Pagoda**, with changes: Shinobu's survivors on a peaceful row (Q14). On load with `q-c4.done`: hide the
  clan's surviving hostile ninjas (as XD-23's burnt stage), the cellar hatch open, Shinobu and four survivors shown.
  Inside may be up to twice the outside in each direction but within 15 sectors and 20 M units² (shrink rooms, never
  re-class). Paper screens per Q15.
- **XD-23 Troll Warren**, with changes: the burn shows one message (below); the smoke mist's density capped (Q5).
- **DD-11A/B/C Troll Holes**, with changes: Hobstadt's court a peaceful row (Q7); the burrow's top uses the `exit`
  preset with no "Exit the Troll Hole?" question (D-24; the source line stays in the ledger); Troll Juice +2 Endurance
  (Q8).
- **DD-13 Ogre Forts**, with changes: the kennel's sabertooths a row in the ogres' faction (below); a playtest of peace
  then a burn (Q9).
- **DD-06 Southern Tower**, with changes: the bodyguards a peaceful row in the Master Thief's faction; the Master
  Thief's boss row at level 32 (Q4).

## Decisions

| # | Question | Decision | Who acts |
| --- | --- | --- | --- |
| Q1 | XD-24's vault door also night-only | Yes: the door's click reads `Xeen.isNight()` (21:00–6:00), refuses by day with the adapted line; stays open once opened; Draco then fights at any hour | A7 (door, sign, playtest day/night), A3 (ORIGINAL_LINES) |
| Q2 | XD-24's kill XP 8.5k | Accepted (the three Cloudside dungeons 19.4k of 17.9k, +8 %); the five Vampires 40 stay | A2 (Act III recount) |
| Q3 | XD-24's Gnome Vampires 32 vs a party of 25–29 | Stay: the rule is the map's band (30–40), not the party; groups of 2–3; the first room empty (D-11.3) | A7 |
| Q4 | Boss rows | 11123 Clan Master 42, look C, the Ninjas' shuriken, blink on hit 0.2; 11074 Troll Matron 32, look B, frenzy below half health; 11114 The Master Thief **32**, look C, Steal, blink on hit 0.2, faction `inner_circle` friendly to the party, NPC 5109's talking actor on it | A2 (rows), A3 (`q-c4.clan_master`, `q-d19.master_thief` point at them), A7 (place) |
| Q5 | XD-23's smoke | A harmless mist: grey smoke at share 0 on load (`evt.SetMist(0)`), the burn calls `evt.SetMist(1, 60)`, density capped so a lit wall ~1,500 away stays visible, every load with `q-c15.lair_burnt` sets 0 | A7 |
| Q6 | XD-23's chimney exit | Stays, `exit` preset at the chimney ladder's top | A6 (point on the mound's crown on X5, facing away from the smoke hole, clear of spawns), A7 (exit, playtest) |
| Q7 | Hobstadt's court | New Troll tier 11075 "Hobstadt's Guard" (Troll Guard 28, look B), faction `hobstadt` with Hobstadt 11073, friendly at load, hostile on `q-d13.hostile`; the warren's wild trolls hostile; tribute or trial makes troll kinds friendly in DD-11A/B/C only (X5, XD-23, D2's trolls stay hostile) | A2 (row, faction, relations scoped to the three maps), A7 (8 guards; hostility playtest: court peaceful/warren hostile, a fight turns all, tribute friendly in all three, X5 still hostile), A1 (only if map relations carry over) |
| Q8 | Troll Juice | +2 Endurance (permanent, base) and the weakest Poisoned, once per character; a repeat gives a line; text "This stuff is poisonous, but the experience improves you …" | A3 (player bit, hook text), A2 (record), A7 |
| Q9 | The party while a fort burns | Stays in the hall (XD-05's drum method): faces to burning timber with fire lights, hides burn away, ~4 s later charred; roof rubble in the same visit if decorations can be shown by event, else next load | A7 (+ a playtest of peace then burn: ogres hostile in the same visit, else to A1) |
| Q10 | DD-13's east gate | Explicit coordinates until A1's second-arrival word lands | A7 (inside point), A6 (D2's east-gate door) |
| Q11 | Manual of Master Thievery | 1,500 experience once per reading member (player bit); repeat "You learn nothing new" | A3 (hook, bit), A2 (Act III ledger), A7 (book in the library) |
| Q12 | DD-06's mirror | Left out | — |
| Q13 | A wrong gong answer | "The gong booms, and the echo dies away."; the door stays shut; the next click asks again | A7 |
| Q14 | Shinobu's people | New Ninja tier 11124 "Clan Survivor" (Ninja 22), faction `clan` friendly, placed only, not counted; Shinobu (NPC 4530) stands on it with look C | A2 (row), A7 (`q-c4.done` stage), A3 (Kai Wu's done line: "…The ninjas never swept. Someone lives in the cellar, though. I leave rice by the shrine.") |
| Q15 | XD-22's paper screens | The breakable-window route (Sturmford City's panes): destructible `break` brush, `doorway: true`, portal, translucent paper texture. A1 checks before XD-22's L4: (1) transparency with actors seen behind, (2) an unbroken screen stops monster movement and missiles, (3) no see-through door speckle. Fallbacks: (1) fails → opaque lamp-lit screens with painted silhouettes, the crane screen keeps its picture and hover name "Crane screen"; (2) fails → walls that break, no monsters right behind (the four go to the maze's open cells). Clicking or striking the crane screen breaks it | A1 (checks), A7 (two textures, screens), A6 (register) |

**Other items, on A7's defaults unless noted:** XD-22 inside/outside option (a) within the cap; shuriken stay. XD-23's
burn text, one message: "You burn everything you can, and what you cannot burn you throw outside. The warren fills with
smoke, and the trolls that are left will not come back to it." (A3 edits `q-c15.lair`). X5's shut mouth: A6's click
("You drag the frozen hides aside."). XD-24's Count's stair: yes. DD-11's second letter stays (A3: an ORIGINAL_LINES row
marked as paraphrase); pocket strength stays (+5 %); the three return spots on D2 from A6, ~300 from each pit's lip,
clear of D2's troll spawns (keep-clear 512). DD-13: empty halls yes; the kennel: new tier 11413 "Kennel Sabertooth"
(Sabertooth 22) in `xeen_ogres` (friendly on `friends`, hostile on `hostile`; A2). DD-06: bodyguards new Outlaws tier
11115 "Inner Circle Guard" (the Master Thief's numbers, 30, look C), faction `inner_circle`, replacing four of the nine
Master Thieves; the six Rogues 12 stay as filler; the Prince Book readable only with player bit 11292 (the Prince of
Thieves' throne in XD-15): +2 Luck once, others read "For the eyes of the prince only!" (A3 hook, A2 value).
