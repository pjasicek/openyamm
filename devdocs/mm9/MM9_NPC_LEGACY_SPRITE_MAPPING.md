# MM9 NPC Legacy Sprite Mapping

This is a strict MM9-to-MM6/MM7/MM8 replacement catalogue. It does not mix converted MM9 model renders into the
runtime sprite set and does not propose generated replacement art.

The authoritative mapping is:

- `tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv`

The MM9 DAT transcoder consumes this table directly. Recognized MM9 NPC object classes are emitted as normal
OpenYAMM actors using the selected merged MM6-MM8 actor id, so rendering and animation continue through the existing
sprite system. Changing a selection only requires editing this table and regenerating the affected MM9 map.

The generated side-by-side review catalogue is:

- `test_img/mm9_npc_legacy_comparison/index.html`

Each card shows the rendered MM9 reference pose on the left and the selected existing MM6-MM8 standing sprite on the
right, including the merged legacy actor id, actor family, A/B/C rank, confidence, and selection note. The page can be
filtered by MM9 source number, actor/role, legacy id/family, and confidence.

NPC identity and role come from `ACTOR.txt`, while the reference model and skin come from the matching
`MONSTERS.txt` row. Some non-animal `ACTOR.txt` rows use `sheep.abc` as a placeholder and must not be rendered as
sheep.

## Scope

- 137 rows and 136 distinct source numbers exist in the MM9 non-monster inventory.
- The 18 source numbers without a usable MM9 reference model are intentionally excluded.
- All remaining 118 distinct source numbers have exactly one MM6-MM8 replacement.
- The current mapping has 68 high-confidence, 26 medium-confidence, and 24 low-confidence selections.

Low confidence does not mean the entry is unmapped. It means MM6-MM8 has no convincing equivalent, most notably for
children, farm animals, the Wyrdes, Ratatosk, and several unique MM9 characters. The HTML deliberately keeps those
comparisons visible so they can be reassigned to a different existing legacy family after visual review.

## Regeneration

To regenerate an MM9 map with the authoritative replacements, use `regenerate_mm9_maps.sh`. For example:

```bash
tools/mm9_import_discovery/regenerate_mm9_maps.sh --clear-defaults --outdoor BOOTCAMP
```

To regenerate only the visual review catalogue, first generate the source and candidate catalogues, then run:

```bash
python3 tools/mm9_import_discovery/generate_mm9_npc_legacy_comparison_catalog.py
```

The generator rejects missing or extra source numbers, duplicate mapping entries, unknown legacy actor ids, and
missing preview images.
