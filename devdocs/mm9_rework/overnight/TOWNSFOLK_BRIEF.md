# MM9 townsfolk and unique humanoids: batch brief (2026-11-01, user request)

The user asked for 15 more MM9 actors: 10 peasant (townsfolk) bodies and 5 unique humanoids, **at most 5 agents at a time**.
Every agent is the worker for one body. [RUN2_COMMON.md](RUN2_COMMON.md) still binds you (git, installs, leases, regression,
safe deletes, reading your own sheets, the final report), except where this brief overrides it.

## Budget (overrides RUN2_COMMON's stop line)
- User, 2026-11-01: this batch may spend **1000 Meshy credits** in total. The backup balance was 3740 when the user decided, so the
  **new floor is 2740**: before EVERY paid job run `python3 tools/creature_meshy.py balance`; if the backup balance is <= 2740,
  submit nothing.
- At most **60 credits per body**. Prefer fewer: Smart Topology 5 + one 4K retexture 10 is the expected cost.
- Codex images (HD masters, step 0) only through `level_generation/creatures/claude_shared/codex_slot.sh`.

## Bodies, in wave order
Source models and skins are in `mm9/extracted/MODELS/MODELS` and `mm9/extracted/SKINS/SKINS`; MM9's own table
`mm9/extracted/DATA/DATA/MONSTERS.txt` maps each townsfolk row (column 1) to its model and skin. Placement counts are from the
rebuilt MM9 maps (`assets_dev/worlds/mm9/maps/*.raw_objects.yml`, DAT names `Commoner<Race><Sex><A|B>`).

| Wave | Project | MM9 model | Rows (MONSTERS.txt) / skins | Placed |
|---|---|---|---|---|
| 1 | `mm9_peasantm2_claude` | PeasantM2.abc | 44 Human1 MaleA B (M2b), 50 Human2 MaleA A (M2a); other M2 skins c/d | ~98 |
| 1 | `mm9_peasantm1_claude` | PeasantM1.abc | 43 Human1 MaleA A (M1a); skins M1b/c | 67 |
| 1 | `mm9_peasantm1d_claude` | PeasantM1d.abc | 22 Elf MaleA A (M1c) | 53 |
| 1 | `mm9_peasantf8_claude` | PeasantF8.abc | 15/16 Elf FemaleA A/B (F8b/F8a) | 38 |
| 1 | `mm9_peasantm7_claude` | PeasantM7.abc | 51 Human2 MaleA B (M7b) | 34 |
| 2 | `mm9_peasanthom1_claude` | PeasantHOM1.ABC | 57 Half-Orc Male A (HOM1a; HOM1b) | 30 |
| 2 | `mm9_peasantf1_claude` | PeasantF1.abc | 29 Human1 FemaleA A (F1b) | 23 |
| 2 | `mm9_peasantf5_claude` | PeasantF5.abc | 36 Human2 FemaleA A (F5b) | 13 |
| 2 | `mm9_peasantdm1_claude` | PeasantDM1.abc | 8 Dwarf MaleA A (DM1a) | 11 |
| 2 | `mm9_peasantdm2_claude` | PeasantDM2.abc | 9 Dwarf MaleA B (DM2a) | 10 |
| 3 | `mm9_kira_claude` | KIRA.abc (+ KIRASHIELD) | unique; skin KIRAPLATE | 9 |
| 3 | `mm9_bjarni_claude` | BJARNI.abc | unique | 7 |
| 3 | `mm9_tryggva_claude` | TRYGGVA.abc | unique | 5 |
| 3 | `mm9_sven_claude` | SVEN.abc (SVEN_ARG variant exists) | unique | 4 |
| 3 | `mm9_markel_claude` | MARKEL.abc | unique | 4 |

Every other skin of the same model is a colour tier of that body (one shared texture set, region mask, ramps), per the
creature texture rules. Check every row of MONSTERS.txt that names your model, not only the ones above.

## Route
- Read fully: [Claude humanoid NPC playbook](../../../level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md) (incl. its
  "Arm and hand gate"), [HD master references](../../../level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md) (step 0: five
  Codex HD masters from renders of the MM9 model with its skin, never the native renders sent to Meshy),
  [creature textures](../../../level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md),
  [texture quality pass](../../../level_generation/creatures/claude_shared/TEXTURE_QUALITY_PASS.md),
  `level_generation/creatures/claude_shared/MM9_HUMANOID_BRIEF.md`.
