# Monster target selection and party order

Investigated 2026-10-16 after a report that MM7 sharks always attack the leftmost member until that member falls.

## Result

**The inspected MM8 and MM7 default selectors have no party-position weight.** They collect eligible party slots
in order, then return `eligible[rand() % count]`. They do not test the first member and immediately select them.
Ordinary melee and projectile callers reach this selection; neither traced path replaces its result with slot zero.

This establishes the static rule in these executable files. It does not reproduce the reported GIF or establish
what that player's loaded executable, patches, monster data, condition flags or RNG state were doing.

## Inputs and method

| Input | SHA-256 | Provenance |
| --- | --- | --- |
| `mm8_orig/MM8-Rel.exe` | `5326d56459ca74126447bcfd07a8cc85a419663e2281500f0f043f13ffe77a0b` | [Verified GOG-distribution executable](GOG_INSTALLER_VERIFICATION.md) |
| `../reference/Misc-MM8Patch-2.5.7/MMPatches/Install/MM7patch/Files7/mm7.exe` | `673c9805ab4a7b7440aa1be937d0a508ec029f94c7e42be750673a0f977c678c` | Local GrayFace patch installer payload; not authenticated here as original retail/GOG MM7 |

Rizin 0.10.0, repository build `third_party/rizin/build/binrz/rizin/rizin`, x86 disassembler. No decompiler or
emulator was needed. Both PEs use preferred image base `0x400000`; all addresses below are preferred VAs
(subtract `0x400000` for RVAs). Inputs were opened read-only and their hashes rechecked afterward.

The local MMExtension `ChooseTargetPlayer` declaration supplied the MM7 address and a patched-MM8 lead.
That patched-MM8 address, `0x425203`, is **not** the original MM8 selector. A byte search for the preference-field
comparison located the original at `0x425ac2`; its whole control flow and callers were inspected independently.

## MM8 binary evidence

| Address | Observation |
| --- | --- |
| `0x425ac2` | Selector entry; monster pointer is the stack argument `[ebp+8]`; returns zero-based party slot in EAX, `ret 4`. |
| `0x425acf` / `0x425ad9` | Tests 32-bit monster preference mask at `monster+0x88`; zero branches to the default selection. |
| `0x425c66` | Default branch clears candidate count EBX; ESI is the zero-based party slot. |
| `0x425c73` / `0x425c79` | Iterates slots, obtains each character through `0x402741`. Party size is `[0xb7c960]`. |
| `0x425c7e`–`0x425cac` | Rejects any nonzero 64-bit condition timestamp at character offsets `0x60`, `0x68`, `0x70`, `0x78`, `0x80`. |
| `0x425cae`–`0x425cb1` | Appends the slot to a contiguous stack array and increments count once. |
| `0x425cc1`–`0x425cc9` | Calls RNG `0x4dc832`, performs signed `idiv ebx`, uses remainder EDX to load `[ebp+edx*4-0x28]`. |
| `0x425ccf` | Returns zero only if no candidates exist. This is not a preference for a living first member. |

Reference names for condition indices 12–16 are **Paralyzed, Unconscious, Dead, Stoned, Eradicated**.
The two halves of each timestamp are ORed, so either half being nonzero excludes the member.
Sleep and recovery time are not exclusion tests here. The default branch reads no armor, class, sex, health total,
active-character selection or party-position multiplier.

The nonzero-preference branch checks class and sex before applying the same condition exclusions. It also ends
with an RNG remainder selection (`0x425c5b`–`0x425c64`). Its candidate count and write cursor reset per enabled
preference bit (`0x425bc7`, `0x425bcc`), so do not substitute modern OpenEnroth's accumulated-preference algorithm
for this executable when studying combinations of preference flags. This investigation does not propose changing
OpenYAMM's preference policy.

### Callers

- Melee evaluation `0x4373e5`: after range/LOS checks, calls the selector at `0x437526`, pushes its EAX result at
  `0x437532`, then calls damage routine `0x438625` at `0x437540`. The damage routine resolves that party slot at
  `0x438648`–`0x43865e`, before its hit/miss check at `0x438678`.
