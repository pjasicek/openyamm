# Secret faces and Perception difficulty for MM6 maps

Secret faces are faces with `FaceAttribute::IsSecret` (`0x2`). The renderers pulse them red when the party detects
secrets: party Perception >= 2 x the map's Perception difficulty (`GameMechanics::partyDetectsSecretFaces`,
`map_stats.txt` column "Per"). MM7 and MM8 designers authored both. Original MM6 has neither: no MM6 BLV face carries
the bit (MMerge ships the same files) and every MM6 row had Per 0. This folder adds both to the MM6 dungeons
(2026-11-04).

| Script | Does |
|---|---|
| `perception_difficulty.py` | fits Per to monster strength on MM7/MM8 and writes it for a world (`--check`, `--write`) |
| `secret_faces.py` | `calibrate` (rules against MM7's flags), `select` (the MM6 set), `apply [--check]` |
| `review_shots.py` | engine screenshots in front of given faces, one isolated run per map, and a contact sheet |

`apply` and `--write` are idempotent; `--check` on both passes for the committed state. Related:
`tools/pressure_plate_inventory.py` (what each plate does and whether Levitate skips it).

## Perception difficulty

Monster strength of a map is the strongest of its three encounter slots. A slot's strength is the A/B/C levels of its
monster (`monster_data.txt` by picture), weighted by the slot's 1-5 difficulty. On the 102 MM7/MM8 maps with a
difficulty and monsters, `per = 1.883 * sqrt(strength) - 0.909` fits with about 3.3 points of rms error (linear and log
fits are as good). It is rounded and clamped to 1-20. Maps without encounter monsters get 1 (the Arena, NWC and the
small "pending" z-maps), like MM7's Arena.

MM6 results run from 3 (Goblinwatch, Abandoned Temple) to 16 (Temple of the Snake, Dragon's Lair). Shadow Guild gets
10 and Castle Kriegspire 14. The correlation with MM6's own Lock values is 0.65.

The alternative would have been Lock difficulty: in MM7, Per equals Lock on every map, and MM8 matches it on 17 of 47
maps (correlation 0.91). MM6's Lock values only go up to 10, though, and 13 maps hold the default 1, so the user chose
the monster fit. MAW's ruleset patches do not touch the column.

## Which faces: calibration on MM7

`secret_faces.py calibrate` reproduces these numbers.

- 95 % of MM7's secret faces are on doors opened by clicking the door itself. MM7 flags the clickable faces, often
  only 1-3 per door, and often small trims.
- No texture or geometry rule reproduces MM7's choices: precision is at most about 0.4. A "camouflaged front"
  (the front's texture is mostly a static-wall texture of the map and appears on the static walls of the door's rooms)
  finds 74 % of the flagged doors with 0.34 precision. MM7 leaves many plainly camouflaged doors unflagged, and the
  false positives cluster in 7d11, 7d20, 7d27, 7d33 and 7d37.
- MM7 flags its bookcase-style doors without exception: Bookcase, Wine Rack, Vault.
- Camouflaged doors opened only from elsewhere are almost never flagged: 2 of the 63 with a hidden trigger (both
  opened by hidden plates), 0 of the 25 behind a visible lever or switch.
- MM7 flags only 6 of its 977 pressure plates, mostly spell traps.

MM6 is cleaner for this: its ordinary doors almost all carry a "Door" hint (388 self-opening doors against 47 with none). So a camouflaged door with no hover text is hidden by construction.

## The MM6 selection (`secret_faces.py select`)

47 secrets on 90 faces in 22 maps:

- **Hidden doors (34).** Doors opened by clicking them, with a camouflaged clickable front of at least 128x128 and
  no hint, "Wall" or "Flickering Torch". All of the door's self-opening clickable faces are flagged (64 faces in 16
  maps).
- **Remote hidden walls (9).** Camouflaged doors opened only from elsewhere, by an unlabelled plate or face (cd2's
  Signs count as unlabelled here), at least 128x128. Each gets its front and the other faces of the door with the
  same texture and at least a quarter of its area. A wall opened by a visible switch or lever is a puzzle the player
  can see, so those 67 stay unmarked.
- **Triggers (3 maps, 5 faces).** zdtl01's Dresser, which slides aside. cd2's two Signs ("The crimson embers will lead
  the way"), which open hidden walls 11 and 13. The pyramid's unlabelled patterned panel 2066, which teleports.

### Review decisions

Each kind was checked in engine screenshots (`review_shots.py`). Every kept sample was a plain wall, usually at a
corridor's dead end. These were rejected or left out:

- **Too small (under 128x128):** cd1 door 35 (a framed floor hatch), cd3 door 19, hive door 35, zdwj01 door 1
  (door texture, zero area), and oracle door 2 (a girder).
- **Drawn as doors:** the pyramid's "Picture Door" panels, which also say "Door" on hover.
- **Remote walls:** cd2 door 10 (the water-tile barrier), 6d07 door 42 (a big moving section of a hall), and 6d08
  door 2 (the second leaf of an ordinary door pair). These are listed in `REMOTE_EXCLUDED`.
- **Not secrets:** the oracle "Panel" and the sewer "Cylinder" (visible machinery, quest-gated). cd2's door-12 Sign,
  which lights a lava puzzle. 6d07's Mural, which springs an ambush. cd2's water tiles (a barrier).
- **Named story objects:** "Monolith", "Wolf Altar", "Lord of Fire". Their hover text already invites a click.
- **Decorations:** 6d13's "Strange rock", "Druid statue", "Nice Flower" and "Strange tree" open hidden walls, but they
  are decorations, not faces, and cannot carry the bit.
- **Not done:** trap plates (MM7 flags almost none) and outdoor maps.

## Caveats

- **The overrides live in `initial_state`:** a map an existing save has already visited probably keeps its saved face
  attributes, so the flags would show only on a first visit. This is not verified, and no migration exists.
- **Perception gating is not verified:** the default isolated test party saw the pulse even in 6t4, which needs
  Perception 30.
- **Map-specific constants:** the selection constants (`MIN_FRONT_AREA`, hint sets, `REMOTE_EXCLUDED`, `TRIGGERS`)
  encode the review above. Re-running on changed maps needs a new review of what changes.
