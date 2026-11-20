# Research: the five walkthrough maps (2026-11-12)

Inventory measured from `assets_dev`, the case studies in `level_generation/case_studies/` and the map Lua. These
are the held-out maps of [CALIBRATION.md](../CALIBRATION.md); the design page walks through rebuilding each.

## New Sorpigal (`mm6/oute3.odm`)

- 128 × 128 grid at 512; party bounds ±23 143; about 70 % water; town on a coast with islets and a volcano isle.
- 90 BModels, 3 161 faces; 17 homes, services (temple, guilds, shops, bank, stables, tavern in two parts, small keep),
  walls and gate, 3 bridges, pier, crates as chests, wells, fountains, obelisk, Shrine of Luck, dungeon entrances
  (Goblinwatch, Abandoned Temple, Gharik's Forge), dragon tower.
- 479 decorations (371 trees, 41 rocks, flowers, campfires, barrels); 13 carry events (fruit trees with sprite swap,
  buoy volcano, sword in stone, campfire ambush).
- 56 spawns (goblins, peasants), 43 actors, 42 ground items, 18 bound chests.
- 37 `EnterHouse` calls (15 named services, 22 homes). Wells (gold if broke weekly; +2 Luck monthly), fountains
  (+5 HP / SP, 30 charges, daily reset), shrine (month 6), bridge ambush plate, dragon tower fireball timer disabled by
  carrying the keys.
- Exits: west edge to Castle Ironfist (5 days), Goblinwatch (locked by item 2109), Abandoned Temple, Gharik's Forge,
  Dragonsand via the Buccaneers' Lair; boat and coach services.

## Goblinwatch (`mm6/6d01.blv`)

- 59 sectors, 60 portals, 2 290 faces; floors −1280 to +512; long cave arms either side of a built core.
- 38 doors: portcullis-style up doors (120), sliding walls (250–500), a lowering block (504), a moving switch.
- Vault puzzle: 16 lettered keys A–P, one-shot, texture swap `t1swdd` → `t1swdu`; A also casts Fireball, M teleports
  to the maintenance tunnel, P resets; "NILBOG" works. Pillar button lowers two corner pillars hiding treasure rooms.
- 159 lights, 156 torches, 21 campfires; 66 spawns (rat, goblin, bloodsucker); 10 face-built chests.
- Issues in the original: events 38, 54, 57, 58 bound to faces without handlers. (An earlier note here, "key E
  checks key D's map variable", was a misreading: events 20 to 25 test MapVar0 to MapVar5, one each.)

## Shadowspire (`mm8/out06.odm`)

- 84 BModels, 4 507 faces; MM8 makes whole buildings clickable. 41 `06n_*` homes in poor/medium/rich tiers; 11
  services and 33 residences.
- Dungeon entrances as façade models: `d19entrance` (6 parts, up to 4 352 tall), `d20out`, `d21out`, `d49out`.
- 607 decorations (skeletons 95, rune posts 225, dead trees 84, rocks 159); three rune posts are skill-check rewards
  (Disarm Trap 3/5/7).
- 63 spawns (vampire, skeleton archer, bone dragon), 27 actors (19 vampire peasants in group 10, hostile on load;
  8 necromancers); tar pools; random fog days via overlay.
- Exits: north and east to `out04`, south and west to `out02` (direction mapping to confirm).

## Mad Necromancer's Lab (`mm8/d20.blv`)

- 28 sectors, 25 portals, 1 614 faces; three floors (−1024…−896, 0…256, ~545…896); a lift of 513; four double sliding
  doors.
- Traps: hidden plates casting Grandmaster Blades and Fireballs, triggerable by monsters, levitation avoids.
- Prisoner Blazen Stormlance behind a cell door (talk unless in party); bookshelves with random scrolls; drinkable
  vats; group 10 hostile on load, invisible once the Ebonest QBit is set.
- 26 spawns all in group 10; 49 ground items; 4 bound chests.
- Issue in the original: events 14–60 reference doors that do not exist.

## Gharik's Forge (`mm6/6d18.blv`)

- 48 sectors, 58 portals, 2 561 faces; vertical span about 4 950 (floors 1152, 0…128, −896…−384, −2304…−1920).
- 53 doors (25 lever handles); 33 lever events; levers 33–40 toggle overlapping door sets; a bridge mover of 1 280 over
  lava; an elevator floor dropping 2 032; a secret door to the bridge lever; a balcony sequence puzzle (upper NW,
  lower NE, lower SE, lower NW, upper NE).
- Lab door needs the Key to Gharik's Laboratory (2107, from Silver Helm Outpost) and QBits 1035/1223/1400.
- 31 lava faces (originally timer-scripted damage; an overlay converts them to native lava), six eruption timers,
  teleport rescue tiles, a once-per-character fire resistance wall; 52 spawns (sorcerers, fire elementals), 83 lights.
- Issues in the original: lever 35 drives door 53, which has no geometry; faces 115 and 118 overlap on one plane.