- MM9 skeleton and MM9 clips, never Mixamo. The peasant bodies share MM9's townsfolk skeletons and clip libraries (PLAN.md
  "NPCs: shared base rigs": human male 45 joints with `peasantmale` 43 clips and `peasantwork` 18; human female 73 joints with
  `peasantfemale` 20; dwarf male/female with `peasantmaledwarf` 21 / `peasantfemaledwarf` 10; half-orc male/female). One retarget
  per shared skeleton covers all its bodies: reuse what a sibling project already solved.
- **Reference projects:** `mm9_annud_claude` (ShopkeeperHuman2MaleA on the PeasantMale body and clip library: carries only the
  clips its MM9 scripts play, sleeve linings, hand rest; bound as `MM9 54 Shopkeeper`) and `mm9_forad_claude`; `mm9_honkmale_claude`
  / `mm9_honkfemale_claude`, `mm9_njam_claude` (Codex head repaint by landmarks), `mm9_yrsa_claude` (female). Read their READMEs.
- Clips: the MM9 roles (Standing, Walking, Running, Fidget, Hit, Death, Dead, Cower...) plus the library clips the body's MM9
  scripts actually play (check its DAT objects' `ScriptName`s and NPCbase.scr, as Annud did). The user's earlier decision for
  Annud/Forad: carry only the library clips the scripts use.
- `clips_mm9.py`: the soft line `np.sign(off) * np.maximum(np.abs(off) - 0.004, 0.0) * k`, never the hard 4 mm cut.

## Binding
Townsfolk rows draw today as MM6-MM8 stand-ins through `tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv`
(MM9 row -> legacy actor id). Follow how Annud became `MM9 54 Shopkeeper`: an MM9 descriptor per row (world data tables in
`assets_dev/worlds/mm9/data_tables/`, table generator) and the stand-in replaced for your rows. `actors.yml` and the table generator
only under the flock `level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock` (re-read inside the lock; other agents
edit it too). If the binding needs import-tool changes beyond your rows, install the model, write the binding plan in your README
and status file, and report it instead of changing shared import code.

## Ownership and records
- Lease: `python3 tools/creature_workspace.py claim --project level_generation/creatures/<project> --identity mm9:<body>
  --owner <your name> --budget 60`; release at the end.
- Status file `devdocs/mm9_rework/overnight/status/townsfolk_<body>.md`, kept current. Do not edit the overview page or the ledger:
  the orchestrator does.
- At most 2 viewer shot scripts at once, no Chrome left running. Kill only literal PIDs you started.
- Final report: what changed, credits spent, gates, sheets read (absolute paths), what to look at, what you did not check.

## Lessons from wave 1 (orchestrator, 2026-11-01 evening)
- **Map placement is the orchestrator's.** The rebuilt maps place townsfolk with the legacy stand-in ids through
  `transcode_mm9_dat_to_odm.py` (`build_mm9_npc_actor_lines`), so a new descriptor alone does not show in game (Annud's row 54
  neither). Stop at: model installed, `MM9 <row> <role>` descriptors in `actors.yml`, your rows in
  `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated, binding test PASS. Do not change the transcoder or
  regenerate maps; one switch for every row happens after the batch (see `mm9_peasantm1d_claude/README.md`, "Binding plan").
- **Fringe and hairline edge.** PeasantM1d and Ebora both shipped a pale jagged band where the fringe meets the brow. Look
  at the face close-up for it on every tier and fix it (head paint or hair mask) before you install.
- **Sleeves and hands (user, PeasantM7: "hands sticking through the sleeves").** The grafted hand's forearm piece is shaped to the
  cuff opening and pokes out where the sleeve narrows; Meshy also paints skin wedges on cuff cloth. Run
  `mm9_peasantm7_claude/scripts/sleeve_tuck.py`, `sleeve_paint_fix.py` and the gate `sleeve_poke_gate.py` (0 mm in every clip).
  Hands are one clean skin colour with natural nails (`hand_clean.py`): never copy face stubble/lip variation onto them.
- **Eyes and brows (user, PeasantM1: "looks like he has 2 eyebrows? and like weird eye area?").** No light outlined band between
  brows and eyes, no second brow line, eyes open with visible irises from party height, no heavy red rims.
