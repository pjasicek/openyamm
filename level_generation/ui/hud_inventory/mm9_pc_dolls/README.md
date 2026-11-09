# MM9 PC paperdolls: head graft — pilot 2026-11-06

MM6–MM8 give every playable character its own doll body (`character_data.txt`: 77 rows, 77 `pcNNbod` bitmaps with
the head painted in, 71 distinct hand-layer sets), but only a handful of poses: the **doll type** (0 male, 1 female,
2 minotaur, 3 troll, 4 dwarf, 5 dragon). Equipment art is one variant per doll type (`item…v1`–`v5`, chosen in
`GameplayScreenRuntime::resolveEquippedItemHudTextureName`, placed by per-type offsets), and bodies of one type
differ by build and costume (75–95 % silhouette overlap below the neck). So an MM9 character does not need a new
body: it borrows an existing body of its doll type and skin, and only the head is replaced.

## Method

`dolls.py` with `dolls.json` (per character: donor body and row, head box, neck seam, new body name):

1. `prepare`: crops the donor's head-and-shoulders box, enlarges it 4×, builds an identity strip from the
   character's new portrait family (`../mm9_pc_portraits/`, frames 01, 19, 26, 28) and writes a Codex brief that
   repaints only the head and neck above the collar.
2. Codex image generation (`run.sh`, retries transient errors).
3. `extract`: registers the result to the donor on the body below the seam (scale and shift search), blends the
   new head in over a 6 px band at the neck and copies the donor rows below that band unchanged, so the body,
   hand layers, offsets and doll type are the donor's to the pixel (`report.json`: `body_below_seam_identical`).
   Before blending, the new head's skin is moved onto the donor head's skin colour (Lab mean and spread of
   skin-coloured pixels; the donor head was rendered under the same light as the body), and non-skin pixels (hair,
   eyes) get `skin_match_other` (default 0.15) of that shift. Without it the generated neck was a cooler, browner
   tan than the native body's warm salmon skin and the seam showed (user review, 2026-11-06).
   Writes `<body_asset>.png`, `head_compare.png`, `neck_compare.png` (donor | new | portrait) and, through
   `tools/mm9_import_discovery/render_paperdoll_equipment_preview.py` with the new body under the donor's name,
   `equipment_donor.png` / `equipment_new.png` (full helm, citizen hat, cloak, chainmail).

## Pilot PC03

Donor `pc07bod` (row 7, type 0), seam at y 92 of the 272×272 head box. One Codex run, which regenerated once by
itself (`raw_rejected.png`).
- **Registration:** error 6.4, scale 0.985, offset (−1, −1). The body below the seam is identical to the donor's.
- **Head:** matches the portrait family (wavy brown hair, blue eyes). The first composite's skin was cooler and
  browner than the body (head RGB 118, 82, 67 against the donor's 136, 79, 64); the skin transfer fixed the seam.
  It is a little more frontal than the donor's head, and crisper than the soft native body.
- **Equipment:** the full helm hides the new head completely, and the hat sits as on the donor with a little hair
  under the brim. The cloak and chainmail fit exactly as on the donor (`pc03/equipment_compare.png`).

## Batch and install (2026-11-06)

All 20 MM9 PCs, donors in `dolls.json` (overview `dolls_overview.png`, helm and chainmail on every doll
`equipment_overview.png`). Changes after the pilot:
- **Registration:** Codex returns a square image and recomposes tall crops (the 166 px female and 226 px dwarf
  bodies), so `register` searches the scale widely and template-matches the donor's body below the seam (OpenCV:
  run `dolls.py` with a Python that has `cv2`, e.g. the scratch venv of the portrait verification).
- **Head mask:** above the seam, generated pixels replace the donor's only where the new head differs from the donor
  (filled, feathered difference mask); shoulders, arms and clothes Codex copied keep the donor's pixels. This removed
  hard cuts through long hair and tone steps on the shoulders. Seams sit below the donor's hair, beard or hood
  (`seams.png`), band 24 px.
- **Skin target:** the donor's skin just below the seam, or its head skin where there is little skin there.
- **Donors:** PC11 moved from the red dark-elf body pc19 to pc03. PC23 moved from pc29 to pc27: row 29 is an unused
  original row whose female-shaped lich body has male equipment offsets (helms float beside the head).

`install.py` installed the 20 families (1120 frames), the 20 bodies `9pcNNbod`, NPC pictures `npc91NN` (Adventurer's
Guild faces) into `assets_dev/engine/icons_x2/` and `character_data.txt` rows **9001–9024** (9000 + PC number; MMerge
rulesets append their own rows from 78, MAW's Lich Troll 2 is 78). Each row is its donor row with the new body, face
prefix, NPC picture, race (half-orcs Goblin 8, liches 6) and a note; liches are not available at start.
`install_receipt.json` lists every file. The cooker `tools/cook_ui_textures.py` only matches face sets whose prefix
starts with a letter, so `9pc` families (like MM7's `7pc`) load as PNGs, as before.

In game (`--isolated` run, `doll 1 portrait <id>` / `doll 1 equip`): portraits on the basebar and the dolls in the
inventory screen with helm and chainmail for PC03, PC04, PC06, PC09, PC14, PC19, PC24; the MAW ruleset scenario
`tests/scenarios/rulesets/combat_log.yml` passes after the renumbering.
