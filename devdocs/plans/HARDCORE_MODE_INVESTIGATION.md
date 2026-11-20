# Hardcore mode and save integrity

Status: investigation only (2026-10-16). Nothing is implemented. Revisit before adding a hardcore (permadeath) mode.

Goal: a mode where party death ends the run, made as hard as practical to defeat by restoring a copied save, given
that OpenYAMM is offline and open source (GPL-3.0-or-later).

## Ground truth

- An offline game cannot prevent save restoration. The player controls the disk, and the public source lets anyone
  rebuild the game without the check.
- Secrets in the repository (keys, seeds) are public. Obfuscation, custom virtual machines and anti-debugging add
  maintenance cost and do not stop a user who builds from source; skip them.
- Realistic aim: defeat the casual cheats, and show honestly whether a run is unbroken, instead of pretending to
  enforce it.

## Threat tiers

| Cheat | Frequency | Defence |
|---|---|---|
| Kill the process (Alt-F4) before dying, reload | Very common | Single slot, live-run marker, immediate tombstone |
| Copy the save out and paste it back | Common | Out-of-folder ledger with generation counter |
| Back up save folder and ledger together | Rare | Ledger copies in several locations (raises effort only) |
| Disk/VM snapshot, cloud-sync rollback | Very rare | Not preventable offline |
| Patch or rebuild the binary | Trivial | Not preventable |

## Recommended offline design

1. **Roguelike save discipline** (NetHack/Diablo style).
   - One save per hardcore run; no manual saves or slots. Save on quit and at checkpoints such as map transitions.
   - On load, the ledger marks the run *live*. A clean save-and-quit marks it *resumable*. A killed process leaves it
     *live*, so the next load is flagged as an unclean exit.
   - On party wipe, write the tombstone and fsync **before** the death animation or screen.
2. **Ledger outside the save folder.**
   - Per run: random run id, last save generation (monotonic), state (live/resumable/dead), hash of the last save.
   - On load, reject a save whose generation is older than the ledger's, whose hash mismatches, or whose run is dead.
   - Keep copies in several unrelated places (per-user config directory, a second hidden location, the registry on
     Windows, app-private storage on Android). The newest generation and any tombstone win.
3. **Downgrade instead of deleting.** A failed check turns the run into a normal save labelled, for example,
   "Hardcore — broken (stale save restored)" or "(unclean exit)". Show run status on the character/load screen
   ("Hardcore — unbroken, 0 recoveries"). Dead runs become a read-only "Fallen" memorial rather than a deleted file.
   This avoids punishing crashes, disk failures and reinstalls.
4. **Persist RNG state in the save.** Reloading an old save then replays the same rolls, which removes free
   re-rolls. Gameplay code already passes `std::mt19937` and seeds around (`game/gameplay/GameMechanics.h`,
   `ChestRuntime`); check whether that state survives save/load or is reseeded.
5. **Hash chain in the save.** Each save records a hash of the previous one and an append-only event history (run
   start, map changes, recoveries, death). Without a secret key this proves nothing to a determined cheater, but it
   makes casual hex edits break the history and feeds the status display.

Estimated cost of 1–3 (plus 4 if cheap): a few hundred lines around `game/maps/SaveGame.*` and
`game/ui/screens/LoadGameScreen.cpp`. Covers roughly 95 % of real attempts.

## Server-verified replays (only if leaderboards are wanted)

The game still runs locally. The client records the run seed plus every input stamped with its simulation tick
(a few KB per hour) and uploads it with the exact game version. The server re-runs the same engine headless and
compares state hashes at checkpoints and at the end. Precedent: TrackMania, StarCraft/Factorio replays, speedrun
verification. OpenYAMM's headless runner (`--headless-run-scenario`) is the natural base for a verifier.

### Determinism requirement

Identical inputs must give bit-identical results on every machine and build. Typical breakers:

- Gameplay driven by variable frame delta instead of a fixed tick.
- Floating-point differences across compilers, CPUs, fast-math/SIMD paths; x86 versus ARM (Android).
- Iterating `unordered_map` or pointer-ordered containers where order affects gameplay.
- Wall-clock time, thread races, audio or animation completion feeding back into gameplay.
- Any RNG not derived from the run's seeded state.

Replays are tied to the build that recorded them, so the server must keep every released version.
Cheap first probe: run the same headless scenario twice, and on two machines, and compare per-tick state hashes.

### What verification proves, by level

Offline replay verification proves a run is **legal**, not that it was played without rewinding. A cheater can
save-scum in a modified build and submit the stitched winning input stream; with a known seed they can also simulate
ahead to preview dice. Stronger guarantees need connectivity:

| Level | Server role | Stops | Online |
|---|---|---|---|
| 1. Upload replay at end | Re-simulate | Edited saves, impossible stats | Once |
| 2. Streamed append-only log | Accept input chunks; never accept an earlier branch | Rollback / save-scumming | Mostly, with grace periods |
| 3. Server-held randomness | Release seed material only after the preceding inputs are committed | Simulating ahead | Constantly |
| 4. Server-authoritative simulation | Run the world; client sends input and renders | Practically everything | Constantly, plus hosting |

Level 4 is the Diablo 2 Battle.net hardcore model.

### Saves within verified runs

- A save is "state at tick N of this run"; the replay log is segmented across sessions.
- The server never starts from the client's save file. It continues from its own verified state (kept as
  server-side checkpoint snapshots so long campaigns are not re-simulated from the start).
- Normal mode: loading an older save creates a branch; verify the root-to-branch path of the submitted run.
- Hardcore: accept a segment only if its parent is the latest known head.
- Save/load must not desynchronise the client from the server. Either make saves bit-exact for all gameplay state
  (RNG, AI/spell timers, projectiles, animation phases, float positions), or record "save/load at tick N" in the log
  and have the server perform the same serialise/deserialise round trip, so any loss is reproduced identically.
  Map transitions have the same requirement.
- A single playthrough without saves is the trivial one-segment case; practical only for short runs (arena,
  dungeon challenges), not a full campaign.

## Recommendation

Implement the offline design (1–3, plus 4) and present hardcore as an honour system with an "unbroken" badge.
Pursue engine determinism independently: it pays off in replays for bug reports, reproducible regression tests and
desync checks, and keeps server verification (levels 1–2) open for later.
