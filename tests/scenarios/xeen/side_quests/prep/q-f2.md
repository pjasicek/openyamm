# Q-F2 The Dungeon of Death: prep

Quest file `source/quests/q-f2.yml`; started 114040, done 114041, shrines 114043-114045; FD-04 bits 118130 (door),
118131-118142 (words), 118143 (crossword), 118144 (shutter), 118145 (machine), 118148 (Ultimate), 118149 (code).
Preconditions: m39.done 111781 and the Key to the Dragon Tower 12376 (M39); q-d23.released 113462 and Sandro's Key to
the Dungeon of Death 12354 (Q-D23) — console bits and `grant_item`.

- Entry: X7's crag gate (event 66) -> FD-04 (0, -1280, 0); Sandro's door event 75 (door 8) from (0, -700).
- Floors: crossword z -1,024 (cellar stair from the gate hall's north side), Sandro's halls -1,792 (the descent, event
  47 / door 5, at the crossword's north end, (0, 3000)), the gong hall and machine floor -2,560 (the bone stair north of
  the throne room). Clear radii 700 (the floors are 768 apart).
- Sandro's halls have **no opening between the ballroom and the throne room**: welcome (0, 4800) -> ballroom pair
  (event 50, doors 1-2) -> game west (-1568, 5760) -> lesser shrines (-1568, 7000) -> throne (0, 7000) -> great
  shrines (1568, 7000). The crypt door is event 52 (door 4), coffins 42-45.
- Events: clues 18-40 (even), answers as in hooks_fd04.yml (any listed spelling); shrines 82/80/78 (Minor/Lesser/
  Great, Yes/No), 84 the Ultimate (out to X7 (-17920, 16384)); gongs 58/60/62/64, lever 68, the reset chest 16;
  terminal 98 (control room (-1344, 10432), reached through the machine hall); machine 69 (stand (-300, 11500)).
- Reload note: Autobots walk into the machine hall's doorway to maintenance while the party is at the terminal; the
  walk back clears them first.
- Plaques and gongs are clicked from the middle of their halls (click() is not range-gated, as hooks_fd04.yml).
