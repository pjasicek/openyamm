# Discord triage handoff (2026-11-07)

For the next agent working on reported bugs and requests. Read [README.md](README.md) first (schema, statuses,
running a check); this file is the state of the work.

## State

- The whole Discord server is triaged up to 2026-11-07 ~10:00: all 4392 messages of every channel, checkpoint in
  [state.yml](state.yml). The next check reads only newer messages (`/discord-check` or "discord check").
- [ledger.yml](ledger.yml) holds 448 items: 202 done, 47 open (28 bugs, 19 accepted features), 112 needs-decision,
  38 needs-info, 32 not-a-bug, 12 duplicate, 4 declined, 1 cannot-reproduce. [STATUS.md](STATUS.md) is the overview.
- Every bug that was `new` (118) was investigated by reading code and data, without builds or runs: verdict, root
  cause with file:line, effort and recommendation are in each item's `notes` and in
  [INVESTIGATION_2026-11-07.md](INVESTIGATION_2026-11-07.md). The 15 bugs that were `open` before keep their triage
  notes (confirmed by the triage agents or by the owner on Discord).
- Some `done` items rest on uncommitted working-tree fixes (no `commit`, resolution says "working tree"). Give them
  the commit once that work is committed.
- Nothing of this is committed: `devdocs/discord_triage/`, `tools/discord_triage/`, `.agents/skills/discord-check/`,
  the `.claude/skills/discord-check` link and the AGENTS.md pointer are untracked or unstaged changes.

## Open questions for the user

1. **The 13 `decide` bugs and 3 fixes that need a yes**, with recommendations (also in the investigation table):
   - fix: OY-265 Harmondale accuracy well (one missing Clickable flag, also broken in the original), OY-364 make the
     Setag tower villain hostile (map overlay), OY-171 loot bags over water move to land, OY-283 hide the Water Walk
     icon while levitating, OY-244 / OY-249 clearer MAW texts (wording only), OY-23 install the finished v4 ponytail
     model after the hand gate;
   - decline or close: OY-14 ooze size, OY-317 dragon gauntlets (MMerge rule), OY-368 portrait theft frame
     (original data), OY-29 apprentice mage motion (user-approved unless the reporter names a clip);
   - check first: OY-132 ogre ledge (re-test 1.21), OY-24 dismiss sound (does the original play one?);
   - fixes needing a yes: OY-350 Shoals (recommend the original: no casting, free vertical movement, no fall
     damage), OY-302 Ice Blast (recommend keeping today's fan and closing), OY-165 dragon free skills (confirm the
     count with the MAW author).
2. **The 100 feature/feedback items in `needs-decision`**, each with a one-line recommendation in `notes`. The user
   may answer in bulk ("accept OY-59, decline OY-40"); record accept as `open`, decline as `declined` with the date.
   A click-through decision page was offered but not built.
3. **38 needs-info items**: the bot cannot post. Someone must ask the reporters; each item's notes say what to ask
   (mostly "still on 1.21?" plus a save, map or screenshot). A single Discord message covering them was offered.

## Suggested fix order

1. Done in the working tree on 2026-11-07 (not committed): OY-274, OY-177, OY-189, OY-190, OY-141, OY-337, OY-309,
   OY-199, OY-345, OY-182, OY-304, OY-303 and OY-176; each item's `resolution` says how and which test covers it.
2. Done in the working tree later on 2026-11-07: OY-154, OY-192, OY-245, OY-257, OY-216, OY-364, OY-165, OY-240,
   OY-344, OY-350, OY-128 (Barracks only), OY-168, OY-349, OY-137, OY-392, OY-231 (7out02 re-baked). Still open, with
   the reason in their notes: OY-155 (beams need reversed-Z), OY-372, OY-218 and OY-426 (held for the user), OY-412,
   OY-361. Then the small fixes: OY-161, 340, 346, 264, 159, 362, 172, 219, 220, 308, 250, 438, 428, 181, 266, 339;
   OY-202 (fruit bowl) needs a decoration-state save migration first (its notes).
3. The previously open bugs: OY-349 (characters never age), OY-128 and OY-168 (Arcomage Barracks and zero
   production), OY-372 (MM9 Throwing in MM6-MM8), OY-426 (Harpy Witch Mass Curse), OY-390 (rain under roofs),
   OY-415 (outdoor pathing round hills), OY-412 (Peasant class change), and the small text/UI ones.
4. Rendering (OY-231 bell tower bake, OY-137 dark probes, OY-155 indoor depth precision) and the ten model touch-ups
   (OY-3..9, 27..31) as their own tasks under the creature playbooks.

Verdicts are from code reading; confirm each bug (scenario, unit test or game run) before or while fixing it.

## Known interaction

`tests/scenarios/rulesets/maw_bow_disabled.yml` (step 20) and `tests/scenarios/turn_based/single_press_one_member.yml`
(step 12) failed on 2026-11-07 because headless scenarios read the local `settings.ini`, where `smart_click=true` had
been turned on: Smart Click ignores an Attack bound to the left button unless the button itself is down, and scenarios
press the action alone. Scenarios now turn Smart Click off (ScenarioRuntimeDriver); OY-354, OY-376 and OY-434 stand.

## When fixing an item

- Put `OY-<n>` in the commit message; the next check closes it. Updating the ledger yourself is welcome but not
  required: set `status: done`, `commit`, `resolution`, `updated`, then run
  `python3 tools/discord_triage/discord_triage.py check` (validates and rewrites STATUS.md).
- Do not fix bugs during a check unless asked, never post to Discord, and keep author names and quotes out of the
  committed files.