- Projectile collision `0x438f98`: pushes target `-1` at `0x43900a`, calls the same damage routine at `0x439013`.
  For a monster-owned projectile, `0x438a83` tests for `-1`, calls the selector at `0x438a8f`, and stores its result
  at `0x438a94`. There is no first-member override on this route.
- Area damage is a separate case: `0x43770f`–`0x43775b` iterates party slots and applies damage to eligible members;
  it is not choosing one member at random. Special monster spell paths also exist and are outside the default rule.

## MM7 binary cross-check

| Address | Observation |
| --- | --- |
| `0x426dc7` | Selector entry. Preference mask is `monster+0x80`; zero branches at `0x426de9` to the default path. |
| `0x426fa6`–`0x426fe3` | Visits slots 0–3 via pointer table `0xa74f48`, excludes the same five conditions, appends each eligible slot once. |
| `0x426fd7` | Writes candidate slot with `mov [ebp+ebx*4-0x100], esi`; EBX is candidate count. |
| `0x426fe9`–`0x426ff1` | Calls RNG `0x4caac2`, divides by candidate count, loads `[ebp+edx*4-0x100]`. |
| `0x426ffa` | Returns zero if no candidates exist. |
| `0x4390ba` / `0x4390c6` / `0x4390d4` | Melee caller selects a slot, pushes it, calls damage routine `0x439fee`. |
| `0x43aa11` / `0x43aa1c` | Projectile caller pushes `-1`, then calls the damage routine. |
| `0x43a458`–`0x43a469` | Monster-projectile damage checks `-1`, calls selector at `0x43a464`, stores the returned slot. |

This binary also has class/sex/race preferences. Its preference-loop bookkeeping differs from the current
OpenEnroth reconstruction; the default zero-mask path above was checked directly. The supplied report's claim
that its sharks have no preferences was not independently verified against that player's monster records.

## RNG and chances

MM8 `0x4dc832` and MM7 `0x4caac2` both implement the CRT generator:

```text
state = (state * 214013 + 2531011) modulo 2^32
rand  = (state >> 16) & 32767
```

The result is nonnegative, making the signed division remainder a valid candidate-array index.
The observed seed routines are called from initialization using `GetTickCount`: MM8 `0x464985`–`0x46498c`
and MM7 `0x465258`–`0x46525f`. The selectors do not reseed or maintain a preferred/previous target.

Assuming uniformly distributed 15-bit RNG outputs, exact candidate chances are:

| Eligible count | Candidate counts across all 32,768 RNG values | Chance |
| ---: | --- | --- |
| 1 | 32768 | 100% |
| 2 | 16384, 16384 | 50% each |
| 3 | 10923, 10923, 10922 | 33.33435%, 33.33435%, 33.33130% |
| 4 | 8192, 8192, 8192, 8192 | 25% each |
| 5 | 6554, 6554, 6554, 6553, 6553 | 20.00122% for the first three; 19.99817% for the last two |

Thus there is a tiny modulo bias for three/five candidates, but no four-member bias and nothing approaching
exclusive attacks on the first member. These are distributions over RNG values, not measured independent attack
frequencies: the game shares its deterministic RNG with other operations.

For MM7 with all four eligible and no preference match, the default is 25% per slot. If slot 0 becomes ineligible,
the list becomes `[1, 2, 3]`, with approximately one third for each survivor. This explains redistribution after
someone falls, but not the reported exclusive targeting before that point.

