# Co-op on one PC

Several games on this PC in one co-op session, started by one command and ready to play: every game has a
prepared strong party, the first hosts, the others join it and are put beside it. For trying co-op by hand and for
agents' checks. Two games on localhost behave as two PCs on one home network do, except for the second machine's
speed (see [Two machines](../coop_two_machines/README.md) for a real second PC and a bad line).

## Start a session

```sh
tools/coop_local/yamm_multiplayer_2_parties_solo_play_standard.sh   # Standard solo run, one character each, 2 windows
tools/coop_local/yamm_multiplayer_2_parties_maw_solo_play.sh        # MAW solo run, one character each, 2 windows
tools/coop_local/yamm_multiplayer_standard_2_parties_full.sh        # Standard, two parties of five, 2 windows
tools/coop_local/yamm_multiplayer_maw_2_parties_full.sh             # MAW, two parties of five, 2 windows
tools/coop_local/yamm_multiplayer_standard_3_parties.sh             # Standard, parties of five, three and one, 3 windows
```

Each prints when all games are in the session. Close the host's window (the first one) to end them all, or press
Ctrl+C in the terminal. Only the host's window plays sound. The windows are 1280x720 for two games and 960x540 for
three; `--resolution 1600x900` changes it, and `--map out02.odm` starts on another map.

The games are isolated runs (`tools/run_game.sh --isolated`): your own settings are copied, your saves are not
touched. The game must be built first.

**The two solo sessions are solo runs** (the first-person arms and the solo HUD; `standard:solo` and `maw:solo`).
Talents are MAW's: the MAW solo session has them (`talent` in the console sets ranks), the Standard one has the
arms without talents.

**Every player plays its whole party** except in the two solo sessions, where a solo run takes one character.

## In the games

- `coop sync` in any game's console (the `~` key) brings that player to the host; in the host's console it brings
  everyone to the host, and `coop sync <player>` brings everyone to that player (1 is the first guest). A guest's
  `coop sync` works because the launcher turns the host's test commands on (`[coop] test_commands=true`); a host
  started any other way ignores it.
- `coop propose out02.odm` proposes a trip to the others, to see the travel vote without walking to an exit.
- `coop avatar 2` shows the others the second member of the game's party as its body and face (the Multiplayer
  screen has the same choice).
- `hp full` heals the game's own party; `coop damage <player> <amount>` in the host's console hurts one.
- `coop net`, `coop show` and `coop away` say what the session is doing. The other co-op console commands are in
  [the scenario notes](../../tests/scenarios/README.md).

## The parties and the sessions

`run.py --list` prints both.

| Party (`parties.json`) | Who |
| --- | --- |
| `god_lich` | one Lich, level 150, all four elements and Dark at Grandmaster |
| `god_knight` | one Knight, level 150, sword, shield and bow |
| `god_cleric` | one Cleric, level 150, with Heal as an Attack order (an ally below 60 %) and on the Upkeep list |
| `five` | Knight, Cleric, Sorcerer, Thief and Lich at level 120, with MM8, MM7 and lich faces |
| `three` | Knight, Cleric and Sorcerer at level 120, with MM7 and MM9 faces |
| `gear_fine_knight`, `gear_rich_sorceress`, `gear_relic_lich` | one character each in fine, rich and relic gear: the body's glow in the others' games is weak, strong and strongest |
| `size_dwarf`, `size_minotaur`, `size_dragon` | one character each, for the heights the bodies are drawn at |

Two sessions are for looking at the other players' bodies (`run.py standard_3_gear`, `run.py standard_4_sizes`; the
architecture's "Another player's body"): the first shows the glow by gear, the second a human, a dwarf, a minotaur
and a dragon side by side.

They have attributes of 300 to 500 and so thousands of hit points: near immortal against ordinary monsters, not
invulnerable. A party is in the scenario party format (`tests/scenarios/README.md`): add one to `parties.json`,
name it in a session of `profiles.json` (world, map, ruleset as `run_game.sh --ruleset` takes it, the players'
parties; the first hosts), and `run.py <session> --check` says whether it loads.

## For checks without watching

```sh
tools/coop_local/run.py standard_3_parties --hidden --seconds 20
```

starts the games minimized and silent, ends them after the seconds and prints how many joins the host's log names.
`--then "1:coop propose out02.odm"` has a game (0 the host, 1 the first guest) type a console line six seconds
before its screenshot. `--capture 50` has every game save a screenshot (`output/coop_local/<session>/p<n>/session.png`) that many
seconds after it is up; allow about twenty seconds for each later game to start. `--check` only prepares the
parties' saves. The games' logs are named when the session is up; the prepared saves
and tours are in `output/coop_local/<session>/`.

## How it works

1. For each player a headless scenario makes a new game with the party on the map and saves it.
2. The host's game starts from its save with a menu-input tour that types `coop host`; the launcher waits for
   "hosting on UDP port" in its log.
3. Each other game starts from its save with a tour that types `coop join 127.0.0.1` and then `coop sync`.
