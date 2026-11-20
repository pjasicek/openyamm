# Arena dialogue and encounters

Checked on 2026-09-29 with Rizin 0.10.0 against the original GOG-distribution
`mm8_orig/MM8-Rel.exe`, SHA-256
`5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b`.
See [binary provenance](GOG_INSTALLER_VERIFICATION.md) and the [Rizin guide](RIZIN_GUIDE.md).
The executable was opened read-only. These addresses describe disk code in that executable;
they must not be reused for the patched `mm8.exe` or MMerge's runtime hooks.

## Original MM8 behavior

| Address | Observation |
| --- | --- |
| `0x4bce65` | Topic dispatch recognizes 704 and calls the native Arena handler. |
| `0x4bc37d` | Arena interaction: difficulty offer, unfinished fight, reward, or already claimed. |
| `0xb2155f` | Challenge byte: zero before starting, `0x55`–`0x58` for difficulties, `0xff` after reward. |
| `0x4bc3b4` | Completion scans actors, excluding dead/removed/disabled actors and party summons. |
| `0x4bc3ed` | Unfinished fights return the party to `(3849, 5770, 1)`, yaw 512/2048 of a turn. |
| `0x4bc44a` | Victory increments the difficulty's win count, grants awards 46–49, and pays once. |
| `0x4bc60d` | Opponent creation uses the supplied coordinates at Z=257, hostility 4, group 1 (`0x4bc74f`), and clears loot. |
| `0x4bc7b5` | Challenge generation selects level-eligible opponent types and spawns the encounter. |
| `0x4bcb3f`–`0x4bcb9e` | Opponent counts and gold multipliers depend on difficulty. |
| `0x503138` | Twenty pairs of opponent spawn coordinates. |

Let L be the highest effective level of a party member. Bounds in the monster level column
are individually clamped to 2–100. Integer division rounds down.

| Difficulty | Monster levels | Opponents | Gold |
| --- | --- | --- | --- |
| Page | L/2 through L | 6–8 | 50 × L |
| Squire | L/2 through 3L/2 | 6–12 | 100 × L |
| Knight | L/2 through 2L | 10–20 | 200 × L |
| Lord | L through 2L | 20 | 500 × L |

The candidate list supplies up to six randomly selected types, with replacement, from which
the individual opponents are drawn. The Lord lower bound is L in this executable. Both
returning to an unfinished fight and claiming a reward play sound 14060.

Useful read-only commands, after checking the executable hash:

```bash
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -c 'pd 40 @ 0x4bce40;pd 190 @ 0x4bc37d' re_mm8/mm8_orig/MM8-Rel.exe
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 \
  -c 'pd 290 @ 0x4bc7b5;pxw 160 @ 0x503138' re_mm8/mm8_orig/MM8-Rel.exe
```

## OpenYAMM implementation

The missing topic was a native engine action, not an absent map EVT handler. Shared
`ArenaRuntime` now handles topic 704 and all four difficulties. The map-local scene overlays
own the merged monster ID pool and spawn positions; no campaign branch is needed in the runtime.

| World | Map | Arena Master NPC in merged data | Eligible ID range before level/kind filtering |
| --- | --- | --- | --- |
| MM6 | `zarena.blv` | 313 | 475–652 |
| MM7 | `7d05.blv` | 639 | 199–474 |
| MM8 | `d42.blv` | 313 | 1–198 |

World ownership follows the merged table's import ranges. Reused sprite names do not establish
monster ownership. `NoArena` and `Peasant` kinds are excluded. Custom Arenas can declare their
own pools and coordinates in their scene data. The shared count, level, and reward rules follow
the MM8 instructions above; MM6/MM7 binaries were not separately disassembled for this change.
The supplied MM6/MM7/MM8 Arena geometry supports the same spawn layout.

The challenge's difficulty, gold and claimed state live in named map variables. They travel
with normal map snapshots and saves. Each new Arena visit starts with fresh map state, while
loading a save resumes its existing visit. Party win counters and awards remain persistent.
Arena actors activate through the normal indoor AI synchronization and have procedural loot
disabled. Possible opponents' animation definitions are registered when the empty map loads;
sprite textures remain loaded on demand.

`tests/ArenaRuntimeTests.cpp` covers all worlds, difficulties, level bands, opponent exclusions,
return-to-fight behavior, completion with summons, reward idempotence and snapshot persistence.
It also loads the empty Arena maps and verifies that eligible opponents' animation definitions
are available from their scene overlays before any actors spawn.
The three scenarios in `tests/scenarios/arena/` exercise dialogue, spawning, combat completion,
reward collection and a fresh challenge on the next visit through the runtime.