Visible HP loss is also not a target-selection log: hit/miss is checked after selecting the member. Armor can
affect which selected attacks visibly land; [GrayFace's mechanics reference](https://grayface.github.io/mm/mechanics/#chance-to-hit)
documents that separate hit calculation. This is a possible observation confound, not a diagnosis of the GIF.

## Follow-up: seeding, save loading and repeatability

Investigated 2026-10-17 against the same hashes. **No per-attack, per-frame or save-load reseeding call was found.**
Both executable files implement `srand(GetTickCount())` in their application initialization:

| Operation | MM7 | Original MM8 |
| --- | --- | --- |
| Get system uptime | `0x465258` | `0x464985` |
| Pass result to `srand` | `0x46525e`–`0x46525f` | `0x46498b`–`0x46498c` |
| `srand` entry | `0x4caab5` | `0x4dc825` |
| Write seed to `[TLS data + 0x14]` | `0x4caabe` | `0x4dc82e` |
| CRT per-thread data getter | `0x4cecd2` | `0x4e09a2` |
| CRT initial seed of 1 | `0x4cecca` | `0x4e099a` |
| `rand` writes advanced state | `0x4caad6` | `0x4dc846` |

`GetTickCount` supplies milliseconds since system startup, not game time or the saved game's timestamp. Its
timer resolution is typically 10–16 ms, according to [Microsoft's API documentation](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount).
That granularity does not reset the RNG for each attack: the timer is read at the observed startup seed site.
Even a zero seed does not stick at zero, because the update adds the nonzero constant `2531011`.

Rizin finds one incoming call to each `srand`, both from application initialization. An independent scan of the
executable sections for relative CALL/JMP instructions agrees: MM7 `0x46525f`, MM8 `0x46498c` only. No literal
absolute pointer to either `srand` was found in either file. This strengthens the static evidence; it cannot exclude
computed calls or code injected by a DLL.

Each CRT getter calls `TlsGetValue`, allocates/initializes the data only if absent, and otherwise returns the
existing per-thread block. The default seed of 1 is set during creation, **not on every `rand()` call**. The
startup `srand` overwrites that default on the calling thread. The 20 direct getter call sites in each binary were
checked: the seed/read/update sites above are distinct from unrelated CRT error, string-token and exception fields.
No savegame reader appears among those direct getter callers. Thread migration and runtime hooks were not tested.

The normal save/load entry points are MM7 `0x45eec3` / `0x45f4a2` and MM8 `0x45ddb0` / `0x45e3d2`.
They contain no direct call/jump to the seed routine, CRT data getter/initializer or application initialization.
In particular, `party.bin` restores a fixed global region, not the dynamically allocated CRT thread-data block:

- MM7: reads `0x16238` bytes into `0xacce38` at `0x45f0a6`–`0x45f0b0`; save writes the same region at
  `0x45f7d2`–`0x45f7e2`.
- MM8: reads `0x92074` bytes into `0xb20d90` at `0x45deda`–`0x45dee4`; save writes the same region at
  `0x45e656`–`0x45e668`.

Thus simply restoring party state does not restore this RNG. The checked native paths give no evidence that
reloading a save replays a saved random sequence. A process/VM snapshot or a mod that explicitly restores the RNG
would be a different case. MMExtension exposes writable `Game.RandSeed` in its local `Scripts/Structs/00 structs.lua`
at line 712; its existence is not evidence that the reported installation uses it.

### Generator checks and what repeatability would mean

The recovered generator is deterministic. Identical state plus the same sequence of calls reproduces the same
results, consistent with [Microsoft's `srand` contract](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/srand?view=msvc-170).
Identical party/save contents alone do not establish those conditions.

For four candidates, `rand() % 4` uses internal state bits 16–17. Those bits depend only on the low 18 state bits.
An exhaustive check visited all 262,144 such states exactly once before returning to its start, with 65,536 outputs
for each slot. Consequently no initial seed traps successive calls permanently on slot zero. Seeds separated by
a multiple of `2^18` have the same modulo-four stream if call counts remain identical; other RNG uses can still
change gameplay and therefore subsequent call counts.

The longest identical-slot streak in consecutive calls over that cycle is eight, for every slot. Sampling every
second call produces streaks of up to eleven, again for every slot. Fixed strides 1, 2, 3, 4, 5, 8, 16, 32 and 64
were checked across every resulting cycle; their full-cycle slot counts remain equal. **These are arithmetic
experiments, not a limit or frequency prediction for actual attacks.** Other game code consumes RNG values between
target selections, and its branching can correlate with prior outcomes. Uniform full-cycle counts do not prove
independent targeting in every live encounter.

Minimal reproduction of the exhaustive four-slot cycle check:

```python
state = 0
seen = set()
counts = [0] * 4
for _ in range(1 << 18):
    assert state not in seen
    seen.add(state)
    state = (state * 214013 + 2531011) & ((1 << 18) - 1)
    counts[state >> 16] += 1
assert state == 0 and counts == [65536] * 4
```

Raw branch scans, TLS caller windows, save/load disassemblies and arithmetic results are retained under
`work/party_targeting/`, including `rng-raw-branch-scan.json` and `rng-cycle-check.json`.

**Interpretation:** the common bug of calling `srand` repeatedly with the same timestamp is not supported by these
binaries. The report may still describe a reproducible runtime issue. To distinguish it, log the RNG state before
selection, returned random value, candidate list, selected slot and subsequent hit/miss in that installation, and
compare ordinary reloads with full process restarts. The earlier 25% statement describes the default selector's
distribution, not proof that the reported live sequence is impossible.

## Follow-up: resistance and visible hurt reactions

Checked 2026-10-17 in the same fingerprinted MM7 installer executable. Ordinary resistance performs up to four
successive integer halvings, rather than a separate full-resist roll. However, **there is no minimum-one clamp**:
low damage can round to zero (`10 -> 5 -> 2 -> 1 -> 0`).

- Incoming damage routine `0x48d499`: successful resistance checks apply `sar ..., 1` at `0x48d530`, `0x48d553`,
  `0x48d576` and `0x48d599`. The elemental path returns the resulting integer at `0x48d609`.
- Damage application `0x48dc04`: calls that routine at `0x48dc1a`, subtracts its result from HP at `0x48dc1f`,
  and keeps the final damage amount. `0x48dcb8`–`0x48dcbb` skips the hurt reaction when that amount is zero.
- For a nonzero amount, the routine additionally checks whether the character can act before calling reaction 24
  at `0x48dccd`. Reaction dispatcher `0x4948a9` handles voice and face animation, calling the expression setter at
  `0x494a11`. Thus a selected hit can cause no HP loss and skip the normal hurt voice/portrait reaction.

For positive damage entering this resistance calculation at 16 or more, the four ordinary halvings alone leave
at least 1. Special immunity is distinct: `0x48d4e7`–`0x48d4fd` returns zero for class `0x23` (reference name Lich)
when the selected resistance is at least 200. Neither case diagnoses the attacks or party in the reported GIF.
Other effects such as wake-up and attack recovery are not ruled out when the normal hurt reaction is skipped.

The [mechanics reference](https://grayface.github.io/mm/mechanics/#resistances) describes the four resistance tiers.
It also distinguishes actual spells from elemental monster ranged attacks: the latter can still fail a hit roll.
Do not identify an attack as a spell solely from its appearance.

## Reproduction and limits

Reusable labels/comments: [MM8 annotations](mm8_rel_5326d564_party_targeting.rz),
[MM7 annotations](mm7_673c9805_party_targeting.rz). From the repository root:

```bash
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 -e asm.sub.var=false \
  -i re_mm8/mm8_rel_5326d564_party_targeting.rz \
  -c 'aF @ 0x425ac2;pdf @ 0x425ac2;aF @ 0x4dc832;pdf @ 0x4dc832' \
  re_mm8/mm8_orig/MM8-Rel.exe
third_party/rizin/build/binrz/rizin/rizin -N -q -e scr.color=0 -e asm.sub.var=false \
  -i re_mm8/mm7_673c9805_party_targeting.rz \
  -c 'aF @ 0x426dc7;pdf @ 0x426dc7;aF @ 0x4caac2;pdf @ 0x4caac2' \
  reference/Misc-MM8Patch-2.5.7/MMPatches/Install/MM7patch/Files7/mm7.exe
```

Use `asm.sub.var=false`: variable substitution in this Rizin build can hide the scaled index in the displayed
stack-array load. GNU objdump independently confirmed both default branches' candidate writes and indexed reads.
An exhaustive arithmetic check of all 32,768 RNG values for every nonempty eligibility mask of a four-/five-member
party confirmed the counts above. This checks the recovered formula, not execution of the game itself.

No game was launched, no GIF/save was available for instrumentation, and loaded DLL hooks were not inspected.
To settle the specific report, trace each melee call's preference mask, eligible slots, RNG result and returned
slot in that installation, then distinguish selected targets from successful damage. No gameplay code was changed.
