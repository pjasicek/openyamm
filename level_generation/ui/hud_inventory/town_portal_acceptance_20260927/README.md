# Accepted MM6 Town Portal — 2026-09-27

The user accepted the reviewed MM6 Town Portal map and requested installation into `icons_x2`.
All seven reviewed PNGs are now accepted in the canonical ledger and installed in
`assets_dev/engine/icons_x2/` with lowercase names and 0644 permissions.

| Artwork | Installed files |
| --- | --- |
| Map with the small HOMM2 gargoyle over repaired sharp terrain and the southern Titan | `tpenroth.png` |
| Registered destination highlights | `tpblckshr.png`, `tpfrhvn.png`, `tpmist.png`, `tpsorpig.png`, `tpslvrcv.png`, `tpwhtc.png` |

The installed files are byte-identical to the approved browser artwork. The map remains 1280 × 960
(logical 640 × 480); each hover patch retains its native position and exact x2 canvas. Normal-state crops are
review evidence: the game draws the background directly until a destination is highlighted. MM7/MM8 artwork,
placement tables, YAML, and all other accepted icons are unchanged.

[Open the accepted review](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/).
The previous installation, pre-repair map, original artwork, raw generations, exact prompts, terrain/foreground
layers, and highlight masks remain available in the [restoration workspace](../town_portal_fixup_review/README.md).

## Records

- [accepted.json](accepted.json), [authority.json](authority.json), and `receipts/` bind the explicit approval,
  exact reviewed hashes, prior acceptances, and runtime destinations.
- `accepted/engine/icons_x2/` contains immutable accepted exports. `review_before/` preserves the page, data,
  script, notes, and validation report from immediately before publication.
- [../accepted_icons.json](../accepted_icons.json) is the current index of all 9,920 accepted icons; its hash
  is bound to the canonical ledger at `../checkpoint/state.json`.
- `previous_accepted_index.json` and `checkpoint.before.json` preserve the prior publication, including the
  earlier spellbook and minimap acceptances.
- [installed.json](installed.json) records deployment. [validation.json](validation.json) verifies exact
  installed bytes, sizes, permissions, map crops, unchanged hover borders, and preservation of unrelated records.

Publication used `publish.py --apply`; it does not generate or process images. Preparation scripts now refuse
to overwrite this accepted revision. Future repairs should create a new revision and retain these exports.

For verification or future redeployment from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/town_portal_acceptance_20260927/validate.py
```

The last command audits this publication against its immediately preceding ledger/index. For a later unrelated
acceptance, use the current-index deploy check. Release ZIP packaging is separate.
