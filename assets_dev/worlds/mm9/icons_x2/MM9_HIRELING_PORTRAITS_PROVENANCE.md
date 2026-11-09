# MM9 Hireling Portrait Provenance

`9npc01-01.png` to `9npc15-56.png` (15 families × 56 frames, 118×158 RGBA, installed 2026-11-06 with the user's
approval): MM9's hireling portraits (`mm9/extracted/ART/ART/NPCPORTRAITS/NPC01`–`NPC15`, 18 frames of 60×80 each)
rebuilt as MM6–MM8 portrait families in our 56-slot order, so the shared face animation (conditions, buffs, damage,
talking) works for hirelings as for party members. The family number is the MM9 portrait folder number
(Edina A'Mor = NPC07 = `9npc07-`). The hireling HUD references `9npcNN-01`; there is no `character_data.txt` row, so
these faces never appear in party creation.

Generated with Codex built-in image generation from three inputs per sheet: an accepted MM6–MM8 x2 portrait family as
the framing, lighting and state template, the mapped MM9 frames as identity and expression source, and MM9 frame 01 as
identity master; 28 slots per sheet, two sheets per character plus targeted repairs, real alpha from the generator.
Registration with one head size per family; generated alpha is not edited.

Workspace, per-character records (template, mapping, attempts, repairs, face-landmark verification) and the playbook:
`level_generation/ui/hud_inventory/mm9_pc_portraits/` (`characters.json`, `npcNN/`, `PLAYBOOK.md` section 11,
`overview_hirelings.png`).
