# D-101: roofs over the castle wall walks (F21 follow-up), 2026-11-22

Decider's ruling on whether D-97's open battlements stand or the walks get ceilings.

## Decision

- **Q1, Castle Xeen (XD-19) and Castle Basenji (XD-14): (a) keep the open-battlement fix.** The four XD-19 walks
  (`wall_ws`, `wall_wn`, `wall_es`, `wall_en`) and XD-14's `battlements`, `roof_walk` and `moon_tower` stay open to the
  sky, with the outer wall drawn as sky over a 160-high parapet (the wall solid). No ceilings.
- **Q2, Castle Blackfang (DD-14) north walk: (c) keep as built.** Its inner parapet (sill 224, no lintel, 32 thick)
  opens over the courtyard along the whole walk; the 512 outer wall with its skull frieze is the brief's choice.
- **The other 50 open-sky sectors:** none changes. Every kind in the survey (courtyards, ruins, the arena, shafts,
  pits and skylights, terraces, the ravine, the canopy, the open-air maps) is named open by its brief and reads open
  at eye level in the captures.

## The rule (D-97 confirmed, with two additions)

1. **Sky only where the brief names the place outdoors** (D-97's list). Every room or corridor the brief does not
   name outdoors has a ceiling: turrets, galleries, stairs, halls, passages between rooms.
2. **An open place must read open at eye level, not only when the player looks up.** A walk (battlements, wall walk,
   bridge, roof walk) is open along one long side with no lintel above the opening: either a parapet over a
   courtyard or other open sector of the same map (sill at most 320, DD-14's 224 is fine), or its outer wall drawn as
   sky over a parapet. Any other open room opens on a side or is at least 0.75 times as wide as its walls are high.
   A skylight covers at most 35 % of a roofed room's floor. (All D-97.)
3. **New: a parapet whose far side is the void (sky drawn in the wall, nothing of the map beyond) is 160 to 224 high**,
   at least the party's eye height, so the empty ground below the horizon is never seen while standing, and no
   higher than 224, so it still reads as a parapet. The wall behind the sky stays solid (no falls, no missiles out).
4. **New: a walk that fails rule 2 is opened, not roofed**, when its brief gives the sky a purpose (battlements, a
   sky fortress, a moon or flight event); it is roofed only when the brief names it a covered corridor and the sky
   was the generator's theme default.

Not required: crenellations. Merlons on the sky-side parapets would sell "battlement" further and are a welcome
polish later, but a plain coped parapet is MM-style simple and enough.

## Reasoning (short)

- The before captures read as corridors with the lid off; the after captures read as rampart walks with the horizon
  on the parapet line. The fault the user saw was the reading, and the fix removes it in both castles.
- Castle Xeen is the villain's sky fortress on the Clouds of Xeen (MM4: "Now entering Xeendom", "Xeen's Aviary"); its
  brief's mood is "open sky over the battlements". Basenji's moon tower is where the cult calls the moon. Roofing them
  would remove what the briefs built them for; a roofed tower top makes no sense.
- MM6–MM8 indoor castles are mostly roofed, but Xeen in OpenYAMM already uses open-sky BLVs as a world convention
  (X9 itself, the planes, D7). These walks are short, few and on the castles' top floors; everything else is roofed.
  The structural rule (named outdoors, reads open, otherwise a ceiling) is what the U-rows ask for.
- DD-14's north walk already passes rule 2: its whole inner side opens over the courtyard (`before/dd14/03-user_level.png`).
  Lowering the outer wall would lose the high frieze wall that gives Blackfang its closed, gloomy ring.

## Sites affected

- None to rebuild. XD-19 and XD-14 stay as D-97 installed them; DD-14 stays as built.
- `tools/xeen/check_open_sky.py`: same rule, one addition. For a sector of kind `battlements`, `wall_walk`, `terrace`
  or `bridge`, a sky face set in a wall (now only counted) is judged: its sill must be 160 to 224 over the floor, else
  ERROR. The seven D-97 sites pass (160). Open-air maps (D7, P1-P5, X8, X9) and views out (dd02, xd11, xd12, xd17 and
  the rest) stay counted, not judged. Owner: A7 (or whoever next touches the check).
- `tools/xeen/open_sky.yml` and D-97 stand; D-101 adds rule items 3 and 4.

## Rulings I was unsure of

- **The user's intent.** "I dont see the roof" and "should there be roof?" may mean the user wanted ceilings, not
  battlements. I judged the reading, not the words. If the user says these walks should be roofed, (b) is cheap
  (drop the sky theme on the seven rooms) and the rule's item 4 flips for them.
- **Blackfang (Q2).** The user asked in exactly this walk, looking up at 63°, after the inner opening existed, so the
  open side did not fully answer him. Keeping it is a judgment for the brief's high walls; a 160 outer parapet like
  the others is the fallback if he raises it again.
- **The original's presentation.** The research files describe Castle Xeen and Basenji's content, not how their
  upper floors were drawn; I relied on the setting (sky fortress, tower top), not on a measured source.
- **The 224 upper bound** for a void-side parapet is a judgment, chosen to match DD-14's inner sill.
